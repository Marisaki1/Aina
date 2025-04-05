import json
import os
import uuid
from datetime import datetime

class QuestManager:
    def __init__(self):
        self.base_path = "data/quests"
        self._ensure_dirs()
        
    def _ensure_dirs(self):
        for path in ["new", "ongoing", "completed"]:
            os.makedirs(f"{self.base_path}/{path}", exist_ok=True)
    
    def create_quest(self, quest_data):
        try:
            quest_id = quest_data['id']
            with open(f"{self.base_path}/new/{quest_id}.json", "w") as f:
                json.dump(quest_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving quest: {e}")
            return False
    
    def get_all_quests(self):
        """Get all available quests"""
        quests = []
        try:
            for file in os.listdir(f"{self.base_path}/new"):
                if file.endswith(".json"):
                    with open(f"{self.base_path}/new/{file}") as f:
                        quest = json.load(f)
                        quests.append(quest)
            return quests
        except Exception as e:
            print(f"Error listing quests: {e}")
            return []
    
    def get_quest_by_name(self, name):
        for file in os.listdir(f"{self.base_path}/new"):
            if file.endswith(".json"):
                try:
                    with open(f"{self.base_path}/new/{file}") as f:
                        quest = json.load(f)
                        if quest["name"].lower() == name.lower():
                            return quest
                except Exception as e:
                    print(f"Error reading quest file: {e}")
        return None
    
    def start_quest(self, quest_data):
        try:
            quest_id = quest_data["quest_id"]
            with open(f"{self.base_path}/ongoing/{quest_id}.json", "w") as f:
                json.dump(quest_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error starting quest: {e}")
            return False
    
    def get_active_quests(self):
        """Get all active quests"""
        quests = []
        try:
            for file in os.listdir(f"{self.base_path}/ongoing"):
                if file.endswith(".json"):
                    with open(f"{self.base_path}/ongoing/{file}") as f:
                        quest = json.load(f)
                        quests.append(quest)
            return quests
        except Exception as e:
            print(f"Error listing active quests: {e}")
            return []
    
    def get_user_active_quest(self, user_id):
        for file in os.listdir(f"{self.base_path}/ongoing"):
            if file.endswith(".json"):
                try:
                    with open(f"{self.base_path}/ongoing/{file}") as f:
                        quest = json.load(f)
                        if str(user_id) in [str(p) for p in quest["participants"]]:
                            return quest
                except Exception as e:
                    print(f"Error reading quest file: {e}")
        return None
    
    def add_quest_action(self, quest_id, action_data):
        try:
            path = f"{self.base_path}/ongoing/{quest_id}.json"
            with open(path, "r+") as f:
                quest = json.load(f)
                quest["actions"].append(action_data)
                f.seek(0)
                json.dump(quest, f, indent=4)
                f.truncate()
            return True
        except Exception as e:
            print(f"Error adding action: {e}")
            return False
    
    def complete_quest(self, quest_id, completion_time):
        try:
            src = f"{self.base_path}/ongoing/{quest_id}.json"
            dest = f"{self.base_path}/completed/{quest_id}.json"
            
            with open(src) as f:
                quest = json.load(f)
                quest["completion_time"] = completion_time.isoformat()
                quest["status"] = "completed"
                
            os.rename(src, dest)
            with open(dest, "w") as f:
                json.dump(quest, f, indent=4)
            return True
        except Exception as e:
            print(f"Error completing quest: {e}")
            return False
            
    def cancel_quest(self, quest_id):
        """Cancel an ongoing quest and return it to available quests"""
        try:
            # Get the quest data
            src = f"{self.base_path}/ongoing/{quest_id}.json"
            with open(src) as f:
                quest = json.load(f)
            
            # Remove the active quest file
            os.remove(src)
            return True
        except Exception as e:
            print(f"Error canceling quest: {e}")
            return False

class PlayerManager:
    def __init__(self):
        self.players_path = "data/quests/playerdata"
        os.makedirs(self.players_path, exist_ok=True)
    
    def get_player_data(self, user_id):
        path = f"{self.players_path}/{user_id}.json"
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None
    
    def create_player(self, user_id, username):
        data = {
            "id": user_id,
            "username": username,
            "gold": 0,
            "xp": 0,
            "quests_started": 0,
            "quests_completed": 0,
            "items": [],
            "achievements": []
        }
        with open(f"{self.players_path}/{user_id}.json", "w") as f:
            json.dump(data, f, indent=4)
        return data
    
    def update_player_quest_count(self, user_id, action_type):
        data = self.get_player_data(user_id) or self.create_player(user_id, "")
        if action_type == "started":
            data["quests_started"] += 1
        elif action_type == "completed":
            data["quests_completed"] += 1
        with open(f"{self.players_path}/{user_id}.json", "w") as f:
            json.dump(data, f, indent=4)
    
    def add_rewards(self, user_id, gold, xp):
        try:
            data = self.get_player_data(user_id) or self.create_player(user_id, "")
            data["gold"] += gold
            data["xp"] += xp
            with open(f"{self.players_path}/{user_id}.json", "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error adding rewards: {e}")
            return False