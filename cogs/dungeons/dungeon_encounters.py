import random
import asyncio
from typing import Dict, List, Tuple, Any, Optional, Union
import discord
from datetime import datetime, timedelta

import settings

class DungeonEncounterManager:
    """Manages encounters within dungeons, including traps and battles."""
    
    def __init__(self, bot):
        """Initialize the encounter manager."""
        self.bot = bot
        self.settings = settings.DUNGEON_SETTINGS
        self.active_encounters = {}  # {channel_id: encounter_data}
        self.player_cooldowns = {}  # {user_id: timestamp}
        
        # Load encounter tables
        self.trap_encounters = self._load_trap_encounters()
        self.battle_encounters = self._load_battle_encounters()
        self.random_events = self._load_random_events()
    
    def _load_trap_encounters(self) -> List[Dict[str, Any]]:
        """Load trap encounters data"""
        # This would ideally load from a JSON file, but for now we'll define them here
        return [
            {
                "id": "pit_trap",
                "name": "Pit Trap",
                "description": "The floor suddenly gives way beneath you!",
                "difficulty": {
                    "EASY": {"dc": 10, "damage": [5, 10]},
                    "NORMAL": {"dc": 12, "damage": [10, 20]},
                    "HARD": {"dc": 15, "damage": [15, 30]},
                    "LUNATIC": {"dc": 18, "damage": [20, 40]}
                },
                "skill_check": "Dexterity",
                "success_message": "You catch yourself on the edge just in time and pull yourself up safely.",
                "failure_message": "You fall into the pit, taking {damage} damage!"
            },
            {
                "id": "poison_darts",
                "name": "Poison Darts",
                "description": "Darts shoot out from hidden holes in the walls!",
                "difficulty": {
                    "EASY": {"dc": 11, "damage": [5, 15]},
                    "NORMAL": {"dc": 13, "damage": [10, 25]},
                    "HARD": {"dc": 16, "damage": [15, 35]},
                    "LUNATIC": {"dc": 19, "damage": [20, 45]}
                },
                "skill_check": "Dexterity",
                "success_message": "You dodge the darts with impressive reflexes!",
                "failure_message": "The darts strike you, inflicting {damage} damage and mild poison!"
            },
            {
                "id": "magical_runes",
                "name": "Magical Runes",
                "description": "Arcane runes on the floor begin to glow with dangerous energy!",
                "difficulty": {
                    "EASY": {"dc": 10, "damage": [10, 15]},
                    "NORMAL": {"dc": 12, "damage": [15, 25]},
                    "HARD": {"dc": 15, "damage": [20, 35]},
                    "LUNATIC": {"dc": 18, "damage": [25, 50]}
                },
                "skill_check": "Intelligence",
                "success_message": "You quickly decipher the runes and safely disable them.",
                "failure_message": "The runes explode with magical energy, dealing {damage} damage!"
            },
            {
                "id": "falling_rocks",
                "name": "Falling Rocks",
                "description": "You hear a rumbling from above as rocks begin to fall!",
                "difficulty": {
                    "EASY": {"dc": 10, "damage": [5, 15]},
                    "NORMAL": {"dc": 12, "damage": [10, 25]},
                    "HARD": {"dc": 15, "damage": [15, 35]},
                    "LUNATIC": {"dc": 18, "damage": [20, 45]}
                },
                "skill_check": "Strength",
                "success_message": "You shield yourself and push through the falling debris!",
                "failure_message": "You're caught in the rockfall, taking {damage} damage!"
            },
            {
                "id": "gas_trap",
                "name": "Poisonous Gas",
                "description": "A noxious green gas begins filling the room!",
                "difficulty": {
                    "EASY": {"dc": 11, "damage": [5, 10]},
                    "NORMAL": {"dc": 13, "damage": [10, 20]},
                    "HARD": {"dc": 16, "damage": [15, 30]},
                    "LUNATIC": {"dc": 19, "damage": [20, 40]}
                },
                "skill_check": "Constitution",
                "success_message": "You hold your breath and make it through the gas cloud!",
                "failure_message": "You inhale the gas, coughing violently and taking {damage} damage!"
            }
        ]
    
    def _load_battle_encounters(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load battle encounters data, organized by difficulty"""
        # This would ideally load from a JSON file, but for now we'll define them here
        return {
            "EASY": [
                {
                    "id": "goblin_scout",
                    "name": "Goblin Scout",
                    "description": "A small, sneaky goblin wielding a knife!",
                    "hp": 20,
                    "attack": 5,
                    "defense": 3,
                    "xp": 50,
                    "gold": 10,
                    "special": "None"
                },
                {
                    "id": "giant_rat",
                    "name": "Giant Rat",
                    "description": "An oversized rodent with vicious teeth!",
                    "hp": 15,
                    "attack": 4,
                    "defense": 2,
                    "xp": 30,
                    "gold": 5,
                    "special": "None"
                },
                {
                    "id": "skeleton",
                    "name": "Skeleton",
                    "description": "A reanimated skeleton wielding a rusty sword!",
                    "hp": 25,
                    "attack": 6,
                    "defense": 4,
                    "xp": 60,
                    "gold": 15,
                    "special": "Undead"
                }
            ],
            "NORMAL": [
                {
                    "id": "goblin_warrior",
                    "name": "Goblin Warrior",
                    "description": "A battle-hardened goblin with crude but effective armor!",
                    "hp": 40,
                    "attack": 8,
                    "defense": 6,
                    "xp": 100,
                    "gold": 25,
                    "special": "None"
                },
                {
                    "id": "zombie",
                    "name": "Zombie",
                    "description": "A shambling undead creature with rotting flesh!",
                    "hp": 50,
                    "attack": 7,
                    "defense": 5,
                    "xp": 90,
                    "gold": 20,
                    "special": "Undead"
                },
                {
                    "id": "giant_spider",
                    "name": "Giant Spider",
                    "description": "A massive arachnid with venomous fangs!",
                    "hp": 35,
                    "attack": 9,
                    "defense": 4,
                    "xp": 110,
                    "gold": 30,
                    "special": "Poison"
                }
            ],
            "HARD": [
                {
                    "id": "orc_warrior",
                    "name": "Orc Warrior",
                    "description": "A muscular orc with a massive battleaxe!",
                    "hp": 80,
                    "attack": 12,
                    "defense": 8,
                    "xp": 200,
                    "gold": 50,
                    "special": "Rage"
                },
                {
                    "id": "wraith",
                    "name": "Wraith",
                    "description": "A malevolent spirit that seems to float through the air!",
                    "hp": 65,
                    "attack": 14,
                    "defense": 10,
                    "xp": 220,
                    "gold": 60,
                    "special": "Drain"
                },
                {
                    "id": "minotaur",
                    "name": "Minotaur",
                    "description": "A towering bull-headed humanoid with a massive hammer!",
                    "hp": 100,
                    "attack": 15,
                    "defense": 12,
                    "xp": 250,
                    "gold": 70,
                    "special": "Charge"
                }
            ],
            "LUNATIC": [
                {
                    "id": "dragon_wyrmling",
                    "name": "Dragon Wyrmling",
                    "description": "A young dragon with developing scales and growing power!",
                    "hp": 150,
                    "attack": 20,
                    "defense": 15,
                    "xp": 500,
                    "gold": 200,
                    "special": "Breath"
                },
                {
                    "id": "lich",
                    "name": "Lich",
                    "description": "An undead sorcerer of immense power!",
                    "hp": 120,
                    "attack": 25,
                    "defense": 18,
                    "xp": 450,
                    "gold": 180,
                    "special": "Magic"
                },
                {
                    "id": "demon",
                    "name": "Lesser Demon",
                    "description": "A terrifying fiend from another plane of existence!",
                    "hp": 180,
                    "attack": 22,
                    "defense": 16,
                    "xp": 550,
                    "gold": 250,
                    "special": "Fire"
                }
            ]
        }
    
    def _load_random_events(self) -> List[Dict[str, Any]]:
        """Load random events that can occur in the dungeon"""
        return [
            {
                "id": "healing_fountain",
                "name": "Healing Fountain",
                "description": "You discover a magical fountain that restores health!",
                "effect": "heal",
                "value": 30,
                "message": "You drink from the fountain and feel revitalized! (+{value} HP)"
            },
            {
                "id": "treasure_cache",
                "name": "Hidden Treasure",
                "description": "You find a small cache of gold hidden in a loose stone!",
                "effect": "gold",
                "value": [20, 50],
                "message": "You pocket {value} gold coins!"
            },
            {
                "id": "magical_shrine",
                "name": "Magical Shrine",
                "description": "You come across a small shrine radiating magical energy.",
                "effect": "buff",
                "value": "random",
                "message": "The shrine's magic infuses you with power! ({value})"
            },
            {
                "id": "collapsed_passage",
                "name": "Collapsed Passage",
                "description": "Part of the dungeon has collapsed, blocking your path!",
                "effect": "obstacle",
                "value": "strength",
                "message": "You manage to clear a path through the debris."
            },
            {
                "id": "mysterious_stranger",
                "name": "Mysterious Stranger",
                "description": "You encounter a hooded figure who offers you advice.",
                "effect": "info",
                "value": "random",
                "message": "The stranger whispers: '{value}'"
            }
        ]
    
    async def handle_trap_encounter(self, channel, user, dungeon_difficulty):
        """
        Handle a trap encounter for a player
        
        Args:
            channel: Discord channel
            user: The user who triggered the trap
            dungeon_difficulty: The dungeon's difficulty level
        """
        # Select a random trap
        trap = random.choice(self.trap_encounters)
        
        # Get difficulty settings for the trap
        diff_settings = trap["difficulty"][dungeon_difficulty]
        
        # Create trap encounter embed
        embed = discord.Embed(
            title=f"⚠️ {trap['name']} Trap!",
            description=trap["description"],
            color=settings.EMBED_COLORS["WARNING"]
        )
        
        embed.add_field(
            name="Skill Check",
            value=f"**{trap['skill_check']}** check (DC {diff_settings['dc']})",
            inline=False
        )
        
        # Add instructions
        embed.add_field(
            name="Action Required",
            value=f"React with 🎲 to attempt to disarm or avoid the trap!",
            inline=False
        )
        
        # Send trap message
        trap_msg = await channel.send(content=user.mention, embed=embed)
        await trap_msg.add_reaction("🎲")
        
        # Store the encounter
        self.active_encounters[f"{channel.id}_{user.id}"] = {
            "type": "trap",
            "data": trap,
            "difficulty": dungeon_difficulty,
            "message_id": trap_msg.id,
            "expires": datetime.now() + timedelta(minutes=2)
        }
        
        # Set up a timeout for the encounter
        self.bot.loop.create_task(
            self._expire_encounter(channel.id, user.id, trap_msg.id)
        )
    
    async def handle_battle_encounter(self, channel, user, dungeon_difficulty):
        """
        Handle a battle encounter for a player
        
        Args:
            channel: Discord channel
            user: The user who triggered the battle
            dungeon_difficulty: The dungeon's difficulty level
        """
        # Select a random enemy based on difficulty
        enemy = random.choice(self.battle_encounters[dungeon_difficulty])
        
        # Create battle encounter embed
        embed = discord.Embed(
            title=f"⚔️ Enemy Encountered: {enemy['name']}!",
            description=enemy["description"],
            color=settings.EMBED_COLORS["ERROR"]
        )
        
        # Add enemy stats
        embed.add_field(
            name="Enemy Stats",
            value=(
                f"**HP:** {enemy['hp']}\n"
                f"**Attack:** {enemy['attack']}\n"
                f"**Defense:** {enemy['defense']}\n"
                f"**Special:** {enemy['special']}"
            ),
            inline=True
        )
        
        # Add rewards
        embed.add_field(
            name="Potential Rewards",
            value=(
                f"**XP:** {enemy['xp']}\n"
                f"**Gold:** {enemy['gold']}"
            ),
            inline=True
        )
        
        # Add instructions (placeholder for now)
        embed.add_field(
            name="Combat Actions",
            value=(
                "React with:\n"
                "⚔️ - Attack\n"
                "🛡️ - Defend\n"
                "✨ - Use Skill\n"
                "🧪 - Use Item\n"
                "🏃 - Run Away"
            ),
            inline=False
        )
        
        # Send battle message
        battle_msg = await channel.send(content=user.mention, embed=embed)
        
        # Add reaction options
        await battle_msg.add_reaction("⚔️")  # Attack
        await battle_msg.add_reaction("🛡️")  # Defend
        await battle_msg.add_reaction("✨")  # Skill
        await battle_msg.add_reaction("🧪")  # Item
        await battle_msg.add_reaction("🏃")  # Run
        
        # Store the encounter
        self.active_encounters[f"{channel.id}_{user.id}"] = {
            "type": "battle",
            "data": enemy,
            "difficulty": dungeon_difficulty,
            "message_id": battle_msg.id,
            "expires": datetime.now() + timedelta(minutes=5),
            "state": {
                "enemy_hp": enemy["hp"],
                "turn": 0,
                "status_effects": []
            }
        }
        
        # Set up a timeout for the encounter
        self.bot.loop.create_task(
            self._expire_encounter(channel.id, user.id, battle_msg.id)
        )
    
    async def handle_random_event(self, channel, user):
        """
        Handle a random event for a player
        
        Args:
            channel: Discord channel
            user: The user who triggered the event
        """
        # Select a random event
        event = random.choice(self.random_events)
        
        # Process the event based on its effect
        if event["effect"] == "gold":
            if isinstance(event["value"], list):
                value = random.randint(event["value"][0], event["value"][1])
            else:
                value = event["value"]
            
            message = event["message"].format(value=value)
        elif event["effect"] == "heal":
            value = event["value"]
            message = event["message"].format(value=value)
        elif event["effect"] == "buff":
            buffs = ["Strength +2", "Dexterity +2", "Intelligence +2", "Luck +2"]
            value = random.choice(buffs)
            message = event["message"].format(value=value)
        elif event["effect"] == "info":
            hints = [
                "Beware the eastern passage...",
                "The north chamber holds great treasure.",
                "Look for hidden symbols on the walls.",
                "Sometimes running is wiser than fighting.",
                "The next floor has more dangerous enemies."
            ]
            value = random.choice(hints)
            message = event["message"].format(value=value)
        else:
            value = "unknown effect"
            message = "Something strange happens."
        
        # Create event embed
        embed = discord.Embed(
            title=f"✨ {event['name']}",
            description=event["description"],
            color=settings.EMBED_COLORS["INFO"]
        )
        
        embed.add_field(
            name="Result",
            value=message,
            inline=False
        )
        
        # Send event message
        await channel.send(content=user.mention, embed=embed)
        
        # Apply rewards if applicable (placeholder for now)
        # This would integrate with your player stats system
    
    async def handle_encounter_reaction(self, reaction, user):
        """
        Process a reaction to an active encounter
        
        Args:
            reaction: The Discord reaction
            user: The user who reacted
        """
        # Check if this is for an active encounter
        key = f"{reaction.message.channel.id}_{user.id}"
        if key not in self.active_encounters:
            return
        
        encounter = self.active_encounters[key]
        
        # Check if this is the right message
        if reaction.message.id != encounter["message_id"]:
            return
        
        # Process based on encounter type
        if encounter["type"] == "trap":
            await self._handle_trap_reaction(reaction, user, encounter)
        elif encounter["type"] == "battle":
            await self._handle_battle_reaction(reaction, user, encounter)
    
    async def _handle_trap_reaction(self, reaction, user, encounter):
        """Handle reaction to a trap encounter"""
        if str(reaction.emoji) != "🎲":
            return
            
        # Get trap data
        trap = encounter["data"]
        diff_settings = trap["difficulty"][encounter["difficulty"]]
        
        # Simulate skill check (placeholder - would integrate with character stats)
        dc = diff_settings["dc"]
        
        # TODO: This would use the player's actual stats
        # For now, just generate a random roll
        roll = random.randint(1, 20)
        stat_bonus = random.randint(0, 5)  # Placeholder for stat bonus
        total = roll + stat_bonus
        
        # Check for success
        success = total >= dc
        
        # Calculate damage if failed
        damage = 0
        if not success:
            damage = random.randint(diff_settings["damage"][0], diff_settings["damage"][1])
        
        # Create result embed
        if success:
            color = settings.EMBED_COLORS["SUCCESS"]
            title = "✅ Trap Avoided!"
            description = trap["success_message"]
        else:
            color = settings.EMBED_COLORS["ERROR"]
            title = "❌ Trap Triggered!"
            description = trap["failure_message"].format(damage=damage)
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        embed.add_field(
            name="Skill Check",
            value=f"**{trap['skill_check']}**: {roll} + {stat_bonus} = {total} vs DC {dc}",
            inline=False
        )
        
        if not success:
            embed.add_field(
                name="Damage",
                value=f"You take {damage} damage!",
                inline=False
            )
        
        # Send result
        await reaction.message.channel.send(content=user.mention, embed=embed)
        
        # Clean up
        try:
            await reaction.message.clear_reactions()
        except:
            pass
            
        # Remove encounter from active list
        key = f"{reaction.message.channel.id}_{user.id}"
        if key in self.active_encounters:
            del self.active_encounters[key]
    
    async def _handle_battle_reaction(self, reaction, user, encounter):
        """Handle reaction to a battle encounter"""
        # Get emoji and check if it's a valid action
        emoji = str(reaction.emoji)
        valid_actions = ["⚔️", "🛡️", "✨", "🧪", "🏃"]
        
        if emoji not in valid_actions:
            return
        
        # Get battle data
        enemy = encounter["data"]
        battle_state = encounter["state"]
        
        # Process the action (placeholder combat system)
        embed = None
        
        if emoji == "⚔️":  # Attack
            # Player attacks
            attack_roll = random.randint(1, 20)
            attack_bonus = random.randint(1, 5)  # Would use player stats
            total_attack = attack_roll + attack_bonus
            
            # Check hit
            if total_attack > enemy["defense"]:
                # Calculate damage
                damage = random.randint(5, 10) + random.randint(0, 3)  # Would use weapon and stats
                battle_state["enemy_hp"] -= damage
                
                if battle_state["enemy_hp"] <= 0:
                    # Enemy defeated
                    embed = await self._create_victory_embed(user, enemy)
                    
                    # Clean up encounter
                    await self._end_battle(reaction.message.channel, user, True)
                    return
                else:
                    # Enemy still alive, show damage
                    embed = discord.Embed(
                        title="⚔️ Attack!",
                        description=f"You strike the {enemy['name']} for {damage} damage!",
                        color=settings.EMBED_COLORS["INFO"]
                    )
                    
                    # Add enemy HP
                    embed.add_field(
                        name="Enemy Status",
                        value=f"**HP:** {battle_state['enemy_hp']}/{enemy['hp']}",
                        inline=False
                    )
            else:
                # Miss
                embed = discord.Embed(
                    title="⚔️ Attack Missed!",
                    description=f"Your attack fails to hit the {enemy['name']}!",
                    color=settings.EMBED_COLORS["WARNING"]
                )
                
            # Enemy attacks back
            await self._enemy_attack(reaction.message.channel, user, encounter, embed)
                
        elif emoji == "🛡️":  # Defend
            # Increase defense for this turn
            battle_state["status_effects"].append({"type": "defend", "turns": 1})
            
            embed = discord.Embed(
                title="🛡️ Defend!",
                description=f"You raise your defenses against the {enemy['name']}!",
                color=settings.EMBED_COLORS["INFO"]
            )
            
            # Enemy attacks with disadvantage
            await self._enemy_attack(reaction.message.channel, user, encounter, embed, disadvantage=True)
            
        elif emoji == "✨":  # Use Skill
            # Placeholder for skill usage
            embed = discord.Embed(
                title="✨ Skill Used!",
                description="Skill system is not implemented yet!",
                color=settings.EMBED_COLORS["INFO"]
            )
            
            # Enemy attacks back
            await self._enemy_attack(reaction.message.channel, user, encounter, embed)
            
        elif emoji == "🧪":  # Use Item
            # Placeholder for item usage
            embed = discord.Embed(
                title="🧪 Item Used!",
                description="Item system is not implemented yet!",
                color=settings.EMBED_COLORS["INFO"]
            )
            
            # Enemy attacks back
            await self._enemy_attack(reaction.message.channel, user, encounter, embed)
            
        elif emoji == "🏃":  # Run Away
            # Chance to escape based on enemy
            escape_chance = random.random()
            
            if escape_chance > 0.3:  # 70% success rate for now
                embed = discord.Embed(
                    title="🏃 Escaped!",
                    description=f"You successfully flee from the {enemy['name']}!",
                    color=settings.EMBED_COLORS["SUCCESS"]
                )
                
                # End battle without rewards
                await reaction.message.channel.send(content=user.mention, embed=embed)
                await self._end_battle(reaction.message.channel, user, False)
                return
            else:
                embed = discord.Embed(
                    title="🏃 Failed to Escape!",
                    description=f"You try to run but the {enemy['name']} blocks your path!",
                    color=settings.EMBED_COLORS["WARNING"]
                )
                
                # Enemy gets an attack of opportunity
                await self._enemy_attack(reaction.message.channel, user, encounter, embed, advantage=True)
    
    async def _enemy_attack(self, channel, user, encounter, embed, advantage=False, disadvantage=False):
        """Process enemy attack"""
        enemy = encounter["data"]
        battle_state = encounter["state"]
        
        # Calculate attack roll with advantage/disadvantage
        if advantage:
            attack_roll = max(random.randint(1, 20), random.randint(1, 20))
        elif disadvantage:
            attack_roll = min(random.randint(1, 20), random.randint(1, 20))
        else:
            attack_roll = random.randint(1, 20)
            
        attack_bonus = enemy["attack"] // 4
        total_attack = attack_roll + attack_bonus
        
        # Player defense (placeholder)
        # Would use player's actual defense stat
        player_defense = 10
        for effect in battle_state["status_effects"]:
            if effect["type"] == "defend":
                player_defense += 5
        
        # Check if attack hits
        if total_attack > player_defense:
            # Calculate damage
            damage = random.randint(enemy["attack"] // 2, enemy["attack"])
            
            # Add enemy attack result to embed
            embed.add_field(
                name="🗡️ Enemy Attack",
                value=f"The {enemy['name']} hits you for {damage} damage!",
                inline=False
            )
            
            # Apply special effects if any
            if enemy["special"] == "Poison":
                embed.add_field(
                    name="☠️ Poison",
                    value="You are poisoned! (Placeholder effect)",
                    inline=False
                )
            elif enemy["special"] == "Drain":
                embed.add_field(
                    name="🌑 Life Drain",
                    value="You feel your energy being drained! (Placeholder effect)",
                    inline=False
                )
        else:
            # Add miss to embed
            embed.add_field(
                name="🗡️ Enemy Attack",
                value=f"The {enemy['name']} tries to attack but misses!",
                inline=False
            )
        
        # Increment turn counter
        battle_state["turn"] += 1
        
        # Update status effects
        updated_effects = []
        for effect in battle_state["status_effects"]:
            effect["turns"] -= 1
            if effect["turns"] > 0:
                updated_effects.append(effect)
        battle_state["status_effects"] = updated_effects
        
        # Send result
        await channel.send(content=user.mention, embed=embed)
    
    async def _create_victory_embed(self, user, enemy):
        """Create victory embed for defeated enemy"""
        xp = enemy["xp"]
        gold = enemy["gold"]
        
        embed = discord.Embed(
            title="🎉 Victory!",
            description=f"You have defeated the {enemy['name']}!",
            color=settings.EMBED_COLORS["SUCCESS"]
        )
        
        # Add rewards
        embed.add_field(
            name="Rewards",
            value=f"**XP:** {xp}\n**Gold:** {gold}",
            inline=False
        )
        
        # TODO: Add random loot drops
        
        return embed
    
    async def _end_battle(self, channel, user, victory=True):
        """End a battle encounter and clean up"""
        key = f"{channel.id}_{user.id}"
        
        # Remove from active encounters
        if key in self.active_encounters:
            encounter = self.active_encounters[key]
            
            # Try to clean up message reactions
            try:
                message = await channel.fetch_message(encounter["message_id"])
                await message.clear_reactions()
            except:
                pass
                
            # Remove encounter
            del self.active_encounters[key]
    
    async def _expire_encounter(self, channel_id, user_id, message_id):
        """
        Handle encounter expiration after timeout
        
        Args:
            channel_id: Discord channel ID
            user_id: User ID
            message_id: Encounter message ID
        """
        key = f"{channel_id}_{user_id}"
        await asyncio.sleep(120)  # Wait for 2 minutes
        
        # Check if encounter is still active
        if key in self.active_encounters:
            encounter = self.active_encounters[key]
            
            # Check if it's the same message
            if encounter["message_id"] == message_id:
                # Get channel
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    return
                
                # Create timeout embed
                embed = discord.Embed(
                    title="⌛ Encounter Timed Out",
                    description="You took too long to respond and the opportunity passed.",
                    color=settings.EMBED_COLORS["WARNING"]
                )
                
                # Send timeout message
                await channel.send(content=f"<@{user_id}>", embed=embed)
                
                # Try to clear reactions on original message
                try:
                    message = await channel.fetch_message(message_id)
                    await message.clear_reactions()
                except:
                    pass
                
                # Remove encounter
                del self.active_encounters[key]
                
    def is_on_cooldown(self, user_id):
        """
        Check if a user is on encounter cooldown
        
        Args:
            user_id: User ID
            
        Returns:
            True if on cooldown, False otherwise
        """
        if user_id not in self.player_cooldowns:
            return False
            
        now = datetime.now()
        cooldown_end = self.player_cooldowns[user_id]
        
        return now < cooldown_end
    
    def set_cooldown(self, user_id, seconds=60):
        """
        Set cooldown for a user
        
        Args:
            user_id: User ID
            seconds: Cooldown duration in seconds
        """
        self.player_cooldowns[user_id] = datetime.now() + timedelta(seconds=seconds)
    
    def should_trigger_random_encounter(self, dungeon):
        """
        Check if a random encounter should be triggered
        
        Args:
            dungeon: Dungeon data
            
        Returns:
            True if encounter should trigger, False otherwise
        """
        # Get chance from settings
        chance = self.settings["ENCOUNTERS"]["RANDOM_MOVE_CHANCE"]
        
        # Roll for encounter
        roll = random.random()
        
        return roll < chance

# This file contains additional encounter methods that extend dungeon_encounters.py
# These methods would be part of the DungeonEncounterManager class

    def get_chest_loot(self, dungeon_difficulty, floor_level):
        """
        Generate loot for a dungeon chest
        
        Args:
            dungeon_difficulty: Difficulty level of the dungeon
            floor_level: Current floor number (higher floors = better loot)
            
        Returns:
            Dictionary of loot items
        """
        # Base values for different difficulties
        difficulty_multipliers = {
            "EASY": 1.0,
            "NORMAL": 1.5,
            "HARD": 2.0,
            "LUNATIC": 3.0
        }
        
        # Floor bonus (higher floors give better loot)
        floor_multiplier = 1.0 + (floor_level * 0.1)
        
        # Base gold amount
        base_gold = random.randint(20, 50)
        gold_amount = int(base_gold * difficulty_multipliers[dungeon_difficulty] * floor_multiplier)
        
        # Determine number of items (0-3 based on difficulty and floor)
        max_items = min(3, int(difficulty_multipliers[dungeon_difficulty] + (floor_level // 2)))
        num_items = random.randint(0, max_items)
        
        # Chance for special items based on difficulty
        special_chance = 0.05 * difficulty_multipliers[dungeon_difficulty] * floor_multiplier
        
        # Generate items
        items = []
        for _ in range(num_items):
            item_type = self._determine_item_type(special_chance)
            item = self._generate_random_item(item_type, dungeon_difficulty, floor_level)
            items.append(item)
        
        # Compile loot
        loot = {
            "gold": gold_amount,
            "items": items
        }
        
        return loot
    
    def _determine_item_type(self, special_chance):
        """Determine the type of item to generate"""
        roll = random.random()
        
        if roll < special_chance:
            return "special"
        elif roll < 0.3:
            return "weapon"
        elif roll < 0.6:
            return "armor"
        else:
            return "consumable"
    
    def _generate_random_item(self, item_type, difficulty, floor_level):
        """Generate a random item of the specified type"""
        if item_type == "weapon":
            weapons = [
                "Dagger", "Sword", "Axe", "Mace", "Spear", "Bow", "Staff", "Wand"
            ]
            prefixes = [
                "", "Sharp ", "Sturdy ", "Precise ", "Balanced ", "Ancient ", "Enchanted "
            ]
            
            # Higher difficulty and floor level give better prefixes
            prefix_index = min(len(prefixes) - 1, 
                              int(random.random() * (floor_level // 2) * 
                                  {"EASY": 0.5, "NORMAL": 1.0, "HARD": 1.5, "LUNATIC": 2.0}[difficulty]))
            
            name = f"{prefixes[prefix_index]}{random.choice(weapons)}"
            power = int(5 + (floor_level * 0.5) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            
            return {
                "name": name,
                "type": "weapon",
                "power": power,
                "description": f"Deals {power} damage"
            }
            
        elif item_type == "armor":
            armors = [
                "Helmet", "Chestplate", "Leggings", "Boots", "Shield", "Gauntlets", "Cloak"
            ]
            prefixes = [
                "", "Sturdy ", "Reinforced ", "Protective ", "Heavy ", "Lightweight ", "Enchanted "
            ]
            
            # Higher difficulty and floor level give better prefixes
            prefix_index = min(len(prefixes) - 1, 
                              int(random.random() * (floor_level // 2) * 
                                  {"EASY": 0.5, "NORMAL": 1.0, "HARD": 1.5, "LUNATIC": 2.0}[difficulty]))
            
            name = f"{prefixes[prefix_index]}{random.choice(armors)}"
            defense = int(3 + (floor_level * 0.3) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            
            return {
                "name": name,
                "type": "armor",
                "defense": defense,
                "description": f"Provides {defense} defense"
            }
            
        elif item_type == "consumable":
            consumables = [
                "Health Potion", "Mana Potion", "Antidote", "Elixir", "Scroll", "Bomb", "Throwing Knife"
            ]
            
            name = random.choice(consumables)
            
            # Define effect based on item name
            if "Health" in name:
                effect = "Restores health"
                power = int(20 + (floor_level * 5) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            elif "Mana" in name:
                effect = "Restores mana"
                power = int(15 + (floor_level * 4) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            elif "Antidote" in name:
                effect = "Cures poison"
                power = 1
            elif "Elixir" in name:
                effect = "Temporary stat boost"
                power = int(2 + (floor_level * 0.2) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            elif "Scroll" in name:
                effect = "One-use spell"
                power = int(10 + (floor_level * 2) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            else:
                effect = "Deals damage"
                power = int(15 + (floor_level * 3) * {"EASY": 1, "NORMAL": 1.2, "HARD": 1.5, "LUNATIC": 2.0}[difficulty])
            
            return {
                "name": name,
                "type": "consumable",
                "power": power,
                "effect": effect,
                "description": f"{effect} ({power})"
            }
            
        elif item_type == "special":
            specials = [
                "Ancient Relic", "Magic Orb", "Enchanted Gem", "Mysterious Artifact", 
                "Rare Crystal", "Legendary Fragment", "Dungeon Key"
            ]
            
            name = random.choice(specials)
            
            return {
                "name": name,
                "type": "special",
                "rarity": {"EASY": "Uncommon", "NORMAL": "Rare", "HARD": "Very Rare", "LUNATIC": "Legendary"}[difficulty],
                "description": "A valuable treasure with mysterious properties."
            }
    
    async def handle_chest_interaction(self, channel, user, dungeon_difficulty, floor_level):
        """
        Handle a player interacting with a chest
        
        Args:
            channel: Discord channel
            user: The user who opened the chest
            dungeon_difficulty: Difficulty level of the dungeon
            floor_level: Current floor number
        """
        # Determine if the chest is trapped
        trap_chance = {"EASY": 0.1, "NORMAL": 0.2, "HARD": 0.3, "LUNATIC": 0.4}[dungeon_difficulty]
        
        if random.random() < trap_chance:
            # Chest is trapped
            await channel.send(f"⚠️ {user.mention} The chest is trapped!")
            await self.handle_trap_encounter(channel, user, dungeon_difficulty)
            return
        
        # Generate loot
        loot = self.get_chest_loot(dungeon_difficulty, floor_level)
        
        # Create chest embed
        embed = discord.Embed(
            title="🎁 Treasure Chest",
            description=f"{user.mention} found a treasure chest!",
            color=settings.EMBED_COLORS["SUCCESS"]
        )
        
        # Add gold to embed
        embed.add_field(
            name="💰 Gold",
            value=f"{loot['gold']} coins",
            inline=False
        )
        
        # Add items to embed if any
        if loot["items"]:
            items_text = ""
            for item in loot["items"]:
                items_text += f"**{item['name']}** - {item['description']}\n"
            
            embed.add_field(
                name="📦 Items",
                value=items_text,
                inline=False
            )
        else:
            embed.add_field(
                name="📦 Items",
                value="No items found in this chest.",
                inline=False
            )
        
        # Send result
        await channel.send(embed=embed)
        
        # TODO: Actually give the rewards to the player
        # This would integrate with your inventory system
    
    async def handle_boss_encounter(self, channel, users, dungeon_difficulty, floor_level):
        """
        Handle a boss encounter for a group of players
        
        Args:
            channel: Discord channel
            users: List of users involved
            dungeon_difficulty: Difficulty level of the dungeon
            floor_level: Current floor number
        """
        # Select a boss based on difficulty and floor level
        boss = self._select_boss(dungeon_difficulty, floor_level)
        
        # Scale boss based on number of players
        player_count = len(users)
        boss["hp"] = boss["hp"] * (1 + (player_count - 1) * 0.5)
        boss["attack"] = boss["attack"] * (1 + (player_count - 1) * 0.3)
        
        # Create boss encounter embed
        embed = discord.Embed(
            title=f"🔥 BOSS BATTLE: {boss['name']}!",
            description=boss["description"],
            color=settings.EMBED_COLORS["ERROR"]
        )
        
        # Add boss stats
        embed.add_field(
            name="Boss Stats",
            value=(
                f"**HP:** {boss['hp']}\n"
                f"**Attack:** {boss['attack']}\n"
                f"**Defense:** {boss['defense']}\n"
                f"**Special:** {boss['special']}"
            ),
            inline=True
        )
        
        # Add rewards
        embed.add_field(
            name="Potential Rewards",
            value=(
                f"**XP:** {boss['xp']}\n"
                f"**Gold:** {boss['gold']}\n"
                f"**Special:** {boss['drop']}"
            ),
            inline=True
        )
        
        # Add instructions (placeholder for now)
        embed.add_field(
            name="Boss Battle",
            value=(
                "This is a placeholder for boss battles.\n"
                "In the future, this will be an interactive group battle experience!"
            ),
            inline=False
        )
        
        # Add player list
        players_text = "\n".join([user.mention for user in users])
        embed.add_field(
            name="Participating Players",
            value=players_text,
            inline=False
        )
        
        # Send boss message
        await channel.send(embed=embed)
        
        # TODO: Implement actual boss battle mechanics
        # For now, just simulate a victory after a delay
        await asyncio.sleep(3)
        
        # Victory message
        victory_embed = discord.Embed(
            title=f"🎉 Boss Defeated: {boss['name']}",
            description=f"After an epic battle, the boss has been defeated!",
            color=settings.EMBED_COLORS["SUCCESS"]
        )
        
        # Add rewards
        rewards_text = (
            f"**XP:** {boss['xp']} (shared)\n"
            f"**Gold:** {boss['gold']} (shared)\n"
            f"**Special Drop:** {boss['drop']}"
        )
        victory_embed.add_field(
            name="💰 Rewards",
            value=rewards_text,
            inline=False
        )
        
        # Send victory message
        await channel.send(embed=victory_embed)
    
    def _select_boss(self, difficulty, floor_level):
        """Select an appropriate boss based on difficulty and floor level"""
        # Boss categories
        early_bosses = [
            {
                "name": "Giant Slime",
                "description": "A massive, pulsating slime that consumes everything in its path!",
                "hp": 150,
                "attack": 15,
                "defense": 10,
                "special": "Splits into smaller slimes when damaged",
                "xp": 300,
                "gold": 150,
                "drop": "Slime Core"
            },
            {
                "name": "Goblin King",
                "description": "A large, cunning goblin wearing a crude crown and wielding a spiked club!",
                "hp": 180,
                "attack": 20,
                "defense": 12,
                "special": "Calls goblin minions",
                "xp": 350,
                "gold": 200,
                "drop": "Goblin Crown"
            }
        ]
        
        mid_bosses = [
            {
                "name": "Stone Golem",
                "description": "A massive construct of animated stone with glowing runes etched into its surface!",
                "hp": 300,
                "attack": 25,
                "defense": 20,
                "special": "Earthquake attack",
                "xp": 600,
                "gold": 300,
                "drop": "Golem Core"
            },
            {
                "name": "Necromancer",
                "description": "A sinister spellcaster surrounded by floating skeletal minions!",
                "hp": 250,
                "attack": 30,
                "defense": 15,
                "special": "Raises undead minions",
                "xp": 550,
                "gold": 350,
                "drop": "Necromantic Tome"
            }
        ]
        
        late_bosses = [
            {
                "name": "Ancient Dragon",
                "description": "A massive, ancient dragon with scales that shimmer with magical energy!",
                "hp": 500,
                "attack": 40,
                "defense": 30,
                "special": "Breath weapon",
                "xp": 1200,
                "gold": 800,
                "drop": "Dragon Scale"
            },
            {
                "name": "Lich Lord",
                "description": "A powerful undead sorcerer radiating dark energy and ancient knowledge!",
                "hp": 450,
                "attack": 45,
                "defense": 25,
                "special": "Soul drain",
                "xp": 1100,
                "gold": 750,
                "drop": "Phylactery Shard"
            }
        ]
        
        final_bosses = [
            {
                "name": "Dungeon Master",
                "description": "The powerful entity that controls this entire dungeon, now manifesting to face you directly!",
                "hp": 800,
                "attack": 60,
                "defense": 40,
                "special": "Reality warping",
                "xp": 2000,
                "gold": 1500,
                "drop": "Master's Key"
            },
            {
                "name": "Void Leviathan",
                "description": "A colossal entity from beyond reality that has nested in the depths of this dungeon!",
                "hp": 1000,
                "attack": 70,
                "defense": 50,
                "special": "Void corruption",
                "xp": 2500,
                "gold": 2000,
                "drop": "Void Essence"
            }
        ]
        
        # Select boss category based on floor level
        if floor_level <= 3:
            boss_list = early_bosses
        elif floor_level <= 6:
            boss_list = mid_bosses
        elif floor_level <= 10:
            boss_list = late_bosses
        else:
            boss_list = final_bosses
        
        # Select random boss from the appropriate category
        boss = random.choice(boss_list)
        
        # Apply difficulty multiplier
        difficulty_mult = {
            "EASY": 0.75,
            "NORMAL": 1.0,
            "HARD": 1.5,
            "LUNATIC": 2.0
        }[difficulty]
        
        boss["hp"] = int(boss["hp"] * difficulty_mult)
        boss["attack"] = int(boss["attack"] * difficulty_mult)
        boss["defense"] = int(boss["defense"] * difficulty_mult)
        boss["xp"] = int(boss["xp"] * difficulty_mult)
        boss["gold"] = int(boss["gold"] * difficulty_mult)
        
        return boss
    
    def generate_dungeon_key_points(self, dungeon_size, complexity, num_floors):
        """
        Generate key encounter points for a dungeon
        
        Args:
            dungeon_size: Size of the dungeon (SMALL, MEDIUM, LARGE)
            complexity: Complexity of the dungeon (EASY, NORMAL, HARD)
            num_floors: Number of floors in the dungeon
            
        Returns:
            Dictionary of key points for each floor
        """
        key_points = {}
        
        # Determine number of encounters based on size and complexity
        size_factors = {
            "SMALL": 1.0,
            "MEDIUM": 1.5,
            "LARGE": 2.0
        }
        
        complexity_factors = {
            "EASY": 0.8,
            "NORMAL": 1.0,
            "HARD": 1.2
        }
        
        # For each floor, generate key points
        for floor in range(num_floors):
            floor_key_points = {
                "traps": [],
                "enemies": [],
                "chests": [],
                "special_rooms": []
            }
            
            # Adjust number of encounters based on floor level
            floor_factor = 1.0 + (floor * 0.1)
            
            # Calculate base counts
            base_trap_count = 2 * size_factors[dungeon_size] * complexity_factors[complexity] * floor_factor
            base_enemy_count = 3 * size_factors[dungeon_size] * complexity_factors[complexity] * floor_factor
            base_chest_count = 1 * size_factors[dungeon_size] * complexity_factors[complexity] * floor_factor
            base_special_count = 0.5 * size_factors[dungeon_size] * complexity_factors[complexity] * floor_factor
            
            # Randomize counts slightly
            trap_count = max(1, int(base_trap_count * random.uniform(0.8, 1.2)))
            enemy_count = max(2, int(base_enemy_count * random.uniform(0.8, 1.2)))
            chest_count = max(1, int(base_chest_count * random.uniform(0.8, 1.2)))
            special_count = max(0, int(base_special_count * random.uniform(0.8, 1.2)))
            
            # Last floor always has a boss instead of normal enemies
            if floor == num_floors - 1:
                floor_key_points["boss"] = True
                enemy_count = max(1, enemy_count // 2)  # Fewer normal enemies on boss floor
            
            # Store counts
            floor_key_points["trap_count"] = trap_count
            floor_key_points["enemy_count"] = enemy_count
            floor_key_points["chest_count"] = chest_count
            floor_key_points["special_count"] = special_count
            
            # Store in overall key points
            key_points[floor] = floor_key_points
        
        return key_points