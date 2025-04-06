import discord
from discord.ext import commands
import asyncio
import os
from .llm_core import LLMManager
import time
import functools

class Conversation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.llm_manager = None
        self.thinking_messages = [
            "Hmm, let me think about that...",
            "Processing your request...",
            "Thinking...",
            "Let me consider that for a moment..."
        ]
        self.active_conversations = set()
        
        # Load LLM manager in the background to avoid blocking bot startup
        self.bot.loop.create_task(self.initialize_llm())
    
    async def initialize_llm(self):
        """Initialize the LLM manager in the background"""
        await self.bot.wait_until_ready()
        try:
            self.llm_manager = LLMManager()
            print("✅ LLM Manager initialized")
        except Exception as e:
            print(f"❌ Failed to initialize LLM Manager: {e}")
    
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
        
        # Check if LLM is initialized
        if not self.llm_manager:
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
            # This is the correct way to use to_thread with functions that take arguments
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                functools.partial(
                    self.llm_manager.get_response,
                    ctx.author.id,
                    message
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
            
        except Exception as e:
            await thinking_message.delete()
            await ctx.send(f"I encountered an error: {str(e)}")
            print(f"Error in chat: {e}")
    
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
    async def debug_llm(self, ctx):
        """Debug command to check LLM status"""
        if self.llm_manager is None:
            await ctx.send("⚠️ LLM Manager not initialized yet")
            return
            
        if self.llm_manager.model is None:
            await ctx.send("❌ LLM Model failed to load")
            return
            
        await ctx.send("✅ LLM system is operational")
    
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