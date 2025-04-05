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
            os.makedirs(os.path.join(self.base_path, path), exist_ok=True)
    
    def create_quest(self, quest_data):
        try:
            quest_id = quest_data['id']
            with open(os.path.join(self.base_path, "new", f"{quest_id}.json"), "w") as f:
                json.dump(quest_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving quest: {e}")
            return False
    
    def get_all_quests(self):
        """Get all available quests"""
        quests = []
        try:
            for file in os.listdir(os.path.join(self.base_path, "new")):
                if file.endswith(".json"):
                    with open(os.path.join(self.base_path, "new", file)) as f:
                        quest = json.load(f)
                        quests.append(quest)
            return quests
        except Exception as e:
            print(f"Error listing quests: {e}")
            return []
    
    def get_quest_by_name(self, name):
        for file in os.listdir(os.path.join(self.base_path, "new")):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(self.base_path, "new", file)) as f:
                        quest = json.load(f)
                        if quest["name"].lower() == name.lower():
                            return quest
                except Exception as e:
                    print(f"Error reading quest file: {e}")
        return None
    
    def start_quest(self, quest_data):
        try:
            quest_id = quest_data["quest_id"]
            with open(os.path.join(self.base_path, "ongoing", f"{quest_id}.json"), "w") as f:
                json.dump(quest_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error starting quest: {e}")
            return False
    
    def get_active_quests(self):
        """Get all active quests"""
        quests = []
        try:
            for file in os.listdir(os.path.join(self.base_path, "ongoing")):
                if file.endswith(".json"):
                    with open(os.path.join(self.base_path, "ongoing", file)) as f:
                        quest = json.load(f)
                        quests.append(quest)
            return quests
        except Exception as e:
            print(f"Error listing active quests: {e}")
            return []
    
    def get_user_active_quest(self, user_id):
        user_id_str = str(user_id)  # Ensure user_id is a string for comparison
        try:
            for file in os.listdir(os.path.join(self.base_path, "ongoing")):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(self.base_path, "ongoing", file)) as f:
                            quest = json.load(f)
                            # Convert all participant IDs to strings for comparison
                            participants = [str(p) for p in quest.get("participants", [])]
                            if user_id_str in participants:
                                return quest
                    except Exception as e:
                        print(f"Error reading quest file: {e}")
        except Exception as e:
            print(f"Error accessing ongoing quests directory: {e}")
        return None
    
    def add_quest_action(self, quest_id, action_data):
        try:
            path = os.path.join(self.base_path, "ongoing", f"{quest_id}.json")
            with open(path, "r+") as f:
                quest = json.load(f)
                if "actions" not in quest:
                    quest["actions"] = []
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
            src = os.path.join(self.base_path, "ongoing", f"{quest_id}.json")
            dest = os.path.join(self.base_path, "completed", f"{quest_id}.json")
            
            with open(src) as f:
                quest = json.load(f)
                quest["completion_time"] = completion_time.isoformat()
                quest["status"] = "completed"
                
            with open(dest, "w") as f:
                json.dump(quest, f, indent=4)
                
            # Only remove the original file after successfully writing the new one
            os.remove(src)
            return True
        except Exception as e:
            print(f"Error completing quest: {e}")
            return False
            
    def cancel_quest(self, quest_id):
        """Cancel an ongoing quest and return it to available quests"""
        try:
            # Get the quest data
            src = os.path.join(self.base_path, "ongoing", f"{quest_id}.json")
            if not os.path.exists(src):
                print(f"Quest file not found: {src}")
                return False
                
            # Remove the active quest file
            os.remove(src)
            return True
        except Exception as e:
            print(f"Error canceling quest: {e}")
            return False