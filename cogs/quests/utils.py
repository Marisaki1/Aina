import discord

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
    return discord.Embed(**kwargs).set_footer(text="Quest System v1.0")

def format_duration(duration):
    hours, minutes = map(int, duration.split(':'))
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours >1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes >1 else ''}")
    return " ".join(parts) or "Instant"