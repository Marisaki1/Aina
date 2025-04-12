import discord
from discord.ext import commands
import os
import asyncio
import random
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import settings
from .dungeon_manager import DungeonManager
from .dungeon_generator import DungeonGenerator
from .dungeon_renderer import DungeonRenderer
from .dungeon_encounters import DungeonEncounterManager

class Dungeons(commands.Cog):
    def __init__(self, bot):
        """Initialize the dungeon cog"""
        self.bot = bot
        
        # Initialize managers
        self.dungeon_manager = DungeonManager(bot)
        self.generator = DungeonGenerator()
        self.renderer = DungeonRenderer()
        self.encounter_manager = DungeonEncounterManager(bot)
        
        # Load settings
        self.settings = settings.DUNGEON_SETTINGS
        self.cell_types = settings.CELL_TYPES
        self.direction_emojis = settings.DIRECTION_EMOJIS
    
    @commands.group(name="dungeon", aliases=["dg"], invoke_without_command=True)
    async def dungeon(self, ctx):
        """Main dungeon command group"""
        embed = discord.Embed(
            title="🏰 Dungeon System",
            description="Explore procedurally generated dungeons with your friends!",
            color=settings.EMBED_COLORS["DUNGEON"]
        )
        
        command_list = (
            "`!dungeon create` - Create a new dungeon adventure\n"
            "`!dungeon join` - Join an active dungeon\n"
            "`!dungeon leave` - Leave the current dungeon\n"
            "`!dungeon status` - Show dungeon status\n"
            "`!dungeon list` - List saved dungeons\n"
            "`!dungeon load <id>` - Load a saved dungeon\n"
            "`!dungeon end` - End the current dungeon (leader only)"
        )
        
        embed.add_field(name="Commands", value=command_list, inline=False)
        
        examples = (
            "`!dungeon create` - Create a dungeon with default settings\n"
            "`!dungeon create size:large difficulty:hard` - Create a large, hard dungeon"
        )
        
        embed.add_field(name="Examples", value=examples, inline=False)
        
        embed.set_footer(text="Use arrow reactions to move once in a dungeon")
        
        await ctx.send(embed=embed)
    
    @dungeon.command(name="create")
    async def create_dungeon(self, ctx, *, options=None):
        """
        Create a new dungeon adventure
        
        Usage: !dungeon create [options]
        Options:
          size: SMALL, MEDIUM, LARGE (default: MEDIUM)
          complexity: EASY, NORMAL, HARD (default: NORMAL)
          floors: SMALL, MEDIUM, LARGE, EXTREME (default: SMALL)
          difficulty: EASY, NORMAL, HARD, LUNATIC (default: NORMAL)
          name: Custom dungeon name
        """
        # Parse options
        size = "MEDIUM"
        complexity = "NORMAL"
        floors_type = "SMALL"
        difficulty = "NORMAL"
        custom_name = None
        
        if options:
            option_parts = options.split()
            for part in option_parts:
                if ":" in part:
                    key, value = part.split(":", 1)
                    key = key.lower()
                    value = value.upper()
                    
                    if key == "size" and value in ["SMALL", "MEDIUM", "LARGE"]:
                        size = value
                    elif key == "complexity" and value in ["EASY", "NORMAL", "HARD"]:
                        complexity = value
                    elif key == "floors" and value in ["SMALL", "MEDIUM", "LARGE", "EXTREME"]:
                        floors_type = value
                    elif key == "difficulty" and value in ["EASY", "NORMAL", "HARD", "LUNATIC"]:
                        difficulty = value
                    elif key == "name":
                        custom_name = value.title()  # Convert to title case
        
        # Create progress message
        progress_msg = await ctx.send("🔄 Generating dungeon... Please wait.")
        
        # Create the dungeon
        success = await self.dungeon_manager.create_dungeon(
            ctx, size, complexity, floors_type, difficulty, custom_name
        )
        
        if not success:
            await progress_msg.delete()
            return
        
        # Generate a rich description
        size_desc = self.settings["SIZES"][size]["name"]
        complexity_desc = self.settings["COMPLEXITY"][complexity]["name"]
        floors_desc = self.settings["FLOORS"][floors_type]["name"]
        difficulty_desc = self.settings["DIFFICULTY"][difficulty]["name"]
        
        # Get dungeon info
        dungeon = self.dungeon_manager.active_dungeons.get(str(ctx.channel.id))
        
        if not dungeon:
            await progress_msg.delete()
            await ctx.send("❌ An error occurred while creating the dungeon.")
            return
        
        # Create success embed
        embed = discord.Embed(
            title=f"🏰 Dungeon Created: {dungeon['name']}",
            description=f"A new dungeon adventure has been created!",
            color=settings.EMBED_COLORS["DUNGEON"]
        )
        
        embed.add_field(
            name="Dungeon Info",
            value=(
                f"**Size:** {size_desc}\n"
                f"**Complexity:** {complexity_desc}\n"
                f"**Floors:** {floors_desc} ({dungeon['num_floors']} floors)\n"
                f"**Difficulty:** {difficulty_desc}"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Players",
            value=f"{ctx.author.mention} (Leader)",
            inline=True
        )
        
        embed.add_field(
            name="How to Play",
            value="Use the arrow reactions to move your character. Interact with objects in the dungeon by moving onto them.",
            inline=False
        )
        
        embed.set_footer(text=f"Dungeon ID: {dungeon['id']}")
        
        # Delete progress message
        await progress_msg.delete()
        
        # Send success message
        await ctx.send(embed=embed)
        
        # Render the dungeon view
        await self.dungeon_manager.refresh_dungeon_view(ctx.channel)
    
    @dungeon.command(name="join")
    async def join_dungeon(self, ctx):
        """Join the active dungeon in this channel"""
        await self.dungeon_manager.join_dungeon(ctx)
    
    @dungeon.command(name="leave")
    async def leave_dungeon(self, ctx):
        """Leave the active dungeon in this channel"""
        await self.dungeon_manager.leave_dungeon(ctx)
    
    @dungeon.command(name="end")
    async def end_dungeon(self, ctx):
        """End the active dungeon in this channel (leader only)"""
        await self.dungeon_manager.end_dungeon(ctx)
    
    @dungeon.command(name="status")
    async def dungeon_status(self, ctx):
        """Show the status of the active dungeon"""
        channel_id = str(ctx.channel.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.dungeon_manager.active_dungeons:
            await ctx.send("❌ No active dungeon in this channel!")
            return
        
        dungeon = self.dungeon_manager.active_dungeons[channel_id]
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # Get leader info
        leader_id = dungeon["leader_id"]
        leader = self.bot.get_user(leader_id)
        leader_name = leader.display_name if leader else f"User ID: {leader_id}"
        
        # Create status embed
        embed = discord.Embed(
            title=f"🏰 Dungeon Status: {dungeon['name']}",
            description=f"Currently on Floor {current_floor + 1}/{dungeon['num_floors']}",
            color=settings.EMBED_COLORS["DUNGEON"]
        )
        
        # Add dungeon info
        embed.add_field(
            name="Dungeon Info",
            value=(
                f"**Size:** {self.settings['SIZES'][dungeon['size']]['name']}\n"
                f"**Complexity:** {self.settings['COMPLEXITY'][dungeon['complexity']]['name']}\n"
                f"**Difficulty:** {self.settings['DIFFICULTY'][dungeon['difficulty']]['name']}\n"
                f"**Leader:** {leader_name}"
            ),
            inline=False
        )
        
        # Add player list
        players = []
        for player_id in floor["player_positions"]:
            player = self.bot.get_user(int(player_id))
            if player:
                players.append(player.mention)
            else:
                players.append(f"User ID: {player_id}")
        
        embed.add_field(
            name=f"Players ({len(players)})",
            value="\n".join(players) or "No players",
            inline=False
        )
        
        # Add dungeon stats
        floor_elements = floor["elements"]
        
        embed.add_field(
            name="Floor Elements",
            value=(
                f"**Chests:** {len(floor_elements['chests'])}\n"
                f"**Traps:** {len(floor_elements['traps'])}\n"
                f"**Enemies:** {len(floor_elements['enemies'])}"
            ),
            inline=True
        )
        
        embed.set_footer(text=f"Dungeon ID: {dungeon['id']}")
        
        await ctx.send(embed=embed)
    
    @dungeon.command(name="list")
    async def list_dungeons(self, ctx):
        """List all saved dungeons"""
        # Get saved dungeons
        dungeons = self.dungeon_manager.list_saved_dungeons()
        
        if not dungeons:
            await ctx.send("❌ No saved dungeons found!")
            return
        
        # Create list embed
        embed = discord.Embed(
            title="💾 Saved Dungeons",
            description=f"Found {len(dungeons)} saved dungeons:",
            color=settings.EMBED_COLORS["DUNGEON"]
        )
        
        # Add each dungeon to the embed
        for i, dungeon in enumerate(dungeons[:10]):  # Show max 10 dungeons
            # Parse creation date
            try:
                created_date = datetime.fromisoformat(dungeon["created_at"])
                date_str = created_date.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = "Unknown date"
            
            # Add field for this dungeon
            embed.add_field(
                name=f"{i+1}. {dungeon['name']}",
                value=(
                    f"**ID:** `{dungeon['id']}`\n"
                    f"**Size:** {dungeon['size']}\n"
                    f"**Difficulty:** {dungeon['difficulty']}\n"
                    f"**Floors:** {dungeon['current_floor'] + 1}/{dungeon['num_floors']}\n"
                    f"**Created:** {date_str}"
                ),
                inline=True
            )
        
        # Add note if there are more dungeons
        if len(dungeons) > 10:
            embed.set_footer(text=f"Showing 10 of {len(dungeons)} dungeons")
        
        await ctx.send(embed=embed)
    
    @dungeon.command(name="load")
    async def load_dungeon(self, ctx, dungeon_id: str):
        """Load a saved dungeon"""
        # Check if dungeon exists
        success = self.dungeon_manager.load_dungeon_state(str(ctx.channel.id), dungeon_id)
        
        if not success:
            await ctx.send(f"❌ Could not load dungeon with ID `{dungeon_id}`!")
            return
        
        # Get loaded dungeon
        dungeon = self.dungeon_manager.active_dungeons.get(str(ctx.channel.id))
        
        if not dungeon:
            await ctx.send("❌ An error occurred while loading the dungeon.")
            return
        
        # Create success embed
        embed = discord.Embed(
            title=f"💾 Dungeon Loaded: {dungeon['name']}",
            description=f"Successfully loaded the dungeon!",
            color=settings.EMBED_COLORS["DUNGEON"]
        )
        
        embed.add_field(
            name="Dungeon Info",
            value=(
                f"**Size:** {self.settings['SIZES'][dungeon['size']]['name']}\n"
                f"**Complexity:** {self.settings['COMPLEXITY'][dungeon['complexity']]['name']}\n"
                f"**Floors:** {dungeon['current_floor'] + 1}/{dungeon['num_floors']}\n"
                f"**Difficulty:** {self.settings['DIFFICULTY'][dungeon['difficulty']]['name']}"
            ),
            inline=False
        )
        
        # Set ctx.author as the leader if there isn't one
        if "leader_id" not in dungeon or not dungeon["leader_id"]:
            dungeon["leader_id"] = ctx.author.id
        
        # Add leader info
        leader_id = dungeon["leader_id"]
        leader = self.bot.get_user(leader_id)
        leader_name = leader.mention if leader else f"User ID: {leader_id}"
        
        embed.add_field(
            name="Leader",
            value=leader_name,
            inline=True
        )
        
        embed.set_footer(text=f"Dungeon ID: {dungeon['id']}")
        
        # Send success message
        await ctx.send(embed=embed)
        
        # Refresh the dungeon view
        await self.dungeon_manager.refresh_dungeon_view(ctx.channel)
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle movement and interaction reactions"""
        # Ignore bot's own reactions
        if user.bot:
            return
        
        # Process movement if it's a direction emoji
        if str(reaction.emoji) in self.direction_emojis.values():
            moved = await self.dungeon_manager.move_player(reaction, user)
            
            # If player moved, check for random encounter
            if moved:
                channel_id = str(reaction.message.channel.id)
                if channel_id in self.dungeon_manager.active_dungeons:
                    dungeon = self.dungeon_manager.active_dungeons[channel_id]
                    
                    # Check if player is on cooldown
                    if not self.encounter_manager.is_on_cooldown(user.id):
                        # Check for random encounter
                        if self.encounter_manager.should_trigger_random_encounter(dungeon):
                            # Set cooldown
                            self.encounter_manager.set_cooldown(user.id, 
                                                              self.settings["ENCOUNTERS"]["COOLDOWN_MOVES"] * 30)
                            
                            # Roll for encounter type
                            encounter_type = random.choices(
                                ["trap", "battle", "event"],
                                weights=[0.3, 0.5, 0.2],
                                k=1
                            )[0]
                            
                            # Handle encounter
                            if encounter_type == "trap":
                                await self.encounter_manager.handle_trap_encounter(
                                    reaction.message.channel, user, dungeon["difficulty"]
                                )
                            elif encounter_type == "battle":
                                await self.encounter_manager.handle_battle_encounter(
                                    reaction.message.channel, user, dungeon["difficulty"]
                                )
                            elif encounter_type == "event":
                                await self.encounter_manager.handle_random_event(
                                    reaction.message.channel, user
                                )
            
            # Update the dungeon view if needed
            if moved:
                await self.dungeon_manager.refresh_dungeon_view(reaction.message.channel)
                
            # Remove the user's reaction
            try:
                await reaction.remove(user)
            except:
                pass
        
        # Handle floor transition confirmation
        elif str(reaction.emoji) == "✅":
            transition = await self.dungeon_manager.handle_floor_transition(reaction, user)
            
            # Remove the user's reaction
            try:
                await reaction.remove(user)
            except:
                pass
        
        # Handle encounter reactions
        else:
            await self.encounter_manager.handle_encounter_reaction(reaction, user)

async def setup(bot):
    await bot.add_cog(Dungeons(bot))