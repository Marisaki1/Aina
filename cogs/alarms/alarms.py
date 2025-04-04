import discord
from discord.ext import commands
from .alarm_core import AlarmManager
import re
import os
from datetime import datetime
import pytz

class Alarms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_manager = AlarmManager()
        self.timezone = pytz.timezone('Asia/Manila')
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

    @commands.command()
    async def setalarm(self, ctx, time=None, *, message=None):
        """Set an alarm! Example: !setalarm 10:30 Wake up!"""
        if not time or not message:
            await ctx.send("❌ Please provide both time and message. Example: `!setalarm 10:30 Wake up!`")
            return
            
        # Validate time format (HH:MM)
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time):
            await ctx.send("❌ Invalid time format. Please use 24-hour format (HH:MM). Example: `10:30` or `23:15`")
            return
            
        image_url = None
        # Check for attached images
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.content_type.startswith('image/'):
                    image_url = attachment.url
                    break
                    
        repeat = None
        # Check for repeat flag in message
        if "[daily]" in message.lower():
            repeat = "daily"
            message = message.replace("[daily]", "").strip()
        elif "[weekly]" in message.lower():
            repeat = "weekly"  
            message = message.replace("[weekly]", "").strip()
            
        self.alarm_manager.add_alarm(
            str(ctx.guild.id), 
            time, 
            message, 
            ctx.author.id, 
            image_url=image_url,
            repeat=repeat
        )
        
        # Create embed for confirmation
        embed = discord.Embed(
            title="⏰ Alarm Set",
            description=f"Your alarm has been set for **{time}**",
            color=discord.Color.green(),
            timestamp=datetime.now(self.timezone)
        )
        embed.add_field(name="Message", value=message, inline=False)
        embed.add_field(name="Timezone", value="Philippine Time (Asia/Manila)", inline=True)
        
        if repeat:
            embed.add_field(name="Repeats", value=repeat.capitalize(), inline=True)
            
        if image_url:
            embed.set_thumbnail(url=image_url)
            embed.add_field(name="Image", value="✅ Included", inline=True)
            
        embed.set_footer(text=f"Set by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def alarms(self, ctx):
        """List all active alarms"""
        alarms = self.alarm_manager.list_alarms(str(ctx.guild.id))
        if not alarms:
            await ctx.send("No alarms set.")
            return

        current_time = datetime.now(self.timezone).strftime("%H:%M")
        embed = discord.Embed(
            title="⏰ Active Alarms", 
            description=f"Current time: **{current_time}** (Philippine Time)",
            color=discord.Color.blue(),
            timestamp=datetime.now(self.timezone)
        )
        
        for i, alarm in enumerate(alarms):
            user = ctx.guild.get_member(int(alarm['user_id']))
            username = user.display_name if user else "Unknown User"
            
            repeat_text = f" [{alarm['repeat']}]" if alarm.get('repeat') else ""
            image_text = " 🖼️" if alarm.get('image_url') else ""
            
            value = f"{alarm['message']}{image_text} - <@{alarm['user_id']}>"
            embed.add_field(
                name=f"{i+1}. {alarm['time']}{repeat_text}", 
                value=value, 
                inline=False
            )

        embed.set_footer(text="Use !removealarm <number> to remove an alarm")
        await ctx.send(embed=embed)

    @commands.command()
    async def removealarm(self, ctx, index: int = None):
        """Remove an alarm by index"""
        if index is None:
            await ctx.send("❌ Please specify which alarm to remove by number. Use `!alarms` to see the list.")
            return
            
        if self.alarm_manager.remove_alarm(str(ctx.guild.id), index - 1):
            await ctx.send(f"🗑️ Alarm **#{index}** removed.")
        else:
            await ctx.send("❌ Invalid alarm number.")
            
    @commands.command()
    async def time(self, ctx):
        """Show current Philippine time"""
        current_time = datetime.now(self.timezone)
        formatted_time = current_time.strftime("%I:%M %p")
        formatted_date = current_time.strftime("%A, %B %d, %Y")
        
        embed = discord.Embed(
            title="🕒 Current Philippine Time",
            description=f"**{formatted_time}**\n{formatted_date}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Asia/Manila timezone")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Alarms(bot))