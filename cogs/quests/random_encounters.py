import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
import re

from .utils import create_embed, send_temp_message
from .player_manager import PlayerManager
from .npc_problems import NPCProblemManager
from .player_classes import PlayerClassHandler

class NewRandomEncounters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player_manager = PlayerManager()
        self.npc_problem_manager = NPCProblemManager()
        self.player_class_handler = PlayerClassHandler()
        self.active_encounters = {}  # Track active encounters by channel
        self.pending_encounters = {}  # Track pending "about to happen" encounters
        self.encounter_cooldowns = {}  # Track cooldown periods for channels
        
        # Load configuration
        self.QUEST_CHANNELS_FILE = "data/quests/channels/enabled_channels.json"
        
        # Start the random encounter task
        self.spawn_random_encounter.start()
    
    def cog_unload(self):
        # Stop the task when the cog is unloaded
        self.spawn_random_encounter.cancel()
    
    @tasks.loop(seconds=30)  # Check every 30 seconds for possible encounter
    async def spawn_random_encounter(self):
        """Periodically check if it's time to spawn a random encounter"""
        # Process all guilds and channels concurrently
        tasks = []
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                tasks.append(self._process_channel_for_encounter(channel))
        
        await asyncio.gather(*tasks)

    async def _process_channel_for_encounter(self, channel):
        """Check and potentially spawn an encounter in a single channel"""
        # Skip if channel is not enabled
        if not self._is_channel_enabled(channel.guild.id, channel.id):
            return
        
        # Skip if there's already an active encounter in this channel
        if channel.id in self.active_encounters or channel.id in self.pending_encounters:
            return
            
        # Skip if channel is on cooldown
        if channel.id in self.encounter_cooldowns:
            if datetime.now() < self.encounter_cooldowns[channel.id]:
                return
            else:
                # Cooldown expired
                del self.encounter_cooldowns[channel.id]
        
        # Random chance to spawn an encounter (approx 5% chance per check, which is every 30 seconds)
        if random.randint(1, 20) == 1:
            try:
                # Create a pending encounter (not assigned to any specific user yet)
                await self.create_pending_encounter(channel)
            except Exception as e:
                print(f"Error creating pending encounter in {channel.name}: {e}")
    
    async def create_pending_encounter(self, channel):
        """Create and send a 'something is about to happen' encounter message"""
        # Create an embed for the pending encounter
        embed = create_embed(
            title="⚡ An Event is About to Happen!",
            description="Something interesting is unfolding... Be the first to investigate!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="How to Participate",
            value="React with 🔍 to investigate this event.",
            inline=False
        )
        
        embed.set_footer(text="This opportunity will disappear in 2 minutes")
        
        # Send the encounter message
        encounter_message = await channel.send(embed=embed)
        
        # Add the investigation reaction
        await encounter_message.add_reaction("🔍")
        
        # Store in pending encounters
        self.pending_encounters[channel.id] = {
            "message_id": encounter_message.id,
            "expires": datetime.now() + timedelta(minutes=2),  # Expires after 2 minutes
            "message": encounter_message  # Store the message object for easier deletion later
        }
        
        # Schedule automatic expiration
        self.bot.loop.create_task(self._expire_pending_encounter(channel.id, encounter_message.id))
    
    async def create_encounter(self, channel, user_id, original_message=None):
        """Create and send a random encounter to the channel for a specific user"""
        # Get player data or create new if not exists
        player_data = self.player_manager.get_player_data(user_id)
        if not player_data:
            player_data = self.player_manager.create_player(user_id, str(user_id))
        
        # Get player level
        player_level = player_data.get("level", 1)
        
        # Get player location
        location = player_data.get("location", "Rivermeet")
        
        # Determine encounter type (event or combat)
        encounter_type = random.choice(["Random Event", "Random Encounter"])
        
        # Get random problem for the location and player level
        problem_data = self.npc_problem_manager.get_random_problem(location, player_level)
        
        # Create embed for the encounter
        embed = await self._create_encounter_embed(user_id, encounter_type, problem_data)
        
        # If we have an original message, edit it, otherwise send a new one
        if original_message:
            encounter_message = original_message
            await encounter_message.edit(embed=embed)
            await encounter_message.clear_reactions()  # Clear the "investigate" reaction
        else:
            encounter_message = await channel.send(embed=embed)
        
        # Add reaction options for choices
        choice_reactions = ["1️⃣", "2️⃣", "3️⃣"]
        for i in range(len(problem_data["selected_choices"])):
            await encounter_message.add_reaction(choice_reactions[i])
            
        # Store the encounter data for reaction handling
        self.active_encounters[channel.id] = {
            "message_id": encounter_message.id,
            "user_id": user_id,
            "problem_data": problem_data,
            "encounter_type": encounter_type,
            "expires": datetime.now() + timedelta(minutes=2),  # Encounter expires after 2 minutes
            "message": encounter_message  # Store the message object for easier deletion later
        }
        
        # Schedule automatic expiration
        self.bot.loop.create_task(self._expire_encounter(channel.id, encounter_message.id))
        
        # If this was converted from a pending encounter, remove it from pending
        if channel.id in self.pending_encounters:
            del self.pending_encounters[channel.id]
    
    async def _create_encounter_embed(self, user_id, encounter_type, problem_data):
        """Create an embed for the encounter"""
        npc_name = problem_data["npc"]
        problem_text = problem_data["problem"]
        
        # Format the scenario description
        scenario = f"You encounter {npc_name}. {problem_text}"
        
        # Format the choices
        choices_text = ""
        for i, choice in enumerate(problem_data["selected_choices"]):
            choice_text = choice.get("text", "Option text missing")
            choices_text += f"{i+1}. {choice_text}\n"
        
        # Create the embed
        embed = create_embed(
            title=f"⚔️ {encounter_type}!",
            description=f"<@{user_id}> has encountered something!\n\n{scenario}",
            color=discord.Color.purple() if encounter_type == "Random Encounter" else discord.Color.teal()
        )
        
        # Add choices to embed
        embed.add_field(
            name="Choices (React with 1️⃣, 2️⃣, or 3️⃣):",
            value=choices_text,
            inline=False
        )
        
        # Add a note for skill checks
        embed.set_footer(text=f"Each choice has a skill check • {encounter_type} • React to respond")
        
        return embed
    
    async def get_active_users(self, channel):
        """Get a list of active user IDs in the channel within the last 10 minutes"""
        active_users = []
        try:
            time_threshold = datetime.now() - timedelta(minutes=10)
            
            # Get recent messages
            async for message in channel.history(limit=20, after=time_threshold):
                if (not message.author.bot and 
                    message.author.id not in active_users):
                    active_users.append(message.author.id)
        except Exception as e:
            print(f"Error getting active users: {e}")
        
        return active_users
    
    async def _expire_pending_encounter(self, channel_id, message_id):
        """Remove the pending encounter after it expires"""
        await asyncio.sleep(120)  # Wait for 2 minutes
        
        # Check if this pending encounter is still active and hasn't been claimed
        if channel_id in self.pending_encounters and self.pending_encounters[channel_id]["message_id"] == message_id:
            try:
                # Get the message object
                message = self.pending_encounters[channel_id].get("message")
                if not message:
                    # Get the channel and fetch the message if we don't have it stored
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(message_id)
                        except discord.NotFound:
                            pass  # Message was already deleted
                
                if message:
                    # Create an expiration notice
                    embed = create_embed(
                        title="⌛ Event Opportunity Missed",
                        description="The event has passed without anyone investigating.",
                        color=discord.Color.dark_gray()
                    )
                    
                    # Update the message
                    await message.edit(embed=embed)
                    
                    # Clear reactions
                    await message.clear_reactions()
                    
                    # Delete the message after a delay
                    await asyncio.sleep(30)  # Wait 30 seconds before deleting
                    await message.delete()
                
                # Remove from pending encounters
                del self.pending_encounters[channel_id]
                
                # Set a cooldown for this channel to prevent immediate new encounters
                self.encounter_cooldowns[channel_id] = datetime.now() + timedelta(minutes=2)
            except Exception as e:
                print(f"Error expiring pending encounter: {e}")
                # Still try to clean up
                if channel_id in self.pending_encounters:
                    del self.pending_encounters[channel_id]
    
    async def _expire_encounter(self, channel_id, message_id):
        """Remove the encounter after it expires"""
        await asyncio.sleep(120)  # Wait for 2 minutes
        
        # Check if this encounter is still active and hasn't been handled
        if channel_id in self.active_encounters and self.active_encounters[channel_id]["message_id"] == message_id:
            try:
                # Get the message object
                message = self.active_encounters[channel_id].get("message")
                if not message:
                    # Get the channel and fetch the message if we don't have it stored
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(message_id)
                        except discord.NotFound:
                            pass  # Message was already deleted
                
                if message:
                    # Create an expiration notice
                    embed = create_embed(
                        title="⌛ Encounter Expired",
                        description="The opportunity has passed.",
                        color=discord.Color.dark_gray()
                    )
                    
                    # Update the message
                    await message.edit(embed=embed)
                    
                    # Clear reactions
                    await message.clear_reactions()
                    
                    # Delete the message after a delay
                    await asyncio.sleep(30)  # Wait 30 seconds before deleting
                    await message.delete()
                
                # Remove from active encounters
                del self.active_encounters[channel_id]
                
                # Set a cooldown for this channel to prevent immediate new encounters
                self.encounter_cooldowns[channel_id] = datetime.now() + timedelta(minutes=2)
            except Exception as e:
                print(f"Error expiring encounter: {e}")
                # Still try to clean up
                if channel_id in self.active_encounters:
                    del self.active_encounters[channel_id]
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle user interactions via reactions"""
        # Ignore bot reactions
        if user.bot:
            return
        
        channel_id = reaction.message.channel.id
        
        # Check if this is for a pending encounter (investigate reaction)
        if channel_id in self.pending_encounters and reaction.message.id == self.pending_encounters[channel_id]["message_id"]:
            if str(reaction.emoji) == "🔍":
                # Check if user has a player class
                has_player_class = False
                player_classes = self.player_class_handler.get_player_classes(user.id)
                if player_classes:  # If they have any classes
                    has_player_class = True
                
                if has_player_class:
                    # Convert this pending encounter to an active encounter for this user
                    await self.create_encounter(
                        reaction.message.channel, 
                        user.id,
                        original_message=reaction.message
                    )
                else:
                    # Inform the user they need to create a character first
                    error_msg = await reaction.message.channel.send(
                        f"{user.mention}, you need to create a character first! Use `!quests new` to create one."
                    )
                    await send_temp_message(error_msg, 15)  # Delete after 15 seconds
                    
                    # Remove their reaction
                    try:
                        await reaction.remove(user)
                    except:
                        pass  # Ignore if we can't remove the reaction
            return
        
        # Check if this is for an active encounter (choice reactions)
        if channel_id in self.active_encounters:
            encounter = self.active_encounters[channel_id]
            
            # Check if this is the right message
            if reaction.message.id != encounter["message_id"]:
                return
            
            # Check if this is the target user
            if user.id != encounter["user_id"]:
                # If not the target user, remove their reaction
                try:
                    await reaction.remove(user)
                except:
                    pass  # Ignore if we can't remove the reaction
                return
                
            # Check if the encounter is still active
            if encounter["expires"] < datetime.now():
                return
                
            # Get the choice index (1, 2, or 3)
            choice_emojis = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2}
            if str(reaction.emoji) not in choice_emojis:
                return
                
            choice_idx = choice_emojis[str(reaction.emoji)]
            problem_data = encounter["problem_data"]
            
            # Check if the choice is valid
            if choice_idx >= len(problem_data["selected_choices"]):
                return
            
            # Get the selected choice
            selected_choice = problem_data["selected_choices"][choice_idx]
            
            # Determine if this is a correct choice
            is_correct = choice_idx in problem_data["correct_indices"]
            
            # If correct choice, check skill DC
            success = False
            if is_correct:
                # Get player data
                player_data = self.player_manager.get_player_data(user.id)
                
                # Get skill and DC information
                skill_name = selected_choice.get("skill", "Unknown")
                skill_dc = selected_choice.get("skill_dc", 10)
                
                # Check if player meets the DC with their skill (simplified version)
                player_skill = self._get_player_skill_level(player_data, skill_name)
                
                # Roll d20 + skill modifier
                skill_roll = random.randint(1, 20) + player_skill
                
                # Success if roll meets or exceeds DC
                success = skill_roll >= skill_dc
                
                # Create result message
                if success:
                    outcome_text = selected_choice.get("success_outcome", "You succeed at the task.")
                    result_title = f"✅ Success! ({skill_name} check: {skill_roll} vs DC {skill_dc})"
                    result_color = discord.Color.green()
                else:
                    outcome_text = selected_choice.get("failure_outcome", "You fail at the task.")
                    result_title = f"❌ Failed Skill Check ({skill_name}: {skill_roll} vs DC {skill_dc})"
                    result_color = discord.Color.red()
            else:
                # For incorrect choices, always fail
                outcome_text = selected_choice.get("outcome", "Your approach fails completely.")
                result_title = "❌ Failure!"
                result_color = discord.Color.red()
                success = False
            
            # Create result embed
            result_embed = create_embed(
                title=result_title,
                description=outcome_text,
                color=result_color
            )
            
            # If success, add rewards to player
            if success:
                # Generate random rewards
                xp = random.randint(100, 300)
                gold = random.randint(10, 50)
                
                # Add rewards to player
                player_data = self.player_manager.get_player_data(user.id)
                if player_data:
                    player_data["xp"] = player_data.get("xp", 0) + xp
                    player_data["gold"] = player_data.get("gold", 0) + gold
                    
                    # Check for level up
                    old_level = player_data.get("level", 1)
                    new_level = max(1, 1 + int((player_data["xp"] / 100) ** 0.5))
                    
                    if new_level > old_level:
                        player_data["level"] = new_level
                        result_embed.add_field(
                            name="🌟 Level Up!",
                            value=f"You've reached level {new_level}!",
                            inline=False
                        )
                    
                    self.player_manager.save_player_data(user.id, player_data)
                
                # Add rewards info to embed
                result_embed.add_field(
                    name="💰 Rewards",
                    value=f"**+{xp} XP**\n**+{gold} Gold**",
                    inline=False
                )
            
            # Send result message
            result_message = await reaction.message.channel.send(embed=result_embed)
            
            # Update the original message to show it's been resolved
            try:
                original_embed = reaction.message.embeds[0]
                original_embed.set_footer(text="This encounter has been resolved")
                await reaction.message.edit(embed=original_embed)
                await reaction.message.clear_reactions()
                
                # Delete the original message after a delay
                self.bot.loop.create_task(self._delayed_delete(reaction.message, 30))
            except Exception as e:
                print(f"Error updating original message: {e}")
            
            # Remove this encounter from active encounters
            if channel_id in self.active_encounters:
                del self.active_encounters[channel_id]
                
            # Set a cooldown for this channel
            self.encounter_cooldowns[channel_id] = datetime.now() + timedelta(minutes=2)
            
            # Auto-delete result after 1 minute
            await send_temp_message(result_message, 60)

    async def _delayed_delete(self, message, delay_seconds=30):
        """Delete a message after a delay"""
        await asyncio.sleep(delay_seconds)
        try:
            await message.delete()
        except:
            pass  # Ignore errors (message might be already deleted)

    def _get_player_skill_level(self, player_data, skill_name):
        """
        Calculate a player's effective skill level.
        This is a placeholder implementation that should be expanded with the
        actual player skill system.
        """
        if not player_data:
            return 0
            
        # Get player level as base
        player_level = player_data.get("level", 1)
        
        # Get skills from player data (to be implemented with class system)
        skills = player_data.get("skills", {})
        
        # Get specific skill bonus if it exists
        skill_bonus = skills.get(skill_name, 0)
        
        # Get ability score bonus
        ability_score_bonus = self._get_ability_score_bonus(player_data, skill_name)
        
        # Calculate total
        # Formula: level/4 (rounded down) + skill bonus + ability score bonus
        return player_level // 4 + skill_bonus + ability_score_bonus
    
    def _get_ability_score_bonus(self, player_data, skill_name):
        """Get the ability score bonus for a specific skill"""
        # Map of skills to ability scores
        skill_to_ability = {
            "Acrobatics": "dexterity",
            "Animal Handling": "wisdom",
            "Arcana": "intelligence",
            "Athletics": "strength",
            "Deception": "charisma",
            "History": "intelligence",
            "Insight": "wisdom",
            "Intimidation": "charisma",
            "Investigation": "intelligence",
            "Medicine": "wisdom",
            "Nature": "intelligence",
            "Perception": "wisdom",
            "Performance": "charisma",
            "Persuasion": "charisma",
            "Religion": "intelligence",
            "Sleight of Hand": "dexterity",
            "Stealth": "dexterity",
            "Survival": "wisdom"
        }
        
        # Get the related ability score
        ability = skill_to_ability.get(skill_name, "intelligence")  # Default to INT
        
        # Get ability scores from player data
        ability_scores = player_data.get("ability_scores", {})
        
        # Get the ability score value
        score = ability_scores.get(ability, 10)  # Default to 10
        
        # Calculate bonus: (score - 10) / 2, rounded down
        return (score - 10) // 2
    
    def _is_channel_enabled(self, guild_id, channel_id):
        """Check if random encounters are enabled for a specific channel"""
        try:
            # Check if the channels file exists
            if not os.path.exists(self.QUEST_CHANNELS_FILE):
                return False
                
            # Load the enabled channels
            with open(self.QUEST_CHANNELS_FILE, 'r') as f:
                enabled_channels = json.load(f)
                
            # Convert IDs to strings for comparison
            guild_id_str = str(guild_id)
            channel_id_str = str(channel_id)
            
            # Check if channel is enabled
            return (guild_id_str in enabled_channels and 
                   channel_id_str in enabled_channels[guild_id_str])
        except Exception as e:
            print(f"Error checking if channel is enabled: {e}")
            return False
    
    def refresh_enabled_channels(self):
        """Refresh the list of enabled channels (called from other modules)"""
        # This is just a stub in case we need to do any processing when channels change
        pass

async def setup(bot):
    await bot.add_cog(NewRandomEncounters(bot))