import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta
import pytz
from .alarm_core import AlarmManager
import os

class AlarmScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_manager = AlarmManager()
        self.check_alarms.start()
        
        # Use Philippine time zone
        self.timezone = pytz.timezone('Asia/Manila')
        self.alarm_images_dir = "assets/images/alarms"
        print(f"✅ Alarm scheduler initialized with timezone: {self.timezone}")

    @tasks.loop(seconds=60)  # Runs every minute
    async def check_alarms(self):
        # Get current time in Philippine timezone
        now = datetime.now(self.timezone)
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A").lower()
        
        alarms = self.alarm_manager.load_alarms()
        
        for guild_id, alarm_list in list(alarms.items()):
            triggered_alarms = []
            
            for i, alarm in enumerate(alarm_list):
                # Skip if time doesn't match
                if alarm.get("time") != current_time:
                    continue
                    
                # For weekly alarms, check if it's the right day
                if alarm.get("repeat") == "weekly":
                    # For now, we'll trigger weekly alarms on the current day
                    # In a future update, you might want to add a specific day selection
                    pass
                
                triggered_alarms.append(i)
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                        
                    # Get channels to notify
                    channels_to_notify = []
                    channel_names = alarm.get("channels", [])
                    for channel_name in channel_names:
                        channel = discord.utils.get(guild.text_channels, name=channel_name)
                        if channel:
                            channels_to_notify.append(channel)
                            
                    # If no valid channels, skip this alarm
                    if not channels_to_notify:
                        continue
                    
                    # Create embed for the alarm
                    embed = discord.Embed(
                        title="⏰ Alarm!",
                        description=alarm.get("message", "Alarm triggered!"), 
                        color=discord.Color.green(),
                        timestamp=datetime.now(self.timezone)
                    )
                    
                    # Add image if specified
                    image_file = None
                    image_name = alarm.get("image")
                    if image_name:
                        image_path = os.path.join(self.alarm_images_dir, image_name)
                        if os.path.exists(image_path):
                            image_file = discord.File(image_path, filename=image_name)
                            embed.set_image(url=f"attachment://{image_name}")
                    
                    # Get members to mention
                    members_to_ping = []
                    member_ids = alarm.get("members", [])
                    for member_id in member_ids:
                        member = guild.get_member(int(member_id))
                        if member:
                            members_to_ping.append(member.mention)
                    
                    # Add mentions to the message if any
                    mentions = " ".join(members_to_ping)
                    
                    # Send to each channel
                    for channel in channels_to_notify:
                        try:
                            if image_file:
                                # Need to create a new file object for each send
                                new_file = discord.File(os.path.join(self.alarm_images_dir, image_name), filename=image_name)
                                await channel.send(content=mentions if mentions else None, embed=embed, file=new_file)
                            else:
                                await channel.send(content=mentions if mentions else None, embed=embed)
                        except Exception as e:
                            print(f"❌ Error sending alarm to channel {channel.name}: {e}")
                    
                    # Also DM each member individually
                    for member_id in member_ids:
                        try:
                            member = guild.get_member(int(member_id))
                            if member:
                                dm_channel = member.dm_channel or await member.create_dm()
                                if image_file:
                                    # Need to create a new file object for each send
                                    new_file = discord.File(os.path.join(self.alarm_images_dir, image_name), filename=image_name)
                                    await dm_channel.send(embed=embed, file=new_file)
                                else:
                                    await dm_channel.send(embed=embed)
                        except Exception as e:
                            print(f"❌ Error sending DM to user {member_id}: {e}")
                    
                    print(f"✅ Alarm triggered for guild {guild.name} at {current_time}")
                    
                except Exception as e:
                    print(f"❌ Error triggering alarm: {e}")
            
            # Remove one-time alarms after they trigger
            for index in reversed(triggered_alarms):
                alarm = alarm_list[index]
                if alarm.get("repeat", "once") == "once":
                    alarms[guild_id].pop(index)
            
            self.alarm_manager.save_alarms(alarms)

    @check_alarms.before_loop
    async def before_check_alarms(self):
        await self.bot.wait_until_ready()
        print("🕒 Alarm checker is ready!")

async def setup(bot):
    await bot.add_cog(AlarmScheduler(bot))