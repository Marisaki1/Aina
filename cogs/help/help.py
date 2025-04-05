import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        
    @commands.command()
    async def help(self, ctx, command=None):
        """Show help for commands"""
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
                "`!chat` - Talk with Aina\n"
                "`!endchat` - End your conversation with Aina"
            )
            embed.add_field(name="💬 Conversation Commands", value=chat_commands, inline=False)
            
            help_commands = "`!help [command]` - Show detailed help for a specific command"
            embed.add_field(name="❓ Help Commands", value=help_commands, inline=False)
            
            embed.set_footer(text="Type !help <command> for more info on a specific command.")
            await ctx.send(embed=embed)

        elif command.lower() == "setalarm":
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


            # Add these additional elif blocks to the help() command
        elif command.lower() == "alarm_images":
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

        elif command.lower() == "alarms":
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

        elif command.lower() == "removealarm":
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

        elif command.lower() == "editalarm":
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

        # Add similar blocks for other commands...

async def setup(bot):
    await bot.add_cog(Help(bot))