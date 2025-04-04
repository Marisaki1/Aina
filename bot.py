import discord
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load .env token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set bot prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load all cogs (commands & events)
async def load_cogs():
    await bot.load_extension("cogs.alarms.alarms")
    await bot.load_extension("cogs.alarms.scheduler")
    await bot.load_extension("cogs.events")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

asyncio.run(main())
