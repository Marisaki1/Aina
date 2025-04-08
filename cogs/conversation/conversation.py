import discord
from discord.ext import commands
import asyncio
import os
import time
import functools
from core.llm import LLMManager
from core.memory import MemoryManager

class Conversation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.llm_manager = None
        self.memory_manager = None
        self.thinking_messages = [
            "Hmm, let me think about that...",
            "Processing your request...",
            "Thinking...",
            "Let me consider that for a moment..."
        ]
        self.active_conversations = set()
        
        # Load managers in the background to avoid blocking bot startup
        self.bot.loop.create_task(self.initialize_systems())
    
    async def initialize_systems(self):
        """Initialize the LLM and memory managers in the background"""
        await self.bot.wait_until_ready()
        try:
            # Initialize memory manager first
            self.memory_manager = MemoryManager()
            print("✅ Memory Manager initialized")
            
            # Initialize LLM manager
            self.llm_manager = LLMManager()
            print("✅ LLM Manager initialized")
            
            # Connect the two systems
            self.llm_manager.set_memory_manager(self.memory_manager)
            
        except Exception as e:
            print(f"❌ Failed to initialize systems: {e}")
    
    def get_conversation_status(self, user_id):
        """Check if a conversation is active for a user"""
        return user_id in self.active_conversations
    
    @commands.command()
    async def chat(self, ctx, *, message=None):
        """Start or continue a conversation with Aina"""
        if message is None:
            embed = discord.Embed(
                title="💬 Chat with Aina",
                description="You can chat with me using the `!chat` command followed by your message.",
                color=discord.Color.purple()
            )
            embed.add_field(name="Example", value="`!chat Hello, how are you today?`", inline=False)
            embed.add_field(name="End Conversation", value="Use `!endchat` to end our conversation", inline=False)
            await ctx.send(embed=embed)
            return
        
        # Check if systems are initialized
        if not self.llm_manager or not self.memory_manager:
            await ctx.send("I'm still warming up. Please try again in a moment.")
            return
            
        # Indicate the bot is "thinking"
        thinking_idx = int(time.time()) % len(self.thinking_messages)
        thinking_message = await ctx.send(self.thinking_messages[thinking_idx])
        
        # Mark this user as having an active conversation
        self.active_conversations.add(ctx.author.id)
        
        # Process in a separate thread to avoid blocking
        try:
            # Create a partial function to call in the executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                functools.partial(
                    self.llm_manager.get_response,
                    ctx.author.id,
                    message,
                    interface_type="discord",
                    context={"channel": ctx.channel.name if hasattr(ctx.channel, "name") else "DM"}
                )
            )
            
            # Create response embed
            embed = discord.Embed(
                description=response,
                color=discord.Color.purple()
            )
            embed.set_author(name="Aina", icon_url=self.bot.user.display_avatar.url)
            embed.set_footer(text="Reply with !chat to continue the conversation")
            
            # Delete the thinking message and send the response
            await thinking_message.delete()
            await ctx.send(embed=embed)
            
            # Store user information if we learn something new
            await self.update_user_memory(ctx.author, message, response)
            
        except Exception as e:
            await thinking_message.delete()
            await ctx.send(f"I encountered an error: {str(e)}")
            print(f"Error in chat: {e}")
    
    async def update_user_memory(self, user, message, response):
        """Update memory with user information when appropriate"""
        if not self.memory_manager:
            return
            
        # Extract potential user information (this is a simple heuristic)
        if "my name is" in message.lower() or "I am" in message or "I'm " in message:
            # Store this as potential user information
            self.memory_manager.personal_memory.store_user_info(
                user_id=str(user.id),
                text=f"User mentioned: '{message}'",
                info_type="self_disclosure",
                importance=0.7
            )
        
        # Check for preferences
        if "I like" in message or "I love" in message or "I enjoy" in message or "I prefer" in message:
            self.memory_manager.personal_memory.store_user_preference(
                user_id=str(user.id),
                text=f"User expressed preference: '{message}'",
                preference_type="general",
                importance=0.6
            )
    
    @commands.command()
    async def endchat(self, ctx):
        """End the current conversation and clear history"""
        if not self.llm_manager:
            await ctx.send("Chat system is still initializing.")
            return
            
        if ctx.author.id in self.active_conversations:
            self.active_conversations.remove(ctx.author.id)
            
            # Clear conversation history
            self.llm_manager.clear_history(ctx.author.id)
            
            embed = discord.Embed(
                title="Conversation Ended",
                description="I've cleared our conversation history. Feel free to start a new chat anytime!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have an active conversation with me.")
    
    @commands.command()
    async def memory(self, ctx, action=None, *, query=None):
        """Memory system commands"""
        if not self.memory_manager:
            await ctx.send("Memory system is still initializing.")
            return
        
        if action is None or action.lower() == "help":
            embed = discord.Embed(
                title="Memory Commands",
                description="Commands for interacting with my memory system:",
                color=discord.Color.blue()
            )
            embed.add_field(name="!memory search [query]", value="Search my memories", inline=False)
            embed.add_field(name="!memory profile", value="View what I know about you", inline=False)
            embed.add_field(name="!memory reflect", value="Generate a reflection on recent memories", inline=False)
            await ctx.send(embed=embed)
            return
        
        if action.lower() == "search" and query:
            # Search memories
            thinking_message = await ctx.send("Searching my memories...")
            
            try:
                loop = asyncio.get_event_loop()
                memories = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.memory_manager.search_memories,
                        query=query,
                        limit=5
                    )
                )
                
                if memories:
                    embed = discord.Embed(
                        title=f"Memory Search: '{query}'",
                        description="Here's what I found in my memories:",
                        color=discord.Color.gold()
                    )
                    
                    for i, memory in enumerate(memories, 1):
                        memory_type = memory.get("memory_type", "unknown")
                        similarity = memory.get("similarity", 0.0)
                        embed.add_field(
                            name=f"{i}. {memory_type.capitalize()} Memory ({similarity:.2f})",
                            value=memory["text"][:1024],
                            inline=False
                        )
                else:
                    embed = discord.Embed(
                        title=f"Memory Search: '{query}'",
                        description="I couldn't find any relevant memories.",
                        color=discord.Color.gold()
                    )
                
                await thinking_message.delete()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await thinking_message.delete()
                await ctx.send(f"Error searching memories: {str(e)}")
        
        elif action.lower() == "profile":
            # Get user profile
            thinking_message = await ctx.send("Retrieving your profile...")
            
            try:
                loop = asyncio.get_event_loop()
                summary = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.memory_manager.personal_memory.get_user_summary,
                        user_id=str(ctx.author.id)
                    )
                )
                
                embed = discord.Embed(
                    title=f"User Profile: {ctx.author.display_name}",
                    description=summary,
                    color=discord.Color.green()
                )
                
                await thinking_message.delete()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await thinking_message.delete()
                await ctx.send(f"Error retrieving profile: {str(e)}")
        
        elif action.lower() == "reflect":
            # Generate reflection
            thinking_message = await ctx.send("Reflecting on my recent memories...")
            
            try:
                loop = asyncio.get_event_loop()
                reflection = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.memory_manager.trigger_reflection,
                        reflection_type="daily"
                    )
                )
                
                embed = discord.Embed(
                    title="Memory Reflection",
                    description=reflection.get("summary", "No reflection generated."),
                    color=discord.Color.purple()
                )
                
                if reflection.get("insights"):
                    insights_text = "\n".join([f"• {insight['text']}" for insight in reflection["insights"][:3]])
                    embed.add_field(name="Insights", value=insights_text, inline=False)
                
                await thinking_message.delete()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await thinking_message.delete()
                await ctx.send(f"Error generating reflection: {str(e)}")
        
        else:
            await ctx.send("Unknown memory command. Use `!memory help` to see available commands.")
    
    @commands.command()
    async def debug_systems(self, ctx):
        """Debug command to check systems status"""
        embed = discord.Embed(
            title="Systems Status",
            description="Current status of Aina's systems:",
            color=discord.Color.blue()
        )
        
        # Check LLM status
        if self.llm_manager is None:
            llm_status = "⚠️ Not initialized"
        elif self.llm_manager.model is None:
            llm_status = "❌ Failed to load"
        else:
            llm_status = "✅ Operational"
        
        # Check memory status
        if self.memory_manager is None:
            memory_status = "⚠️ Not initialized"
        else:
            try:
                # Get memory counts
                core_count = self.memory_manager.storage.count('core')
                episodic_count = self.memory_manager.storage.count('episodic')
                semantic_count = self.memory_manager.storage.count('semantic')
                personal_count = self.memory_manager.storage.count('personal')
                
                memory_status = f"✅ Operational\n• Core: {core_count}\n• Episodic: {episodic_count}\n• Semantic: {semantic_count}\n• Personal: {personal_count}"
            except Exception as e:
                memory_status = f"⚠️ Error: {str(e)}"
        
        embed.add_field(name="LLM System", value=llm_status, inline=False)
        embed.add_field(name="Memory System", value=memory_status, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for direct messages to continue conversations"""
        # Ignore messages from bots including self
        if message.author.bot:
            return
            
        # Handle DMs as continuation of conversations
        if isinstance(message.channel, discord.DMChannel):
            # If there's an active conversation, process the message as chat
            if self.get_conversation_status(message.author.id):
                # Create a mock context object for the chat command
                ctx = await self.bot.get_context(message)
                
                # Skip if it's a command
                if ctx.valid:
                    return
                    
                # Process as chat message
                await self.chat(ctx, message=message.content)

async def setup(bot):
    await bot.add_cog(Conversation(bot))