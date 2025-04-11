import discord
import asyncio

DIFFICULTY_COLORS = {
    "Easy": discord.Color.green(),
    "Normal": discord.Color.blue(),
    "Hard": discord.Color.orange(),
    "Lunatic": discord.Color.red()
}

DIFFICULTY_EMOJIS = {
    "Easy": "🌱",
    "Normal": "⚔️",
    "Hard": "🔥",
    "Lunatic": "💀"
}

def create_embed(**kwargs):
    return discord.Embed(**kwargs).set_footer(text="Quest System v1.1")

def format_duration(duration):
    hours, minutes = map(int, duration.split(':'))
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours >1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes >1 else ''}")
    return " ".join(parts) or "Instant"

async def send_temp_message(message, delay_seconds=60):
    """Delete a message after specified delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except discord.NotFound:
        pass  # Message was already deleted
    except Exception as e:
        print(f"Error deleting message: {e}")
        
async def create_and_send_temp_embed(channel, title, description, color=discord.Color.blue(), delay_seconds=60):
    """Create, send, and auto-delete an embed message"""
    embed = create_embed(title=title, description=description, color=color)
    message = await channel.send(embed=embed)
    await send_temp_message(message, delay_seconds)
    return message