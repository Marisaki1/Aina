# Aina - AI Assistant with Memory

Aina is an AI assistant Discord bot with advanced memory capabilities, allowing it to remember conversations, learn about users, and maintain persistent knowledge.

## 🌟 Features

- 💬 Natural conversation through Discord or terminal interface
- 🧠 Advanced memory system with four memory types:
  - Core Memory - Identity and values
  - Episodic Memory - Recent experiences
  - Semantic Memory - Long-term knowledge
  - Personal Memory - User-specific information
- ⏰ Alarm system with customizable settings
- ⚔️ Quest system for fun interactive adventures
- 👁️ Optional vision capabilities (webcam and screen analysis)
- 🔊 Optional speech recognition and text-to-speech

## 🔧 Installation

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for Qdrant vector database)
- Discord Bot Token and application

### Option 1: Using Docker (recommended)

1. Clone the repository:
```bash
git clone https://github.com/Marisaki1/Aina.git
cd Aina
```

2. Create a `.env` file with your Discord token:
```
DISCORD_TOKEN=your_discord_token_here
```

3. Start the services with Docker Compose:
```bash
docker-compose up -d
```

4. Run the Discord bot:
```bash
docker build -t aina-bot .
docker run --env-file .env --network=host aina-bot
```

### Option 2: Using Conda Environment

1. Clone the repository:
```bash
git clone https://github.com/Marisaki1/Aina.git
cd Aina
```

2. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate aina-env
```

3. Create a `.env` file with your Discord token:
```
DISCORD_TOKEN=your_discord_token_here
```

4. Start Qdrant with Docker:
```bash
docker-compose up -d qdrant
```

5. Run the Discord bot:
```bash
python aina_discord.py
```

## 📋 Commands

### Conversation Commands
- `!chat` - Start or continue a conversation with Aina
- `!endchat` - End the current conversation

### Alarm Commands
- `!setalarm` - Set an alarm with various options
- `!alarm_images` - Show available alarm images
- `!alarms` - List all active alarms
- `!editalarm` - Edit an existing alarm
- `!removealarm` - Remove an alarm

### Quest Commands
- `!quests create` - Create new quest
- `!quests list` - List available quests
- `!quests select <quest_name>` - View quest details
- `!quests start <quest_name> [p: @user1, @user2...]` - Start a quest
- `!quests action <message/attachment>` - Log quest progress
- `!quests complete` - Finish active quest
- And many more! See `!help quests` for details

### Memory Commands
- `!memory search [query]` - Search Aina's memories
- `!memory profile` - View what Aina knows about you
- `!memory reflect` - Generate a reflection on recent memories

## 🧠 Memory System Architecture

Aina's memory system uses Qdrant vector database for semantic search and retrieval. Text is embedded using sentence-transformers to find similar memories.

### Memory Types:

1. **Core Memory**: Identity, values, and fundamental knowledge
2. **Episodic Memory**: Recent experiences and interactions
3. **Semantic Memory**: Long-term knowledge and facts
4. **Personal Memory**: User-specific information and preferences

## 🖥️ Terminal Interface

Aina also provides a terminal interface for direct interaction:

```bash
python aina_terminal.py
```

Terminal commands start with `!` just like in Discord, but you can also chat directly by typing messages.

## 📝 Configuration

Configuration files can be found in the `data/aina/config` directory:
- `memory_config.json` - Memory system settings
- `personality.json` - Aina's personality traits

## 🗂️ Project Structure

```
aina/
├── aina_discord.py           # Discord bot entry point
├── aina_terminal.py          # Terminal interface
├── core/                     # Core functionality
│   ├── agent.py              # Central agent logic
│   ├── memory/               # Memory systems
│   │   ├── memory_manager.py # Memory orchestration
│   │   └── storage.py        # Qdrant interface
│   └── llm/                  # Language model functionality
├── cogs/                     # Discord command modules
├── utils/                    # Utility functions
└── data/                     # Data storage
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Special thanks to all contributors and supporters!