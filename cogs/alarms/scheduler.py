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
        
        # Use Philippine time zone
        self.timezone = pytz.timezone('Asia/Manila')
        print(f"✅ Alarm scheduler initialized with timezone: {self.timezone}")

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_alarms(self):
        # Get current time in Philippine timezone
        now = datetime.now(self.timezone).strftime("%H:%M")
        alarms = self.alarm_manager.load_alarms()
        
        for guild_id, alarm_list in list(alarms.items()):
            triggered_alarms = []
            
            for i, alarm in enumerate(alarm_list):
                if alarm["time"] == now:
                    triggered_alarms.append(i)
                    try:
                        guild = self.bot.get_guild(int(guild_id))
                        if guild:
                            user = guild.get_member(int(alarm["user_id"]))
                            if user:
                                channel = user.dm_channel or await user.create_dm()
                                
                                embed = discord.Embed(
                                    title="⏰ Alarm!", 
                                    description=alarm["message"], 
                                    color=discord.Color.green(),
                                    timestamp=datetime.now(self.timezone)
                                )
                                embed.set_footer(text="Philippine Time")
                                
                                if alarm["image_url"]:
                                    embed.set_image(url=alarm["image_url"])
                                
                                await channel.send(embed=embed)
                                print(f"✅ Alarm triggered for user {user.name} at {now}")
                                
                                # If channel is different from DM, also send to the general channel
                                general_channel = discord.utils.get(guild.text_channels, name="general")
                                if general_channel:
                                    embed.set_author(name=f"Alarm for {user.display_name}", icon_url=user.display_avatar.url)
                                    await general_channel.send(embed=embed)
                    except Exception as e:
                        print(f"❌ Error triggering alarm: {e}")
            
            # Handle repeat alarms
            for index in reversed(triggered_alarms):
                alarm = alarm_list[index]
                if alarm.get("repeat"):
                    # Keep this alarm for repeating
                    pass
                else:
                    # Remove one-time alarms after they trigger
                    alarms[guild_id].pop(index)
            
            self.alarm_manager.save_alarms(alarms)

    @check_alarms.before_loop
    async def before_check_alarms(self):
        await self.bot.wait_until_ready()
        print("🕒 Alarm checker is ready!")

async def setup(bot):
    await bot.add_cog(AlarmScheduler(bot))