import discord
from discord.ext import commands
from .alarm_core import AlarmManager

class Alarms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_manager = AlarmManager()

    @commands.command()
    async def setalarm(self, ctx, time, *, message):
        """Set an alarm! Example: !setalarm 10:30 Wake up!"""
        self.alarm_manager.add_alarm(str(ctx.guild.id), time, message, ctx.author.id)
        await ctx.send(f"✅ Alarm set for **{time}** with message: `{message}`")

    @commands.command()
    async def alarms(self, ctx):
        """List all active alarms"""
        alarms = self.alarm_manager.list_alarms(str(ctx.guild.id))
        if not alarms:
            await ctx.send("No alarms set.")
            return

        embed = discord.Embed(title="⏰ Active Alarms", color=discord.Color.blue())
        for i, alarm in enumerate(alarms):
            embed.add_field(name=f"{i+1}. {alarm['time']}", value=f"{alarm['message']} - <@{alarm['user_id']}>", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def removealarm(self, ctx, index: int):
        """Remove an alarm by index"""
        if self.alarm_manager.remove_alarm(str(ctx.guild.id), index - 1):
            await ctx.send(f"🗑️ Alarm **#{index}** removed.")
        else:
            await ctx.send("❌ Invalid alarm number.")

async def setup(bot):
    await bot.add_cog(Alarms(bot))
