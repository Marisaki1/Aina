import discord
from discord.ext import commands
import asyncio
import os
import time
import functools
from typing import Dict, List, Optional, Any, Callable

class DiscordInterface:
    """
    Discord-specific interface for Aina.
    Handles Discord messaging, events, and interactions.
    """
    
    def __init__(self, bot, agent):
        """
        Initialize Discord interface.
        
        Args:
            bot: Discord bot instance
            agent: Agent instance
        """
        self.bot = bot
        self.agent = agent
        self.active_conversations = set()
        self.thinking_messages = [
            "Hmm, let me think about that...",
            "Processing your request...",
            "Thinking...",
            "Let me consider that for a moment..."
        ]
    
    def get_conversation_status(self, user_id: int) -> bool:
        """
        Check if a conversation is active for a user.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            True if conversation is active, False otherwise
        """
        return user_id in self.active_conversations
    
    async def process_message(self, ctx, message: str) -> None:
        """
        Process a Discord message and generate a response.
        
        Args:
            ctx: Discord context
            message: Message content
        """
        if not message:
            return
        
        # Indicate the bot is "thinking"
        thinking_idx = int(time.time()) % len(self.thinking_messages)
        thinking_message = await ctx.send(self.thinking_messages[thinking_idx])
        
        # Mark this user as having an active conversation
        self.active_conversations.add(ctx.author.id)
        
        # Process in a separate thread to avoid blocking
        try:
            # Create context for the agent
            context = {
                "channel": ctx.channel.name if hasattr(ctx.channel, "name") else "DM",
                "guild": ctx.guild.name if ctx.guild else "DM",
                "interface_type": "discord"
            }
            
            # Get response from agent
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                functools.partial(
                    self.agent.process_message,
                    user_id=str(ctx.author.id),
                    message=message,
                    interface_type="discord",
                    context=context
                )
            )
            
            # Delete the thinking message
            await thinking_message.delete()
            
            # Create and send response embed
            await self.send_response(ctx, response)
            
        except Exception as e:
            await thinking_message.delete()
            await ctx.send(f"I encountered an error: {str(e)}")
            print(f"Error processing message: {e}")
    
    async def send_response(self, ctx, response_text: str) -> None:
        """
        Send a response as a Discord embed.
        
        Args:
            ctx: Discord context
            response_text: Response text
        """
        # Create response embed
        embed = discord.Embed(
            description=response_text,
            color=discord.Color.purple()
        )
        embed.set_author(name="Aina", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Reply with !chat to continue the conversation")
        
        # Send the response
        await ctx.send(embed=embed)
    
    async def end_conversation(self, ctx) -> None:
        """
        End a conversation with a user.
        
        Args:
            ctx: Discord context
        """
        if ctx.author.id in self.active_conversations:
            self.active_conversations.remove(ctx.author.id)
            
            # Clear conversation history
            self.agent.llm_manager.clear_history(str(ctx.author.id), interface_type="discord")
            
            embed = discord.Embed(
                title="Conversation Ended",
                description="I've cleared our conversation history. Feel free to start a new chat anytime!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have an active conversation with me.")
    
    async def handle_memory_command(self, ctx, action: str, query: Optional[str] = None) -> None:
        """
        Handle memory-related commands.
        
        Args:
            ctx: Discord context
            action: Action to perform (search, profile, etc.)
            query: Search query if applicable
        """
        if action == "search" and query:
            # Search memories
            thinking_message = await ctx.send("Searching my memories...")
            
            try:
                loop = asyncio.get_event_loop()
                memories = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.agent.search_memory,
                        query=query,
                        user_id=str(ctx.author.id)
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
        
        elif action == "profile":
            # Get user profile
            thinking_message = await ctx.send("Retrieving your profile...")
            
            try:
                loop = asyncio.get_event_loop()
                user_info = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.agent.get_user_info,
                        user_id=str(ctx.author.id)
                    )
                )
                
                if user_info and "memory_profile" in user_info:
                    profile = user_info["memory_profile"]
                    
                    embed = discord.Embed(
                        title=f"User Profile: {ctx.author.display_name}",
                        color=discord.Color.green()
                    )
                    
                    # Add profile sections
                    if profile.get("traits"):
                        traits_text = "\n".join([f"• {trait['text']}" for trait in profile["traits"][:3]])
                        embed.add_field(name="Traits", value=traits_text or "None", inline=False)
                    
                    if profile.get("preferences"):
                        prefs_text = "\n".join([f"• {pref['text']}" for pref in profile["preferences"][:3]])
                        embed.add_field(name="Preferences", value=prefs_text or "None", inline=False)
                    
                    if profile.get("info"):
                        info_text = "\n".join([f"• {info['text']}" for info in profile["info"][:3]])
                        embed.add_field(name="Information", value=info_text or "None", inline=False)
                    
                    if profile.get("interaction_summaries"):
                        summary = profile["interaction_summaries"][0]["text"] if profile["interaction_summaries"] else "None"
                        embed.add_field(name="Recent Interaction", value=summary, inline=False)
                else:
                    embed = discord.Embed(
                        title=f"User Profile: {ctx.author.display_name}",
                        description="I don't have much information about you yet.",
                        color=discord.Color.green()
                    )
                
                await thinking_message.delete()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await thinking_message.delete()
                await ctx.send(f"Error retrieving profile: {str(e)}")
        
        elif action == "reflect":
            # Generate reflection
            thinking_message = await ctx.send("Reflecting on my memories...")
            
            try:
                loop = asyncio.get_event_loop()
                reflection = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.agent.create_reflection,
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
                
                embed.set_footer(text=f"Based on {reflection.get('memory_count', 0)} memories")
                
                await thinking_message.delete()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await thinking_message.delete()
                await ctx.send(f"Error generating reflection: {str(e)}")
        
        else:
            embed = discord.Embed(
                title="Memory Commands",
                description="Commands for interacting with my memory system:",
                color=discord.Color.blue()
            )
            embed.add_field(name="!memory search [query]", value="Search my memories", inline=False)
            embed.add_field(name="!memory profile", value="View what I know about you", inline=False)
            embed.add_field(name="!memory reflect", value="Generate a reflection on recent memories", inline=False)
            
            await ctx.send(embed=embed)
    
    async def handle_status_command(self, ctx) -> None:
        """
        Handle status command.
        
        Args:
            ctx: Discord context
        """
        status = self.agent.get_status()
        
        embed = discord.Embed(
            title="Aina Status",
            color=discord.Color.blue()
        )
        
        # General status
        embed.add_field(
            name="General",
            value=f"Status: {status['status']}\nUptime: {status['uptime']}\nActive Users: {status['active_users']}",
            inline=False
        )
        
        # Memory stats
        memory_text = ""
        for memory_type, count in status.get('memory_stats', {}).items():
            memory_text += f"{memory_type.capitalize()}: {count} memories\n"
        
        embed.add_field(
            name="Memory",
            value=memory_text or "No memory stats available",
            inline=False
        )
        
        # Last reflection
        last_reflection_hours = status.get('last_reflection', 0) / 3600
        embed.add_field(
            name="Reflection",
            value=f"Last reflection: {last_reflection_hours:.1f} hours ago",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def update_bot_status(self, activity_type: int = 0, activity_text: str = "with memory") -> None:
        """
        Update the bot's status in Discord.
        
        Args:
            activity_type: Discord activity type
            activity_text: Status text
        """
        activity = discord.Activity(
            type=activity_type,
            name=activity_text
        )
        asyncio.create_task(self.bot.change_presence(activity=activity))