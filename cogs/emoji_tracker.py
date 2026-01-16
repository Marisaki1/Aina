import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import re
from typing import Dict, List, Optional

class EmojiTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data/emoji_tracking"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_server_data_file(self, guild_id: int) -> str:
        """Get the data file path for a specific server"""
        return os.path.join(self.data_dir, f"{guild_id}.json")
    
    def load_server_data(self, guild_id: int) -> Dict:
        """Load emoji/sticker data for a specific server"""
        file_path = self.get_server_data_file(guild_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "emojis": {},
            "stickers": {},
            "server_name": "",
            "last_updated": datetime.now().isoformat()
        }
    
    def save_server_data(self, guild_id: int, data: Dict) -> None:
        """Save emoji/sticker data for a specific server"""
        data["last_updated"] = datetime.now().isoformat()
        file_path = self.get_server_data_file(guild_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def extract_custom_emojis(self, content: str) -> List[str]:
        """Extract custom emoji IDs from message content"""
        # Pattern for custom emojis: <:name:id> or <a:name:id>
        pattern = r'<a?:(\w+):(\d+)>'
        matches = re.findall(pattern, content)
        return [match[1] for match in matches]  # Return emoji IDs
    
    def update_emoji_usage(self, guild_id: int, emoji_id: str, emoji_name: str) -> None:
        """Update usage statistics for an emoji"""
        data = self.load_server_data(guild_id)
        
        if emoji_id not in data["emojis"]:
            data["emojis"][emoji_id] = {
                "name": emoji_name,
                "count": 0,
                "first_used": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
        
        data["emojis"][emoji_id]["count"] += 1
        data["emojis"][emoji_id]["last_used"] = datetime.now().isoformat()
        data["emojis"][emoji_id]["name"] = emoji_name  # Update name in case it changed
        
        self.save_server_data(guild_id, data)
    
    def update_sticker_usage(self, guild_id: int, sticker_id: int, sticker_name: str) -> None:
        """Update usage statistics for a sticker"""
        data = self.load_server_data(guild_id)
        sticker_id_str = str(sticker_id)
        
        if sticker_id_str not in data["stickers"]:
            data["stickers"][sticker_id_str] = {
                "name": sticker_name,
                "count": 0,
                "first_used": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat()
            }
        
        data["stickers"][sticker_id_str]["count"] += 1
        data["stickers"][sticker_id_str]["last_used"] = datetime.now().isoformat()
        data["stickers"][sticker_id_str]["name"] = sticker_name  # Update name in case it changed
        
        self.save_server_data(guild_id, data)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track emoji and sticker usage in messages"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id
        
        # Track custom emojis in message content
        emoji_ids = self.extract_custom_emojis(message.content)
        for emoji_id in emoji_ids:
            # Find the actual emoji object to get its name
            emoji = discord.utils.get(message.guild.emojis, id=int(emoji_id))
            if emoji:  # Only track emojis from this server
                self.update_emoji_usage(guild_id, emoji_id, emoji.name)
        
        # Track stickers
        if message.stickers:
            for sticker in message.stickers:
                # Only track server stickers (guild stickers)
                if hasattr(sticker, 'guild_id') and sticker.guild_id == guild_id:
                    self.update_sticker_usage(guild_id, sticker.id, sticker.name)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Track emoji usage in reactions"""
        if user.bot or not reaction.message.guild:
            return
        
        guild_id = reaction.message.guild.id
        
        # Check if it's a custom emoji from this server
        if hasattr(reaction.emoji, 'id'):
            emoji = discord.utils.get(reaction.message.guild.emojis, id=reaction.emoji.id)
            if emoji:  # Only track emojis from this server
                self.update_emoji_usage(guild_id, str(emoji.id), emoji.name)

    @commands.command(name="emojistats", aliases=["es"])
    async def emoji_stats(self, ctx, limit: int = 10):
        """Show emoji usage statistics for this server"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        data = self.load_server_data(ctx.guild.id)
        
        if not data["emojis"]:
            await ctx.send("📊 No emoji usage data found for this server yet!")
            return
        
        # Sort emojis by usage count
        sorted_emojis = sorted(
            data["emojis"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        embed = discord.Embed(
            title=f"📊 Emoji Usage Statistics - {ctx.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        description = ""
        for i, (emoji_id, emoji_data) in enumerate(sorted_emojis[:limit]):
            emoji = discord.utils.get(ctx.guild.emojis, id=int(emoji_id))
            emoji_display = str(emoji) if emoji else f"❌ Deleted Emoji ({emoji_data['name']})"
            
            last_used = datetime.fromisoformat(emoji_data["last_used"])
            last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
            
            description += f"**{i+1}.** {emoji_display} `:{emoji_data['name']}:`\n"
            description += f"   📈 **{emoji_data['count']}** uses | 🕐 Last: {last_used_str}\n\n"
        
        embed.description = description
        embed.set_footer(text=f"Showing top {min(limit, len(sorted_emojis))} emojis | Total tracked: {len(data['emojis'])}")
        
        await ctx.send(embed=embed)

    @commands.command(name="stickerstats", aliases=["ss"])
    async def sticker_stats(self, ctx, limit: int = 10):
        """Show sticker usage statistics for this server"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        data = self.load_server_data(ctx.guild.id)
        
        if not data["stickers"]:
            await ctx.send("📊 No sticker usage data found for this server yet!")
            return
        
        # Sort stickers by usage count
        sorted_stickers = sorted(
            data["stickers"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        embed = discord.Embed(
            title=f"🏷️ Sticker Usage Statistics - {ctx.guild.name}",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        description = ""
        for i, (sticker_id, sticker_data) in enumerate(sorted_stickers[:limit]):
            sticker = discord.utils.get(ctx.guild.stickers, id=int(sticker_id))
            sticker_display = f"🏷️ {sticker_data['name']}" if not sticker else f"🏷️ {sticker.name}"
            
            last_used = datetime.fromisoformat(sticker_data["last_used"])
            last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
            
            description += f"**{i+1}.** {sticker_display}\n"
            description += f"   📈 **{sticker_data['count']}** uses | 🕐 Last: {last_used_str}\n\n"
        
        embed.description = description
        embed.set_footer(text=f"Showing top {min(limit, len(sorted_stickers))} stickers | Total tracked: {len(data['stickers'])}")
        
        await ctx.send(embed=embed)

    @commands.command(name="emojiinfo", aliases=["ei"])
    async def emoji_info(self, ctx, emoji: discord.Emoji):
        """Get detailed information about a specific emoji"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        # Check if emoji is from this server
        if emoji.guild_id != ctx.guild.id:
            await ctx.send("❌ I can only show stats for emojis from this server!")
            return
        
        data = self.load_server_data(ctx.guild.id)
        emoji_id = str(emoji.id)
        
        if emoji_id not in data["emojis"]:
            await ctx.send(f"📊 No usage data found for {emoji} yet!")
            return
        
        emoji_data = data["emojis"][emoji_id]
        
        embed = discord.Embed(
            title=f"📊 Emoji Information: {emoji}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Name", value=f"`:{emoji_data['name']}:`", inline=True)
        embed.add_field(name="ID", value=emoji_id, inline=True)
        embed.add_field(name="Total Uses", value=emoji_data['count'], inline=True)
        
        first_used = datetime.fromisoformat(emoji_data['first_used'])
        last_used = datetime.fromisoformat(emoji_data['last_used'])
        
        embed.add_field(name="First Used", value=first_used.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="Last Used", value=last_used.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="Animated", value="Yes" if emoji.animated else "No", inline=True)
        
        embed.set_thumbnail(url=emoji.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="clearemojistats")
    @commands.has_permissions(administrator=True)
    async def clear_emoji_stats(self, ctx):
        """Clear all emoji and sticker statistics for this server (Admin only)"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        # Create confirmation embed
        embed = discord.Embed(
            title="⚠️ Clear Statistics",
            description="Are you sure you want to clear all emoji and sticker statistics for this server?",
            color=discord.Color.red()
        )
        embed.add_field(name="Warning", value="This action cannot be undone!", inline=False)
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Clear the data
                file_path = self.get_server_data_file(ctx.guild.id)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                embed = discord.Embed(
                    title="✅ Statistics Cleared",
                    description="All emoji and sticker statistics have been cleared for this server.",
                    color=discord.Color.green()
                )
                await message.edit(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Cancelled",
                    description="Statistics clearing cancelled.",
                    color=discord.Color.blue()
                )
                await message.edit(embed=embed)
                
        except:
            embed = discord.Embed(
                title="⏰ Timed Out",
                description="Statistics clearing timed out.",
                color=discord.Color.grey()
            )
            await message.edit(embed=embed)

    @commands.command(name="trackingstats")
    async def tracking_stats(self, ctx):
        """Show overall tracking statistics for this server"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        data = self.load_server_data(ctx.guild.id)
        
        embed = discord.Embed(
            title=f"📊 Tracking Overview - {ctx.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        total_emoji_uses = sum(emoji_data["count"] for emoji_data in data["emojis"].values())
        total_sticker_uses = sum(sticker_data["count"] for sticker_data in data["stickers"].values())
        
        embed.add_field(name="📱 Tracked Emojis", value=len(data["emojis"]), inline=True)
        embed.add_field(name="🏷️ Tracked Stickers", value=len(data["stickers"]), inline=True)
        embed.add_field(name="📈 Total Emoji Uses", value=total_emoji_uses, inline=True)
        embed.add_field(name="📈 Total Sticker Uses", value=total_sticker_uses, inline=True)
        embed.add_field(name="📈 Combined Uses", value=total_emoji_uses + total_sticker_uses, inline=True)
        
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])
            embed.add_field(name="🕐 Last Updated", value=last_updated.strftime("%Y-%m-%d %H:%M"), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="scanhistory")
    @commands.has_permissions(administrator=True)
    async def scan_history(self, ctx, days: int = 30, channel: discord.TextChannel = None):
        """Scan message history to collect emoji usage data (Admin only)"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in servers!")
            return
        
        if days > 365:
            await ctx.send("❌ Maximum scan period is 365 days!")
            return
        
        # Create initial progress message
        progress_embed = discord.Embed(
            title="🔍 Scanning Message History",
            description="Starting scan...",
            color=discord.Color.orange()
        )
        progress_message = await ctx.send(embed=progress_embed)
        
        total_messages = 0
        total_emojis_found = 0
        total_stickers_found = 0
        channels_scanned = 0
        
        # Calculate date limit
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Determine which channels to scan
            channels_to_scan = [channel] if channel else ctx.guild.text_channels
            
            for ch in channels_to_scan:
                # Check if bot has permission to read message history
                if not ch.permissions_for(ctx.guild.me).read_message_history:
                    continue
                
                channels_scanned += 1
                channel_messages = 0
                
                # Update progress
                progress_embed.description = f"📂 Scanning #{ch.name}...\n"
                progress_embed.description += f"Channels scanned: {channels_scanned}/{len(channels_to_scan)}\n"
                progress_embed.description += f"Messages processed: {total_messages}\n"
                progress_embed.description += f"Emojis found: {total_emojis_found}\n"
                progress_embed.description += f"Stickers found: {total_stickers_found}"
                await progress_message.edit(embed=progress_embed)
                
                try:
                    async for message in ch.history(limit=None, after=cutoff_date):
                        total_messages += 1
                        channel_messages += 1
                        
                        # Process emojis in message content
                        emoji_ids = self.extract_custom_emojis(message.content)
                        for emoji_id in emoji_ids:
                            emoji = discord.utils.get(ctx.guild.emojis, id=int(emoji_id))
                            if emoji:
                                self.update_emoji_usage_historical(ctx.guild.id, emoji_id, emoji.name, message.created_at)
                                total_emojis_found += 1
                        
                        # Process reactions
                        for reaction in message.reactions:
                            if hasattr(reaction.emoji, 'id'):
                                emoji = discord.utils.get(ctx.guild.emojis, id=reaction.emoji.id)
                                if emoji:
                                    # Count each reaction
                                    for _ in range(reaction.count):
                                        self.update_emoji_usage_historical(ctx.guild.id, str(emoji.id), emoji.name, message.created_at)
                                        total_emojis_found += 1
                        
                        # Process stickers
                        if message.stickers:
                            for sticker in message.stickers:
                                if hasattr(sticker, 'guild_id') and sticker.guild_id == ctx.guild.id:
                                    self.update_sticker_usage_historical(ctx.guild.id, sticker.id, sticker.name, message.created_at)
                                    total_stickers_found += 1
                        
                        # Update progress every 100 messages
                        if total_messages % 100 == 0:
                            progress_embed.description = f"📂 Scanning #{ch.name}... ({channel_messages} messages)\n"
                            progress_embed.description += f"Channels scanned: {channels_scanned}/{len(channels_to_scan)}\n"
                            progress_embed.description += f"Messages processed: {total_messages}\n"
                            progress_embed.description += f"Emojis found: {total_emojis_found}\n"
                            progress_embed.description += f"Stickers found: {total_stickers_found}"
                            await progress_message.edit(embed=progress_embed)
                
                except discord.Forbidden:
                    continue  # Skip channels we can't access
                except Exception as e:
                    print(f"Error scanning #{ch.name}: {e}")
                    continue
        
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Scan Error",
                description=f"An error occurred during scanning: {e}",
                color=discord.Color.red()
            )
            await progress_message.edit(embed=error_embed)
            return
        
        # Final results
        final_embed = discord.Embed(
            title="✅ History Scan Complete",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        final_embed.add_field(name="📅 Period Scanned", value=f"{days} days", inline=True)
        final_embed.add_field(name="📂 Channels Scanned", value=channels_scanned, inline=True)
        final_embed.add_field(name="📨 Messages Processed", value=total_messages, inline=True)
        final_embed.add_field(name="😀 Emojis Found", value=total_emojis_found, inline=True)
        final_embed.add_field(name="🏷️ Stickers Found", value=total_stickers_found, inline=True)
        final_embed.add_field(name="⏱️ Total Found", value=total_emojis_found + total_stickers_found, inline=True)
        
        final_embed.set_footer(text="Historical data has been added to tracking statistics")
        
        await progress_message.edit(embed=final_embed)

    def update_emoji_usage_historical(self, guild_id: int, emoji_id: str, emoji_name: str, message_date: datetime) -> None:
        """Update usage statistics for an emoji with historical date"""
        data = self.load_server_data(guild_id)
        
        if emoji_id not in data["emojis"]:
            data["emojis"][emoji_id] = {
                "name": emoji_name,
                "count": 0,
                "first_used": message_date.isoformat(),
                "last_used": message_date.isoformat()
            }
        
        data["emojis"][emoji_id]["count"] += 1
        data["emojis"][emoji_id]["name"] = emoji_name
        
        # Update first_used if this message is older
        current_first = datetime.fromisoformat(data["emojis"][emoji_id]["first_used"])
        if message_date < current_first:
            data["emojis"][emoji_id]["first_used"] = message_date.isoformat()
        
        # Update last_used if this message is newer
        current_last = datetime.fromisoformat(data["emojis"][emoji_id]["last_used"])
        if message_date > current_last:
            data["emojis"][emoji_id]["last_used"] = message_date.isoformat()
        
        self.save_server_data(guild_id, data)
    
    def update_sticker_usage_historical(self, guild_id: int, sticker_id: int, sticker_name: str, message_date: datetime) -> None:
        """Update usage statistics for a sticker with historical date"""
        data = self.load_server_data(guild_id)
        sticker_id_str = str(sticker_id)
        
        if sticker_id_str not in data["stickers"]:
            data["stickers"][sticker_id_str] = {
                "name": sticker_name,
                "count": 0,
                "first_used": message_date.isoformat(),
                "last_used": message_date.isoformat()
            }
        
        data["stickers"][sticker_id_str]["count"] += 1
        data["stickers"][sticker_id_str]["name"] = sticker_name
        
        # Update first_used if this message is older
        current_first = datetime.fromisoformat(data["stickers"][sticker_id_str]["first_used"])
        if message_date < current_first:
            data["stickers"][sticker_id_str]["first_used"] = message_date.isoformat()
        
        # Update last_used if this message is newer
        current_last = datetime.fromisoformat(data["stickers"][sticker_id_str]["last_used"])
        if message_date > current_last:
            data["stickers"][sticker_id_str]["last_used"] = message_date.isoformat()
        
        self.save_server_data(guild_id, data)

async def setup(bot):
    await bot.add_cog(EmojiTracker(bot))