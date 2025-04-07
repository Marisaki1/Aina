import random
from typing import Dict, List, Tuple, Any

class ScenarioMaker:
    def __init__(self):
        self.location_scenarios = {
            "Town of Rivermeet": self._rivermeet_scenarios,
            "Whispering Forest": self._forest_scenarios,
            "Dragonclaw Mountains": self._mountain_scenarios,
            "Crystal Caves": self._cave_scenarios,
            "Shadowmire Swamp": self._swamp_scenarios,
            "Forgotten Ruins": self._ruins_scenarios,
            "Sunlit Plains": self._plains_scenarios,
            "Frostpeak Village": self._frostpeak_scenarios,
            "Emerald Sea": self._sea_scenarios
        }
    
    def generate_scenario(self, location: str) -> Dict[str, Any]:
        """Generate a scenario for the specified location"""
        # Get the location-specific scenario generator
        scenario_generator = self.location_scenarios.get(location, self._default_scenarios)
        
        # Generate the scenario
        return scenario_generator()
    
    def _rivermeet_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Town of Rivermeet"""
        # 1. Select NPCs (1-2)
        npcs = [
            "Mayor Thadrick Goldvein", "Sister Maribel", "Garrick the Unseen",
            "Captain Durnan", "Old Ma Tusk", "Zorvut the Mad",
            "Lira the Silver-Tongued", "Brother Alden", "The Black Eel", 
            "Hedwig the Ratcatcher"
        ]
        
        # Determine if we use 1 or 2 NPCs (10% chance for 2)
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        
        # 2. Select a location in Rivermeet
        locations = [
            "The Drowned Rat Tavern", "The Cliffside Catacombs", "The Rusty Bridge",
            "The Moonlit Market", "The Fisherman's Guild", "The Abandoned Lighthouse",
            "The Glassblade Forge", "The Temple of the Whispering Dawn", "The Sewer Grate #13",
            "The Governor's Vineyard"
        ]
        selected_location = random.choice(locations)
        
        # 3. Select a problem
        problems = [
            "A doppelgänger has replaced a key NPC",
            "A cursed item is causing townsfolk to vanish",
            "A rival adventuring party is sabotaging the PCs",
            "A smuggler's ship is carrying a deadly secret",
            "A noble is secretly a vampire spawn",
            "A child's imaginary friend is actually a fey spirit",
            "A local gang is extorting businesses",
            "A druid is poisoning the river to drive humans out",
            "A ghost demands justice for an unsolved murder",
            "A mimic colony has infested a building"
        ]
        selected_problem = random.choice(problems)
        
        # 4. Select skills to test (3 skills)
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Thieves' Tools / Lockpicking"
        ]
        selected_skills = random.sample(skills, 3)
        
        # Create scenario prompt
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        # Generate descriptions for the choices
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        # Randomly determine which choice leads to success (0-indexed)
        success_choice = random.randint(0, 2)
        
        # Generate detailed outcomes for each choice
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _forest_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Whispering Forest"""
        # Forest NPCs
        npcs = [
            "Elara the Dryad", "Thorne the Ranger", "Wispling the Sprite",
            "Elder Oakroot", "The Whispering Wind", "Silverbranch the Treant",
            "Mossback the Hermit", "The Forest Witch", "Glimmerlight the Willo-wisp",
            "Grumblefoot the Fungal Goblin"
        ]
        
        # Forest locations
        locations = [
            "The Ancient Oak Circle", "The Whispering Hollow", "The Mushroom Glade", 
            "The Forgotten Elven Ruins", "The Spider's Web Clearing", "The Luminous Pool",
            "The Twisted Thicket", "The Misty Grove", "The Hunter's Lodge",
            "The Faerie Ring"
        ]
        
        # Forest problems
        problems = [
            "A blight is spreading through the trees",
            "Fey creatures are kidnapping travelers",
            "A gateway to the Feywild is leaking chaotic magic",
            "A logging operation threatens a sacred grove",
            "Ancient forest guardians have awakened aggressively",
            "A druid circle has gone feral",
            "Undead animals stalk the paths at night",
            "A forgotten curse is twisting wildlife into monsters",
            "Plant creatures are attacking travelers",
            "The seasons are changing too rapidly"
        ]
        
        # Create scenario similar to Rivermeet but with forest theme
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills (same as Rivermeet)
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Nature / Herbalism Kit"  # Replaced lockpicking with nature/herbalism for forest
        ]
        selected_skills = random.sample(skills, 3)
        
        # Create scenario prompt
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        # Generate descriptions for the choices
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        # Randomly determine which choice leads to success (0-indexed)
        success_choice = random.randint(0, 2)
        
        # Generate detailed outcomes for each choice
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _mountain_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Dragonclaw Mountains"""
        # Mountain NPCs
        npcs = [
            "Krag the Stone Giant", "Grimbeard the Dwarf Prospector", "Skyshriek the Harpy",
            "Avalanche the Goliath Chief", "Stormcaller the Dragon Shaman", "Rimewind the Ice Witch",
            "Granitefoot the Mountain Hermit", "Cloudwatcher the Oracle", "Rockslide the Earth Elemental",
            "Peakwhisper the Griffon Rider"
        ]
        
        # Mountain locations
        locations = [
            "The Frozen Summit", "The Dragon's Lair", "The Abandoned Mine", 
            "The Precarious Bridge", "The Hot Springs Cavern", "The Eagle's Eyrie",
            "The Dwarven Outpost", "The Rockslide Path", "The Mountain Shrine",
            "The Crystal Overlook"
        ]
        
        # Mountain problems
        problems = [
            "A young dragon is terrorizing mountain villages",
            "Avalanches are being caused by something magical",
            "A lost dwarven treasure has been discovered",
            "Mountain tribes are gathering for war",
            "An ancient tomb has been uncovered by erosion",
            "Storm clouds gather unnaturally around a peak",
            "Miners have dug too deep and awakened something",
            "A rare magical crystal is causing strange effects",
            "Giant eagles are stealing livestock and people",
            "The mountain pass has been mysteriously sealed"
        ]
        
        # Create scenario with mountain theme
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills (same base with some mountain specifics)
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Smith's Tools / Climber's Kit"  # Mountain-appropriate skills
        ]
        selected_skills = random.sample(skills, 3)
        
        # Similar structure as the other locations
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _cave_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Crystal Caves"""
        # Cave NPCs
        npcs = [
            "Glimmer the Crystal Keeper", "Darkeye the Blind Seer", "Echofinder the Bat Whisperer",
            "Deepdelver the Miner", "Stalagmite the Stone Dwarf", "Shimmergleam the Gem Dragon",
            "Crystalspinner the Spider Queen", "Umbrashade the Dark Elf", "Glowmold the Fungal Being",
            "Rockbiter the Galeb Duhr"
        ]
        
        # Cave locations
        locations = [
            "The Crystal Chamber", "The Underground Lake", "The Luminous Fungi Grove", 
            "The Narrow Passage", "The Bottomless Chasm", "The Echoing Gallery",
            "The Gemstone Deposit", "The Ancient Inscriptions", "The Subterranean River",
            "The Guardian Statues"
        ]
        
        # Cave problems
        problems = [
            "Crystals are absorbing magic from visitors",
            "A rare crystal formation predicts disaster",
            "Underground tremors threaten to collapse passages",
            "Ancient cave drawings come to life when touched",
            "A lost expedition has become trapped",
            "Crystal growths are spreading too rapidly",
            "Bizarre cave creatures are emerging from deeper tunnels",
            "An underground civilization claims ownership of the caves",
            "The water source has become tainted by something",
            "Strange echoes are disorienting explorers"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Jeweler's Tools / Miner's Tools",
            "Darkvision / Tremorsense"  # Cave-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _swamp_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Shadowmire Swamp"""
        # Swamp NPCs
        npcs = [
            "Murkwater the Lizardfolk Shaman", "Witherleaf the Hag", "Croaktongue the Bullywug Chief",
            "Bogstench the Troll", "Mossback the Tortoise Sage", "Slimescale the Black Dragon",
            "Fogweaver the Will-o'-Wisp", "Rotroot the Myconid", "Miremind the Yuan-ti",
            "Dampwick the Swamp Hermit"
        ]
        
        # Swamp locations
        locations = [
            "The Sunken Temple", "The Witch's Hut", "The Rotting Tree", 
            "The Bubbling Pools", "The Foggy Crossroads", "The Ancient Burial Mound",
            "The Serpent's Lair", "The Mossy Ruins", "The Quicksand Pit",
            "The Croaking Hollow"
        ]
        
        # Swamp problems
        problems = [
            "A curse is turning people into swamp creatures",
            "Ancient ruins are rising from the bog",
            "The water is being corrupted by dark magic",
            "Swamp gas causes hallucinations and madness",
            "A territorial beast is attacking travelers",
            "Undead are rising from poorly buried graves",
            "Poisonous plants are spreading beyond the swamp",
            "A lost artifact calls monsters to its location",
            "Rival factions of swamp dwellers are at war",
            "Strange lights lead travelers to their doom"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Herbalism Kit / Poisoner's Kit",
            "Nature / Swimming"  # Swamp-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _ruins_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Forgotten Ruins"""
        # Ruins NPCs
        npcs = [
            "Dustwalker the Archaeologist", "Timeworn the Ghost", "Runekeeper the Wizard",
            "Stonefist the Guardian Golem", "Cryptreader the Scholar", "Bindingbreaker the Warlock",
            "Trapmaster the Kobold", "Pastecho the Oracle", "Relicseeker the Collector",
            "Gravedigger the Necromancer"
        ]
        
        # Ruins locations
        locations = [
            "The Collapsed Grand Hall", "The Sealed Vault", "The Crumbling Tower", 
            "The Ancient Library", "The Sacrificial Chamber", "The Throne Room",
            "The Underground Catacombs", "The Arcane Laboratory", "The Overgrown Courtyard",
            "The Broken Portal"
        ]
        
        # Ruins problems
        problems = [
            "Ancient constructs are reactivating",
            "A sealed evil is breaking free",
            "A temporal anomaly shows glimpses of the past",
            "A cursed artifact seeks a new owner",
            "The ruins are slowly rebuilding themselves",
            "Tomb raiders have disturbed something dangerous",
            "Dimensional rifts are forming in weakened areas",
            "Ancient traps are still deadly and active",
            "The ghosts of former inhabitants seek resolution",
            "Rival expeditions are fighting over discoveries"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Thieves' Tools / Ancient Languages"  # Ruins-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _plains_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Sunlit Plains"""
        # Plains NPCs
        npcs = [
            "Windrunner the Centaur", "Goldgrain the Halfling Farmer", "Skygazer the Astronomer",
            "Stampede the Minotaur Nomad", "Seedsower the Druid", "Grasswhisper the Ranger",
            "Dustcloud the Earth Genasi", "Herdmaster the Shepherd", "Sunflare the Fire Priest",
            "Longstride the Horse Tamer"
        ]
        
        # Plains locations
        locations = [
            "The Standing Stones", "The Nomad Camp", "The Lone Tree", 
            "The Ancient Battlefield", "The Trading Crossroads", "The Oracle's Tent",
            "The Wild Horse Plains", "The Burial Mounds", "The Hidden Valley",
            "The Harvest Festival"
        ]
        
        # Plains problems
        problems = [
            "Unusual weather patterns are destroying crops",
            "Nomadic tribes are gathering for an unknown purpose",
            "Strange marks appearing in fields overnight",
            "A legendary beast has been spotted after centuries",
            "Raiders are targeting isolated farmsteads",
            "The earth itself seems to be moving or changing",
            "Ancient burial sites are being disturbed",
            "A meteor has crashed with strange effects",
            "Spirits of fallen warriors rise at dusk",
            "Refugees are fleeing from something in the east"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Nature / Farming"  # Plains-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _frostpeak_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Frostpeak Village"""
        # Frostpeak NPCs
        npcs = [
            "Icebeard the Village Elder", "Frostbloom the Alchemist", "Snowdancer the Shaman",
            "Chillfist the Tavern Owner", "Rimeheart the Healer", "Blizzardcaller the Sorcerer",
            "Northwind the Cartographer", "Coldforge the Blacksmith", "Winterwhisper the Fortune Teller",
            "Frostclaw the Hunter"
        ]
        
        # Frostpeak locations
        locations = [
            "The Frozen Hearth Inn", "The Ice Chapel", "The Lookout Tower", 
            "The Hot Springs", "The Trading Post", "The Elder's Lodge",
            "The Slippery Path", "The Avalanche Pass", "The Frozen Lake",
            "The Winter Festival Grounds"
        ]
        
        # Frostpeak problems
        problems = [
            "Winter has lasted too long - something magical is causing it",
            "Frost giants are threatening the village",
            "An ice elemental is freezing villagers",
            "Supplies are running dangerously low",
            "A hibernating monster has awakened early",
            "Someone is selling fake protective charms",
            "Children have gone missing during a blizzard",
            "An ancient prophecy about eternal winter is coming true",
            "A mysterious illness is spreading among villagers",
            "A rival village has stolen an important artifact"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Cold Resistance / Brewing"  # Frostpeak-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _sea_scenarios(self) -> Dict[str, Any]:
        """Generate scenarios specific to Emerald Sea"""
        # Sea NPCs
        npcs = [
            "Captain Waverider", "Coral the Mermaid", "Deepcurrent the Triton",
            "Saltbeard the Old Sailor", "Tidecaller the Sea Witch", "Stormchaser the Navigator",
            "Pearlseeker the Diver", "Krakenfriend the Sea Warlock", "Wavesong the Siren",
            "Driftwood the Shipwright"
        ]
        
        # Sea locations
        locations = [
            "The Merchant Fleet", "The Sunken Temple", "The Pirate Cove", 
            "The Coral Reef", "The Whirlpool", "The Sea Caves",
            "The Ghost Ship", "The Trading Port", "The Island Lighthouse",
            "The Underwater Grotto"
        ]
        
        # Sea problems
        problems = [
            "A sea monster is attacking ships",
            "A terrible storm won't dissipate",
            "Sirens are luring sailors to their doom",
            "A cursed treasure has been recovered",
            "Pirates are blockading an important trade route",
            "The tide hasn't changed in days",
            "Sea creatures are fleeing from something in the deep",
            "A ghost ship appears only in the fog",
            "An underwater civilization has made contact",
            "A magical whirlpool is growing larger"
        ]
        
        # Create scenario
        npc_count = 2 if random.random() < 0.1 else 1
        selected_npcs = random.sample(npcs, npc_count)
        selected_location = random.choice(locations)
        selected_problem = random.choice(problems)
        
        # Skills
        skills = [
            "Persuasion / Deception", "Stealth / Sleight of Hand", "Investigation / Arcana",
            "Intimidation / Insight", "Athletics / Acrobatics", "Survival / Animal Handling",
            "Religion / History", "Medicine / Perception", "Performance / Disguise Kit",
            "Navigator's Tools / Swimming"  # Sea-specific skills
        ]
        selected_skills = random.sample(skills, 3)
        
        npc_string = " and ".join(selected_npcs)
        skill_string = ", ".join(selected_skills)
        prompt = f"Generate a scenario that involves {npc_string}, {selected_location}, and {selected_problem}. The choices should involve {skill_string}."
        
        choice_descriptions = []
        for skill in selected_skills:
            skill_parts = skill.split(" / ")
            main_skill = skill_parts[0]
            choice_descriptions.append(f"Use {main_skill} to handle the situation")
        
        success_choice = random.randint(0, 2)
        
        outcomes = []
        for i, choice in enumerate(choice_descriptions):
            if i == success_choice:
                outcomes.append(f"{i+1}. ✅ Success! Using {selected_skills[i]} worked perfectly.")
            else:
                outcomes.append(f"{i+1}. ❌ Failure! Using {selected_skills[i]} backfired.")
        
        return {
            "prompt": prompt,
            "npcs": selected_npcs,
            "location": selected_location,
            "problem": selected_problem,
            "skills": selected_skills,
            "choices": [f"{i+1}. {desc}" for i, desc in enumerate(choice_descriptions)],
            "outcomes": outcomes,
            "success_index": success_choice
        }
    
    def _default_scenarios(self) -> Dict[str, Any]:
        """Default scenario generator for locations without specific implementations"""
        # This method will be expanded by you later
        # For now, it creates a basic scenario using the Rivermeet template
        return self._rivermeet_scenarios()