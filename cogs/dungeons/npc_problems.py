import random
from typing import Dict, List, Any, Optional

class NPCProblemManager:
    """Manages NPC problems and encounters in dungeons"""
    
    def __init__(self):
        # Load NPC problems data
        self.npcs = self._load_npc_data()
        self.problems = self._load_problem_data()
        self.locations = self._load_location_data()
    
    def _load_npc_data(self) -> List[str]:
        """Load NPC types that can be encountered"""
        return [
            # Humanoids
            "An old dwarf miner",
            "A wounded human soldier",
            "A lost elven scholar",
            "A suspicious halfling",
            "A trapped goblin",
            "A mysterious hooded figure",
            "A half-orc merchant",
            "An eccentric gnome tinkerer",
            "A stern dwarven guard",
            "A frantic human messenger",
            
            # Dungeon denizens
            "A friendly ghost",
            "A talking gargoyle",
            "A chained mimic",
            "A wounded fairy",
            "A cursed spirit",
            "An animated statue",
            "A sentient slime",
            "A trapped elemental",
            "A lost homunculus",
            "A dungeon keeper",
            
            # Magical beings
            "An injured familiar",
            "A mischievous imp",
            "A trapped genie",
            "A forgetful wizard",
            "An ethereal messenger",
            "A dimensional traveler",
            "A fallen angel",
            "A mysterious oracle",
            "A spectral librarian",
            "A time-displaced scholar"
        ]
    
    def _load_problem_data(self) -> List[Dict[str, Any]]:
        """Load problem scenarios that NPCs can present"""
        return [
            {
                "problem": "is trapped under a fallen pillar and begs for your help.",
                "choices": [
                    {
                        "text": "Help free them from the pillar",
                        "skill": "Strength",
                        "skill_dc": 12,
                        "success_outcome": "You successfully lift the pillar, freeing the trapped creature who rewards you with valuable information about the dungeon ahead.",
                        "failure_outcome": "Despite your efforts, the pillar is too heavy. The creature suggests trying to find a lever nearby that might help."
                    },
                    {
                        "text": "Search for a lever or mechanical way to lift the pillar",
                        "skill": "Investigation",
                        "skill_dc": 14,
                        "success_outcome": "You discover a hidden mechanism that safely lifts the pillar. The grateful creature shares some valuable treasure with you.",
                        "failure_outcome": "You can't find any mechanism to help. The creature suggests using brute strength instead."
                    },
                    {
                        "text": "Suspect a trap and refuse to help",
                        "skill": "Insight",
                        "skill_dc": 16,
                        "success_outcome": "Your instincts were right - it was an elaborate ruse. You avoid the trap and the creature slithers away, dropping a valuable item in its haste.",
                        "failure_outcome": "Your suspicion was misplaced. The genuine plea for help goes unanswered, and you miss an opportunity for alliance."
                    }
                ]
            },
            {
                "problem": "offers to trade a mysterious artifact for medical supplies.",
                "choices": [
                    {
                        "text": "Provide medical assistance",
                        "skill": "Medicine",
                        "skill_dc": 13,
                        "success_outcome": "Your medical expertise proves invaluable. The grateful creature gives you the artifact and additional information about its powers.",
                        "failure_outcome": "Your medical skills are insufficient. The creature seems worse after your attempt, but still reluctantly trades the artifact."
                    },
                    {
                        "text": "Examine the artifact before agreeing",
                        "skill": "Arcana",
                        "skill_dc": 15,
                        "success_outcome": "You identify the artifact as a valuable magical item. You trade fairly and both parties leave satisfied.",
                        "failure_outcome": "You can't determine the artifact's value. You make the trade anyway, unsure if you got a good deal."
                    },
                    {
                        "text": "Negotiate for more information",
                        "skill": "Persuasion",
                        "skill_dc": 14,
                        "success_outcome": "Your silver tongue convinces them to tell you about a hidden treasure room on this floor before making the trade.",
                        "failure_outcome": "Your attempts at negotiation make them suspicious. They withdraw the offer and shuffle away nervously."
                    }
                ]
            },
            {
                "problem": "guards a door and will only let you pass by solving a riddle.",
                "choices": [
                    {
                        "text": "Listen to and solve the riddle",
                        "skill": "Intelligence",
                        "skill_dc": 15,
                        "success_outcome": "You solve the riddle with ease. Impressed, the guardian not only lets you pass but gives you a valuable clue about what lies ahead.",
                        "failure_outcome": "The riddle stumps you. The guardian allows you another approach, but seems disappointed."
                    },
                    {
                        "text": "Intimidate the guardian to let you pass",
                        "skill": "Intimidation",
                        "skill_dc": 16,
                        "success_outcome": "Your fearsome demeanor makes the guardian reconsider the riddle policy. It steps aside nervously, letting you pass without trouble.",
                        "failure_outcome": "Your attempt at intimidation fails miserably. The guardian seems amused and now requires you to solve two riddles."
                    },
                    {
                        "text": "Search for another way around",
                        "skill": "Perception",
                        "skill_dc": 14,
                        "success_outcome": "You notice a small hidden passage nearby that bypasses the door entirely. The guardian doesn't even notice you slipping past.",
                        "failure_outcome": "After wasting time searching, you find no alternative route. The guardian still waits with its riddle, now seeming more smug."
                    }
                ]
            },
            {
                "problem": "is being attacked by dungeon monsters and cries for help.",
                "choices": [
                    {
                        "text": "Charge in to help fight the monsters",
                        "skill": "Strength",
                        "skill_dc": 14,
                        "success_outcome": "You drive off the monsters with your combat prowess. The grateful creature rewards you with a valuable trinket.",
                        "failure_outcome": "The monsters are tougher than expected. Though you eventually prevail, both you and the creature are wounded in the process."
                    },
                    {
                        "text": "Create a distraction to help them escape",
                        "skill": "Dexterity",
                        "skill_dc": 13,
                        "success_outcome": "Your clever distraction allows both of you to escape unharmed. The creature thanks you and offers information about nearby treasure.",
                        "failure_outcome": "Your distraction fails to draw away all the monsters. You still need to fight, but the creature manages to escape in the confusion."
                    },
                    {
                        "text": "Observe first to determine if it's a trap",
                        "skill": "Insight",
                        "skill_dc": 15,
                        "success_outcome": "Your caution reveals the 'attack' is staged. You confront the would-be trickster, who surrenders a valuable item rather than face your wrath.",
                        "failure_outcome": "While you hesitate, the situation worsens. When you finally intervene, the creature is wounded but still grateful for your help."
                    }
                ]
            },
            {
                "problem": "offers to reveal a secret passage in exchange for help finding a lost item.",
                "choices": [
                    {
                        "text": "Agree to help find the item",
                        "skill": "Investigation",
                        "skill_dc": 14,
                        "success_outcome": "Your careful search finds the lost item quickly. The grateful being shows you a secret passage that bypasses many dungeon hazards.",
                        "failure_outcome": "After much time searching, you cannot find the item. The being reluctantly gives you vague directions, but no secret passage."
                    },
                    {
                        "text": "Use magic or special skills to locate the item faster",
                        "skill": "Arcana",
                        "skill_dc": 15,
                        "success_outcome": "Your magical insight leads you straight to the item. Impressed by your abilities, the being reveals not one but two secret routes.",
                        "failure_outcome": "Your magical approach fails to locate the item. You'll need to resort to a manual search or try another approach."
                    },
                    {
                        "text": "Persuade them to reveal the passage first",
                        "skill": "Persuasion",
                        "skill_dc": 16,
                        "success_outcome": "Your compelling argument convinces them to show you the passage first as a sign of good faith. You can still choose to help afterward.",
                        "failure_outcome": "They refuse your proposal, insisting on finding the item first. Your negotiation has only made them more stubborn."
                    }
                ]
            },
            {
                "problem": "is wounded and asks for your help deciphering an ancient text that might contain a healing spell.",
                "choices": [
                    {
                        "text": "Try to decipher the text",
                        "skill": "History",
                        "skill_dc": 15,
                        "success_outcome": "You successfully translate the text, revealing a powerful healing ritual. After healing the being, they teach you the spell as well.",
                        "failure_outcome": "The text proves too obscure for your knowledge. The being suggests another approach to their problem."
                    },
                    {
                        "text": "Use your own medical knowledge to help",
                        "skill": "Medicine",
                        "skill_dc": 13,
                        "success_outcome": "Your medical expertise proves more practical than any spell. The healed being gratefully shares a valuable secret about the dungeon.",
                        "failure_outcome": "Your medical treatment provides only temporary relief. The being still needs the spell, but appreciates your effort."
                    },
                    {
                        "text": "Search nearby for healing herbs or supplies",
                        "skill": "Nature",
                        "skill_dc": 14,
                        "success_outcome": "You find rare healing herbs growing in the dungeon's shadows. These prove more effective than the spell would have been.",
                        "failure_outcome": "Your search yields only common plants with minimal healing properties. The being thanks you but still needs better treatment."
                    }
                ]
            },
            {
                "problem": "challenges you to a game of skill or chance for a valuable prize.",
                "choices": [
                    {
                        "text": "Accept the game and play fair",
                        "skill": "Dexterity",
                        "skill_dc": 13,
                        "success_outcome": "Your natural skill wins the game fairly. The being congratulates you and awards a magical item as the prize.",
                        "failure_outcome": "Despite your best efforts, you lose the game. The being offers a consolation: a piece of advice about an upcoming dungeon hazard."
                    },
                    {
                        "text": "Try to bend the rules in your favor",
                        "skill": "Sleight of Hand",
                        "skill_dc": 16,
                        "success_outcome": "You subtly manipulate the game to ensure victory. The being doesn't notice your trickery and reluctantly hands over the prize.",
                        "failure_outcome": "The being catches you cheating! Furious, they refuse to give you any prize and warn other dungeon denizens about your dishonesty."
                    },
                    {
                        "text": "Analyze the game for optimal strategy",
                        "skill": "Intelligence",
                        "skill_dc": 15,
                        "success_outcome": "You quickly identify the mathematical patterns in the game and develop an unbeatable strategy, winning handily.",
                        "failure_outcome": "The game proves more complex than you anticipated. Your overthinking leads to a loss, though the being offers to teach you the correct strategy."
                    }
                ]
            },
            {
                "problem": "is magically bound to the dungeon and begs for help breaking the curse.",
                "choices": [
                    {
                        "text": "Attempt to dispel the magic directly",
                        "skill": "Arcana",
                        "skill_dc": 17,
                        "success_outcome": "Your magical knowledge allows you to unravel the binding spell. The freed being rewards you with a powerful magical artifact.",
                        "failure_outcome": "The curse resists your attempts to dispel it. The being suggests seeking specific components that might help break the curse."
                    },
                    {
                        "text": "Research the curse using nearby runes and tomes",
                        "skill": "Investigation",
                        "skill_dc": 15,
                        "success_outcome": "Your research reveals the curse's weakness. Following the discovered method breaks the spell easily, earning you a grateful ally.",
                        "failure_outcome": "The available information is insufficient to understand the curse fully. You'll need another approach or more specific knowledge."
                    },
                    {
                        "text": "Offer to deliver a message to someone outside who can help",
                        "skill": "Persuasion",
                        "skill_dc": 13,
                        "success_outcome": "The being trusts you with a message and a token for someone who can help later. They also share valuable dungeon secrets as a down payment.",
                        "failure_outcome": "The being doesn't trust you enough for this task. They withdraw their request, preferring to wait for someone they deem more trustworthy."
                    }
                ]
            },
            {
                "problem": "claims to be lost and asks for directions to escape the dungeon.",
                "choices": [
                    {
                        "text": "Offer to guide them to safety",
                        "skill": "Survival",
                        "skill_dc": 14,
                        "success_outcome": "Your navigational skills prove reliable. As you guide them to a safer area, they share valuable secrets about the deeper dungeon levels.",
                        "failure_outcome": "You become disoriented in the twisting passages. After wandering for some time, you both end up back where you started."
                    },
                    {
                        "text": "Draw them a map based on what you've explored",
                        "skill": "Intelligence",
                        "skill_dc": 13,
                        "success_outcome": "Your detailed map impresses them. In exchange, they mark several hidden treasures on it that you hadn't discovered yet.",
                        "failure_outcome": "Your map contains several critical errors. The being points these out, and you realize you're more lost than you thought."
                    },
                    {
                        "text": "Question their story and true intentions",
                        "skill": "Insight",
                        "skill_dc": 16,
                        "success_outcome": "Your suspicion was warranted - they're not lost at all, but testing adventurers. Impressed by your perceptiveness, they offer genuine help.",
                        "failure_outcome": "Your questioning offends them. They were genuinely lost, and now they refuse your help entirely, shuffling away in anger."
                    }
                ]
            },
            {
                "problem": "offers to sell you dungeon supplies but at suspiciously high prices.",
                "choices": [
                    {
                        "text": "Negotiate for better prices",
                        "skill": "Persuasion",
                        "skill_dc": 15,
                        "success_outcome": "Your haggling skills impress the merchant, who agrees to reasonable prices and throws in an extra item for free.",
                        "failure_outcome": "The merchant refuses to budge on their exorbitant prices. You'll need to pay full price or try another approach."
                    },
                    {
                        "text": "Intimidate them into offering fair prices",
                        "skill": "Intimidation",
                        "skill_dc": 14,
                        "success_outcome": "Your menacing presence convinces the merchant to offer fair prices immediately. They even reveal they have rarer items 'for preferred customers.'",
                        "failure_outcome": "The merchant stands firm against your threats, and calls for nearby guards. You should probably leave before things escalate."
                    },
                    {
                        "text": "Investigate why their prices are so high",
                        "skill": "Insight",
                        "skill_dc": 13,
                        "success_outcome": "You learn they're being extorted by dungeon creatures. Offering to help with this problem earns you their gratitude and wholesale prices.",
                        "failure_outcome": "Your inquiries make the merchant uncomfortable. They refuse to explain their pricing and become more guarded around you."
                    }
                ]
            }
        ]
    
    def _load_location_data(self) -> Dict[str, List[str]]:
        """Load location-specific descriptions and encounters"""
        return {
            "Rivermeet": [
                "near the entrance, where faint light still filters through",
                "in a damp corner where water trickles down the walls",
                "beside a small underground stream that flows through the dungeon",
                "near some abandoned mining equipment",
                "beside crumbling statues of forgotten heroes"
            ],
            "Shadowfen": [
                "in a section shrouded with strange, luminescent fungi",
                "near an altar with disturbing carvings",
                "in a laboratory filled with broken alchemical equipment",
                "beside a pit that drops into darkness",
                "near a wall covered in mysterious runes"
            ],
            "Ironhold": [
                "in an ancient forge that still radiates heat",
                "near massive iron doors with dwarvish inscriptions",
                "among the remains of some mechanical constructs",
                "in a treasure vault with empty pedestals",
                "beside a lava channel that provides light and heat"
            ],
            "Crystalpeak": [
                "surrounded by glowing crystals that respond to sound",
                "in a chamber where gravity seems slightly altered",
                "near a pool of water that shows strange reflections",
                "beside a crystal formation that hums with magic",
                "in a garden of petrified plants"
            ],
            "Abyssdepth": [
                "near a tear in reality that whispers madness",
                "beside an obelisk covered in eyes that follow your movement",
                "in a chamber where shadows move independently of light sources",
                "near a pit that seems to have no bottom",
                "surrounded by statues of beings with too many limbs"
            ],
            "Celestia": [
                "in a chamber filled with impossible architecture",
                "beside a floating island of earth and stone",
                "near a portal that shows glimpses of other worlds",
                "in a garden where plants grow without soil or light",
                "beneath a ceiling that appears to be the night sky"
            ]
        }
    
    def get_random_problem(self, location: str, player_level: int) -> Dict[str, Any]:
        """
        Generate a random NPC problem based on location and player level
        
        Args:
            location: Current location name
            player_level: Player's level
            
        Returns:
            Dictionary with problem data
        """
        # Get location descriptions or use default
        location_descs = self.locations.get(location, self.locations["Rivermeet"])
        location_desc = random.choice(location_descs)
        
        # Select random NPC
        npc = random.choice(self.npcs)
        
        # Select random problem
        problem_template = random.choice(self.problems)
        
        # Create full problem description with location context
        full_problem = f"{npc} {problem_template['problem']} You find them {location_desc}."
        
        # Select 3 random choices (or all if there are only 3 or fewer)
        all_choices = problem_template["choices"]
        if len(all_choices) <= 3:
            selected_choices = all_choices
        else:
            selected_choices = random.sample(all_choices, 3)
        
        # Adjust difficulty based on player level
        for choice in selected_choices:
            base_dc = choice["skill_dc"]
            # Slight adjustment for level, but not too much
            level_adjustment = min(5, max(-3, (player_level - 1) // 2 - 2))
            choice["skill_dc"] = max(5, base_dc + level_adjustment)
        
        # Determine which choices would lead to success (those with a reasonable DC)
        correct_indices = []
        for i, choice in enumerate(selected_choices):
            # For simplicity, all choices with DC <= player_level + 10 are potentially successful
            if choice["skill_dc"] <= player_level + 10:
                correct_indices.append(i)
        
        # Ensure at least one correct choice
        if not correct_indices:
            # Make the easiest choice correct
            easiest_index = min(range(len(selected_choices)), 
                               key=lambda i: selected_choices[i]["skill_dc"])
            correct_indices.append(easiest_index)
        
        # Compile the problem data
        problem_data = {
            "npc": npc,
            "problem": full_problem,
            "selected_choices": selected_choices,
            "correct_indices": correct_indices,
            "location": location,
            "location_desc": location_desc
        }
        
        return problem_data