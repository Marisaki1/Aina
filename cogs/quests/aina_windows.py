import json
import os
from typing import Dict, Any, Optional, List, Tuple, Union

class ConfigManager:
    """Centralized configuration management system for Aina"""
    
    def __init__(self):
        """Initialize the configuration manager"""
        self.config_dir = "data/config"
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configurations
        self.default_configs = {
            "random_encounters": self._get_default_encounter_config(),
            "ui_settings": self._get_default_ui_config(),
            "player_classes": self._get_default_class_config(),
            "town_thresholds": self._get_default_threshold_config(),
            "rewards": self._get_default_rewards_config()
        }
        
        # Initialize configurations
        self.configs = {}
        self._load_all_configs()
    
    def _get_default_encounter_config(self) -> Dict[str, Any]:
        """Get default configuration for random encounters"""
        return {
            "encounter_chance": 5,  # Percentage chance per check
            "cooldown_minutes": 2,  # Cooldown between encounters in a channel
            "expiration_minutes": 2,  # How long an encounter remains active
            "auto_delete_minutes": 1,  # Auto-delete result messages after this many minutes
            "min_xp_reward": 100,
            "max_xp_reward": 300,
            "min_gold_reward": 10,
            "max_gold_reward": 50,
            "enabled": True
        }
    
    def _get_default_ui_config(self) -> Dict[str, Any]:
        """Get default configuration for UI settings"""
        return {
            "default_embed_color": "0x3498db",  # Blue
            "error_embed_color": "0xe74c3c",  # Red
            "success_embed_color": "0x2ecc71",  # Green
            "info_embed_color": "0xf1c40f",  # Yellow
            "message_timeout_seconds": 60,  # Default timeout for temporary messages
            "pagination_timeout_seconds": 120,  # Timeout for paginated messages
            "max_items_per_page": 10,  # Maximum items to display per page
            "bot_name": "Aina",
            "bot_avatar_url": "",
            "footer_text": "Quest System v1.0"
        }
    
    def _get_default_class_config(self) -> Dict[str, Any]:
        """Get default configuration for player classes"""
        return {
            "starting_ability_score": 10,
            "max_ability_score": 20,
            "primary_ability_bonus": 1,
            "starting_skill_points": 1,
            "xp_per_level": 100,
            "level_up_ability_points": 1,
            "level_up_skill_points": 1,
            "reset_cost_multiplier": 50  # Gold cost = level * multiplier
        }
    
    def _get_default_threshold_config(self) -> Dict[str, Any]:
        """Get default configuration for town thresholds"""
        return {
            "Rivermeet": {
                "levels": [
                    {"min": 1, "max": 3, "correct_choices": 1},
                    {"min": 4, "max": 6, "correct_choices": 2},
                    {"min": 7, "max": 9, "correct_choices": 3}
                ],
                "min_dc": 10,
                "max_dc": 18
            },
            "Whispering Forest": {
                "levels": [
                    {"min": 1, "max": 4, "correct_choices": 1},
                    {"min": 5, "max": 8, "correct_choices": 2},
                    {"min": 9, "max": 12, "correct_choices": 3}
                ],
                "min_dc": 12,
                "max_dc": 20
            },
            "Dragonclaw Mountains": {
                "levels": [
                    {"min": 4, "max": 7, "correct_choices": 1},
                    {"min": 8, "max": 12, "correct_choices": 2},
                    {"min": 13, "max": 16, "correct_choices": 3}
                ],
                "min_dc": 14,
                "max_dc": 22
            },
            "Default": {
                "levels": [
                    {"min": 1, "max": 5, "correct_choices": 1},
                    {"min": 6, "max": 10, "correct_choices": 2},
                    {"min": 11, "max": 20, "correct_choices": 3}
                ],
                "min_dc": 10,
                "max_dc": 20
            }
        }
    
    def _get_default_rewards_config(self) -> Dict[str, Any]:
        """Get default configuration for rewards"""
        return {
            "encounter_rewards": {
                "base_xp": 100,
                "level_multiplier": 10,
                "base_gold": 10,
                "level_multiplier": 2
            },
            "quest_rewards": {
                "Easy": {"base_xp": 100, "base_gold": 50},
                "Normal": {"base_xp": 200, "base_gold": 100},
                "Hard": {"base_xp": 350, "base_gold": 200},
                "Lunatic": {"base_xp": 500, "base_gold": 350}
            }
        }
    
    def _load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration from file"""
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        # If config file doesn't exist, create it with defaults
        if not os.path.exists(config_path):
            default_config = self.default_configs.get(config_name, {})
            self._save_config(config_name, default_config)
            return default_config
        
        # Load the configuration
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading {config_name} config: {e}")
            return self.default_configs.get(config_name, {})
    
    def _save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """Save a specific configuration to file"""
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving {config_name} config: {e}")
            return False
    
    def _load_all_configs(self) -> None:
        """Load all configurations"""
        for config_name in self.default_configs.keys():
            self.configs[config_name] = self._load_config(config_name)
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get a specific configuration"""
        return self.configs.get(config_name, {})
    
    def update_config(self, config_name: str, updates: Dict[str, Any]) -> bool:
        """Update a specific configuration with new values"""
        # Check if the config exists
        if config_name not in self.configs:
            return False
        
        # Update the config
        current_config = self.configs[config_name]
        
        # Recursive update
        self._update_recursive(current_config, updates)
        
        # Save the updated config
        success = self._save_config(config_name, current_config)
        
        # If saved successfully, update the in-memory config
        if success:
            self.configs[config_name] = current_config
            
        return success
    
    def _update_recursive(self, current: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update a dictionary with new values"""
        for key, value in updates.items():
            if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._update_recursive(current[key], value)
            else:
                # Update value
                current[key] = value
    
    def reset_config(self, config_name: str) -> bool:
        """Reset a specific configuration to default values"""
        if config_name not in self.default_configs:
            return False
            
        # Reset to default
        default_config = self.default_configs[config_name]
        success = self._save_config(config_name, default_config)
        
        # If saved successfully, update the in-memory config
        if success:
            self.configs[config_name] = default_config
            
        return success
    
    def get_town_threshold(self, location: str, player_level: int) -> Tuple[int, int]:
        """
        Get the number of correct choices and DC range for a specific location and player level
        Returns (correct_choices, min_dc, max_dc)
        """
        # Get town thresholds config
        thresholds = self.get_config("town_thresholds")
        
        # Get location thresholds or default
        location_thresholds = thresholds.get(location)
        if not location_thresholds:
            location_thresholds = thresholds.get("Default")
        
        # Get correct choices based on player level
        correct_choices = 1  # Default
        for level_range in location_thresholds["levels"]:
            if level_range["min"] <= player_level <= level_range["max"]:
                correct_choices = level_range["correct_choices"]
                break
        
        # Get DC range
        min_dc = location_thresholds.get("min_dc", 10)
        max_dc = location_thresholds.get("max_dc", 20)
        
        return (correct_choices, min_dc, max_dc)
    
    def get_encounter_rewards(self, player_level: int) -> Tuple[int, int]:
        """Calculate encounter rewards based on player level"""
        # Get rewards config
        rewards = self.get_config("rewards")
        encounter_rewards = rewards.get("encounter_rewards", {"base_xp": 100, "base_gold": 10})
        
        # Calculate XP reward
        base_xp = encounter_rewards.get("base_xp", 100)
        xp_multiplier = encounter_rewards.get("level_multiplier", 10)
        xp = base_xp + (player_level * xp_multiplier)
        
        # Calculate gold reward
        base_gold = encounter_rewards.get("base_gold", 10)
        gold_multiplier = encounter_rewards.get("level_multiplier", 2)
        gold = base_gold + (player_level * gold_multiplier)
        
        return (xp, gold)
    
    def get_quest_rewards(self, difficulty: str, player_level: int) -> Tuple[int, int]:
        """Calculate quest rewards based on difficulty and player level"""
        # Get rewards config
        rewards = self.get_config("rewards")
        quest_rewards = rewards.get("quest_rewards", {})
        
        # Get difficulty rewards or default to Normal
        difficulty_rewards = quest_rewards.get(difficulty, quest_rewards.get("Normal", {"base_xp": 200, "base_gold": 100}))
        
        # Calculate rewards
        base_xp = difficulty_rewards.get("base_xp", 200)
        base_gold = difficulty_rewards.get("base_gold", 100)
        
        # Scale with player level
        xp = base_xp + (player_level * 20)
        gold = base_gold + (player_level * 5)
        
        return (xp, gold)

# Create a singleton instance
config_manager = ConfigManager()

# Function to get the singleton instance
def get_config_manager() -> ConfigManager:
    return config_manager