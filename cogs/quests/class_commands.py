import discord
from discord.ext import commands
import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from .player_classes import ClassManager, PlayerClassHandler, AbilityScore
from .utils import create_embed, send_temp_message
from .player_manager import PlayerManager

class ClassCommands(commands.Cog):
    """Commands for managing character classes"""
    
    def __init__(self, bot):
        self.bot = bot
        self.class_manager = ClassManager()
        self.player_class_handler = PlayerClassHandler()
        self.player_manager = PlayerManager()
        
        # Track active class selection sessions
        self.active_selections = {}
        self.active_appearance_sessions = {}
    
    @commands.group(name="class", invoke_without_command=True)
    async def class_cmd(self, ctx):
        """View your character classes"""
        # Get player classes
        player_classes = self.player_class_handler.get_player_classes(ctx.author.id)
        
        if not player_classes:
            embed = create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{ctx.author.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Create embed
        embed = create_embed(
            title=f"🧙‍♂️ {ctx.author.display_name}'s Character Classes",
            description=f"You have {len(player_classes)} character class(es).\nTotal Player Level: {self.player_class_handler.get_player_total_level(ctx.author.id)}",
            color=discord.Color.blue()
        )
        
        # Add each class
        for class_name, class_data in player_classes.items():
            level = class_data.get("level", 1)
            xp = class_data.get("xp", 0)
            xp_needed = self.class_manager.get_xp_for_next_level(level)
            
            # Get main ability scores
            ability_scores = class_data.get("ability_scores", {})
            primary_abilities = []
            for ability_name, ability_score in ability_scores.items():
                # Only show scores above 10 (default)
                if ability_score > 10:
                    primary_abilities.append(f"{ability_name.capitalize()}: {ability_score}")
            
            # Build class info
            class_info = f"**Level {level}** - {xp}/{xp_needed} XP\n"
            if primary_abilities:
                class_info += f"**Abilities:** {', '.join(primary_abilities)}\n"
            
            # Add skills with bonuses
            skills = class_data.get("skills", {})
            if skills:
                top_skills = []
                for skill_name, skill_points in sorted(skills.items(), key=lambda x: x[1], reverse=True)[:3]:
                    if skill_points > 0:
                        bonus = self.class_manager.get_skill_bonus(class_data, skill_name)
                        top_skills.append(f"{skill_name} +{bonus}")
                
                if top_skills:
                    class_info += f"**Top Skills:** {', '.join(top_skills)}\n"
            
            embed.add_field(
                name=f"{class_name}",
                value=class_info,
                inline=True
            )
        
        # Add appearance if available
        for class_name, class_data in player_classes.items():
            if class_data.get("appearance_url"):
                embed.set_thumbnail(url=class_data["appearance_url"])
                break
        
        # Add command hints
        embed.add_field(
            name="Commands",
            value=(
                "`!class info <class>` - View detailed class info\n"
                "`!class appearance <class>` - Set class appearance\n"
                "`!quests new` - Create a new class\n"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @class_cmd.command(name="info")
    async def class_info(self, ctx, *, class_name: str = None):
        """View detailed information about a specific class"""
        # Get player classes
        player_classes = self.player_class_handler.get_player_classes(ctx.author.id)
        
        if not player_classes:
            embed = create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{ctx.author.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # [Class selection code remains unchanged]
        # If no class specified and player has only one class, use that
        if not class_name and len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        elif not class_name:
            # Ask which class they want to view
            class_names = list(player_classes.keys())
            class_list = "\n".join([f"**{i+1}.** {name}" for i, name in enumerate(class_names)])
            
            embed = create_embed(
                title="🧙‍♂️ Select Class",
                description=f"Which class would you like to view?\n\n{class_list}\n\nType the number or name of the class.",
                color=discord.Color.blue()
            )
            selection_message = await ctx.send(embed=embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                # Try to parse as number or name
                try:
                    index = int(response.content) - 1
                    if 0 <= index < len(class_names):
                        class_name = class_names[index]
                    else:
                        raise ValueError
                except ValueError:
                    # Try as name
                    found = False
                    for name in class_names:
                        if name.lower() == response.content.lower():
                            class_name = name
                            found = True
                            break
                    
                    if not found:
                        await ctx.send(f"❌ '{response.content}' is not a valid class. Please try again.")
                        return
            
            except asyncio.TimeoutError:
                await ctx.send("⏱️ Selection timed out.")
                return
            finally:
                try:
                    await selection_message.delete()
                    await response.delete()
                except:
                    pass
        
        # Check if the player has this class
        if class_name not in player_classes:
            await ctx.send(f"❌ You don't have a {class_name} class.")
            return
        
        # Get class data
        class_data = player_classes[class_name]
        
        # Calculate derived stats
        ability_scores = class_data.get("ability_scores", {})
        constitution = ability_scores.get("constitution", 10)
        intelligence = ability_scores.get("intelligence", 10)
        wisdom = ability_scores.get("wisdom", 10)
        charisma = ability_scores.get("charisma", 10)
        dexterity = ability_scores.get("dexterity", 10)
        
        # Calculate HP, MP, AC
        hp = constitution * 5
        mp = max(intelligence, wisdom, charisma) * 5
        ac = (dexterity + 1) // 2 + 5  # Integer division rounds down, so add 1 first to effectively round up
        
        # Create beautiful embed with clean layout
        embed = create_embed(
            title=f"📊 {ctx.author.display_name}'s {class_name}",
            description=f"**Level {class_data.get('level', 1)} {class_name}**\n**HP:** {hp} | **MP:** {mp} | **AC:** {ac}",
            color=discord.Color.blue()
        )
        
        # Add appearance if available
        if class_data.get("appearance_url"):
            embed.set_thumbnail(url=class_data["appearance_url"])
        
        # Add XP info
        level = class_data.get("level", 1)
        xp = class_data.get("xp", 0)
        xp_needed = self.class_manager.get_xp_for_next_level(level)
        
        # Create progress bar
        progress = min(1.0, xp / xp_needed)
        bar_length = 15
        filled = int(bar_length * progress)
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        
        embed.add_field(
            name="Experience",
            value=f"**Level:** {level}\n**XP:** {xp}/{xp_needed}\n**Progress:** {progress_bar} {int(progress*100)}%",
            inline=True
        )
        
        # Add ability scores in a clean format
        ability_text = ""
        for ability in AbilityScore:
            score = ability_scores.get(ability.value, 10)
            modifier = self.class_manager.get_ability_modifier(score)
            sign = "+" if modifier >= 0 else ""
            ability_text += f"**{ability.value[:3].upper()}:** {score} ({sign}{modifier})\n"
        
        embed.add_field(
            name="Ability Scores",
            value=ability_text,
            inline=True
        )
        
        # Add top skills (not all skills)
        skills = class_data.get("skills", {})
        if skills:
            top_skills = []
            for skill_name, skill_points in sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5]:
                if skill_points > 0:
                    ability = self.class_manager.get_ability_for_skill(skill_name)
                    ability_mod = self.class_manager.get_ability_modifier(ability_scores.get(ability.value, 10))
                    total = skill_points + ability_mod
                    top_skills.append(f"**{skill_name}:** {skill_points} ({'+' if total >= 0 else ''}{total})")
            
            if top_skills:
                embed.add_field(
                    name="Top Skills",
                    value="\n".join(top_skills) + "\n\n*Use `!class skills` to view all skills*",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Skills",
                    value="No skills trained yet.\n*Use `!class skills` to view all skills*",
                    inline=False
                )
        
        # Add commands
        embed.add_field(
            name="Commands",
            value=(
                "`!class skills` - View all your skills\n"
                "`!class appearance <class>` - Set class appearance\n"
                "`!class reset <class>` - Reset skill & ability distribution"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @class_cmd.command(name="skills")
    async def class_skills(self, ctx, *, class_name: str = None):
        """View all skills for a specific class"""
        # Get player classes
        player_classes = self.player_class_handler.get_player_classes(ctx.author.id)
        
        if not player_classes:
            embed = create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{ctx.author.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # If no class specified and player has only one class, use that
        if not class_name and len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        elif not class_name:
            # Ask which class they want to view skills for
            class_names = list(player_classes.keys())
            class_list = "\n".join([f"**{i+1}.** {name}" for i, name in enumerate(class_names)])
            
            embed = create_embed(
                title="🧙‍♂️ Select Class",
                description=f"Which class would you like to view skills for?\n\n{class_list}\n\nType the number or name of the class.",
                color=discord.Color.blue()
            )
            selection_message = await ctx.send(embed=embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                # Try to parse as number or name
                try:
                    index = int(response.content) - 1
                    if 0 <= index < len(class_names):
                        class_name = class_names[index]
                    else:
                        raise ValueError
                except ValueError:
                    # Try as name
                    found = False
                    for name in class_names:
                        if name.lower() == response.content.lower():
                            class_name = name
                            found = True
                            break
                    
                    if not found:
                        await ctx.send(f"❌ '{response.content}' is not a valid class. Please try again.")
                        return
            
            except asyncio.TimeoutError:
                await ctx.send("⏱️ Selection timed out.")
                return
            finally:
                try:
                    await selection_message.delete()
                    await response.delete()
                except:
                    pass
        
        # Check if the player has this class
        if class_name not in player_classes:
            await ctx.send(f"❌ You don't have a {class_name} class.")
            return
        
        # Get class data
        class_data = player_classes[class_name]
        ability_scores = class_data.get("ability_scores", {})
        skills = class_data.get("skills", {})
        
        # Define all skills and their associated abilities
        all_skills = {
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
        
        # Group skills by ability
        skills_by_ability = {
            "strength": [],
            "dexterity": [],
            "intelligence": [],
            "wisdom": [],
            "charisma": []
        }
        
        # Populate skills with their values
        for skill_name, ability in all_skills.items():
            skill_points = skills.get(skill_name, 0)
            ability_score = ability_scores.get(ability, 10)
            ability_mod = self.class_manager.get_ability_modifier(ability_score)
            total_bonus = skill_points + ability_mod
            
            # Add to the appropriate ability group
            if ability in skills_by_ability:
                skills_by_ability[ability].append((skill_name, skill_points, total_bonus))
        
        # Create a beautiful skills embed
        embed = create_embed(
            title=f"🎯 {ctx.author.display_name}'s {class_name} Skills",
            description=(
                f"Your skill values are calculated as:\n"
                f"**Skill Points + Ability Modifier = Total**\n"
            ),
            color=discord.Color.blue()
        )
        
        # Add appearance if available
        if class_data.get("appearance_url"):
            embed.set_thumbnail(url=class_data["appearance_url"])
        
        # Create skill sections for each ability
        ability_names = {
            "strength": "💪 Strength",
            "dexterity": "🏃 Dexterity",
            "intelligence": "🧠 Intelligence",
            "wisdom": "🦉 Wisdom",
            "charisma": "✨ Charisma"
        }
        
        # Add each ability section with formatted skills
        for ability, skill_list in skills_by_ability.items():
            if skill_list:
                skill_text = ""
                for skill_name, points, bonus in sorted(skill_list, key=lambda x: x[0]):  # Sort by skill name
                    # Format skill name in bold if player has points in it
                    name_format = f"**{skill_name}**" if points > 0 else skill_name
                    sign = "+" if bonus >= 0 else ""
                    skill_text += f"{name_format}: {points} {sign}{bonus}\n"
                
                if skill_text:
                    embed.add_field(
                        name=ability_names.get(ability, ability.capitalize()),
                        value=skill_text,
                        inline=True
                    )
        
        # Add a helpful note at the bottom
        embed.set_footer(text=f"Bold skills indicate trained skills • Level {class_data.get('level', 1)} {class_name}")
        
        await ctx.send(embed=embed)


    @class_cmd.command(name="appearance")
    async def class_appearance(self, ctx, *, class_name: str = None):
        """Set the appearance for a character class"""
        # Get player classes
        player_classes = self.player_class_handler.get_player_classes(ctx.author.id)
        
        if not player_classes:
            embed = create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{ctx.author.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # If no class specified and player has only one class, use that
        if not class_name and len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        elif not class_name:
            # Ask which class they want to set appearance for
            class_names = list(player_classes.keys())
            class_list = "\n".join([f"**{i+1}.** {name}" for i, name in enumerate(class_names)])
            
            embed = create_embed(
                title="🧙‍♂️ Select Class",
                description=f"Which class would you like to set appearance for?\n\n{class_list}\n\nType the number or name of the class.",
                color=discord.Color.blue()
            )
            selection_message = await ctx.send(embed=embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                # Try to parse as number or name
                try:
                    index = int(response.content) - 1
                    if 0 <= index < len(class_names):
                        class_name = class_names[index]
                    else:
                        raise ValueError
                except ValueError:
                    # Try as name
                    found = False
                    for name in class_names:
                        if name.lower() == response.content.lower():
                            class_name = name
                            found = True
                            break
                    
                    if not found:
                        await ctx.send(f"❌ '{response.content}' is not a valid class. Please try again.")
                        return
            
            except asyncio.TimeoutError:
                await ctx.send("⏱️ Selection timed out.")
                return
            finally:
                try:
                    await selection_message.delete()
                    await response.delete()
                except:
                    pass
        
        # Check if the player has this class
        if class_name not in player_classes:
            await ctx.send(f"❌ You don't have a {class_name} class.")
            return
        
        # Start appearance selection
        # Remember this session
        self.active_appearance_sessions[ctx.author.id] = class_name
        
        # Ask for image upload
        embed = create_embed(
            title=f"🖼️ Set Appearance for {class_name}",
            description=f"Please upload an image to set as your {class_name}'s appearance.\n\n**Note:** Upload the image directly in your next message. You have 2 minutes to upload.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for image uploads for class appearances"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if this is an appearance upload
        if message.author.id in self.active_appearance_sessions:
            class_name = self.active_appearance_sessions[message.author.id]
            
            # Check for image attachments
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        # Set the appearance
                        success = self.player_class_handler.set_class_appearance(
                            message.author.id, class_name, attachment.url)
                        
                        if success:
                            embed = create_embed(
                                title="✅ Appearance Set",
                                description=f"Your {class_name}'s appearance has been updated!",
                                color=discord.Color.green()
                            )
                            embed.set_thumbnail(url=attachment.url)
                            await message.channel.send(embed=embed)
                        else:
                            await message.channel.send(f"❌ Failed to set appearance. Please try again.")
                        
                        # Remove this session
                        del self.active_appearance_sessions[message.author.id]
                        return
            
            # No valid image found
            if message.content:
                # If they sent a message without an image, give clarification
                await message.channel.send("Please upload an image file. Type 'cancel' to cancel.")
                
                # Check if they want to cancel
                if message.content.lower() == 'cancel':
                    await message.channel.send("✅ Appearance selection cancelled.")
                    del self.active_appearance_sessions[message.author.id]
    
    @class_cmd.command(name="reset")
    async def class_reset(self, ctx, *, class_name: str = None):
        """Reset skill and ability distribution for a class (costs gold)"""
        # Get player classes
        player_classes = self.player_class_handler.get_player_classes(ctx.author.id)
        
        if not player_classes:
            embed = create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{ctx.author.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # If no class specified and player has only one class, use that
        if not class_name and len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        elif not class_name:
            await ctx.send("❌ Please specify which class you want to reset, like `!class reset Fighter`.")
            return
        
        # Check if the player has this class
        if class_name not in player_classes:
            await ctx.send(f"❌ You don't have a {class_name} class.")
            return
        
        # Get class data
        class_data = player_classes[class_name]
        class_level = class_data.get("level", 1)
        
        # Calculate reset cost
        reset_cost = class_level * 50  # 50 gold per level
        
        # Check if player has enough gold
        player_data = self.player_manager.get_player_data(ctx.author.id)
        if not player_data:
            await ctx.send("❌ Failed to retrieve player data. Please try again.")
            return
        
        player_gold = player_data.get("gold", 0)
        
        if player_gold < reset_cost:
            embed = create_embed(
                title="❌ Insufficient Gold",
                description=f"Resetting your {class_name} (Level {class_level}) costs {reset_cost} gold, but you only have {player_gold} gold.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Confirm reset
        embed = create_embed(
            title=f"🔄 Reset {class_name}",
            description=f"Resetting your **Level {class_level} {class_name}** will cost **{reset_cost} gold**.\n\nThis will reset all skill points and ability score improvements back to their base values. Your level, appearance, and class abilities will be preserved.\n\nAre you sure you want to proceed?",
            color=discord.Color.orange()
        )
        
        # Add confirmation reactions
        confirm_message = await ctx.send(embed=embed)
        await confirm_message.add_reaction("✅")
        await confirm_message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Deduct gold
                player_data["gold"] -= reset_cost
                self.player_manager.save_player_data(ctx.author.id, player_data)
                
                # Reset class distribution
                success = self.player_class_handler.reset_distribution(ctx.author.id, class_name)
                
                if success:
                    embed = create_embed(
                        title="✅ Class Reset",
                        description=f"Your {class_name} has been reset! All skill points and ability score improvements have been returned to their base values.\n\n**{reset_cost} gold** has been deducted from your account.",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                else:
                    # Refund gold if reset failed
                    player_data["gold"] += reset_cost
                    self.player_manager.save_player_data(ctx.author.id, player_data)
                    
                    await ctx.send("❌ Failed to reset class. Your gold has been refunded.")
            else:
                await ctx.send("✅ Reset cancelled. No gold has been deducted.")
                
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Reset confirmation timed out. No gold has been deducted.")
        
        # Clean up the confirmation message
        try:
            await confirm_message.clear_reactions()
        except:
            pass
    
    @commands.command(name="new", aliases=["newclass"])
    async def new_class(self, ctx):
        """Create a new character class"""
        # Check if this is already an active selection
        if ctx.author.id in self.active_selections:
            await ctx.send("❌ You already have an active class selection. Please complete that one first.")
            return
        
        # Create and send class selection embed
        embed = self.class_manager.create_class_selection_embed()
        selection_message = await ctx.send(embed=embed)
        
        # Add class reactions for selection
        class_emojis = {
            "Barbarian": "🪓",
            "Bard": "🎭",
            "Cleric": "🙏",
            "Druid": "🌿",
            "Fighter": "⚔️",
            "Monk": "👊",
            "Paladin": "✝️",
            "Ranger": "🏹",
            "Rogue": "🗡️",
            "Sorcerer": "🔮",
            "Warlock": "😈",
            "Wizard": "📚",
            "Artificer": "⚙️"
        }
        
        # Register this as an active selection
        self.active_selections[ctx.author.id] = {
            "message_id": selection_message.id,
            "emojis": class_emojis
        }
        
        # Add reactions
        for emoji in class_emojis.values():
            await selection_message.add_reaction(emoji)
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle class selection reactions"""
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if this is a class selection
        if user.id not in self.active_selections:
            return
        
        selection_data = self.active_selections[user.id]
        
        # Check if this is the right message
        if reaction.message.id != selection_data["message_id"]:
            return
        
        # Get the selected class based on emoji
        emoji_to_class = {v: k for k, v in selection_data["emojis"].items()}
        selected_class = emoji_to_class.get(str(reaction.emoji))
        
        if not selected_class:
            return
        
        # Check if user already has this class
        if self.player_class_handler.has_class(user.id, selected_class):
            # Get channel and send message
            channel = reaction.message.channel
            error_message = await channel.send(f"❌ You already have the {selected_class} class. Please select a different class.")
            await send_temp_message(error_message, 10)
            return
        
        # Add the class
        success = self.player_class_handler.add_class(user.id, selected_class)
        
        # Clean up the selection
        try:
            del self.active_selections[user.id]
            await reaction.message.clear_reactions()
        except:
            pass
        
        # Get channel for response
        channel = reaction.message.channel
        
        if success:
            # Update the embed to show selection
            embed = create_embed(
                title="✅ Class Selected",
                description=f"You have selected the **{selected_class}** class!\n\nUse `!class` to view your character, `!class info {selected_class}` for details, and `!class appearance {selected_class}` to customize your appearance.",
                color=discord.Color.green()
            )
            await reaction.message.edit(embed=embed)
            
            # Create a more detailed confirmation message
            class_info = self.class_manager.get_class_info(selected_class)
            
            confirm_embed = create_embed(
                title=f"🧙‍♂️ {selected_class} Created",
                description=f"**{class_info['description']}**\n\nYour level 1 {selected_class} is ready for adventure!",
                color=discord.Color.blue()
            )
            
            # Add ability score info
            primary_abilities = [a.value.capitalize() for a in class_info["primary_abilities"]]
            bonus_ability = class_info["bonus_ability"].value.capitalize()
            
            confirm_embed.add_field(
                name="Ability Scores",
                value=f"**Primary:** {', '.join(primary_abilities)}\n**Bonus:** {bonus_ability}",
                inline=True
            )
            
            # Add skill info
            skills = ", ".join(class_info["starting_skills"])
            confirm_embed.add_field(
                name="Starting Skills",
                value=skills,
                inline=True
            )
            
            # Add next steps
            confirm_embed.add_field(
                name="Next Steps",
                value=(
                    "• Upload an appearance image with `!class appearance`\n"
                    "• View your character details with `!class info`\n"
                    "• Join quests with `!quests list`"
                ),
                inline=False
            )
            
            await channel.send(embed=confirm_embed)
        else:
            error_embed = create_embed(
                title="❌ Class Selection Failed",
                description=f"Failed to select the {selected_class} class. Please try again later.",
                color=discord.Color.red()
            )
            await reaction.message.edit(embed=error_embed)

async def setup(bot):
    await bot.add_cog(ClassCommands(bot))