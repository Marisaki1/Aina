import json
import os
import discord
from typing import Dict, List, Any, Optional
from enum import Enum

class AbilityScore(Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"

class ClassManager:
    """Manages character classes for the quest system"""
    
    def __init__(self):
        """Initialize class manager with available classes and their default stats"""
        self.classes = {
            "Barbarian": {
                "description": "🪓 A fierce warrior who can enter a battle rage",
                "primary_abilities": [AbilityScore.STRENGTH, AbilityScore.CONSTITUTION],
                "bonus_ability": AbilityScore.DEXTERITY,
                "starting_skills": ["Athletics", "Intimidation", "Survival", "Nature", "Perception"],
                "image_url": "https://example.com/barbarian.png"
            },
            "Bard": {
                "description": "🎭 A magical performer whose music inspires allies and hinders foes",
                "primary_abilities": [AbilityScore.CHARISMA, AbilityScore.DEXTERITY],
                "bonus_ability": AbilityScore.CONSTITUTION,
                "starting_skills": ["Performance", "Persuasion", "Deception", "Insight", "Arcana"],
                "image_url": "https://example.com/bard.png"
            },
            "Cleric": {
                "description": "🙏 A divine champion who wields holy magic",
                "primary_abilities": [AbilityScore.WISDOM, AbilityScore.CHARISMA],
                "bonus_ability": AbilityScore.CONSTITUTION,
                "starting_skills": ["Religion", "Medicine", "Insight", "Persuasion", "History"],
                "image_url": "https://example.com/cleric.png"
            },
            "Druid": {
                "description": "🌿 A guardian of nature with powerful elemental and animal magic",
                "primary_abilities": [AbilityScore.WISDOM, AbilityScore.CONSTITUTION],
                "bonus_ability": AbilityScore.DEXTERITY,
                "starting_skills": ["Nature", "Animal Handling", "Survival", "Perception", "Medicine"],
                "image_url": "https://example.com/druid.png"
            },
            "Fighter": {
                "description": "⚔️ A master of martial combat with exceptional weapon prowess",
                "primary_abilities": [AbilityScore.STRENGTH, AbilityScore.CONSTITUTION],
                "bonus_ability": AbilityScore.DEXTERITY,
                "starting_skills": ["Athletics", "Intimidation", "Acrobatics", "Survival", "Perception"],
                "image_url": "https://example.com/fighter.png"
            },
            "Monk": {
                "description": "👊 A martial artist who harnesses the power of body and mind",
                "primary_abilities": [AbilityScore.DEXTERITY, AbilityScore.WISDOM],
                "bonus_ability": AbilityScore.STRENGTH,
                "starting_skills": ["Acrobatics", "Stealth", "Religion", "Insight", "Athletics"],
                "image_url": "https://example.com/monk.png"
            },
            "Paladin": {
                "description": "✝️ A holy warrior bound by sacred oaths",
                "primary_abilities": [AbilityScore.STRENGTH, AbilityScore.CHARISMA],
                "bonus_ability": AbilityScore.CONSTITUTION,
                "starting_skills": ["Religion", "Persuasion", "Intimidation", "Medicine", "Insight"],
                "image_url": "https://example.com/paladin.png"
            },
            "Ranger": {
                "description": "🏹 A skilled hunter and wilderness tracker",
                "primary_abilities": [AbilityScore.DEXTERITY, AbilityScore.WISDOM],
                "bonus_ability": AbilityScore.STRENGTH,
                "starting_skills": ["Nature", "Animal Handling", "Stealth", "Survival", "Perception"],
                "image_url": "https://example.com/ranger.png"
            },
            "Rogue": {
                "description": "🗡️ A skilled infiltrator and master of sneak attacks",
                "primary_abilities": [AbilityScore.DEXTERITY, AbilityScore.INTELLIGENCE],
                "bonus_ability": AbilityScore.CHARISMA,
                "starting_skills": ["Stealth", "Sleight of Hand", "Acrobatics", "Deception", "Perception"],
                "image_url": "https://example.com/rogue.png"
            },
            "Sorcerer": {
                "description": "🔮 A spellcaster with innate magical ability",
                "primary_abilities": [AbilityScore.CHARISMA, AbilityScore.CONSTITUTION],
                "bonus_ability": AbilityScore.DEXTERITY,
                "starting_skills": ["Arcana", "Persuasion", "Insight", "Deception", "Religion"],
                "image_url": "https://example.com/sorcerer.png"
            },
            "Warlock": {
                "description": "😈 A wielder of magic bestowed by an otherworldly patron",
                "primary_abilities": [AbilityScore.CHARISMA, AbilityScore.CONSTITUTION],
                "bonus_ability": AbilityScore.WISDOM,
                "starting_skills": ["Arcana", "Deception", "Intimidation", "Religion", "Investigation"],
                "image_url": "https://example.com/warlock.png"
            },
            "Wizard": {
                "description": "📚 A scholarly magic-user capable of powerful spells",
                "primary_abilities": [AbilityScore.INTELLIGENCE, AbilityScore.WISDOM],
                "bonus_ability": AbilityScore.CONSTITUTION,
                "starting_skills": ["Arcana", "History", "Investigation", "Religion", "Medicine"],
                "image_url": "https://example.com/wizard.png"
            },
            "Artificer": {
                "description": "⚙️ A master of magical invention and imbuing objects with power",
                "primary_abilities": [AbilityScore.INTELLIGENCE, AbilityScore.DEXTERITY],
                "bonus_ability": AbilityScore.CONSTITUTION,
                "starting_skills": ["Arcana", "Investigation", "History", "Nature", "Sleight of Hand"],
                "image_url": "https://example.com/artificer.png"
            }
        }
    
    def get_available_classes(self) -> List[str]:
        """Return a list of all available classes"""
        return list(self.classes.keys())
    
    def get_class_info(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Return information about a specific class"""
        return self.classes.get(class_name)
    
    def create_new_character_class(self, class_name: str) -> Dict[str, Any]:
        """Create a new character class instance with default starting values"""
        if class_name not in self.classes:
            return None
            
        class_info = self.classes[class_name]
        
        # Create default ability scores (all start at 10)
        ability_scores = {
            AbilityScore.STRENGTH.value: 10,
            AbilityScore.DEXTERITY.value: 10,
            AbilityScore.CONSTITUTION.value: 10,
            AbilityScore.INTELLIGENCE.value: 10,
            AbilityScore.WISDOM.value: 10,
            AbilityScore.CHARISMA.value: 10
        }
        
        # Add +1 to primary abilities and bonus ability
        for ability in class_info["primary_abilities"]:
            ability_scores[ability.value] += 1
            
        ability_scores[class_info["bonus_ability"].value] += 1
        
        # Create empty skills dictionary
        skills = {}
        
        # Initialize starting skills with 1 point
        for skill in class_info["starting_skills"]:
            skills[skill] = 1
        
        # Create the character class instance
        character_class = {
            "name": class_name,
            "level": 1,
            "xp": 0,
            "ability_scores": ability_scores,
            "skills": skills,
            "equipment": [],
            "abilities": [],
            "appearance_url": None
        }
        
        return character_class
        
    def get_ability_modifier(self, score: int) -> int:
        """Calculate ability modifier from ability score"""
        return (score - 10) // 2
        
    def get_skill_bonus(self, character_class: Dict[str, Any], skill_name: str) -> int:
        """Calculate total bonus for a skill based on ability modifier and skill points"""
        # Get skill value
        skill_value = character_class.get("skills", {}).get(skill_name, 0)
        
        # Get ability score for this skill
        ability = self.get_ability_for_skill(skill_name)
        ability_score = character_class.get("ability_scores", {}).get(ability.value, 10)
        
        # Calculate ability modifier
        ability_mod = self.get_ability_modifier(ability_score)
        
        # Calculate total bonus
        return skill_value + ability_mod
        
    def get_ability_for_skill(self, skill_name: str) -> AbilityScore:
        """Get the associated ability for a skill"""
        # Map skills to abilities
        skill_abilities = {
            "Acrobatics": AbilityScore.DEXTERITY,
            "Animal Handling": AbilityScore.WISDOM,
            "Arcana": AbilityScore.INTELLIGENCE,
            "Athletics": AbilityScore.STRENGTH,
            "Deception": AbilityScore.CHARISMA,
            "History": AbilityScore.INTELLIGENCE,
            "Insight": AbilityScore.WISDOM,
            "Intimidation": AbilityScore.CHARISMA,
            "Investigation": AbilityScore.INTELLIGENCE,
            "Medicine": AbilityScore.WISDOM,
            "Nature": AbilityScore.INTELLIGENCE,
            "Perception": AbilityScore.WISDOM,
            "Performance": AbilityScore.CHARISMA,
            "Persuasion": AbilityScore.CHARISMA,
            "Religion": AbilityScore.INTELLIGENCE,
            "Sleight of Hand": AbilityScore.DEXTERITY,
            "Stealth": AbilityScore.DEXTERITY,
            "Survival": AbilityScore.WISDOM
        }
        
        return skill_abilities.get(skill_name, AbilityScore.INTELLIGENCE)
    
    def level_up_character_class(self, character_class: Dict[str, Any]) -> Dict[str, Any]:
        """Level up a character class"""
        if not character_class:
            return None
            
        # Increment level
        character_class["level"] = character_class.get("level", 1) + 1
        
        # Reset XP to 0 for the new level
        character_class["xp"] = 0
        
        return character_class
    
    def get_xp_for_next_level(self, current_level: int) -> int:
        """Calculate XP needed for the next level"""
        # Simple formula: level * 100
        return current_level * 100
        
    def create_class_selection_embed(self) -> discord.Embed:
        """Create an embed for class selection"""
        embed = discord.Embed(
            title="🧙‍♂️ Choose Your Character Class",
            description="Select a class to begin your adventure! Each class has unique strengths and abilities.",
            color=discord.Color.blue()
        )
        
        # Group classes by type
        martials = ["Barbarian", "Fighter", "Monk", "Paladin", "Ranger", "Rogue"]
        casters = ["Bard", "Cleric", "Druid", "Sorcerer", "Warlock", "Wizard"]
        special = ["Artificer"]
        
        # Add martial classes
        martial_text = ""
        for class_name in martials:
            class_info = self.classes[class_name]
            primary = [a.value.capitalize() for a in class_info["primary_abilities"]]
            martial_text += f"**{class_name}**: {class_info['description']} (Primary: {', '.join(primary)})\n"
            
        embed.add_field(
            name="⚔️ Martial Classes",
            value=martial_text,
            inline=False
        )
        
        # Add spellcaster classes
        caster_text = ""
        for class_name in casters:
            class_info = self.classes[class_name]
            primary = [a.value.capitalize() for a in class_info["primary_abilities"]]
            caster_text += f"**{class_name}**: {class_info['description']} (Primary: {', '.join(primary)})\n"
            
        embed.add_field(
            name="🔮 Spellcaster Classes",
            value=caster_text,
            inline=False
        )
        
        # Add special classes
        special_text = ""
        for class_name in special:
            class_info = self.classes[class_name]
            primary = [a.value.capitalize() for a in class_info["primary_abilities"]]
            special_text += f"**{class_name}**: {class_info['description']} (Primary: {', '.join(primary)})\n"
            
        embed.add_field(
            name="🧪 Special Classes",
            value=special_text,
            inline=False
        )
        
        # Add instructions
        embed.set_footer(text="React to select a class!")
        
        return embed

class PlayerClassHandler:
    """Handles player class data and operations"""
    
    def __init__(self):
        """Initialize the handler with class manager and data path"""
        self.class_manager = ClassManager()
        self.data_path = "data/quests/classes"
        os.makedirs(self.data_path, exist_ok=True)
    
    def get_player_classes(self, user_id: int) -> Dict[str, Any]:
        """Get all classes for a player"""
        player_classes_path = os.path.join(self.data_path, f"{user_id}.json")
        
        if not os.path.exists(player_classes_path):
            return {}
            
        try:
            with open(player_classes_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def has_class(self, user_id: int, class_name: str) -> bool:
        """Check if a player has a specific class"""
        player_classes = self.get_player_classes(user_id)
        return class_name in player_classes
    
    def add_class(self, user_id: int, class_name: str) -> bool:
        """Add a new class to a player"""
        # Check if the class exists
        if class_name not in self.class_manager.get_available_classes():
            return False
            
        # Get player's existing classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player already has this class
        if class_name in player_classes:
            return False
            
        # Create new character class
        new_class = self.class_manager.create_new_character_class(class_name)
        if not new_class:
            return False
            
        # Initialize point tracking
        new_class["used_ability_points"] = 0
        new_class["used_skill_points"] = 0
            
        # Add the new class to the player's classes
        player_classes[class_name] = new_class
        
        # Save the updated classes
        return self._save_player_classes(user_id, player_classes)
    
    def set_class_appearance(self, user_id: int, class_name: str, image_url: str) -> bool:
        """Set the appearance image for a player's class"""
        # Get player's classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player has this class
        if class_name not in player_classes:
            return False
            
        # Update the appearance URL
        player_classes[class_name]["appearance_url"] = image_url
        
        # Save the updated classes
        return self._save_player_classes(user_id, player_classes)
    
    def add_xp(self, user_id: int, class_name: str, xp_amount: int) -> Dict[str, Any]:
        """Add XP to a player's class and handle level up if needed"""
        # Get player's classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player has this class
        if class_name not in player_classes:
            return None
            
        character_class = player_classes[class_name]
        
        # Get current XP and level
        current_xp = character_class.get("xp", 0)
        current_level = character_class.get("level", 1)
        
        # Add XP
        character_class["xp"] = current_xp + xp_amount
        
        # Check for level up
        xp_needed = self.class_manager.get_xp_for_next_level(current_level)
        level_up = False
        notification = ""
        
        if character_class["xp"] >= xp_needed:
            # Level up with the enhanced method
            level_up_result = self.level_up_character_class(user_id, class_name)
            level_up = level_up_result.get("success", False)
            
            if level_up:
                notification = level_up_result.get("notification", "")
                # The class data was already updated and saved in level_up_character_class
                character_class = player_classes[class_name]  # Get fresh data
        else:
            # Save the updated class
            player_classes[class_name] = character_class
            self._save_player_classes(user_id, player_classes)
        
        # Return results
        result = {
            "success": True,
            "level_up": level_up,
            "new_level": character_class["level"],
            "xp": character_class["xp"],
            "xp_needed": self.class_manager.get_xp_for_next_level(character_class["level"]),
            "notification": notification
        }
        
        return result
    
    def level_up_character_class(self, user_id, class_name):
        """Level up a character class and track available points"""
        player_classes = self.get_player_classes(user_id)
        
        if not player_classes or class_name not in player_classes:
            return None
        
        class_data = player_classes[class_name]
        
        # Get current level
        current_level = class_data.get("level", 1)
        new_level = current_level + 1
        
        # Update level
        class_data["level"] = new_level
        class_data["xp"] = 0  # Reset XP for new level
        
        # Check for ability point gain (every 4 levels)
        if new_level % 4 == 0:
            # Show a message about gaining an ability point
            notification = f"🎉 **Level Up!** Your {class_name} has reached level {new_level} and gained an ability point!\nUse `!class increase ability {class_name}` to spend it."
        else:
            notification = f"🎉 **Level Up!** Your {class_name} has reached level {new_level}!"
        
        # Calculate skill points gain
        # Default: INT modifier + 1 (minimum 1)
        ability_scores = class_data.get("ability_scores", {})
        intelligence = ability_scores.get("intelligence", 10)
        int_modifier = max(1, (intelligence - 10) // 2)  # Min of 1
        skill_points_gained = 1 + int_modifier
        
        # Add notification about skill points if they're granted
        if skill_points_gained > 0:
            notification += f"\nYou gained {skill_points_gained} skill points! Use `!class increase skill {class_name}` to spend them."
        
        # Save the updated class
        player_classes[class_name] = class_data
        success = self._save_player_classes(user_id, player_classes)
        
        if success:
            return {
                "success": True,
                "new_level": new_level,
                "notification": notification,
                "ability_point_gained": new_level % 4 == 0,
                "skill_points_gained": skill_points_gained
            }
        else:
            return {
                "success": False
            }
    
    def get_available_ability_points(self, user_id, class_name):
        """Calculate available ability points for a character class"""
        player_classes = self.get_player_classes(user_id)
        
        if not player_classes or class_name not in player_classes:
            return 0
        
        class_data = player_classes[class_name]
        
        # Calculate points: 1 per 4 levels
        level = class_data.get("level", 1)
        used_ability_points = class_data.get("used_ability_points", 0)
        total_ability_points = level // 4
        
        return max(0, total_ability_points - used_ability_points)
    
    def get_available_skill_points(self, user_id, class_name):
        """Calculate available skill points for a character class"""
        player_classes = self.get_player_classes(user_id)
        
        if not player_classes or class_name not in player_classes:
            return 0
        
        class_data = player_classes[class_name]
        
        # Calculate points: 1 + INT modifier per level
        level = class_data.get("level", 1)
        ability_scores = class_data.get("ability_scores", {})
        intelligence = ability_scores.get("intelligence", 10)
        int_modifier = max(1, (intelligence - 10) // 2)  # Min of 1
        
        used_skill_points = class_data.get("used_skill_points", 0)
        total_skill_points = level + (level * int_modifier)
        
        return max(0, total_skill_points - used_skill_points)
    
    def add_skill_point(self, user_id: int, class_name: str, skill_name: str) -> bool:
        """Add a skill point to a player's class skill"""
        # Get player's classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player has this class
        if class_name not in player_classes:
            return False
            
        character_class = player_classes[class_name]
        
        # Check if player has available skill points
        available_points = self.get_available_skill_points(user_id, class_name)
        if available_points <= 0:
            return False
        
        # Get skills
        skills = character_class.get("skills", {})
        
        # Add the skill point
        skills[skill_name] = skills.get(skill_name, 0) + 1
        
        # Update used skill points
        used_points = character_class.get("used_skill_points", 0)
        character_class["used_skill_points"] = used_points + 1
        
        # Update skills
        character_class["skills"] = skills
        
        # Update the class
        player_classes[class_name] = character_class
        
        # Save the updated classes
        return self._save_player_classes(user_id, player_classes)
    
    def add_ability_point(self, user_id: int, class_name: str, ability: AbilityScore) -> bool:
        """Add an ability point to a player's class ability score"""
        # Get player's classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player has this class
        if class_name not in player_classes:
            return False
            
        character_class = player_classes[class_name]
        
        # Check if player has available ability points
        available_points = self.get_available_ability_points(user_id, class_name)
        if available_points <= 0:
            return False
        
        # Get ability scores
        ability_scores = character_class.get("ability_scores", {})
        
        # Check if ability score is already at max (20)
        current_score = ability_scores.get(ability.value, 10)
        if current_score >= 20:
            return False
        
        # Add the ability point
        ability_scores[ability.value] = current_score + 1
        
        # Update used ability points
        used_points = character_class.get("used_ability_points", 0)
        character_class["used_ability_points"] = used_points + 1
        
        # Update ability scores
        character_class["ability_scores"] = ability_scores
        
        # Update the class
        player_classes[class_name] = character_class
        
        # Save the updated classes
        return self._save_player_classes(user_id, player_classes)
    
    def reset_distribution(self, user_id: int, class_name: str) -> bool:
        """Reset a player's skill and ability distribution"""
        # Get player's classes
        player_classes = self.get_player_classes(user_id)
        
        # Check if the player has this class
        if class_name not in player_classes:
            return False
            
        # Create a fresh class with the same level
        character_class = player_classes[class_name]
        current_level = character_class.get("level", 1)
        appearance_url = character_class.get("appearance_url")
        
        # Create a new base character
        new_class = self.class_manager.create_new_character_class(class_name)
        
        # Restore level and appearance
        new_class["level"] = current_level
        new_class["appearance_url"] = appearance_url
        
        # Reset point tracking
        new_class["used_ability_points"] = 0
        new_class["used_skill_points"] = 0
        
        # Update the class
        player_classes[class_name] = new_class
        
        # Save the updated classes
        return self._save_player_classes(user_id, player_classes)
    
    def get_player_total_level(self, user_id: int) -> int:
        """Get the total level of a player across all classes"""
        player_classes = self.get_player_classes(user_id)
        
        total_level = 0
        for class_name, character_class in player_classes.items():
            total_level += character_class.get("level", 1)
            
        return total_level
    
    def _save_player_classes(self, user_id: int, player_classes: Dict[str, Any]) -> bool:
        """Save player classes to file"""
        player_classes_path = os.path.join(self.data_path, f"{user_id}.json")
        
        try:
            with open(player_classes_path, 'w') as f:
                json.dump(player_classes, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving player classes: {e}")
            return False