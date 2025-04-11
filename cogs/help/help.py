import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        
    @commands.command()
    async def help(self, ctx, *args):
        """Show help for commands"""
        # Join all arguments to handle subcommands like "quests select"
        command = ' '.join(args).lower() if args else None
        
        if command is None:
            embed = discord.Embed(
                title="You need help? Kae then, Aina is here to help!",
                description="Here are the commands you can use to tell me what to do:",
                color=discord.Color.blue()
            )
            
            alarm_commands = (
                "`!setalarm` - Set an alarm with various options\n"
                "`!alarm_images` - Show available alarm images\n"
                "`!alarms` - List all active alarms\n"
                "`!editalarm` - Edit an existing alarm\n"
                "`!removealarm` - Remove an alarm\n"
                "`!time` - Show current Philippine time"
            )
            embed.add_field(name="⏰ Alarm Commands", value=alarm_commands, inline=False)
            
            chat_commands = (
                "`!chat` - Talk with Aina (disabled)\n"
                "`!endchat` - End your conversation with Aina (disabled)"
            )
            embed.add_field(name="💬 Conversation Commands", value=chat_commands, inline=False)

            quest_commands = (
                "`!quests create` - Create new quest\n"
                "`!quests list` - List available quests\n"
                "`!quests select <quest_name>` - View quest details\n"
                "`!quests start <quest_name> [p: @user1, @user2...]` - Start a quest with party\n"
                "`!quests action <message/attachment>` - Log quest progress\n"
                "`!quests complete` - Finish active quest\n"
                "`!quests cancel` - Cancel active quest\n"
                "`!quests inventory` - View your items\n"
                "`!quests player` - Interactive player profile with navigation\n"
                "`!quests records` - View quest history\n"
                "`!quests ongoing` - Show active quests\n"
                "`!quests new` - Create a new character class\n"
                "`!quests enable` - Enable random encounters (Admin)\n"
                "`!quests disable` - Disable random encounters (Admin)"
            )
            
            embed.add_field(name="⚔️ Quest System Commands", value=quest_commands, inline=False)

            class_commands = (
                "`!class` - View your character classes\n"
                "`!class info <class>` - View detailed class info\n"
                "`!class skills <class>` - View all skills for a class\n"
                "`!class appearance <class>` - Set class appearance\n"
                "`!class reset <class>` - Reset skill & ability distribution\n"
                "`!quests new` - Create a new character class"
            )
            embed.add_field(name="🧙‍♂️ Class Commands", value=class_commands, inline=False)
            
            help_commands = "`!help [command]` - Show detailed help for a specific command"
            embed.add_field(name="❓ Help Commands", value=help_commands, inline=False)
            
            embed.set_footer(text="Type !help <command> for more info on a specific command.")
            await ctx.send(embed=embed)

        elif command == "setalarm":
            embed = discord.Embed(
                title="!setalarm Command Help",
                description="Set an alarm with various parameters",
                color=discord.Color.green()
            )
            usage = (
                "**Format:** `!setalarm [f: frequency] [c: channels] [m: members] [i: image] <time> <message>`\n\n"
                "**Parameters:**\n"
                "- `f: frequency` - (once, daily, weekly) - Default: once\n"
                "- `c: channels` - (channel names separated by commas) - Default: current channel\n"
                "- `m: members` - (mentions or IDs separated by commas) - Default: command user\n"
                "- `i: image` - (filename from !alarm_images) - Default: random image\n"
                "- `time` - Required - Format: HH:MM (24-hour format)\n"
                "- `message` - Required - The alarm message"
            )
            examples = (
                "**Basic:** `!setalarm 08:30 Wake up!`\n"
                "**Daily alarm:** `!setalarm f: daily 07:00 Time to exercise!`\n"
                "**Multiple channels:** `!setalarm c: general,announcements 12:00 Lunch time!`\n"
                "**With mentions:** `!setalarm m: @User1,@User2 09:00 Standup meeting!`\n"
                "**With image:** `!setalarm i: sunrise.jpg 06:30 Good morning!`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            embed.add_field(name="Examples", value=examples, inline=False)
            await ctx.send(embed=embed)

        elif command == "alarm_images":
            embed = discord.Embed(
                title="!alarm_images Command Help",
                description=f"{ctx.author.mention} Can't you figure it out? It's already as simple as it can be! 😉",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Usage", 
                value="`!alarm_images` - Shows all available alarm images you can use with `!setalarm`",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="`!alarm_images` - Displays a list of images like Tama sleeping",
                inline=False
            )
            await ctx.send(embed=embed)

        elif command == "alarms":
            embed = discord.Embed(
                title="!alarms Command Help",
                description="Lists all active alarms in the server with their details",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usage", 
                value="`!alarms` - Shows all active alarms with their times, messages, and settings",
                inline=False
            )
            embed.add_field(
                name="What you'll see",
                value="• Alarm time\n• Repeat frequency\n• Target channels\n• Mentioned members\n• Associated image",
                inline=False
            )
            await ctx.send(embed=embed)

        elif command == "removealarm":
            embed = discord.Embed(
                title="!removealarm Command Help",
                description=f"{ctx.author.mention} Seriously? It's just `!removealarm [number]`! 😤",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage", 
                value="`!removealarm <number>` - Removes the specified alarm from the list",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="`!removealarm 2` - Deletes the second alarm shown in `!alarms` list",
                inline=False
            )
            await ctx.send(embed=embed)

        elif command == "editalarm":
            embed = discord.Embed(
                title="!editalarm Command Help",
                description="Edit an existing alarm's settings ⚙️",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Format", 
                value="`!editalarm <number> [f: frequency] [c: channels] [m: members] [i: image] [t: time] [msg: message]",
                inline=False
            )
            embed.add_field(
                name="Parameters",
                value=(
                    "• `number` - Alarm number from `!alarms` list\n"
                    "• `f:` - New frequency (once/daily/weekly)\n"
                    "• `c:` - New channels (comma-separated)\n"
                    "• `m:` - New members to notify\n"
                    "• `i:` - New image filename\n"
                    "• `t:` - New time (HH:MM)\n"
                    "• `msg:` - New message content"
                ),
                inline=False
            )
            embed.add_field(
                name="Example 1",
                value="`!editalarm 1 f: weekly msg: Updated meeting time!`\nChanges first alarm to weekly repeat with new message",
                inline=False
            )
            embed.add_field(
                name="Example 2",
                value="`!editalarm 3 t: 15:30 c: general`\nUpdates third alarm to 3:30PM in #general",
                inline=False
            )
            await ctx.send(embed=embed)

        # Quest commands help
        elif command == "quests":
            embed = discord.Embed(
                title="!quests Commands Help",
                description="Adventure awaits! Here's how to use the quest system ⚔️",
                color=discord.Color.purple()
            )
            
            basic_commands = (
                "`!quests list` - View all available quests\n"
                "`!quests select <name>` - See details about a specific quest\n"
                "`!quests start <name> [p: @user1, @user2...]` - Begin a quest with friends\n"
                "`!quests action <message/attachment>` - Log your quest progress\n"
                "`!quests complete` - Finish your active quest\n"
                "`!quests cancel` - Cancel the current quest"
            )
            embed.add_field(name="🗺️ Basic Quest Commands", value=basic_commands, inline=False)
            
            status_commands = (
                "`!quests profile` - See your adventure stats\n"
                "`!quests inventory` - Check your collected items\n"
                "`!quests records` - View your quest history\n"
                "`!quests ongoing` - See all active quests"
            )
            embed.add_field(name="📊 Status Commands", value=status_commands, inline=False)
            
            admin_commands = (
                "`!quests create` - Create a new quest\n"
                "`!quests enable` - Enable random encounters\n"
                "`!quests disable` - Disable random encounters"
            )
            embed.add_field(name="⚙️ Admin Commands", value=admin_commands, inline=False)
            
            embed.set_footer(text="Type !help quests <subcommand> for details on specific quest commands")
            await ctx.send(embed=embed)

        elif command == "quests select":
            embed = discord.Embed(
                title="!quests select Command Help",
                description="View detailed information about a specific quest",
                color=discord.Color.green()
            )
            usage = (
                "**Format:** `!quests select <quest_name>`\n\n"
                "**Parameters:**\n"
                "- `quest_name` - Name of the quest from `!quests list`\n\n"
                "**Example:** `!quests select Dragon Slayer`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)
            
        elif command == "quests list":
            embed = discord.Embed(
                title="!quests list Command Help",
                description="Browse available quests in the adventure board",
                color=discord.Color.gold()
            )
            usage = (
                "**Format:** `!quests list [difficulty]`\n\n"
                "**Optional filters:**\n"
                "- `easy` - Show only easy quests\n"
                "- `medium` - Show only medium difficulty quests\n"
                "- `hard` - Show only challenging quests\n\n"
                "**Examples:**\n"
                "`!quests list` - Show all quests\n"
                "`!quests list hard` - Show only hard quests"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests start":
            embed = discord.Embed(
                title="!quests start Command Help",
                description="Begin an adventure with your party!",
                color=discord.Color.green()
            )
            usage = (
                "**Format:** `!quests start <quest_name> [p: @user1, @user2...]`\n\n"
                "**Parameters:**\n"
                "- `quest_name` - Name of the quest from `!quests list`\n"
                "- `p:` - Optional party members to invite\n\n"
                "**Examples:**\n"
                "`!quests start Forest Exploration`\n"
                "`!quests start Dragon Hunt p: @Knight, @Mage, @Healer`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests action":
            embed = discord.Embed(
                title="!quests action Command Help",
                description="Log your progress during an active quest",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!quests action <message>` or attach image/file\n\n"
                "**Notes:**\n"
                "- Use this to describe what you're doing\n"
                "- Attach images of your progress\n"
                "- May trigger random encounters or rewards\n\n"
                "**Examples:**\n"
                "`!quests action I found the hidden path in the forest!`\n"
                "`!quests action` + screenshot attachment"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests complete":
            embed = discord.Embed(
                title="!quests complete Command Help",
                description="Finish your active quest and claim rewards",
                color=discord.Color.green()
            )
            usage = (
                "**Format:** `!quests complete [summary]`\n\n"
                "**Parameters:**\n"
                "- `summary` - Optional description of your accomplishments\n\n"
                "**Notes:**\n"
                "- Only quest leader can complete the quest\n"
                "- Must have completed objectives\n\n"
                "**Example:** `!quests complete We defeated the dragon after a fierce battle!`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests cancel":
            embed = discord.Embed(
                title="!quests cancel Command Help",
                description="Cancel your active quest",
                color=discord.Color.red()
            )
            usage = (
                "**Format:** `!quests cancel`\n\n"
                "**Notes:**\n"
                "- Only quest leader or admins can cancel\n"
                "- Cancelled quests appear in history\n\n"
                "**Example:** `!quests cancel`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests inventory":
            embed = discord.Embed(
                title="!quests inventory Command Help",
                description="View your collected items and treasures",
                color=discord.Color.gold()
            )
            usage = (
                "**Format:** `!quests inventory [category]`\n\n"
                "**Categories:**\n"
                "- `equipment` - Show only gear\n"
                "- `consumables` - Show only usable items\n" 
                "- `treasures` - Show only valuable items\n\n"
                "**Examples:**\n"
                "`!quests inventory` - Show all items\n"
                "`!quests inventory equipment` - Show only your gear"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests profile" or command == "quests player" or command == "quests info" or command == "quests me":
            embed = discord.Embed(
                title="!quests player Command Help",
                description="View your adventurer profile with interactive navigation",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!quests player [@user]` or `!quests profile` or `!quests me`\n\n"
                "**Parameters:**\n"
                "- `@user` - Optional user to view (defaults to you)\n\n"
                "**Features:**\n"
                "- When viewing your own profile, you get interactive navigation buttons\n"
                "- Use reactions to switch between Profile, Class Info, Skills, and Inventory\n"
                "- When viewing another user's profile, you see a static view\n\n"
                "**Examples:**\n"
                "`!quests player` - View your interactive profile\n"
                "`!quests player @Hero` - View Hero's profile (static)"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests records":
            embed = discord.Embed(
                title="!quests records Command Help",
                description="View your quest history with filters",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!quests records [filter]`\n\n"
                "**Filters:**\n"
                "- `completed` - Show completed quests\n"
                "- `failed` - Show failed/cancelled quests\n"
                "- `select <name>` - View specific quest details\n\n"
                "**Examples:**\n"
                "`!quests records failed`\n"
                "`!quests records select Ancient Ruins`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests ongoing":
            embed = discord.Embed(
                title="!quests ongoing Command Help",
                description="List all active quests in progress",
                color=discord.Color.gold()
            )
            usage = (
                "**Format:** `!quests ongoing`\n\n"
                "Shows:\n"
                "- Quest names\n"
                "- Leaders\n"
                "- Remaining time\n\n"
                "**Example:** `!quests ongoing`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests create":
            embed = discord.Embed(
                title="!quests create Command Help",
                description="Create a new quest (Admin only)",
                color=discord.Color.purple()
            )
            usage = (
                "**Format:** `!quests create`\n\n"
                "**Notes:**\n"
                "- Starts an interactive quest creation wizard\n"
                "- Requires admin permissions\n"
                "- You'll be asked for name, description, objectives, etc.\n\n"
                "**Example:** `!quests create`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests enable":
            embed = discord.Embed(
                title="!quests enable Command Help",
                description="Enable random encounters (Admin only)",
                color=discord.Color.green()
            )
            usage = (
                "**Format:** `!quests enable`\n\n"
                "**Requirements:**\n"
                "- Manage Channels permission\n"
                "- Must be used in target channel\n\n"
                "**Example:** `!quests enable`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "quests disable":
            embed = discord.Embed(
                title="!quests disable Command Help",
                description="Disable random encounters in this channel (Admin only)",
                color=discord.Color.red()
            )
            usage = (
                "**Format:** `!quests disable`\n\n"
                "**Requirements:**\n"
                "- Manage Channels permission\n"
                "- Must be used in target channel\n\n"
                "**Example:** `!quests disable`"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)
            
        elif command == "quests new" or command == "new":
            embed = discord.Embed(
                title="!quests new Command Help",
                description="Create a new character class",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!quests new`\n\n"
                "This command starts the class selection process, allowing you to choose from 13 different character classes. Each class has unique abilities and skills.\n\n"
                "After selecting a class, you can customize it with:\n"
                "- `!class appearance <class>` - Set your character's appearance\n"
                "- `!class info <class>` - View detailed info about your class\n"
                "- `!class reset <class>` - Reset your skills and abilities (costs gold)"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)
            
        elif command == "class":
            embed = discord.Embed(
                title="!class Command Help",
                description="View and manage your character classes",
                color=discord.Color.blue()
            )
            subcommands = (
                "**Basic Command:**\n"
                "`!class` - View all your character classes\n\n"
                "**Subcommands:**\n"
                "`!class info [class]` - View detailed information about a specific class\n"
                "`!class appearance <class>` - Set or change your class appearance with an image\n"
                "`!class reset <class>` - Reset skill and ability distribution (costs gold)"
            )
            embed.add_field(name="Commands", value=subcommands, inline=False)
            
            examples = (
                "`!class` - See a summary of all your classes\n"
                "`!class info Fighter` - View detailed info about your Fighter class\n"
                "`!class appearance Wizard` - Upload an image for your Wizard\n"
                "`!class reset Rogue` - Reset your Rogue's skills and abilities"
            )
            embed.add_field(name="Examples", value=examples, inline=False)
            await ctx.send(embed=embed)

        elif command == "class skills":
            embed = discord.Embed(
                title="!class skills Command Help",
                description="View all skills for your character class",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!class skills [class_name]`\n\n"
                "**Parameters:**\n"
                "- `class_name` - Optional class to view (defaults to your first class)\n\n"
                "**Shows:**\n"
                "- All skills organized by ability type (STR, DEX, INT, WIS, CHA)\n"
                "- Skill points and total bonuses for each skill\n"
                "- Trained skills are highlighted in bold\n\n"
                "**Examples:**\n"
                "`!class skills` - View skills for your first/only class\n"
                "`!class skills Wizard` - View skills for your Wizard class"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "class increase":
            embed = discord.Embed(
                title="!class increase Command Help",
                description="Add points to your abilities or skills",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!class increase <type> [class_name]`\n\n"
                "**Types:**\n"
                "- `ability` - Increase ability scores (STR, DEX, CON, INT, WIS, CHA)\n"
                "- `skill` - Increase skill proficiencies\n\n"
                "**Parameters:**\n"
                "- `class_name` - Optional class to improve (defaults to your first class)\n\n"
                "**Notes:**\n"
                "- Ability points are gained every 4 levels\n"
                "- Skill points are gained every level (based on INT)\n"
                "- Uses interactive emoji reactions to allocate points\n\n"
                "**Examples:**\n"
                "`!class increase ability` - Add points to ability scores\n"
                "`!class increase skill Wizard` - Add points to Wizard skills"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "class increase ability":
            embed = discord.Embed(
                title="!class increase ability Command Help",
                description="🏆 Add points to your character's ability scores",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!class increase ability [class_name]`\n\n"
                "**How it works:**\n"
                "- Interactive interface with emoji reactions\n"
                "- Each character gets 1 ability point every 4 levels\n"
                "- Abilities can be increased to a maximum of 20\n"
                "- Higher ability scores improve related skills\n\n"
                "**Abilities:**\n"
                "💪 **Strength**: Physical power and melee attacks\n"
                "🏃 **Dexterity**: Agility, reflexes, and stealth\n"
                "❤️ **Constitution**: Health and stamina (affects HP)\n"
                "🧠 **Intelligence**: Knowledge and reasoning (affects MP)\n"
                "🦉 **Wisdom**: Perception and insight (affects MP)\n"
                "✨ **Charisma**: Social influence and magic (affects MP)\n\n"
                "**Examples:**\n"
                "`!class increase ability` - Add points to your first class\n"
                "`!class increase ability Rogue` - Improve your Rogue's abilities"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

        elif command == "class increase skill":
            embed = discord.Embed(
                title="!class increase skill Command Help",
                description="🎯 Add points to your character's skills",
                color=discord.Color.blue()
            )
            usage = (
                "**Format:** `!class increase skill [class_name]`\n\n"
                "**How it works:**\n"
                "- Interactive interface with emoji reactions\n"
                "- Characters get skill points each level (1 + INT modifier)\n"
                "- Skills are linked to ability scores (shown in parentheses)\n"
                "- Higher skill points improve your chance at success\n\n"
                "**Skills are organized in pages:**\n"
                "- Use number reactions to increase a skill\n"
                "- Navigate between pages with ⬅️ and ➡️\n"
                "- Cancel anytime with ❌\n\n"
                "**Examples:**\n"
                "`!class increase skill` - Add points to your first class's skills\n"
                "`!class increase skill Wizard` - Improve your Wizard's skills"
            )
            embed.add_field(name="Usage", value=usage, inline=False)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))