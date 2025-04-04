import discord
from discord.ext import tasks, commands
from datetime import datetime
import pytz
from .alarm_core import AlarmManager

class AlarmScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_manager = AlarmManager()
        self.check_alarms.start()

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_alarms(self):
        now = datetime.now(pytz.utc).strftime("%H:%M")
        alarms = self.alarm_manager.load_alarms()

        for guild_id, alarm_list in alarms.items():
            for alarm in alarm_list:
                if alarm["time"] == now:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        user = guild.get_member(alarm["user_id"])
                        channel = user.dm_channel or await user.create_dm()

                        embed = discord.Embed(title="⏰ Alarm!", description=alarm["message"], color=discord.Color.green())
                        if alarm["image_url"]:
                            embed.set_image(url=alarm["image_url"])

                        await channel.send(embed=embed)

    @check_alarms.before_loop
    async def before_check_alarms(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AlarmScheduler(bot))
