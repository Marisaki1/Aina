import discord
from discord.ext import commands
from .alarm_core import AlarmManager
import re
import os
from datetime import datetime
import pytz
import random

class Alarms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_manager = AlarmManager()
        self.timezone = pytz.timezone('Asia/Manila')
        self.alarm_images_dir = "assets/images/alarms"
        
        # Ensure data directory and images directory exist
        os.makedirs("data", exist_ok=True)
        os.makedirs(self.alarm_images_dir, exist_ok=True)

    @commands.command()
    async def setalarm(self, ctx, *, args=None):
        """Set an alarm with various parameters
        
        Format: !setalarm [f: frequency] [c: channels] [m: members] [i: image] <time> <message>
        
        Parameters:
        - f: frequency (once, daily, weekly) - Default: once
        - c: channels (channel names separated by commas) - Default: current channel
        - m: members (mentions or IDs separated by commas) - Default: command user
        - i: image (filename from !alarm images) - Default: random from available images
        - time: Required - Format: HH:MM (24-hour format)
        - message: Required - The alarm message
        
        Example: !setalarm f: daily c: general m: @user1,@user2 i: sunrise.jpg 08:30 Wake up everyone!
        """
        if not args:
            await ctx.send("❌ Please provide at least time and message. Use `!help setalarm` for detailed usage.")
            return
            
        # Initialize default values
        frequency = "once"
        channels = [ctx.channel.name]
        members = [ctx.author.id]
        image = self._get_random_image()
        time_match = None
        message = ""
        
        # Extract parameters with their identifiers
        frequency_match = re.search(r'f:\s*(\w+)', args)
        if frequency_match:
            freq = frequency_match.group(1).lower()
            if freq in ["once", "daily", "weekly"]:
                frequency = freq
            args = args.replace(frequency_match.group(0), "").strip()
        
        channels_match = re.search(r'c:\s*([^f:m:i:0-9]+)', args)
        if channels_match:
            channel_str = channels_match.group(1).strip()
            channels = [c.strip() for c in channel_str.split(",")]
            args = args.replace(channels_match.group(0), "").strip()
        
        members_match = re.search(r'm:\s*([^f:c:i:0-9]+)', args)
        if members_match:
            members_str = members_match.group(1).strip()
            # Handle member mentions or IDs
            members = []
            for member_ref in members_str.split(","):
                member_ref = member_ref.strip()
                if member_ref.startswith("<@") and member_ref.endswith(">"):
                    # Extract ID from mention
                    member_id = int(member_ref[2:-1].replace("!", ""))
                    members.append(member_id)
                else:
                    # Try to find member by name
                    member = discord.utils.get(ctx.guild.members, name=member_ref)
                    if member:
                        members.append(member.id)
            
            # If no valid members found, default to command author
            if not members:
                members = [ctx.author.id]
                
            args = args.replace(members_match.group(0), "").strip()
        
        image_match = re.search(r'i:\s*([^\s]+)', args)
        if image_match:
            img_name = image_match.group(1).strip()
            if self._image_exists(img_name):
                image = img_name
            args = args.replace(image_match.group(0), "").strip()
        
        # Time must be in format HH:MM (24-hour format)
        time_match = re.search(r'([01]\d|2[0-3]):([0-5]\d)', args)
        if not time_match:
            await ctx.send("❌ Invalid or missing time. Please use 24-hour format (HH:MM).")
            return
            
        time_str = time_match.group(0)
        args = args.replace(time_str, "", 1).strip()
        
        # Remaining text is the message
        message = args.strip()
        if not message:
            await ctx.send("❌ Missing alarm message. Please provide a message for your alarm.")
            return
        
        # Validate channels exist
        valid_channels = []
        for channel_name in channels:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
            if channel:
                valid_channels.append(channel.name)
        
        if not valid_channels:
            valid_channels = [ctx.channel.name]
        
        # Add the alarm
        image_path = os.path.join(self.alarm_images_dir, image) if image else None
        image_url = f"file://{image_path}" if image_path else None
        
        alarm_data = {
            "time": time_str,
            "message": message,
            "user_id": ctx.author.id,
            "image": image,
            "repeat": frequency,
            "channels": valid_channels,
            "members": members
        }
        
        self.alarm_manager.add_alarm(str(ctx.guild.id), alarm_data)
        
        # Create embed for confirmation
        embed = discord.Embed(
            title="⏰ Alarm Set",
            description=f"Your alarm has been set for **{time_str}**",
            color=discord.Color.green(),
            timestamp=datetime.now(self.timezone)
        )
        embed.add_field(name="Message", value=message, inline=False)
        embed.add_field(name="Frequency", value=frequency.capitalize(), inline=True)
        embed.add_field(name="Timezone", value="Philippine Time (Asia/Manila)", inline=True)
        
        # Add channels info
        channels_str = ", ".join([f"#{c}" for c in valid_channels])
        embed.add_field(name="Channels", value=channels_str, inline=True)
        
        # Add members info
        members_str = ", ".join([f"<@{m}>" for m in members])
        embed.add_field(name="Notify", value=members_str, inline=True)
        
        if image:
            embed.add_field(name="Image", value=image, inline=True)
            # If file exists locally, add it as thumbnail
            if image_path and os.path.exists(image_path):
                file = discord.File(image_path, filename=image)
                embed.set_thumbnail(url=f"attachment://{image}")
                await ctx.send(embed=embed, file=file)
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command(name="alarm_images", aliases=["alarmimages"])
    async def alarm_images(self, ctx):
        """List all available alarm images"""
        if not os.path.exists(self.alarm_images_dir):
            await ctx.send("❌ No alarm images directory found.")
            return
            
        images = [f for f in os.listdir(self.alarm_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        
        if not images:
            await ctx.send("No alarm images found. Upload images to the `assets/images/alarms` directory.")
            return
            
        embed = discord.Embed(
            title="🖼️ Available Alarm Images",
            description=f"Use image name with `i:` parameter in `!setalarm` command.\nExample: `!setalarm i: {images[0]} 08:30 Wake up!`",
            color=discord.Color.blue()
        )
        
        # Group images in sets of 10 for fields
        for i in range(0, len(images), 10):
            group = images[i:i+10]
            embed.add_field(
                name=f"Images {i+1}-{i+len(group)}",
                value="\n".join([f"• {img}" for img in group]),
                inline=False
            )
        
        # Add sample of random images as thumbnails if available
        if images:
            sample_image = random.choice(images)
            file = discord.File(os.path.join(self.alarm_images_dir, sample_image), filename=sample_image)
            embed.set_thumbnail(url=f"attachment://{sample_image}")
            await ctx.send(embed=embed, file=file)
        else:
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
            # Get username for creator
            user = ctx.guild.get_member(int(alarm.get('user_id', 0)))
            username = user.display_name if user else "Unknown User"
            
            # Format details
            frequency = alarm.get('repeat', 'once').capitalize()
            channels = ", ".join([f"#{c}" for c in alarm.get('channels', [])])
            members = ", ".join([f"<@{m}>" for m in alarm.get('members', [])])
            image = alarm.get('image', 'None')
            time_str = alarm.get('time', '00:00')
            message = alarm.get('message', '')
            
            # Create field for each alarm
            embed.add_field(
                name=f"{i+1}. {time_str} ({frequency})", 
                value=f"**Message:** {message}\n**Channels:** {channels}\n**Notify:** {members}\n**Image:** {image}\n**Created by:** {username}", 
                inline=False
            )

        embed.set_footer(text="Use !editalarm <number> or !removealarm <number> to modify alarms")
        await ctx.send(embed=embed)

    @commands.command()
    async def editalarm(self, ctx, index: int = None, *, args=None):
        """Edit an existing alarm
        
        Format: !editalarm <number> [f: frequency] [c: channels] [m: members] [i: image] [t: time] [msg: message]
        
        Parameters:
        - number: Required - The alarm number from !alarms list
        - f: frequency (once, daily, weekly)
        - c: channels (channel names separated by commas)
        - m: members (mentions or IDs separated by commas)
        - i: image (filename from !alarm images)
        - t: time (Format: HH:MM, 24-hour format)
        - msg: message (New alarm message)
        
        Example: !editalarm 1 f: weekly msg: This is the updated message
        """
        if index is None:
            await ctx.send("❌ Please specify which alarm to edit by number. Use `!alarms` to see the list.")
            return
            
        if args is None:
            await ctx.send("❌ Please specify what to edit. Use `!help editalarm` for detailed usage.")
            return
            
        # Get the alarm to edit
        alarms = self.alarm_manager.list_alarms(str(ctx.guild.id))
        if not alarms or index <= 0 or index > len(alarms):
            await ctx.send("❌ Invalid alarm number.")
            return
            
        alarm = alarms[index - 1]  # Convert to 0-based index
        
        # Extract parameters with their identifiers
        frequency_match = re.search(r'f:\s*(\w+)', args)
        if frequency_match:
            freq = frequency_match.group(1).lower()
            if freq in ["once", "daily", "weekly"]:
                alarm["repeat"] = freq
        
        channels_match = re.search(r'c:\s*([^f:m:i:t:msg:0-9]+)', args)
        if channels_match:
            channel_str = channels_match.group(1).strip()
            channels = [c.strip() for c in channel_str.split(",")]
            # Validate channels exist
            valid_channels = []
            for channel_name in channels:
                channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
                if channel:
                    valid_channels.append(channel.name)
            
            if valid_channels:
                alarm["channels"] = valid_channels
        
        members_match = re.search(r'm:\s*([^f:c:i:t:msg:0-9]+)', args)
        if members_match:
            members_str = members_match.group(1).strip()
            # Handle member mentions or IDs
            members = []
            for member_ref in members_str.split(","):
                member_ref = member_ref.strip()
                if member_ref.startswith("<@") and member_ref.endswith(">"):
                    # Extract ID from mention
                    member_id = int(member_ref[2:-1].replace("!", ""))
                    members.append(member_id)
                else:
                    # Try to find member by name
                    member = discord.utils.get(ctx.guild.members, name=member_ref)
                    if member:
                        members.append(member.id)
            
            # Only update if valid members found
            if members:
                alarm["members"] = members
        
        image_match = re.search(r'i:\s*([^\s]+)', args)
        if image_match:
            img_name = image_match.group(1).strip()
            if self._image_exists(img_name):
                alarm["image"] = img_name
        
        time_match = re.search(r't:\s*([01]\d|2[0-3]):([0-5]\d)', args)
        if time_match:
            alarm["time"] = time_match.group(0).replace("t:", "").strip()
        
        message_match = re.search(r'msg:\s*(.+)$', args)
        if message_match:
            alarm["message"] = message_match.group(1).strip()
        
        # Update the alarm
        self.alarm_manager.update_alarm(str(ctx.guild.id), index - 1, alarm)
        
        # Confirm the update
        embed = discord.Embed(
            title="✅ Alarm Updated",
            description=f"Alarm #{index} has been updated.",
            color=discord.Color.green(),
            timestamp=datetime.now(self.timezone)
        )
        
        # Display updated alarm details
        frequency = alarm.get('repeat', 'once').capitalize()
        channels = ", ".join([f"#{c}" for c in alarm.get('channels', [])])
        members = ", ".join([f"<@{m}>" for m in alarm.get('members', [])])
        image = alarm.get('image', 'None')
        time_str = alarm.get('time', '00:00')
        message = alarm.get('message', '')
        
        embed.add_field(name="Time", value=time_str, inline=True)
        embed.add_field(name="Frequency", value=frequency, inline=True)
        embed.add_field(name="Message", value=message, inline=False)
        embed.add_field(name="Channels", value=channels, inline=True)
        embed.add_field(name="Notify", value=members, inline=True)
        embed.add_field(name="Image", value=image, inline=True)
        
        # Add image if available
        if image and self._image_exists(image):
            image_path = os.path.join(self.alarm_images_dir, image)
            file = discord.File(image_path, filename=image)
            embed.set_thumbnail(url=f"attachment://{image}")
            await ctx.send(embed=embed, file=file)
        else:
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
        
    def _get_random_image(self):
        """Get a random image from the alarms image directory"""
        if not os.path.exists(self.alarm_images_dir):
            return None
            
        images = [f for f in os.listdir(self.alarm_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        return random.choice(images) if images else None
        
    def _image_exists(self, image_name):
        """Check if an image exists in the alarms image directory"""
        if not image_name or not os.path.exists(self.alarm_images_dir):
            return False
            
        return os.path.exists(os.path.join(self.alarm_images_dir, image_name))

async def setup(bot):
    await bot.add_cog(Alarms(bot))