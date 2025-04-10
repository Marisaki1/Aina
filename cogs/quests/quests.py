import re
import discord
from discord.ext import commands
import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from .quest_manager import QuestManager
from .player_manager import PlayerManager
from .utils import create_embed, format_duration, DIFFICULTY_COLORS, DIFFICULTY_EMOJIS

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quest_manager = QuestManager()
        self.player_manager = PlayerManager()
        self.QUEST_CHANNELS_FILE = "data/quests/channels/enabled_channels.json"
        
        # Ensure quest directories exist
        os.makedirs("data/quests/new", exist_ok=True)
        os.makedirs("data/quests/completed", exist_ok=True)
        os.makedirs("data/quests/playerdata", exist_ok=True)
        os.makedirs("data/quests/ongoing", exist_ok=True)
        os.makedirs("data/quests/channels", exist_ok=True)
        
    @commands.group(name="quests", aliases=["quest", "q"], invoke_without_command=True)
    async def quests(self, ctx):
        """Quest system commands"""
        embed = create_embed(
            title="📜 Quest System",
            description="Embark on adventures and complete quests!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Available Commands",
            value=(
                "**!quests create** - Create a new quest\n"
                "**!quests list** - Show all available quests\n"
                "**!quests select <quest_name>** - View quest details\n"
                "**!quests start <quest_name> [p: @user1, @user2...]** - Start a quest\n"
                "**!quests action <message/attachment>** - Record quest progress\n"
                "**!quests complete** - Complete the active quest\n"
                "**!quests cancel** - Cancel the active quest\n"
                "**!quests inventory** - Check your items and gold\n"
                "**!quests player info** - View your player stats\n"
                "**!quests new** - Create a new character class"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    # Add this new command that redirects to the ClassCommands cog's new_class command
    @quests.command(name="new")
    async def new_quest_class(self, ctx):
        """Create a new character class"""
        # Get the ClassCommands cog
        class_commands_cog = self.bot.get_cog("ClassCommands")
        if class_commands_cog:
            # Call the new_class method directly
            await class_commands_cog.new_class(ctx)
        else:
            await ctx.send("❌ Character class system is not available. Please contact an administrator.")

    @quests.command(name="create")
    async def create_quest(self, ctx):
        """Create a new quest through an interactive prompt"""
        author = ctx.author
        channel = ctx.channel
        
        # Start the interactive quest creation process
        await ctx.send(embed=create_embed(
            title="🔮 Quest Creation",
            description="Let's create a new quest together! I'll ask you a few questions.",
            color=discord.Color.blue()
        ))
        
        # Ask for quest name
        await ctx.send(embed=create_embed(
            title="Question 1/4",
            description="**What's the name of the quest?**",
            color=discord.Color.blue()
        ))
        
        def check(m):
            return m.author == author and m.channel == channel
        
        try:
            name_msg = await self.bot.wait_for('message', check=check, timeout=60)
            quest_name = name_msg.content.strip()
            
            if not quest_name:
                return await ctx.send(embed=create_embed(
                    title="❌ Quest Creation Failed",
                    description="The quest name cannot be empty.",
                    color=discord.Color.red()
                ))
            
            # Ask for difficulty
            difficulty_embed = create_embed(
                title="Question 2/4",
                description=(
                    "**What's the difficulty?**\n\n"
                    "1️⃣ Easy\n"
                    "2️⃣ Normal\n"
                    "3️⃣ Hard\n"
                    "4️⃣ Lunatic\n\n"
                    "Type a number (1-4) or the difficulty name."
                ),
                color=discord.Color.blue()
            )
            await ctx.send(embed=difficulty_embed)
            
            diff_msg = await self.bot.wait_for('message', check=check, timeout=60)
            difficulty_input = diff_msg.content.strip().lower()
            
            # Map input to difficulty
            difficulty_map = {
                "1": "Easy", "easy": "Easy",
                "2": "Normal", "normal": "Normal",
                "3": "Hard", "hard": "Hard",
                "4": "Lunatic", "lunatic": "Lunatic"
            }
            
            difficulty = difficulty_map.get(difficulty_input)
            if not difficulty:
                return await ctx.send(embed=create_embed(
                    title="❌ Quest Creation Failed",
                    description="Invalid difficulty. Please choose a number (1-4) or type Easy, Normal, Hard, or Lunatic.",
                    color=discord.Color.red()
                ))
            
            # Ask for quest description
            await ctx.send(embed=create_embed(
                title="Question 3/4",
                description="**What's the Quest Description?**",
                color=discord.Color.blue()
            ))
            
            desc_msg = await self.bot.wait_for('message', check=check, timeout=120)
            description = desc_msg.content.strip()
            
            if not description:
                return await ctx.send(embed=create_embed(
                    title="❌ Quest Creation Failed",
                    description="The quest description cannot be empty.",
                    color=discord.Color.red()
                ))
            
            # Ask for duration
            await ctx.send(embed=create_embed(
                title="Question 4/4",
                description="**How long is the quest duration? (format: hours:minutes)**\nExample: 2:30 for 2 hours and 30 minutes",
                color=discord.Color.blue()
            ))
            
            duration_msg = await self.bot.wait_for('message', check=check, timeout=60)
            duration_input = duration_msg.content.strip()
            
            try:
                hours, minutes = map(int, duration_input.split(':'))
                if hours < 0 or minutes < 0 or minutes >= 60:
                    raise ValueError
                duration = f"{hours:02d}:{minutes:02d}"
            except:
                return await ctx.send(embed=create_embed(
                    title="❌ Quest Creation Failed",
                    description="Invalid duration format. Please use the format hours:minutes (e.g., 2:30).",
                    color=discord.Color.red()
                ))
            
            # Generate unique ID for the quest
            unique_id = f"{quest_name.replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
            
            # Create quest data
            quest_data = {
                "id": unique_id,
                "name": quest_name,
                "description": description,
                "difficulty": difficulty,
                "duration": duration,
                "creator_id": ctx.author.id,
                "created_at": datetime.now().isoformat(),
                "rewards": {
                    "gold": 50 * ["Easy", "Normal", "Hard", "Lunatic"].index(difficulty) + 50,
                    "xp": 100 * ["Easy", "Normal", "Hard", "Lunatic"].index(difficulty) + 100
                }
            }
            
            # Save the quest
            success = self.quest_manager.create_quest(quest_data)
            
            if success:
                # Create a rich embed to show the created quest
                embed = create_embed(
                    title=f"✅ Quest Created: {quest_name}",
                    description=f"**ID:** {unique_id}\n**Description:** {description}",
                    color=DIFFICULTY_COLORS[difficulty]
                )
                embed.add_field(name="Difficulty", value=f"{DIFFICULTY_EMOJIS[difficulty]} {difficulty}", inline=True)
                embed.add_field(name="Duration", value=format_duration(duration), inline=True)
                embed.add_field(name="Rewards", value=f"🪙 {quest_data['rewards']['gold']} Gold\n✨ {quest_data['rewards']['xp']} XP", inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=create_embed(
                    title="❌ Quest Creation Failed",
                    description="There was an error saving the quest. Please try again.",
                    color=discord.Color.red()
                ))
                
        except asyncio.TimeoutError:
            await ctx.send(embed=create_embed(
                title="⏱️ Time's Up!",
                description="Quest creation timed out. Please try again.",
                color=discord.Color.red()
            ))

    @quests.command(name="list", aliases=["lists"])
    async def list_quests(self, ctx):
        """List all available quests"""
        quests = self.quest_manager.get_all_quests()
        
        if not quests:
            return await ctx.send(embed=create_embed(
                title="📜 Available Quests",
                description="There are no quests available at the moment.",
                color=discord.Color.blue()
            ))
        
        # Group quests by difficulty
        quests_by_difficulty = {
            "Easy": [],
            "Normal": [],
            "Hard": [],
            "Lunatic": []
        }
        
        for quest in quests:
            quests_by_difficulty[quest["difficulty"]].append(quest)
        
        embed = create_embed(
            title="📜 Available Quests",
            description="Here are all the quests you can embark on:",
            color=discord.Color.gold()
        )
        
        for difficulty, difficulty_quests in quests_by_difficulty.items():
            if difficulty_quests:
                quest_list = "\n".join([f"• **{q['name']}** - {format_duration(q['duration'])}" for q in difficulty_quests])
                embed.add_field(
                    name=f"{DIFFICULTY_EMOJIS[difficulty]} {difficulty} ({len(difficulty_quests)})",
                    value=quest_list or "No quests at this difficulty.",
                    inline=False
                )
        
        embed.set_footer(text=f"Use '!quests select <quest_name>' to view details • Total: {len(quests)} quests")
        await ctx.send(embed=embed)

    @quests.command(name="select")
    async def select_quest(self, ctx, *, quest_name):
        """View details about a specific quest"""
        quest = self.quest_manager.get_quest_by_name(quest_name)
        
        if not quest:
            return await ctx.send(embed=create_embed(
                title="❓ Quest Not Found",
                description=f"No quest found with the name '{quest_name}'.",
                color=discord.Color.red()
            ))
        
        embed = create_embed(
            title=f"📜 {quest['name']}",
            description=quest['description'],
            color=DIFFICULTY_COLORS[quest['difficulty']]
        )
        
        embed.add_field(name="Difficulty", value=f"{DIFFICULTY_EMOJIS[quest['difficulty']]} {quest['difficulty']}", inline=True)
        embed.add_field(name="Duration", value=format_duration(quest['duration']), inline=True)
        embed.add_field(name="Rewards", value=f"🪙 {quest['rewards']['gold']} Gold\n✨ {quest['rewards']['xp']} XP", inline=True)
        embed.add_field(name="Quest ID", value=f"`{quest['id']}`", inline=True)
        
        # Add a start button
        embed.set_footer(text=f"Use '!quests start {quest['name']}' to begin this quest")
        
        await ctx.send(embed=embed)

    @quests.command(name="start")
    async def start_quest(self, ctx, *, args):
        """Start a quest with optional party members"""
        # Parse quest name and participants
        if " p:" in args.lower():
            quest_name, participants_str = args.split(" p:", 1)
            # Extract mentioned users
            mentioned_users = [user.id for user in ctx.message.mentions]
            # Add the command author if not already in the list
            if ctx.author.id not in mentioned_users:
                mentioned_users.append(ctx.author.id)
        else:
            quest_name = args
            mentioned_users = [ctx.author.id]
            
        # Remove duplicates while preserving order
        participants = []
        for user_id in mentioned_users:
            if user_id not in participants:
                participants.append(user_id)
        
        # Check if the quest exists
        quest = self.quest_manager.get_quest_by_name(quest_name)
        if not quest:
            return await ctx.send(embed=create_embed(
                title="❓ Quest Not Found",
                description=f"No quest found with the name '{quest_name}'.",
                color=discord.Color.red()
            ))
        
        # Check if any participant is already on a quest
        active_quests = self.quest_manager.get_active_quests()
        busy_users = []
        
        for user_id in participants:
            for active_quest in active_quests:
                if user_id in active_quest.get("participants", []):
                    user = self.bot.get_user(user_id)
                    busy_users.append(user.mention if user else f"User ID: {user_id}")
                    break
        
        if busy_users:
            return await ctx.send(embed=create_embed(
                title="⚠️ Party Members Busy",
                description=f"The following users are already on a quest: {', '.join(busy_users)}",
                color=discord.Color.orange()
            ))
        
        # Start the quest
        start_time = datetime.now()
        hours, minutes = map(int, quest['duration'].split(':'))
        end_time = start_time + timedelta(hours=hours, minutes=minutes)
        
        active_quest = {
            "quest_id": quest["id"],
            "name": quest["name"],
            "difficulty": quest["difficulty"],
            "description": quest["description"],
            "participants": participants,
            "leader_id": ctx.author.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "actions": [],
            "status": "active",
            "rewards": quest["rewards"]
        }
        
        success = self.quest_manager.start_quest(active_quest)
        
        if not success:
            return await ctx.send(embed=create_embed(
                title="❌ Failed to Start Quest",
                description="There was an error starting the quest. Please try again.",
                color=discord.Color.red()
            ))
        
        # Create an embed for the quest start
        embed = create_embed(
            title=f"🚀 Quest Started: {quest['name']}",
            description=quest['description'],
            color=DIFFICULTY_COLORS[quest['difficulty']]
        )
        
        # Add quest details
        embed.add_field(name="Difficulty", value=f"{DIFFICULTY_EMOJIS[quest['difficulty']]} {quest['difficulty']}", inline=True)
        embed.add_field(name="Duration", value=format_duration(quest['duration']), inline=True)
        embed.add_field(name="End Time", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        
        # Add party members
        party_members = []
        for user_id in participants:
            user = self.bot.get_user(user_id)
            if user:
                party_members.append(user.mention)
            
        embed.add_field(
            name=f"🧙‍♂️ Party ({len(party_members)})",
            value="\n".join(party_members) if party_members else "Solo quest",
            inline=False
        )
        
        # Add instructions
        embed.add_field(
            name="📝 Next Steps",
            value=(
                "• Use `!quests action <message>` to log your progress\n"
                "• Upload images with `!quests action` to provide visual proof\n"
                "• Complete the quest with `!quests complete` when finished\n"
                "• Cancel anytime with `!quests cancel`"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Update player stats - mark that they started a quest
        for user_id in participants:
            self.player_manager.update_player_quest_count(user_id, "started")

    @quests.command(name="action")
    async def quest_action(self, ctx, *, message=None):
        """Record an action for the active quest"""
        # Check if the user is on an active quest
        active_quest = self.quest_manager.get_user_active_quest(ctx.author.id)
        
        if not active_quest:
            return await ctx.send(embed=create_embed(
                title="❓ No Active Quest",
                description="You're not currently on any quest.",
                color=discord.Color.red()
            ))
        
        # Process action content (message and/or attachments)
        action_data = {
            "user_id": ctx.author.id,
            "username": ctx.author.display_name,
            "timestamp": datetime.now().isoformat(),
            "content": message or "",
            "attachments": []
        }
        
        # Process attachments if any
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                action_data["attachments"].append({
                    "url": attachment.url,
                    "filename": attachment.filename,
                    "content_type": attachment.content_type
                })
        
        # Validate that there's either a message or attachments
        if not action_data["content"] and not action_data["attachments"]:
            return await ctx.send(embed=create_embed(
                title="❌ Invalid Action",
                description="Please provide a message or attach an image to record your quest progress.",
                color=discord.Color.red()
            ))
        
        # Record the action
        success = self.quest_manager.add_quest_action(active_quest["quest_id"], action_data)
        
        if not success:
            return await ctx.send(embed=create_embed(
                title="❌ Failed to Record Action",
                description="There was an error recording your action. Please try again.",
                color=discord.Color.red()
            ))
        
        # Confirm action recorded
        embed = create_embed(
            title="✅ Action Recorded",
            description=f"Your progress on **{active_quest['name']}** has been recorded!",
            color=discord.Color.green()
        )
        
        # Show action details
        if action_data["content"]:
            embed.add_field(name="📝 Message", value=action_data["content"], inline=False)
        
        if action_data["attachments"]:
            attachment_urls = "\n".join([f"[{a['filename']}]({a['url']})" for a in action_data["attachments"]])
            embed.add_field(name="🖼️ Attachments", value=attachment_urls, inline=False)
            
            # Set the first image as thumbnail if it's an image
            for attachment in action_data["attachments"]:
                if attachment["content_type"] and attachment["content_type"].startswith("image/"):
                    embed.set_thumbnail(url=attachment["url"])
                    break
        
        embed.set_footer(text="Use '!quests complete' when you're ready to finish the quest")
        await ctx.send(embed=embed)

    @quests.command(name="complete")
    async def complete_quest(self, ctx):
        """Complete the active quest"""
        # Check if the user is on an active quest
        active_quest = self.quest_manager.get_user_active_quest(ctx.author.id)
        
        if not active_quest:
            return await ctx.send(embed=create_embed(
                title="❓ No Active Quest",
                description="You're not currently on any quest.",
                color=discord.Color.red()
            ))
        
        # Check if any actions were recorded
        if not active_quest.get("actions", []):
            return await ctx.send(embed=create_embed(
                title="⚠️ No Progress Recorded",
                description="You need to record progress with `!quests action` before completing the quest.",
                color=discord.Color.orange()
            ))
        
        # Complete the quest
        completion_time = datetime.now()
        completion_success = self.quest_manager.complete_quest(active_quest["quest_id"], completion_time)
        
        if not completion_success:
            return await ctx.send(embed=create_embed(
                title="❌ Failed to Complete Quest",
                description="There was an error completing the quest. Please try again.",
                color=discord.Color.red()
            ))
        
        # Award rewards to all participants
        # Update the rewards section in complete_quest method
        rewards_given = []
        for user_id in active_quest["participants"]:
            user = self.bot.get_user(user_id)
            if not user:
                continue
                
            # Award gold and XP
            gold = active_quest["rewards"]["gold"]
            xp = active_quest["rewards"]["xp"]
            
            try:
                reward_success = self.player_manager.add_rewards(user_id, gold, xp)
                if reward_success:
                    rewards_given.append(f"{user.mention}: +{gold} 🪙, +{xp} ✨")
                
                # Update quest completion count
                self.player_manager.update_player_quest_count(user_id, "completed")
            except Exception as e:
                print(f"Error giving rewards to {user_id}: {e}")
        
        # Create a completion embed
        embed = create_embed(
            title=f"🎉 Quest Completed: {active_quest['name']}",
            description=f"Congratulations on completing the {DIFFICULTY_EMOJIS[active_quest['difficulty']]} **{active_quest['difficulty']}** quest!",
            color=DIFFICULTY_COLORS[active_quest['difficulty']]
        )
        
        # Add quest stats
        start_time = datetime.fromisoformat(active_quest["start_time"])
        time_taken = completion_time - start_time
        hours, remainder = divmod(time_taken.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed.add_field(
            name="⏱️ Quest Stats",
            value=(
                f"**Started:** <t:{int(start_time.timestamp())}:R>\n"
                f"**Time Taken:** {int(hours)}h {int(minutes)}m {int(seconds)}s\n"
                f"**Actions Recorded:** {len(active_quest.get('actions', []))}"
            ),
            inline=False
        )
        
        # Add rewards section
        embed.add_field(
            name="💰 Rewards Given",
            value="\n".join(rewards_given) or "No rewards were distributed.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    # Replace the cancel_quest method in cogs/quests/quests.py with this:

    @quests.command(name="cancel")
    async def cancel_quest(self, ctx):
        """Cancel the active quest"""
        # Check if the user is on an active quest
        active_quest = self.quest_manager.get_user_active_quest(ctx.author.id)
        
        if not active_quest:
            return await ctx.send(embed=create_embed(
                title="❓ No Active Quest",
                description="You're not currently on any quest.",
                color=discord.Color.red()
            ))
        
        # Only allow the quest leader or server admin to cancel
        if ctx.author.id != active_quest["leader_id"] and not ctx.author.guild_permissions.administrator:
            return await ctx.send(embed=create_embed(
                title="❌ Permission Denied",
                description="Only the quest leader or a server admin can cancel this quest.",
                color=discord.Color.red()
            ))
        
        # Cancel the quest and move it to failed
        try:
            cancel_time = datetime.now()
            cancel_success = self.quest_manager.fail_quest(active_quest["quest_id"], cancel_time)
            
            if not cancel_success:
                return await ctx.send(embed=create_embed(
                    title="❌ Failed to Cancel Quest",
                    description="There was an error cancelling the quest. Please try again.",
                    color=discord.Color.red()
                ))
        except Exception as e:
            return await ctx.send(embed=create_embed(
                title="❌ Error Cancelling Quest",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            ))
        
        # Create a cancellation embed
        embed = create_embed(
            title=f"🚫 Quest Cancelled: {active_quest['name']}",
            description="The quest has been cancelled.",
            color=discord.Color.red()
        )
        
        # Add participants
        participants = []
        for user_id in active_quest["participants"]:
            user = self.bot.get_user(user_id)
            if user:
                participants.append(user.mention)
                
        if participants:
            embed.add_field(
                name="👥 Participants Notified",
                value="\n".join(participants),
                inline=False
            )
        
        embed.set_footer(text="Use '!quests list' to view available quests")
        await ctx.send(embed=embed)
        
    @quests.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx):
        """Display your inventory of items and gold"""
        player_data = self.player_manager.get_player_data(ctx.author.id)
        
        if not player_data:
            # Create new player data if not exists
            player_data = self.player_manager.create_player(ctx.author.id, ctx.author.display_name)
            
        # Create inventory embed
        embed = create_embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            description="Your collected treasures and rewards",
            color=discord.Color.gold()
        )
        
        # Add currency section
        embed.add_field(
            name="💰 Currency",
            value=f"**Gold:** 🪙 {player_data.get('gold', 0):,}",
            inline=False
        )
        
        # Add items section (create tabs if more than 10 items)
        items = player_data.get("items", [])
        if not items:
            embed.add_field(
                name="📦 Items",
                value="You don't have any items yet. Complete quests to earn rewards!",
                inline=False
            )
        else:
            # Group items by type
            items_by_type = {}
            for item in items:
                item_type = item.get("type", "Miscellaneous")
                if item_type not in items_by_type:
                    items_by_type[item_type] = []
                items_by_type[item_type].append(item)
            
            # Display items by type (max 3 types to avoid embed limit)
            for i, (item_type, type_items) in enumerate(list(items_by_type.items())[:3]):
                item_list = "\n".join([f"• **{item['name']}** x{item.get('quantity', 1)}" for item in type_items[:5]])
                if len(type_items) > 5:
                    item_list += f"\n*...and {len(type_items) - 5} more {item_type}*"
                    
                embed.add_field(
                    name=f"📦 {item_type} ({len(type_items)})",
                    value=item_list,
                    inline=True
                )
            
            # If there are more types, mention them
            if len(items_by_type) > 3:
                remaining_types = len(items_by_type) - 3
                embed.set_footer(text=f"Use '!quests inventory [type]' to view specific categories • +{remaining_types} more categories")
        
        await ctx.send(embed=embed)
    
    @quests.command(name="player", aliases=["profile", "info"])
    async def player_info(self, ctx, user: discord.Member = None):
        """Display player stats and information"""
        target_user = user or ctx.author
        player_data = self.player_manager.get_player_data(target_user.id)
        
        if not player_data:
            # Create new player data if not exists
            player_data = self.player_manager.create_player(target_user.id, target_user.display_name)
        
        # Calculate level based on XP
        xp = player_data.get("xp", 0)
        level = max(1, 1 + int((xp / 100) ** 0.5))  # Ensure minimum level 1
        next_level_xp = ((level) ** 2) * 100
        prev_level_xp = ((level-1) ** 2) * 100
        xp_needed = next_level_xp - prev_level_xp
        xp_progress = min(1.0, (xp - prev_level_xp) / max(1, xp_needed)) 
        
        # Create progress bar
        progress_bar_length = 10
        filled_blocks = int(xp_progress * progress_bar_length)
        progress_bar = "█" * filled_blocks + "░" * (progress_bar_length - filled_blocks)
        
        # Create player info embed
        embed = create_embed(
            title=f"🏆 {target_user.display_name}'s Profile",
            description=f"Level {level} Adventurer",
            color=discord.Color.blue()
        )
        
        # Add avatar if available
        if target_user.avatar:
            embed.set_thumbnail(url=target_user.avatar.url)
        
        # Add stats section
        embed.add_field(
            name="📊 Stats",
            value=(
                f"**Level:** {level}\n"
                f"**XP:** {xp:,} / {next_level_xp:,}\n"
                f"**Progress:** {progress_bar} {int(xp_progress*100)}%\n"
                f"**Gold:** 🪙 {player_data.get('gold', 0):,}"
            ),
            inline=True
        )
        
        # Add quest stats
        quests_started = player_data.get("quests_started", 0)
        quests_completed = player_data.get("quests_completed", 0)
        completion_rate = (quests_completed / quests_started * 100) if quests_started > 0 else 0
        
        embed.add_field(
            name="🔍 Quest History",
            value=(
                f"**Started:** {quests_started}\n"
                f"**Completed:** {quests_completed}\n"
                f"**Completion Rate:** {completion_rate:.1f}%\n"
                f"**Active Quest:** {'Yes' if self.quest_manager.get_user_active_quest(target_user.id) else 'No'}"
            ),
            inline=True
        )
        
        # Add achievements if any
        achievements = player_data.get("achievements", [])
        if achievements:
            achiev_list = "\n".join([f"• {a['name']}" for a in achievements[:3]])
            if len(achievements) > 3:
                achiev_list += f"\n...and {len(achievements)-3} more"
            embed.add_field(
                name="🏅 Achievements",
                value=achiev_list,
                inline=False
            )
        
        await ctx.send(embed=embed)

    # Add this inside the Quests class in cogs/quests/quest.py, alongside other commands

    @quests.command(name="records", aliases=["history"])
    async def quest_records(self, ctx, filter_type=None, *, quest_name=None):
        """View your quest history with optional filters"""
        user_id = ctx.author.id
        
        # Get all completed quests
        completed_quests = self._get_user_completed_quests(user_id)
        
        # Get all failed/canceled quests
        failed_quests = self._get_user_failed_quests(user_id) 
        
        if quest_name and filter_type != "select":
            return await ctx.send(embed=create_embed(
                title="❌ Invalid Command Usage",
                description="Quest name can only be used with `select` filter. Try `!quests records select <quest_name>`.",
                color=discord.Color.red()
            ))
        
        # Handle specific quest details view
        if filter_type == "select" and quest_name:
            return await self._display_quest_details(ctx, user_id, quest_name)
        
        # Apply filters
        if filter_type == "completed":
            quests_to_display = completed_quests
            title = "✅ Completed Quests"
            empty_message = "You haven't completed any quests yet."
        elif filter_type == "failed":
            quests_to_display = failed_quests
            title = "❌ Failed/Cancelled Quests"
            empty_message = "You haven't failed or cancelled any quests."
        else:
            quests_to_display = completed_quests + failed_quests
            title = "📜 Quest History"
            empty_message = "You haven't participated in any quests yet."
            
        # Sort all quests by date (most recent first)
        quests_to_display.sort(key=lambda q: q.get("completion_time", q.get("cancelled_time", "")), reverse=True)
        
        if not quests_to_display:
            return await ctx.send(embed=create_embed(
                title=title,
                description=empty_message,
                color=discord.Color.blue()
            ))
        
        # Create paginated view of quests (20 per page)
        page = 0
        max_page = (len(quests_to_display) - 1) // 20
        
        # Function to generate embed for the current page
        def get_page_embed(page_num):
            start_idx = page_num * 20
            end_idx = min(start_idx + 20, len(quests_to_display))
            
            embed = create_embed(
                title=title,
                description=f"Showing quests {start_idx+1}-{end_idx} of {len(quests_to_display)}",
                color=discord.Color.gold()
            )
            
            # Group quests by difficulty for better organization
            quests_by_difficulty = {
                "Easy": [],
                "Normal": [],
                "Hard": [],
                "Lunatic": []
            }
            
            for quest in quests_to_display[start_idx:end_idx]:
                difficulty = quest.get("difficulty", "Normal")
                quests_by_difficulty[difficulty].append(quest)
            
            # Add fields for each difficulty that has quests
            for difficulty, diff_quests in quests_by_difficulty.items():
                if diff_quests:
                    quest_list = ""
                    for q in diff_quests:
                        # Format the quest entry
                        quest_time = q.get("completion_time") or q.get("cancelled_time", "")
                        if quest_time:
                            quest_time = datetime.fromisoformat(quest_time)
                            time_str = f"<t:{int(quest_time.timestamp())}:R>"
                        else:
                            time_str = "Unknown time"
                        
                        status = "✅" if "completion_time" in q else "❌"
                        quest_list += f"{status} **{q['name']}** - {time_str}\n"
                    
                    embed.add_field(
                        name=f"{DIFFICULTY_EMOJIS[difficulty]} {difficulty} ({len(diff_quests)})",
                        value=quest_list or "No quests at this difficulty.",
                        inline=False
                    )
            
            embed.set_footer(text=f"Page {page_num+1}/{max_page+1} • Use '!quests records select <quest_name>' to view details")
            return embed
        
        # Send the first page
        message = await ctx.send(embed=get_page_embed(page))
        
        # If there's only one page, don't add reactions
        if max_page == 0:
            return
        
        # Add pagination reactions
        pagination_emojis = ["⬅️", "➡️"]
        for emoji in pagination_emojis:
            await message.add_reaction(emoji)
        
        # Define a check for the reaction
        def check(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == message.id
                and str(reaction.emoji) in pagination_emojis
            )
        
        # Wait for reactions and paginate
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                
                # Handle navigation
                if str(reaction.emoji) == "⬅️" and page > 0:
                    page -= 1
                elif str(reaction.emoji) == "➡️" and page < max_page:
                    page += 1
                else:
                    await message.remove_reaction(str(reaction.emoji), user)
                    continue
                    
                # Update the embed with the new page
                await message.edit(embed=get_page_embed(page))
                await message.remove_reaction(str(reaction.emoji), user)
                
            except asyncio.TimeoutError:
                # Stop listening for reactions after timeout
                break

    # Add these helper methods to the Quests class

    def _get_user_completed_quests(self, user_id):
        """Get all completed quests for a user"""
        completed_quests = []
        try:
            completed_dir = os.path.join(self.quest_manager.base_path, "completed")
            for file in os.listdir(completed_dir):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(completed_dir, file)) as f:
                            quest = json.load(f)
                            if str(user_id) in [str(p) for p in quest.get("participants", [])]:
                                completed_quests.append(quest)
                    except Exception as e:
                        print(f"Error reading completed quest file: {e}")
        except Exception as e:
            print(f"Error accessing completed quests directory: {e}")
        return completed_quests

    def _get_user_failed_quests(self, user_id):
        """Get all failed/cancelled quests for a user"""
        failed_quests = []
        try:
            failed_dir = os.path.join(self.quest_manager.base_path, "failed")
            # Create the directory if it doesn't exist
            os.makedirs(failed_dir, exist_ok=True)
            
            for file in os.listdir(failed_dir):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(failed_dir, file)) as f:
                            quest = json.load(f)
                            if str(user_id) in [str(p) for p in quest.get("participants", [])]:
                                failed_quests.append(quest)
                    except Exception as e:
                        print(f"Error reading failed quest file: {e}")
        except Exception as e:
            print(f"Error accessing failed quests directory: {e}")
        return failed_quests

    async def _display_quest_details(self, ctx, user_id, quest_name):
        """Display detailed information about a specific quest, including actions taken"""
        # Search in both completed and failed quests
        all_quests = self._get_user_completed_quests(user_id) + self._get_user_failed_quests(user_id)
        
        # Find the quest by name (case-insensitive)
        target_quest = None
        for quest in all_quests:
            if quest["name"].lower() == quest_name.lower():
                target_quest = quest
                break
        
        if not target_quest:
            return await ctx.send(embed=create_embed(
                title="❓ Quest Not Found",
                description=f"No quest found with the name '{quest_name}' in your history.",
                color=discord.Color.red()
            ))
        
        # Create a rich embed to display quest details
        is_completed = "completion_time" in target_quest
        
        embed = create_embed(
            title=f"{'✅' if is_completed else '❌'} {target_quest['name']}",
            description=target_quest.get("description", "No description available."),
            color=DIFFICULTY_COLORS[target_quest.get("difficulty", "Normal")]
        )
        
        # Add basic quest info
        embed.add_field(
            name="📊 Quest Info",
            value=(
                f"**Difficulty:** {DIFFICULTY_EMOJIS[target_quest.get('difficulty', 'Normal')]} {target_quest.get('difficulty', 'Normal')}\n"
                f"**Status:** {'Completed' if is_completed else 'Failed/Cancelled'}\n"
                f"**Participants:** {len(target_quest.get('participants', []))}"
            ),
            inline=True
        )
        
        # Add timing information
        start_time = datetime.fromisoformat(target_quest.get("start_time", datetime.now().isoformat()))
        end_time_field = "completion_time" if is_completed else "cancelled_time"
        end_time = datetime.fromisoformat(target_quest.get(end_time_field, datetime.now().isoformat()))
        
        # Calculate duration
        duration = end_time - start_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed.add_field(
            name="⏱️ Timeline",
            value=(
                f"**Started:** <t:{int(start_time.timestamp())}:R>\n"
                f"**{'Completed' if is_completed else 'Cancelled'}:** <t:{int(end_time.timestamp())}:R>\n"
                f"**Duration:** {int(hours)}h {int(minutes)}m {int(seconds)}s"
            ),
            inline=True
        )
        
        # Add reward info (if completed)
        if is_completed and "rewards" in target_quest:
            embed.add_field(
                name="💰 Rewards",
                value=(
                    f"**Gold:** 🪙 {target_quest['rewards'].get('gold', 0)}\n"
                    f"**XP:** ✨ {target_quest['rewards'].get('xp', 0)}"
                ),
                inline=True
            )
        
        # Add actions section (paginated if many)
        actions = target_quest.get("actions", [])
        if actions:
            # Format the actions list (limited to first 5 for embed size)
            action_list = ""
            for i, action in enumerate(actions[:5]):
                user_id = action.get("user_id")
                user = self.bot.get_user(user_id) if user_id else None
                username = user.display_name if user else action.get("username", "Unknown User")
                timestamp = datetime.fromisoformat(action.get("timestamp", datetime.now().isoformat()))
                
                content = action.get("content", "")
                if content and len(content) > 50:
                    content = content[:47] + "..."
                    
                action_list += f"**{i+1}.** {username} - <t:{int(timestamp.timestamp())}:R>\n"
                if content:
                    action_list += f"└ {content}\n"
                
                attachments = action.get("attachments", [])
                for attachment in attachments:
                    url = attachment.get("url")
                    if url:
                        action_list += f"└ 🖼️ [Attachment]({url})\n"
            
            # Add note if there are more actions
            if len(actions) > 5:
                action_list += f"*...and {len(actions) - 5} more actions*"
                
            embed.add_field(
                name=f"📝 Actions ({len(actions)})",
                value=action_list or "No actions recorded.",
                inline=False
            )
        else:
            embed.add_field(
                name="📝 Actions",
                value="No actions were recorded for this quest.",
                inline=False
            )
        
        await ctx.send(embed=embed)

    # Add this to the Quests class in cogs/quests/quests.py

    @quests.command(name="ongoing", aliases=["active"])
    async def ongoing_quests(self, ctx):
        """Display currently ongoing quests"""
        ongoing = self.quest_manager.get_ongoing_quests()
        
        if not ongoing:
            return await ctx.send(embed=create_embed(
                title="📜 Ongoing Quests",
                description="There are no ongoing quests at the moment.",
                color=discord.Color.blue()
            ))
        
        # Group quests by difficulty
        quests_by_difficulty = {
            "Easy": [],
            "Normal": [],
            "Hard": [],
            "Lunatic": []
        }
        
        for quest in ongoing:
            quests_by_difficulty[quest["difficulty"]].append(quest)
        
        embed = create_embed(
            title="⚔️ Ongoing Quests",
            description=f"There are currently {len(ongoing)} active quests:",
            color=discord.Color.gold()
        )
        
        # Add a field for each difficulty level
        for difficulty, difficulty_quests in quests_by_difficulty.items():
            if difficulty_quests:
                quest_list = ""
                for quest in difficulty_quests:
                    # Get leader info
                    leader_id = quest.get("leader_id")
                    leader = self.bot.get_user(leader_id) if leader_id else None
                    leader_name = leader.display_name if leader else "Unknown"
                    
                    # Get time info
                    start_time = datetime.fromisoformat(quest.get("start_time", datetime.now().isoformat()))
                    end_time = datetime.fromisoformat(quest.get("end_time", datetime.now().isoformat()))
                    
                    # Format quest entry
                    quest_list += (
                        f"• **{quest['name']}**\n"
                        f"└ Leader: {leader_name}\n"
                        f"└ Party: {len(quest.get('participants', []))}\n"
                        f"└ Ends: <t:{int(end_time.timestamp())}:R>\n"
                    )
                
                embed.add_field(
                    name=f"{DIFFICULTY_EMOJIS[difficulty]} {difficulty} ({len(difficulty_quests)})",
                    value=quest_list or "No quests at this difficulty.",
                    inline=False
                )
        
        embed.set_footer(text="Use '!quests select <quest_name>' to view detailed quest information")
        await ctx.send(embed=embed)

    @quests.command(name="enable")
    @commands.has_permissions(manage_channels=True)
    async def enable_quests(self, ctx, *, options=None):
        """
        Enable random encounters in this channel with optional timing parameters.
        
        Usage:
        !quests enable - Enable with default timing
        !quests enable t: mm:ss c: mm:ss - Set timing and cooldown
        """
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        # Default values
        encounter_time = "05:00"  # 5 minutes
        cooldown_time = "10:00"  # 10 minutes
        
        # Parse options if provided
        if options:
            # Extract timing parameter (t:)
            time_match = re.search(r't:\s*(\d{2}:\d{2})', options)
            if time_match:
                encounter_time = time_match.group(1)
                
            # Extract cooldown parameter (c:)
            cooldown_match = re.search(r'c:\s*(\d{2}:\d{2})', options)
            if cooldown_match:
                cooldown_time = cooldown_match.group(1)
        
        # Parse the time values to seconds
        try:
            encounter_minutes, encounter_seconds = map(int, encounter_time.split(':'))
            encounter_total_seconds = encounter_minutes * 60 + encounter_seconds
            
            cooldown_minutes, cooldown_seconds = map(int, cooldown_time.split(':'))
            cooldown_total_seconds = cooldown_minutes * 60 + cooldown_seconds
            
            if encounter_total_seconds < 1 or cooldown_total_seconds < 1:
                return await ctx.send(embed=create_embed(
                    title="❌ Invalid Time Values",
                    description="Time and cooldown values must be at least 1 second.",
                    color=discord.Color.red()
                ))
        except ValueError:
            return await ctx.send(embed=create_embed(
                title="❌ Invalid Format",
                description="Please use the format `!quests enable t: mm:ss c: mm:ss`",
                color=discord.Color.red()
            ))
        
        # Enable the channel and save timing settings
        timing_data = {
            "enabled": True,
            "encounter_time": encounter_time,
            "encounter_seconds": encounter_total_seconds,
            "cooldown_time": cooldown_time,
            "cooldown_seconds": cooldown_total_seconds
        }
        
        self.set_channel_enabled(guild_id, channel_id, True, timing_data)
        
        # Create a beautiful confirmation embed
        embed = create_embed(
            title="✅ Random Encounters Enabled",
            description=f"Random encounters are now enabled in this channel with custom timing.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="⏱️ Encounter Timing",
            value=f"**Frequency:** Every {encounter_minutes}m {encounter_seconds}s\n**Cooldown:** {cooldown_minutes}m {cooldown_seconds}s after each encounter",
            inline=False
        )
        
        embed.set_footer(text="Use '!quests disable' to turn off random encounters in this channel")
        
        # If you want to notify the random encounters cog about this change
        random_encounters_cog = self.bot.get_cog("NewRandomEncounters")
        if random_encounters_cog:
            random_encounters_cog.refresh_enabled_channels()
        
        await ctx.send(embed=embed)

    @quests.command(name="disable")
    @commands.has_permissions(manage_channels=True)
    async def disable_quests(self, ctx):
        """Disable random encounters in this channel"""
        self.set_channel_enabled(ctx.guild.id, ctx.channel.id, False)
        
        embed = create_embed(
            title="🚫 Random Encounters Disabled",
            description=f"Random encounters are now disabled in this channel.",
            color=discord.Color.red()
        )
        
        # If you want to notify the random encounters cog about this change
        random_encounters_cog = self.bot.get_cog("RandomEncounters")
        if random_encounters_cog:
            random_encounters_cog.refresh_enabled_channels()
        
        await ctx.send(embed=embed)

    def _load_enabled_channels(self):
        """Load the list of channels where random encounters are enabled"""
        try:
            with open(self.QUEST_CHANNELS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Corrupted channels file, resetting...")
            return {}
        except FileNotFoundError:
            print("Creating new channels file...")
            return {}

    def _save_enabled_channels(self, data):
        """Save the list of enabled channels"""
        with open(self.QUEST_CHANNELS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def is_channel_enabled(self, guild_id, channel_id):
        """Check if random encounters are enabled for a specific channel"""
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        
        enabled_channels = self._load_enabled_channels()
        
        # If guild has no configuration, use default (disabled)
        if guild_id not in enabled_channels:
            return False
        
        # If channel has specific configuration, use it
        return channel_id in enabled_channels[guild_id]

    def set_channel_enabled(self, guild_id, channel_id, enabled=True, timing_data=None):
        """Enable or disable random encounters for a specific channel, with optional timing data"""
        guild_id = str(guild_id)
        channel_id = str(channel_id)
        
        enabled_channels = self._load_enabled_channels()
        
        # Initialize guild entry if it doesn't exist
        if guild_id not in enabled_channels:
            enabled_channels[guild_id] = {}
        
        # Add or remove the channel from the enabled list
        if enabled:
            if timing_data:
                enabled_channels[guild_id][channel_id] = timing_data
            else:
                # Default timing data
                enabled_channels[guild_id][channel_id] = {
                    "enabled": True,
                    "encounter_time": "05:00",  # 5 minutes
                    "encounter_seconds": 300,
                    "cooldown_time": "10:00",  # 10 minutes
                    "cooldown_seconds": 600
                }
        elif channel_id in enabled_channels[guild_id]:
            del enabled_channels[guild_id][channel_id]
        
        # Save the changes
        self._save_enabled_channels(enabled_channels)
        
        return enabled

    # Add this to the Quests class in quests.py

    @quests.command(name="profile", aliases=["me"])
    async def interactive_profile(self, ctx):
        """Interactive profile with navigation reactions"""
        user = ctx.author
        
        # Create initial embed with player info
        embed = await self._create_player_info_embed(user)
        
        # Send the message
        profile_message = await ctx.send(embed=embed)
        
        # Add navigation reactions
        reactions = {
            "👤": "profile",  # Profile
            "🧙‍♂️": "class",   # Class Info
            "🎯": "skills",   # Skills
            "🎒": "inventory" # Inventory
        }
        
        for emoji in reactions.keys():
            await profile_message.add_reaction(emoji)
        
        def check(reaction, reactor):
            return (reactor == user and 
                    str(reaction.emoji) in reactions and 
                    reaction.message.id == profile_message.id)
        
        # Wait for reactions
        while True:
            try:
                reaction, reactor = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                # Remove the user's reaction
                try:
                    await profile_message.remove_reaction(reaction.emoji, reactor)
                except:
                    pass  # Ignore if we can't remove it
                
                # Get the page type
                page_type = reactions[str(reaction.emoji)]
                
                # Update the embed based on reaction
                if page_type == "profile":
                    embed = await self._create_player_info_embed(user)
                elif page_type == "class":
                    embed = await self._create_class_info_embed(user)
                elif page_type == "skills":
                    embed = await self._create_skills_embed(user)
                elif page_type == "inventory":
                    embed = await self._create_inventory_embed(user)
                
                # Update the message
                await profile_message.edit(embed=embed)
                
            except asyncio.TimeoutError:
                # After timeout, remove our reactions and stop listening
                try:
                    await profile_message.clear_reactions()
                except:
                    pass
                break

    # Helper methods for creating the various embeds
    async def _create_player_info_embed(self, user):
        """Create player info embed"""
        player_data = self.player_manager.get_player_data(user.id)
        
        if not player_data:
            player_data = self.player_manager.create_player(user.id, user.display_name)
        
        # Calculate level based on XP
        xp = player_data.get("xp", 0)
        level = max(1, 1 + int((xp / 100) ** 0.5))
        next_level_xp = ((level) ** 2) * 100
        prev_level_xp = ((level-1) ** 2) * 100
        xp_needed = next_level_xp - prev_level_xp
        xp_progress = min(1.0, (xp - prev_level_xp) / max(1, xp_needed)) 
        
        # Create progress bar
        progress_bar_length = 15
        filled_blocks = int(xp_progress * progress_bar_length)
        progress_bar = "█" * filled_blocks + "░" * (progress_bar_length - filled_blocks)
        
        # Create player info embed
        embed = create_embed(
            title=f"👤 {user.display_name}'s Profile",
            description=f"Level {level} Adventurer\n*Click reactions below to navigate*",
            color=discord.Color.blue()
        )
        
        # Add avatar if available
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        # Add stats section
        embed.add_field(
            name="📊 Stats",
            value=(
                f"**Level:** {level}\n"
                f"**XP:** {xp:,} / {next_level_xp:,}\n"
                f"**Progress:** {progress_bar} {int(xp_progress*100)}%\n"
                f"**Gold:** 🪙 {player_data.get('gold', 0):,}"
            ),
            inline=True
        )
        
        # Add quest stats
        quests_started = player_data.get("quests_started", 0)
        quests_completed = player_data.get("quests_completed", 0)
        completion_rate = (quests_completed / quests_started * 100) if quests_started > 0 else 0
        
        embed.add_field(
            name="🔍 Quest History",
            value=(
                f"**Started:** {quests_started}\n"
                f"**Completed:** {quests_completed}\n"
                f"**Completion Rate:** {completion_rate:.1f}%\n"
                f"**Active Quest:** {'Yes' if self.quest_manager.get_user_active_quest(user.id) else 'No'}"
            ),
            inline=True
        )
        
        # Add navigation guide
        embed.add_field(
            name="📋 Navigation",
            value=(
                "👤 Profile\n"
                "🧙‍♂️ Class Info\n"
                "🎯 Skills\n"
                "🎒 Inventory"
            ),
            inline=False
        )
        
        return embed

    async def _create_class_info_embed(self, user):
        """Create class info embed"""
        # Get the ClassCommands cog
        class_commands_cog = self.bot.get_cog("ClassCommands")
        if not class_commands_cog:
            return create_embed(
                title="❌ Class System Unavailable",
                description="The class system is currently unavailable.",
                color=discord.Color.red()
            )
        
        # Get player classes
        player_classes = class_commands_cog.player_class_handler.get_player_classes(user.id)
        
        if not player_classes:
            return create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{user.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
        
        # If only one class, use that, otherwise use the first one
        if len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        else:
            class_name = list(player_classes.keys())[0]
        
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
        ac = (dexterity + 1) // 2 + 5
        
        # Create class info embed
        embed = create_embed(
            title=f"🧙‍♂️ {user.display_name}'s {class_name}",
            description=f"**Level {class_data.get('level', 1)} {class_name}**\n**HP:** {hp} | **MP:** {mp} | **AC:** {ac}\n*Click reactions below to navigate*",
            color=discord.Color.blue()
        )
        
        # Add appearance if available
        if class_data.get("appearance_url"):
            embed.set_thumbnail(url=class_data["appearance_url"])
        
        # Add XP info
        level = class_data.get("level", 1)
        xp = class_data.get("xp", 0)
        xp_needed = class_commands_cog.class_manager.get_xp_for_next_level(level)
        
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
        
        # Add ability scores
        ability_text = ""
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = ability_scores.get(ability, 10)
            modifier = (score - 10) // 2
            sign = "+" if modifier >= 0 else ""
            ability_text += f"**{ability[:3].upper()}:** {score} ({sign}{modifier})\n"
        
        embed.add_field(
            name="Ability Scores",
            value=ability_text,
            inline=True
        )
        
        # Add navigation guide
        embed.add_field(
            name="📋 Navigation",
            value=(
                "👤 Profile\n"
                "🧙‍♂️ Class Info\n"
                "🎯 Skills\n"
                "🎒 Inventory"
            ),
            inline=False
        )
        
        return embed

    async def _create_skills_embed(self, user):
        """Create skills embed"""
        # Get the ClassCommands cog
        class_commands_cog = self.bot.get_cog("ClassCommands")
        if not class_commands_cog:
            return create_embed(
                title="❌ Class System Unavailable",
                description="The class system is currently unavailable.",
                color=discord.Color.red()
            )
        
        # Get player classes
        player_classes = class_commands_cog.player_class_handler.get_player_classes(user.id)
        
        if not player_classes:
            return create_embed(
                title="🧙‍♂️ No Character Classes",
                description=f"{user.mention}, you don't have any character classes yet. Use `!quests new` to create your first character class!",
                color=discord.Color.orange()
            )
        
        # If only one class, use that, otherwise use the first one
        if len(player_classes) == 1:
            class_name = list(player_classes.keys())[0]
        else:
            class_name = list(player_classes.keys())[0]
        
        # Get class data
        class_data = player_classes[class_name]
        ability_scores = class_data.get("ability_scores", {})
        skills = class_data.get("skills", {})
        
        # Create skills embed
        embed = create_embed(
            title=f"🎯 {user.display_name}'s {class_name} Skills",
            description=f"Level {class_data.get('level', 1)} {class_name}\n*Click reactions below to navigate*",
            color=discord.Color.blue()
        )
        
        # Add appearance if available
        if class_data.get("appearance_url"):
            embed.set_thumbnail(url=class_data["appearance_url"])
        
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
            ability_mod = (ability_score - 10) // 2
            total_bonus = skill_points + ability_mod
            
            # Add to the appropriate ability group
            if ability in skills_by_ability:
                skills_by_ability[ability].append((skill_name, skill_points, total_bonus))
        
        # Display skills by ability
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
                for skill_name, points, bonus in sorted(skill_list, key=lambda x: x[0]):
                    name_format = f"**{skill_name}**" if points > 0 else skill_name
                    sign = "+" if bonus >= 0 else ""
                    skill_text += f"{name_format}: {points} ({sign}{bonus})\n"
                
                if skill_text:
                    embed.add_field(
                        name=ability_names.get(ability, ability.capitalize()),
                        value=skill_text,
                        inline=True
                    )
        
        # Add navigation guide
        embed.add_field(
            name="📋 Navigation",
            value=(
                "👤 Profile\n"
                "🧙‍♂️ Class Info\n"
                "🎯 Skills\n"
                "🎒 Inventory"
            ),
            inline=False
        )
        
        return embed

    async def _create_inventory_embed(self, user):
        """Create inventory embed"""
        player_data = self.player_manager.get_player_data(user.id)
        
        if not player_data:
            player_data = self.player_manager.create_player(user.id, user.display_name)
        
        # Create inventory embed
        embed = create_embed(
            title=f"🎒 {user.display_name}'s Inventory",
            description="Your collected treasures and rewards\n*Click reactions below to navigate*",
            color=discord.Color.gold()
        )
        
        # Add currency section
        embed.add_field(
            name="💰 Currency",
            value=f"**Gold:** 🪙 {player_data.get('gold', 0):,}",
            inline=False
        )
        
        # Add items section
        items = player_data.get("items", [])
        if not items:
            embed.add_field(
                name="📦 Items",
                value="You don't have any items yet. Complete quests to earn rewards!",
                inline=False
            )
        else:
            # Group items by type
            items_by_type = {}
            for item in items:
                item_type = item.get("type", "Miscellaneous")
                if item_type not in items_by_type:
                    items_by_type[item_type] = []
                items_by_type[item_type].append(item)
            
            # Display items by type
            for item_type, type_items in list(items_by_type.items())[:3]:
                item_list = "\n".join([f"• **{item['name']}** x{item.get('quantity', 1)}" for item in type_items[:5]])
                if len(type_items) > 5:
                    item_list += f"\n*...and {len(type_items) - 5} more {item_type}*"
                    
                embed.add_field(
                    name=f"📦 {item_type} ({len(type_items)})",
                    value=item_list,
                    inline=True
                )
        
        # Add navigation guide
        embed.add_field(
            name="📋 Navigation",
            value=(
                "👤 Profile\n"
                "🧙‍♂️ Class Info\n"
                "🎯 Skills\n"
                "🎒 Inventory"
            ),
            inline=False
        )
        
        return embed

async def setup(bot):
    await bot.add_cog(Quests(bot))