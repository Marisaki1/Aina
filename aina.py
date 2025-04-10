import discord
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ Error: No Discord token found in .env file")
    print("Please create a .env file with your Discord token (DISCORD_TOKEN=your_token_here)")
    exit(1)

# Set bot prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("assets/images/alarms", exist_ok=True)
os.makedirs("data/quests", exist_ok=True)  # For quest system data

# Load all cogs (commands & events)
async def load_cogs():
    try:
        # Load alarm cogs
        await bot.load_extension("cogs.help.help")
        await bot.load_extension("cogs.alarms.alarms")
        await bot.load_extension("cogs.alarms.scheduler")
        
        # Load quest cogs
        await bot.load_extension("cogs.quests.quests")
        await bot.load_extension("cogs.quests.class_commands")  # Added this line to load the class commands
        await bot.load_extension("cogs.quests.random_encounters")
        
        # Load events cog
        await bot.load_extension("cogs.events")
        
        print("✅ All cogs loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading cogs: {e}")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is connected to Discord!")
    print(f"🤖 Bot ID: {bot.user.id}")
    print(f"🌐 Connected to {len(bot.guilds)} servers")
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="with papa (!help)"
        )
    )

@bot.event 
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: {error}")
    else:
        await ctx.send(f"❌ An error occurred: {error}")
        print(f"Command error: {error}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())