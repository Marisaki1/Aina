import json
import os
from datetime import datetime

class PlayerManager:
    def __init__(self):
        self.players_path = "data/quests/playerdata"
        os.makedirs(self.players_path, exist_ok=True)

    def _get_player_path(self, user_id):
        return os.path.join(self.players_path, f"{user_id}.json")

    def get_player_data(self, user_id):
        path = self._get_player_path(user_id)
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading player data: {e}")
            return None

    def create_player(self, user_id, username):
        default_data = {
            "user_id": str(user_id),
            "username": username,
            "level": 1,
            "xp": 0,
            "gold": 0,
            "inventory": [],
            "items": [],  # For backward compatibility
            "quests_started": 0,
            "quests_completed": 0,
            "achievements": [],
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
        self.save_player_data(user_id, default_data)
        return default_data

    def save_player_data(self, user_id, data):
        path = self._get_player_path(user_id)
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving player data: {e}")
            return False

    def update_player_quest_count(self, user_id, count_type):
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        if count_type == "started":
            player["quests_started"] += 1
        elif count_type == "completed":
            player["quests_completed"] += 1
        player["last_active"] = datetime.now().isoformat()
        return self.save_player_data(user_id, player)

    def add_rewards(self, user_id, gold, xp):
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        
        # Update gold
        player["gold"] += gold
        
        # Update XP and level
        player["xp"] += xp
        new_level = 1 + int((player["xp"] / 100) ** 0.5)
        if new_level > player["level"]:
            player["level"] = new_level
        
        player["last_active"] = datetime.now().isoformat()
        return self.save_player_data(user_id, player)

    def get_player_inventory(self, user_id):
        player = self.get_player_data(user_id)
        if not player:
            return []
            
        # Check both inventory and items fields for compatibility
        inventory = player.get("inventory", [])
        items = player.get("items", [])
        
        # Return combined inventory, removing duplicates
        combined = inventory + [item for item in items if item not in inventory]
        return combined

    def update_inventory(self, user_id, items):
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        player["inventory"] = items
        player["items"] = items  # Keep both fields in sync
        return self.save_player_data(user_id, player)

    def add_achievement(self, user_id, achievement):
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        player["achievements"].append({
            "name": achievement,
            "date": datetime.now().isoformat()
        })
        return self.save_player_data(user_id, player)