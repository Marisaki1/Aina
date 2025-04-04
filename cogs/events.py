import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ {self.bot.user} is online and ready!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"🎉 Joined new server: {guild.name}")

# ✅ Required for loading the cog properly in Discord.py v2.0+
async def setup(bot):
    await bot.add_cog(Events(bot))
