import json
import os
import random
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

import discord
from discord.ext import tasks

import settings
from .dungeon_generator import DungeonGenerator
from .dungeon_renderer import DungeonRenderer

class DungeonManager:
    def __init__(self, bot):
        """Initialize the dungeon manager"""
        self.bot = bot
        self.settings = settings.DUNGEON_SETTINGS
        self.cell_types = settings.CELL_TYPES
        self.direction_emojis = settings.DIRECTION_EMOJIS
        
        # Initialize generators and renderers
        self.generator = DungeonGenerator()
        self.renderer = DungeonRenderer()
        
        # Track active dungeon sessions
        self.active_dungeons = {}  # {channel_id: dungeon_data}
        
        # Start auto-save task
        self.auto_save_dungeons.start()
    
    def cog_unload(self):
        # Stop the auto-save task when the cog is unloaded
        self.auto_save_dungeons.cancel()
    
    @tasks.loop(minutes=5)
    async def auto_save_dungeons(self):
        """Periodically save all active dungeons"""
        if not self.settings["SAVE"]["ENABLED"]:
            return
            
        for channel_id, dungeon in self.active_dungeons.items():
            try:
                self.save_dungeon_state(channel_id)
            except Exception as e:
                print(f"Error auto-saving dungeon in channel {channel_id}: {e}")
    
    async def create_dungeon(self, ctx, size="MEDIUM", complexity="NORMAL", 
                             floors_type="SMALL", difficulty="NORMAL", custom_name=None) -> bool:
        """
        Create a new dungeon for a channel
        
        Args:
            ctx: Command context
            size: Dungeon size (SMALL, MEDIUM, LARGE)
            complexity: Dungeon complexity (EASY, NORMAL, HARD)
            floors_type: Number of floors (SMALL, MEDIUM, LARGE, EXTREME)
            difficulty: Encounter difficulty (EASY, NORMAL, HARD, LUNATIC)
            custom_name: Optional custom name for the dungeon
            
        Returns:
            True if dungeon was created successfully
        """
        channel_id = str(ctx.channel.id)
        
        # Check if a dungeon is already active in this channel
        if channel_id in self.active_dungeons:
            await ctx.send("❌ A dungeon is already active in this channel!")
            return False
        
        # Generate new dungeon
        dungeon = self.generator.generate_dungeon(
            size=size,
            complexity=complexity,
            floors_type=floors_type,
            difficulty=difficulty
        )
        
        # Set custom name if provided
        if custom_name:
            dungeon["name"] = custom_name
        
        # Add creator info
        dungeon["creator_id"] = ctx.author.id
        dungeon["leader_id"] = ctx.author.id
        
        # Initialize player at starting position
        floor = dungeon["floors"][0]
        start_pos = floor["start_pos"]
        
        # Add the creator as the first player
        floor["player_positions"][str(ctx.author.id)] = start_pos
        
        # Initialize message tracking
        dungeon["message_id"] = None
        
        # Store in active dungeons
        self.active_dungeons[channel_id] = dungeon
        
        # Save initial state
        self.save_dungeon_state(channel_id)
        
        return True
    
    async def join_dungeon(self, ctx) -> bool:
        """
        Let a player join an active dungeon
        
        Args:
            ctx: Command context
            
        Returns:
            True if player joined successfully
        """
        channel_id = str(ctx.channel.id)
        user_id = str(ctx.author.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            await ctx.send("❌ No active dungeon in this channel!")
            return False
        
        dungeon = self.active_dungeons[channel_id]
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # If player is already in the dungeon, don't add again
        if user_id in floor["player_positions"]:
            await ctx.send(f"⚠️ {ctx.author.mention} is already in the dungeon!")
            return False
        
        # Add player at the starting position of the current floor
        floor["player_positions"][user_id] = floor["start_pos"]
        
        # Update the dungeon image
        await self.refresh_dungeon_view(ctx.channel)
        
        await ctx.send(f"✅ {ctx.author.mention} joined the dungeon!")
        return True
    
    async def leave_dungeon(self, ctx) -> bool:
        """
        Let a player leave the dungeon
        
        Args:
            ctx: Command context
            
        Returns:
            True if player left successfully
        """
        channel_id = str(ctx.channel.id)
        user_id = str(ctx.author.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            await ctx.send("❌ No active dungeon in this channel!")
            return False
        
        dungeon = self.active_dungeons[channel_id]
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # Check if player is in the dungeon
        if user_id not in floor["player_positions"]:
            await ctx.send(f"⚠️ {ctx.author.mention} is not in the dungeon!")
            return False
        
        # If leader is leaving and there are other players,
        # assign leadership to another player
        if user_id == str(dungeon["leader_id"]) and len(floor["player_positions"]) > 1:
            # Find another player to be leader
            for player_id in floor["player_positions"]:
                if player_id != user_id:
                    dungeon["leader_id"] = int(player_id)
                    leader = self.bot.get_user(int(player_id))
                    leader_mention = leader.mention if leader else f"User ID: {player_id}"
                    await ctx.send(f"👑 Leadership transferred to {leader_mention}!")
                    break
        
        # Remove player from the dungeon
        del floor["player_positions"][user_id]
        
        # If no players left, offer to end the dungeon
        if not floor["player_positions"]:
            # Save state before ending
            self.save_dungeon_state(channel_id)
            
            confirm_msg = await ctx.send(
                "🚪 All players have left the dungeon. React with ✅ to save and end the dungeon, or ❌ to keep it active."
            )
            
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            def check(reaction, user):
                return (user == ctx.author and 
                        str(reaction.emoji) in ["✅", "❌"] and 
                        reaction.message.id == confirm_msg.id)
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    del self.active_dungeons[channel_id]
                    await ctx.send("🏰 Dungeon saved and ended!")
                else:
                    await ctx.send("🏰 Dungeon remains active. Players can rejoin later.")
            except asyncio.TimeoutError:
                await ctx.send("⏰ No response received. Dungeon remains active.")
            
            # Clean up the confirmation message
            try:
                await confirm_msg.delete()
            except:
                pass
        else:
            # Update the dungeon image
            await self.refresh_dungeon_view(ctx.channel)
            
            await ctx.send(f"👋 {ctx.author.mention} left the dungeon!")
        
        return True
    
    async def end_dungeon(self, ctx) -> bool:
        """
        End an active dungeon in a channel
        
        Args:
            ctx: Command context
            
        Returns:
            True if dungeon was ended successfully
        """
        channel_id = str(ctx.channel.id)
        user_id = ctx.author.id
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            await ctx.send("❌ No active dungeon in this channel!")
            return False
        
        dungeon = self.active_dungeons[channel_id]
        
        # Only allow the dungeon leader or admin to end it
        if user_id != dungeon["leader_id"] and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only the dungeon leader or a server admin can end this dungeon!")
            return False
        
        # Save the final state before ending
        self.save_dungeon_state(channel_id)
        
        # Remove from active dungeons
        del self.active_dungeons[channel_id]
        
        await ctx.send("✅ Dungeon ended!")
        return True
    
    async def move_player(self, reaction, user) -> bool:
        """
        Move a player based on their reaction
        
        Args:
            reaction: The reaction object
            user: The user who reacted
            
        Returns:
            True if movement was successful
        """
        channel_id = str(reaction.message.channel.id)
        user_id = str(user.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            return False
        
        dungeon = self.active_dungeons[channel_id]
        
        # Check if this is the dungeon message
        if reaction.message.id != dungeon["message_id"]:
            return False
        
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # Check if the user is in the dungeon
        if user_id not in floor["player_positions"]:
            # Add new player with starting position
            floor["player_positions"][user_id] = floor["start_pos"]
            player_pos = floor["start_pos"]
        else:
            player_pos = floor["player_positions"][user_id]
        
        # Get current position
        y, x = player_pos
        
        # Parse movement direction
        moved = False
        new_pos = None
        
        if str(reaction.emoji) == self.direction_emojis["UP"] and y > 0:  # Up
            new_pos = (y - 1, x)
        elif str(reaction.emoji) == self.direction_emojis["DOWN"] and y < floor["height"] - 1:  # Down
            new_pos = (y + 1, x)
        elif str(reaction.emoji) == self.direction_emojis["LEFT"] and x > 0:  # Left
            new_pos = (y, x - 1)
        elif str(reaction.emoji) == self.direction_emojis["RIGHT"] and x < floor["width"] - 1:  # Right
            new_pos = (y, x + 1)
        
        # Validate that new position is a walkable cell
        if new_pos:
            new_y, new_x = new_pos
            cell_type = floor["grid"][new_y][new_x]
            
            # Check if cell is not a wall
            if cell_type != self.cell_types["WALL"]:
                # Update player position
                floor["player_positions"][user_id] = new_pos
                moved = True
                
                # Update revealed cells
                self.renderer.update_revealed_cells(dungeon, current_floor)
                
                # Check for interactions at the new position
                await self.check_position_interactions(reaction.message.channel, user, new_pos)
        
        return moved
    
    async def check_position_interactions(self, channel, user, position) -> None:
        """
        Check and handle interactions for a player's new position
        
        Args:
            channel: The Discord channel
            user: The user who moved
            position: The new position (y, x)
        """
        channel_id = str(channel.id)
        user_id = str(user.id)
        
        # Get dungeon data
        dungeon = self.active_dungeons.get(channel_id)
        if not dungeon:
            return
        
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # Get the cell type at the new position
        y, x = position
        cell_type = floor["grid"][y][x]
        
        # Handle different cell types
        if cell_type == self.cell_types["STAIRS_UP"]:
            # Check if there are other players on the stairs
            players_on_stairs = [p_id for p_id, pos in floor["player_positions"].items() if pos == position]
            
            # If any player is on stairs, add a check reaction to confirm
            dungeon_message = await channel.fetch_message(dungeon["message_id"])
            
            # Remove previous check reaction if it exists
            try:
                for reaction in dungeon_message.reactions:
                    if str(reaction.emoji) == "✅":
                        await dungeon_message.clear_reaction("✅")
                        break
            except:
                pass
            
            # Add check reaction if players are on stairs
            if players_on_stairs:
                try:
                    await dungeon_message.add_reaction("✅")
                except:
                    pass
            
        elif cell_type == self.cell_types["CHEST"]:
            # For now, just notify about chest
            await channel.send(f"🎁 {user.mention} found a chest! (Placeholder for chest interaction)")
            
            # Convert chest to path after looting
            floor["grid"][y][x] = self.cell_types["PATH"]
            
        elif cell_type == self.cell_types["TRAP"]:
            # For now, just notify about trap
            await channel.send(f"⚠️ {user.mention} triggered a trap! (Placeholder for trap encounter)")
            
            # Convert trap to path after triggering
            floor["grid"][y][x] = self.cell_types["PATH"]
            
        elif cell_type == self.cell_types["ENEMY"]:
            # For now, just notify about enemy
            await channel.send(f"👹 {user.mention} encountered an enemy! (Placeholder for combat)")
            
            # Convert enemy to path after defeating
            floor["grid"][y][x] = self.cell_types["PATH"]
            
        elif cell_type == self.cell_types["END"]:
            # Player reached the end of the final floor
            await channel.send(f"🏆 {user.mention} reached the end of the dungeon! (Placeholder for completion rewards)")
    
    async def handle_floor_transition(self, reaction, user) -> bool:
        """
        Handle transition between floors when a player uses the check reaction on stairs
        
        Args:
            reaction: The reaction object
            user: The user who reacted
            
        Returns:
            True if floor transition was successful
        """
        if str(reaction.emoji) != "✅":
            return False
        
        channel_id = str(reaction.message.channel.id)
        user_id = str(user.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            return False
        
        dungeon = self.active_dungeons[channel_id]
        
        # Check if this is the dungeon message
        if reaction.message.id != dungeon["message_id"]:
            return False
        
        current_floor = dungeon["current_floor"]
        floor = dungeon["floors"][current_floor]
        
        # Check if user is in the dungeon
        if user_id not in floor["player_positions"]:
            return False
        
        # Check if player is on stairs
        player_pos = floor["player_positions"][user_id]
        y, x = player_pos
        cell_type = floor["grid"][y][x]
        
        if cell_type != self.cell_types["STAIRS_UP"]:
            return False
        
        # Check if there are more floors
        if current_floor >= dungeon["num_floors"] - 1:
            await reaction.message.channel.send("⚠️ This is already the highest floor!")
            return False
        
        # Prepare for floor transition
        next_floor = current_floor + 1
        next_floor_data = dungeon["floors"][next_floor]
        
        # Move all players to the starting position of the next floor
        for player_id in floor["player_positions"]:
            next_floor_data["player_positions"][player_id] = next_floor_data["start_pos"]
        
        # Update current floor
        dungeon["current_floor"] = next_floor
        
        # Update the dungeon view
        await self.refresh_dungeon_view(reaction.message.channel)
        
        await reaction.message.channel.send(f"🪜 All players ascended to floor {next_floor + 1}!")
        return True
    
    async def refresh_dungeon_view(self, channel) -> None:
        """
        Update the dungeon display in the channel
        
        Args:
            channel: The Discord channel
        """
        channel_id = str(channel.id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            return
        
        dungeon = self.active_dungeons[channel_id]
        current_floor = dungeon["current_floor"]
        
        # Generate dungeon image
        dungeon_image = self.renderer.render_dungeon(dungeon, current_floor)
        
        # Check if there's an existing message to edit
        message_id = dungeon["message_id"]
        existing_message = None
        
        if message_id:
            try:
                existing_message = await channel.fetch_message(message_id)
            except:
                existing_message = None
        
        # If there's no existing message or we couldn't fetch it, send a new one
        if not existing_message:
            message = await channel.send(
                f"🏰 **{dungeon['name']}** - Floor {current_floor + 1}/{dungeon['num_floors']}",
                file=discord.File(fp=dungeon_image, filename="dungeon.png")
            )
            dungeon["message_id"] = message.id
        else:
            # Edit the existing message
            await existing_message.edit(
                content=f"🏰 **{dungeon['name']}** - Floor {current_floor + 1}/{dungeon['num_floors']}",
                attachments=[discord.File(fp=dungeon_image, filename="dungeon.png")]
            )
            message = existing_message
        
        # Add movement controls and clear existing reactions if needed
        try:
            await message.clear_reactions()
        except:
            pass
        
        await message.add_reaction(self.direction_emojis["UP"])  # Up
        await message.add_reaction(self.direction_emojis["DOWN"])  # Down
        await message.add_reaction(self.direction_emojis["LEFT"])  # Left
        await message.add_reaction(self.direction_emojis["RIGHT"])  # Right
        
        # Check if any player is on stairs, if so add check reaction
        floor = dungeon["floors"][current_floor]
        for player_id, pos in floor["player_positions"].items():
            y, x = pos
            cell_type = floor["grid"][y][x]
            
            if cell_type == self.cell_types["STAIRS_UP"]:
                await message.add_reaction("✅")
                break
    
    def save_dungeon_state(self, channel_id: str) -> bool:
        """
        Save the current state of a dungeon
        
        Args:
            channel_id: The channel ID
            
        Returns:
            True if save was successful
        """
        if not self.settings["SAVE"]["ENABLED"]:
            return False
            
        channel_id = str(channel_id)
        
        # Check if a dungeon is active in this channel
        if channel_id not in self.active_dungeons:
            return False
        
        dungeon = self.active_dungeons[channel_id]
        
        # Save the dungeon state
        try:
            save_file = f"{dungeon['id']}.json"
            save_path = os.path.join(self.settings["SAVE"]["SAVE_DIR"], save_file)
            
            with open(save_path, 'w') as f:
                json.dump(dungeon, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error saving dungeon state: {e}")
            return False
    
    def load_dungeon_state(self, channel_id: str, dungeon_id: str) -> bool:
        """
        Load a previously saved dungeon state
        
        Args:
            channel_id: The channel ID
            dungeon_id: The dungeon ID
            
        Returns:
            True if load was successful
        """
        if not self.settings["SAVE"]["ENABLED"]:
            return False
            
        channel_id = str(channel_id)
        
        # Check if a dungeon is already active in this channel
        if channel_id in self.active_dungeons:
            return False
        
        # Load the dungeon state
        try:
            save_file = f"{dungeon_id}.json"
            save_path = os.path.join(self.settings["SAVE"]["SAVE_DIR"], save_file)
            
            if not os.path.exists(save_path):
                return False
            
            with open(save_path, 'r') as f:
                dungeon = json.load(f)
                
            # Reset message ID since we'll create a new message
            dungeon["message_id"] = None
            
            # Store in active dungeons
            self.active_dungeons[channel_id] = dungeon
            
            return True
        except Exception as e:
            print(f"Error loading dungeon state: {e}")
            return False
    
    def list_saved_dungeons(self) -> List[Dict[str, Any]]:
        """
        List all saved dungeons
        
        Returns:
            List of dungeon metadata
        """
        if not self.settings["SAVE"]["ENABLED"]:
            return []
            
        dungeons = []
        save_dir = self.settings["SAVE"]["SAVE_DIR"]
        
        try:
            # Get all json files in the save directory
            for file in os.listdir(save_dir):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(save_dir, file), 'r') as f:
                            dungeon = json.load(f)
                            
                        # Extract relevant metadata
                        dungeons.append({
                            "id": dungeon["id"],
                            "name": dungeon["name"],
                            "created_at": dungeon["created_at"],
                            "size": dungeon["size"],
                            "complexity": dungeon["complexity"],
                            "difficulty": dungeon["difficulty"],
                            "num_floors": dungeon["num_floors"],
                            "current_floor": dungeon["current_floor"]
                        })
                    except:
                        continue
        except Exception as e:
            print(f"Error listing saved dungeons: {e}")
        
        return dungeons