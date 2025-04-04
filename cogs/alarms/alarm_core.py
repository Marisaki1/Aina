import discord
from discord.ext import commands
import json
import os

ALARM_FILE = "data/alarms.json"

class AlarmManager:
    def __init__(self):
        # Make sure the data directory exists
        os.makedirs(os.path.dirname(ALARM_FILE), exist_ok=True)
        
        # Create alarm file if it doesn't exist
        if not os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, "w") as f:
                json.dump({}, f)
    
    def load_alarms(self):
        try:
            with open(ALARM_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is empty or has invalid JSON, return empty dict
            return {}

    def save_alarms(self, alarms):
        with open(ALARM_FILE, "w") as f:
            json.dump(alarms, f, indent=4)

    def add_alarm(self, guild_id, time, message, user_id, image_url=None, repeat=None):
        alarms = self.load_alarms()

        # Convert guild_id to string for JSON compatibility
        guild_id = str(guild_id)
        
        if guild_id not in alarms:
            alarms[guild_id] = []

        alarms[guild_id].append({
            "time": time,
            "message": message,
            "user_id": user_id,
            "image_url": image_url,
            "repeat": repeat
        })

        self.save_alarms(alarms)
        return True

    def remove_alarm(self, guild_id, index):
        alarms = self.load_alarms()
        guild_id = str(guild_id)

        if guild_id in alarms and 0 <= index < len(alarms[guild_id]):
            alarms[guild_id].pop(index)
            self.save_alarms(alarms)
            return True
        return False

    def list_alarms(self, guild_id):
        alarms = self.load_alarms()
        guild_id = str(guild_id)
        return alarms.get(guild_id, [])
        
    def clear_all_alarms(self, guild_id):
        alarms = self.load_alarms()
        guild_id = str(guild_id)
        
        if guild_id in alarms:
            alarms[guild_id] = []
            self.save_alarms(alarms)
            return True
        return False