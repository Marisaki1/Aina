import discord
import os

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Discord Bot Settings
BOT_PREFIX = "!"
BOT_STATUS = "with papa (!help)"

# Dungeon System Settings
DUNGEON_SETTINGS = {
    # Dungeon Sizes (grid dimensions)
    "SIZES": {
        "SMALL": {"width": 10, "height": 10, "name": "Small Dungeon"},
        "MEDIUM": {"width": 15, "height": 15, "name": "Medium Dungeon"},
        "LARGE": {"width": 20, "height": 20, "name": "Large Dungeon"}
    },
    
    # Dungeon Complexity (affects path generation)
    "COMPLEXITY": {
        "EASY": {"branch_factor": 0.2, "dead_ends": 2, "name": "Easy"},
        "NORMAL": {"branch_factor": 0.4, "dead_ends": 4, "name": "Normal"},
        "HARD": {"branch_factor": 0.6, "dead_ends": 8, "name": "Hard"}
    },
    
    # Dungeon Floors Configuration
    "FLOORS": {
        "SMALL": {"min": 1, "max": 3, "name": "Few Floors"},
        "MEDIUM": {"min": 4, "max": 6, "name": "Several Floors"},
        "LARGE": {"min": 7, "max": 10, "name": "Many Floors"},
        "EXTREME": {"min": 20, "max": 20, "name": "Extreme Tower"}
    },
    
    # Dungeon Difficulty (affects enemies and traps)
    "DIFFICULTY": {
        "EASY": {"trap_chance": 0.1, "enemy_strength": 0.8, "name": "Easy"},
        "NORMAL": {"trap_chance": 0.2, "enemy_strength": 1.0, "name": "Normal"},
        "HARD": {"trap_chance": 0.3, "enemy_strength": 1.3, "name": "Hard"},
        "LUNATIC": {"trap_chance": 0.4, "enemy_strength": 1.8, "name": "Lunatic"}
    },
    
    # Visual Settings
    "COLORS": {
        "WALL": (50, 50, 50),       # Dark gray for walls
        "PATH": (200, 200, 200),     # Light gray for paths
        "START": (0, 255, 0),        # Green for starting point
        "END": (255, 0, 0),          # Red for ending point
        "PLAYER": (0, 0, 255),       # Blue for player
        "CHEST": (255, 215, 0),      # Gold for chests
        "TRAP": (255, 0, 255),       # Magenta for traps
        "STAIRS": (150, 75, 0),      # Brown for stairs
        "FOG": (30, 30, 30)          # Almost black for fog of war
    },
    
    # Encounter Settings
    "ENCOUNTERS": {
        "FIXED_CHANCE": 0.7,         # Chance that a fixed encounter spawns
        "RANDOM_MOVE_CHANCE": 0.05,  # Chance of random encounter per move
        "COOLDOWN_MOVES": 5          # Minimum moves before another random encounter
    },
    
    # Interactive Elements
    # In settings.py, add these to your ELEMENTS section
    "ELEMENTS": {
        "STAIRS": "🪜",              # Stairs/ladder emoji
        "CHEST": "🎁",               # Chest emoji
        "TRAP": "⚠️",                # Trap warning emoji
        "ENEMY": "👹",               # Enemy emoji
        "KEY": "🔑",                 # Key emoji
        "DOOR": "🚪",                # Door emoji
        "INTERACT": "✅",            # Interaction confirmation emoji
        "START": "🏠",               # Start position
        "END": "🏆",                 # End position (goal)
        "STAIRS_UP": "⬆️",           # Upward stairs 
        "STAIRS_DOWN": "⬇️",         # Downward stairs
        "PLAYER": "🧙",              # Player character
        "WALL": "🧱",                # Wall (though this might be visually heavy)
        "PATH": "⬜",                # Path (empty space)
        "FOG": "🌫️"                 # Fog of war
    },
    
    # Fog of War
    "FOG_OF_WAR": {
        "ENABLED": True,
        "VISIBILITY_RADIUS": 1       # Cells visible around player (1 = 3x3 area)
    },
    
    # Save System
    "SAVE": {
        "ENABLED": True,
        "AUTO_SAVE_MINUTES": 5,      # How often to auto-save dungeon state
        "SAVE_DIR": os.path.join(DATA_DIR, "dungeons", "saves")
    },
    
    # File paths
    "PATHS": {
        "DUNGEONS_DIR": os.path.join(DATA_DIR, "dungeons"),
        "TEMPLATES_DIR": os.path.join(ASSETS_DIR, "images", "dungeons", "templates"),
        "TILES_DIR": os.path.join(ASSETS_DIR, "images", "dungeons", "tiles")
    }
}

# Ensure dungeon directories exist
os.makedirs(DUNGEON_SETTINGS["SAVE"]["SAVE_DIR"], exist_ok=True)
os.makedirs(DUNGEON_SETTINGS["PATHS"]["DUNGEONS_DIR"], exist_ok=True)
os.makedirs(DUNGEON_SETTINGS["PATHS"]["TEMPLATES_DIR"], exist_ok=True)
os.makedirs(DUNGEON_SETTINGS["PATHS"]["TILES_DIR"], exist_ok=True)

# Quest System Settings (for reference/integration)
QUEST_SETTINGS = {
    "XP_MULTIPLIERS": {
        "EASY": 1.0,
        "NORMAL": 1.5,
        "HARD": 2.0,
        "LUNATIC": 3.0
    },
    "GOLD_MULTIPLIERS": {
        "EASY": 1.0,
        "NORMAL": 1.5,
        "HARD": 2.0,
        "LUNATIC": 3.0
    }
}

# Reaction Emojis
DIRECTION_EMOJIS = {
    "UP": "⬆️",
    "DOWN": "⬇️",
    "LEFT": "⬅️",
    "RIGHT": "➡️"
}

# Interactive Emojis
INTERACTIVE_EMOJIS = {
    "CONFIRM": "✅",
    "CANCEL": "❌",
    "INFO": "ℹ️",
    "SETTINGS": "⚙️",
    "NEXT": "➡️",
    "PREVIOUS": "⬅️",
    "START": "▶️",
    "PAUSE": "⏸️",
    "STOP": "⏹️"
}

# Discord Embed Colors
EMBED_COLORS = {
    "SUCCESS": discord.Color.green(),
    "ERROR": discord.Color.red(),
    "INFO": discord.Color.blue(),
    "WARNING": discord.Color.gold(),
    "DUNGEON": discord.Color.dark_purple()
}

# Dungeon Cell Types (for grid representation)
CELL_TYPES = {
    "WALL": 0,
    "PATH": 1,
    "START": 2,
    "END": 3,
    "STAIRS_UP": 4,
    "STAIRS_DOWN": 5,
    "CHEST": 6,
    "TRAP": 7,
    "ENEMY": 8,
    "KEY": 9,
    "DOOR": 10,
    "FOG": 11
}

