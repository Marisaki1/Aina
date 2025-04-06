import discord
from discord.ext import commands, tasks
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
from .utils import create_embed
from .player_manager import PlayerManager

class RandomEncounters(commands.Cog):
    def __init__(self, bot, llm_manager):
        self.bot = bot
        self.llm_manager = llm_manager  # Your GGUF AI model manager
        self.player_manager = PlayerManager()
        self.active_encounters = {}  # Track active encounters by channel
        self.encounter_messages = {}  # Track encounter messages
        
        # Ensure player location data directory exists
        os.makedirs("data/quests/playerdata", exist_ok=True)
        
        # Start the random encounter task
        self.spawn_random_encounter.start()
    
    def cog_unload(self):
        # Stop the task when the cog is unloaded
        self.spawn_random_encounter.cancel()
    
    @tasks.loop(minutes=1)  # Check every minute
    async def spawn_random_encounter(self):
        # Get all text channels in all guilds
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                # Skip if there's already an active encounter in this channel
                if channel.id in self.active_encounters:
                    continue
                
                # Random chance to spawn an encounter (approx every 5-10 minutes)
                # This means a 1/7 chance each minute to spawn
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
        location = player_data.get("location", "Town of Rivermeet")
        if "location" not in player_data:
            player_data["location"] = "Town of Rivermeet"
            self.player_manager.save_player_data(target_user_id, player_data)
        
        # Generate encounter content using LLM
        prompt = f"""
        You are a Dungeon Master guiding a player through a Dungeons & Dragons 5e adventure.
        The player is currently in a **{location}**.
        Your job is to:
        - Present a short, immersive scenario appropriate to the current location.
        - Offer 3 distinct choices the player might make.
        - Only one choice should lead to a successful outcome.
        - Describe the outcome of **each** choice with flavor and D&D-style detail.
        Use the following format:
        Scenario:
        [Write a short, engaging scenario that fits the setting.]
        Choices:
        1. [Option 1]
        2. [Option 2]
        3. [Option 3]
        Outcomes:
        1. ❌ [Failure outcome and consequences]
        2. ✅ [Success outcome and why it worked]
        3. ❌ [Failure outcome and why it didn't work]
        If it's a {encounter_type} then the scenario should be a {"battle" if encounter_type == "Random Encounter" else "normal"} scenario.
        If it's a success then reward the player 100-300 XP and 10-50 Gold.
        """
        
        # Call your LLM manager to generate the encounter
        encounter_content = await self.generate_encounter(prompt)
        
        # Parse the generated content
        scenario, choices, outcomes = self.parse_encounter_content(encounter_content)
        
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
        
        # Schedule removal after 1 minute
        self.bot.loop.create_task(self.expire_encounter(channel.id, encounter_message.id))
    
    async def generate_encounter(self, prompt):
        """Generate encounter content using LLM manager"""
        try:
            # This will depend on your specific LLM implementation
            # For example:
            response = await self.llm_manager.generate(prompt)
            return response
            
            # If you don't have an async LLM manager, you might need to use:
            # loop = asyncio.get_event_loop()
            # response = await loop.run_in_executor(None, lambda: self.llm_manager.generate(prompt))
            # return response
        except Exception as e:
            print(f"Error generating encounter: {e}")
            return """
            Scenario:
            You encounter a mysterious fog in the path ahead. It seems to shimmer with an otherworldly glow.
            
            Choices:
            1. Walk straight through the fog
            2. Throw a stone into the fog to see what happens
            3. Try to go around the fog by leaving the path
            
            Outcomes:
            1. ❌ You walk into the fog and start feeling disoriented and sick. You take 2 damage as the magic fog drains your energy.
            2. ✅ The stone creates a pathway through the fog as it disrupts the magical energies. You follow the path safely and find 25 gold coins on the other side. Gain 150 XP.
            3. ❌ Going around leads you into a patch of poisonous plants. You get a rash and lose 1 health from the irritation.
            """
    
    def parse_encounter_content(self, content):
        """Parse the generated content into scenario, choices, and outcomes"""
        sections = content.split("Scenario:", 1)
        if len(sections) > 1:
            content = sections[1]
        
        # Split the content by headers
        parts = content.split("Choices:", 1)
        if len(parts) < 2:
            # Fallback if format is wrong
            return (
                "You encounter something unusual...",
                "1. Option A\n2. Option B\n3. Option C",
                ["Failure", "Success", "Failure"]
            )
        
        scenario = parts[0].strip()
        remaining = parts[1]
        
        parts = remaining.split("Outcomes:", 1)
        if len(parts) < 2:
            choices = "1. Option A\n2. Option B\n3. Option C"
            outcomes = ["Failure", "Success", "Failure"]
        else:
            choices = parts[0].strip()
            outcomes_text = parts[1].strip()
            
            # Parse outcomes
            outcomes = []
            outcome_lines = outcomes_text.split("\n")
            current_outcome = ""
            
            for line in outcome_lines:
                if line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
                    if current_outcome:
                        outcomes.append(current_outcome)
                    current_outcome = line
                elif current_outcome:
                    current_outcome += " " + line.strip()
            
            if current_outcome:
                outcomes.append(current_outcome)
            
            # Ensure we have exactly 3 outcomes
            while len(outcomes) < 3:
                outcomes.append("Outcome not provided")
        
        return scenario, choices, outcomes
    
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
                    # Get the message
                    # try:
                    #     message = await channel.fetch_message(message_id)
                        
                    #     # Update the embed to show it's expired
                    #     embed = message.embeds[0]
                    #     embed.title += " (Expired)"
                    #     embed.color = discord.Color.darker_grey()
                    #     embed.set_footer(text="This encounter has expired")
                        
                    #     await message.edit(embed=embed)
                    # except discord.NotFound:
                    #     pass  # Message was deleted
                # In the expire_encounter method, replace the message edit with:
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.delete()
                    except discord.NotFound:
                        pass  # Message was already deleted

                # Remove from active encounters
                del self.active_encounters[channel_id]
            except Exception as e:
                print(f"Error expiring encounter: {e}")
    
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
            
            # If success, award XP and gold
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
            
            # Send result message
            await reaction.message.channel.send(embed=result_embed)
            
            # Update original message
            original_embed = reaction.message.embeds[0]
            original_embed.title += " (Resolved)"
            original_embed.set_footer(text=f"Resolved by {user.display_name}")
            await reaction.message.edit(embed=original_embed)
            
            # Remove from active encounters
            del self.active_encounters[channel_id]
        
    @commands.group(name="location", invoke_without_command=True)
    async def location(self, ctx):
        """View or change your character's location"""
        player_data = self.player_manager.get_player_data(ctx.author.id)
        
        if not player_data:
            # Create new player data if not exists
            player_data = self.player_manager.create_player(ctx.author.id, ctx.author.display_name)
        
        # Get or set player location
        location = player_data.get("location", "Town of Rivermeet")
        if "location" not in player_data:
            player_data["location"] = "Town of Rivermeet"
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
            "Town of Rivermeet", "Whispering Forest", "Dragonclaw Mountains", 
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
        
        old_location = player_data.get("location", "Town of Rivermeet")
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
            "Town of Rivermeet", "Whispering Forest", "Dragonclaw Mountains", 
            "Crystal Caves", "Shadowmire Swamp", "Forgotten Ruins",
            "Sunlit Plains", "Frostpeak Village", "Emerald Sea"
        ]
        
        embed = create_embed(
            title="🗺️ Available Locations",
            description="Travel to these locations to encounter different events and challenges:",
            color=discord.Color.blue()
        )
        
        # Group locations by type
        towns = ["Town of Rivermeet", "Frostpeak Village"]
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

async def setup(bot):
    # Import the updated LLM manager class
    from .llm_manager import LLMManager
    
    # Initialize LLM manager with proper configuration
    # Note: This will use the underlying implementation from llm_core.py
    llm_manager = LLMManager()
    
    # Add the cog to the bot
    await bot.add_cog(RandomEncounters(bot, llm_manager)) # type: ignore