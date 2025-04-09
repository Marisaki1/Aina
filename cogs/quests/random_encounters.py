import re
import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
from .utils import create_embed
from .player_manager import PlayerManager
from .scenario_maker import ScenarioMaker

class RandomEncounters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player_manager = PlayerManager()
        self.active_encounters = {}  # Track active encounters by channel
        self.encounter_messages = {}  # Track encounter messages
        self.scenario_maker = ScenarioMaker()  # Scenario maker instance
        
        # Ensure player location data directory exists
        os.makedirs("data/quests/playerdata", exist_ok=True)
        
        # Start the random encounter task
        self.spawn_random_encounter.start()
    
    def cog_unload(self):
        # Stop the task when the cog is unloaded
        self.spawn_random_encounter.cancel()
    
    @tasks.loop(seconds=2)  # Check every minute
    async def spawn_random_encounter(self):
        # Process all guilds and channels concurrently
        tasks = []
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                tasks.append(self._process_channel_for_encounter(channel))
        
        await asyncio.gather(*tasks)

    async def _process_channel_for_encounter(self, channel):
        """Check and potentially spawn an encounter in a single channel"""
        # Skip if there's already an active encounter in this channel
        if channel.id in self.active_encounters:
            return
        
        # Random chance to spawn an encounter (approx every 5-10 minutes)
        if random.randint(1, 7) == 1:
            try:
                # Randomly choose between encounter and event
                encounter_type = random.choice(["Random Encounter", "Random Event"])
                
                # Create and send the encounter
                await self.create_encounter(channel, encounter_type)
            except Exception as e:
                print(f"Error creating encounter in {channel.name}: {e}")
    
    async def create_encounter(self, channel, encounter_type):
        """Create and send a random encounter or event to the channel"""
        # Get active users in the channel with recent messages
        active_users = await self.get_active_users(channel)
        
        if not active_users:
            return  # No active users, don't spawn encounter
        
        # Select a random active user for the encounter
        target_user_id = random.choice(active_users)
        
        # Get player location or set default
        player_data = self.player_manager.get_player_data(target_user_id)
        if not player_data:
            # Create new player data if not exists
            player_data = self.player_manager.create_player(target_user_id, str(target_user_id))
        
        # Get or set player location
        location = player_data.get("location", "Rivermeet")
        if "location" not in player_data:
            player_data["location"] = "Rivermeet"
            self.player_manager.save_player_data(target_user_id, player_data)
        
        # Generate a scenario using the ScenarioMaker
        scenario_data = self.scenario_maker.generate_scenario(location)
        
        # Create encounter content using scenario data
        scenario, choices, outcomes = self.create_encounter_from_scenario_data(scenario_data, encounter_type)
        
        # Create embed
        embed = create_embed(
            title=f"⚔️ {encounter_type}!",
            description=f"<@{target_user_id}> has encountered something!\n\n{scenario}",
            color=discord.Color.purple() if encounter_type == "Random Encounter" else discord.Color.teal()
        )
        
        # Add choices to embed
        embed.add_field(
            name="Choices (React with 1️⃣, 2️⃣, or 3️⃣):",
            value=choices,
            inline=False
        )
        
        # Send the encounter message
        encounter_message = await channel.send(embed=embed)
        
        # Add reactions for choices
        await encounter_message.add_reaction("1️⃣")
        await encounter_message.add_reaction("2️⃣")
        await encounter_message.add_reaction("3️⃣")
        
        # Store encounter data
        self.active_encounters[channel.id] = {
            "message_id": encounter_message.id,
            "user_id": target_user_id,
            "encounter_type": encounter_type,
            "outcomes": outcomes,
            "expires": datetime.now() + timedelta(minutes=1)
        }

        # Save encounter data for reuse
        self.save_encounter_data(  
            target_user_id,
            location,
            encounter_type,
            scenario,
            choices,
            outcomes
        )        

        # Schedule removal after 1 minute
        self.bot.loop.create_task(self.expire_encounter(channel.id, encounter_message.id))
    
    def create_encounter_from_scenario_data(self, scenario_data, encounter_type):
        """Create a structured encounter from scenario data"""
        # Extract relevant data
        npcs = " and ".join(scenario_data["npcs"])
        location = scenario_data["location"]
        problem = scenario_data["problem"]
        
        # Create scenario text
        scenario_text = f"You encounter {npcs} at {location}. {problem}."
        
        # Get choices and outcomes from scenario data
        choices = "\n".join(scenario_data["choices"])
        outcomes = scenario_data["outcomes"]
        
        return scenario_text, choices, outcomes
    
    def save_encounter_data(self, target_user_id, location, encounter_type, scenario, choices, outcomes):
        """Save encounter data to JSON file for reuse"""
        encounter_file = "data/quests/encounters.json"
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(encounter_file), exist_ok=True)
        
        # Load existing encounters
        try:
            with open(encounter_file, "r") as f:
                encounters = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            encounters = []
        
        # Process outcomes to ensure they're separate
        processed_outcomes = []
        for outcome in outcomes:
            # Clean up the outcome text
            processed_outcomes.append(outcome.strip())
        
        # Make sure we have exactly 3 outcomes
        while len(processed_outcomes) < 3:
            processed_outcomes.append(f"{len(processed_outcomes)+1}. Outcome not provided")
        
        # Find success index
        success_index = -1
        for i, outcome in enumerate(processed_outcomes):
            if "✅" in outcome:
                success_index = i
                break
        
        # If no success found, default to option 2
        if success_index == -1:
            success_index = 1
        
        # Create new encounter record
        encounter_data = {
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "encounter_type": encounter_type,
            "user_id": target_user_id,
            "scenario": scenario,
            "choices": choices,
            "outcomes": processed_outcomes,
            "success_index": success_index
        }
        
        # Add to encounters list
        encounters.append(encounter_data)
        
        # Save back to file (limit to 1000 encounters to prevent file bloat)
        if len(encounters) > 1000:
            encounters = encounters[-1000:]
        
        with open(encounter_file, "w") as f:
            json.dump(encounters, f, indent=4)
        
        print(f"Saved encounter data for {location} ({encounter_type})")

    async def get_active_users(self, channel):
        """Get a list of active user IDs in the channel within the last 10 minutes"""
        active_users = []
        try:
            time_threshold = datetime.now() - timedelta(minutes=10)
            
            # Get recent messages
            async for message in channel.history(limit=10, after=time_threshold):
                if (not message.author.bot and 
                    message.author.id not in active_users):
                    active_users.append(message.author.id)
        except Exception as e:
            print(f"Error getting active users: {e}")
        
        return active_users
    
    async def expire_encounter(self, channel_id, message_id):
        """Remove the encounter after 1 minute"""
        await asyncio.sleep(60)  # Wait for 1 minute
        
        if channel_id in self.active_encounters and self.active_encounters[channel_id]["message_id"] == message_id:
            try:
                # Get the channel
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Get and delete the message
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.delete()
                    except discord.NotFound:
                        pass  # Message was already deleted

                # Remove from active encounters
                del self.active_encounters[channel_id]
            except Exception as e:
                print(f"Error expiring encounter: {e}")
    
    async def delete_after_delay(self, message, delay_seconds):
        """Delete a message after specified delay"""
        await asyncio.sleep(delay_seconds)
        try:
            await message.delete()
        except discord.NotFound:
            pass  # Message was already deleted
        except Exception as e:
            print(f"Error deleting result message: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle user choices via reactions"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if this is for one of our encounters
        channel_id = reaction.message.channel.id
        if channel_id not in self.active_encounters:
            return
            
        encounter = self.active_encounters[channel_id]
        
        # Check if this is the target user
        if user.id != encounter["user_id"]:
            return
            
        # Check if this is the right message
        if reaction.message.id != encounter["message_id"]:
            return
            
        # Check if the encounter is still active
        if encounter["expires"] < datetime.now():
            return
            
        # Get the choice index (1, 2, or 3)
        choice_emojis = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2}
        if reaction.emoji not in choice_emojis:
            return
            
        choice_idx = choice_emojis[reaction.emoji]
        
        # Get the outcome
        if choice_idx < len(encounter["outcomes"]):
            outcome = encounter["outcomes"][choice_idx]
            
            # Determine if success or failure
            is_success = "✅" in outcome
            
            # Strip the success/failure emoji from the outcome text
            clean_outcome = outcome.replace("✅ ", "").replace("❌ ", "")
            
            # Create result embed
            result_embed = create_embed(
                title=f"{'✅ Success!' if is_success else '❌ Failure!'}",
                description=clean_outcome,  # Only show the chosen outcome text
                color=discord.Color.green() if is_success else discord.Color.red()
            )
            
            # If success, add rewards to player
            if is_success:
                # Generate random rewards
                xp = random.randint(100, 300)
                gold = random.randint(10, 50)
                
                # Add rewards to player
                player_data = self.player_manager.get_player_data(user.id)
                if player_data:
                    player_data["xp"] = player_data.get("xp", 0) + xp
                    player_data["gold"] = player_data.get("gold", 0) + gold
                    self.player_manager.save_player_data(user.id, player_data)
                
                # Add rewards info to embed
                result_embed.add_field(
                    name="💰 Rewards",
                    value=f"**+{xp} XP**\n**+{gold} Gold**",
                    inline=False
                )
            
            # Add Quest System version to footer
            result_embed.set_footer(text="Quest System v1.0")
            
            # Send result message
            result_message = await reaction.message.channel.send(embed=result_embed)
            
            # Schedule result message deletion after 1 minute
            self.bot.loop.create_task(self.delete_after_delay(result_message, 60))
            
            # Mark this encounter as completed but keep it visible for a while
            if channel_id in self.active_encounters:
                # Update the encounter data to mark it as handled
                self.active_encounters[channel_id]["handled"] = True
                
                # Schedule the original encounter message deletion after 30 seconds
                # This gives players time to read both the original scenario and the outcome
                self.bot.loop.create_task(self.delete_after_delay(reaction.message, 30))
                
                # Remove from active encounters after a delay
                self.bot.loop.create_task(self.remove_encounter_after_delay(channel_id, encounter["message_id"], 30))

    async def remove_encounter_after_delay(self, channel_id, message_id, delay_seconds):
        """Remove the encounter from tracking after a delay"""
        await asyncio.sleep(delay_seconds)
        if channel_id in self.active_encounters and self.active_encounters[channel_id]["message_id"] == message_id:
            del self.active_encounters[channel_id]
        
    @commands.group(name="location", invoke_without_command=True)
    async def location(self, ctx):
        """View or change your character's location"""
        player_data = self.player_manager.get_player_data(ctx.author.id)
        
        if not player_data:
            # Create new player data if not exists
            player_data = self.player_manager.create_player(ctx.author.id, ctx.author.display_name)
        
        # Get or set player location
        location = player_data.get("location", "Rivermeet")
        if "location" not in player_data:
            player_data["location"] = "Rivermeet"
            self.player_manager.save_player_data(ctx.author.id, player_data)
        
        embed = create_embed(
            title="🗺️ Your Location",
            description=f"You are currently in **{location}**.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Available Commands",
            value=(
                "**!location set <place>** - Change your location\n"
                "**!location list** - View available locations"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @location.command(name="set")
    async def set_location(self, ctx, *, new_location):
        """Set your character's location"""
        # List of allowed locations
        allowed_locations = [
            "Rivermeet", "Whispering Forest", "Dragonclaw Mountains", 
            "Crystal Caves", "Shadowmire Swamp", "Forgotten Ruins",
            "Sunlit Plains", "Frostpeak Village", "Emerald Sea"
        ]
        
        # Normalize input for fuzzy matching
        normalized_input = new_location.lower()
        best_match = None
        
        for location in allowed_locations:
            if location.lower() == normalized_input:
                best_match = location
                break
            elif location.lower() in normalized_input or normalized_input in location.lower():
                best_match = location
        
        if not best_match:
            embed = create_embed(
                title="❌ Invalid Location",
                description=f"'{new_location}' is not a recognized location.\nUse `!location list` to see available locations.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Update player location
        player_data = self.player_manager.get_player_data(ctx.author.id)
        if not player_data:
            player_data = self.player_manager.create_player(ctx.author.id, ctx.author.display_name)
        
        old_location = player_data.get("location", "Rivermeet")
        player_data["location"] = best_match
        self.player_manager.save_player_data(ctx.author.id, player_data)
        
        # Send confirmation
        embed = create_embed(
            title="🗺️ Location Changed",
            description=f"You have traveled from **{old_location}** to **{best_match}**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @location.command(name="list")
    async def list_locations(self, ctx):
        """List all available locations"""
        locations = [
            "Rivermeet", "Whispering Forest", "Dragonclaw Mountains", 
            "Crystal Caves", "Shadowmire Swamp", "Forgotten Ruins",
            "Sunlit Plains", "Frostpeak Village", "Emerald Sea"
        ]
        
        embed = create_embed(
            title="🗺️ Available Locations",
            description="Travel to these locations to encounter different events and challenges:",
            color=discord.Color.blue()
        )
        
        # Group locations by type
        towns = ["Rivermeet", "Frostpeak Village"]
        wilderness = ["Whispering Forest", "Shadowmire Swamp", "Sunlit Plains", "Emerald Sea"]
        dangerous = ["Dragonclaw Mountains", "Crystal Caves", "Forgotten Ruins"]
        
        embed.add_field(
            name="🏘️ Towns & Settlements",
            value="\n".join([f"• {loc}" for loc in towns]),
            inline=False
        )
        
        embed.add_field(
            name="🌲 Wilderness",
            value="\n".join([f"• {loc}" for loc in wilderness]),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Dangerous Areas",
            value="\n".join([f"• {loc}" for loc in dangerous]),
            inline=False
        )
        
        embed.set_footer(text="Use !location set <place> to travel to a new location")
        await ctx.send(embed=embed)

    def refresh_enabled_channels(self):
        """Refresh the list of enabled channels"""
        # This is a placeholder for any functionality needed to refresh enabled channels
        pass

async def setup(bot):
    await bot.add_cog(RandomEncounters(bot))