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

    def create_player(self, user_id, username=None):
        """Create a new player profile"""
        timestamp = datetime.now().isoformat()
        player_data = {
            "user_id": str(user_id),
            "username": username or str(user_id),
            "level": 1,
            "xp": 0,
            "gold": 0,
            "inventory": [],
            "items": [],
            "quests_started": 0,
            "quests_completed": 0,
            "achievements": [],
            "location": "Rivermeet",  # Add default location
            "created_at": timestamp,
            "last_active": timestamp,
            # New fields for class system
            "ability_scores": {
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            },
            "skills": {},
            "active_class": None  # Currently active class for the player
        }
        
        # Save to file
        self.save_player_data(user_id, player_data)
        return player_data
    
    def update_player_location(self, user_id, location):
        """Update a player's location"""
        player_data = self.get_player_data(user_id)
        
        if not player_data:
            player_data = self.create_player(user_id)
        
        player_data["location"] = location
        player_data["last_active"] = datetime.now().isoformat()
        
        # Save updated data
        self.save_player_data(user_id, player_data)
        return player_data

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
        
    def set_active_class(self, user_id, class_name):
        """Set the active class for a player"""
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        player["active_class"] = class_name
        player["last_active"] = datetime.now().isoformat()
        return self.save_player_data(user_id, player)
        
    def get_active_class(self, user_id):
        """Get a player's active class name"""
        player = self.get_player_data(user_id)
        if not player:
            return None
        return player.get("active_class")
        
    def add_ability_score(self, user_id, ability, amount=1):
        """Add points to a player's ability score"""
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        
        if "ability_scores" not in player:
            player["ability_scores"] = {
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            }
        
        # Add points to the ability score
        current = player["ability_scores"].get(ability, 10)
        player["ability_scores"][ability] = current + amount
        
        player["last_active"] = datetime.now().isoformat()
        return self.save_player_data(user_id, player)
    
    def add_skill_point(self, user_id, skill, amount=1):
        """Add points to a player's skill"""
        player = self.get_player_data(user_id) or self.create_player(user_id, str(user_id))
        
        if "skills" not in player:
            player["skills"] = {}
        
        # Add points to the skill
        current = player["skills"].get(skill, 0)
        player["skills"][skill] = current + amount
        
        player["last_active"] = datetime.now().isoformat()
        return self.save_player_data(user_id, player)