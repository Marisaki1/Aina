import random
from typing import Dict, List, Any, Tuple

# This file contains data for NPC problems and their choices
# Format follows the specification in the requirements

class NPCProblemManager:
    """Manages NPC problems and their choices for random encounters"""
    
    def __init__(self):
        # Initialize the NPC problems database
        self.npc_problems = self._init_rivermeet_problems()
        
    def get_random_problem(self, location: str, player_level: int) -> Dict[str, Any]:
        """Get a random problem for the specified location and player level"""
        if location not in self.npc_problems:
            location = "Rivermeet"  # Default to Rivermeet if location not found
            
        # Get all NPCs for the location
        npcs = list(self.npc_problems[location].keys())
        
        # Select a random NPC
        selected_npc = random.choice(npcs)
        
        # Get all problems for the NPC
        problems = self.npc_problems[location][selected_npc]
        
        # Select a random problem
        selected_problem = random.choice(problems)
        
        # Copy the problem to avoid modifying the original
        problem_copy = selected_problem.copy()
        
        # Add NPC name to the problem
        problem_copy["npc"] = selected_npc
        
        # Get selection pattern based on player level and location
        correct_choices = self._get_correct_choices_count(location, player_level)
        
        # Select choices based on the correct_choices count
        choices, correct_indices = self._select_choices(problem_copy["choices"], 
                                                       correct_choices)
        
        problem_copy["selected_choices"] = choices
        problem_copy["correct_indices"] = correct_indices
        
        return problem_copy
    
    def _get_correct_choices_count(self, location: str, player_level: int) -> int:
        """Determine how many correct choices to include based on location and player level"""
        if location == "Rivermeet":
            if 1 <= player_level <= 3:
                return 1
            elif 4 <= player_level <= 6:
                return 2
            else:  # 7-9
                return 3
        
        # Default for other locations
        return 1
    
    def _select_choices(self, all_choices: Dict, correct_count: int) -> Tuple[List, List]:
        """
        Select 3 choices from all_choices, ensuring correct_count correct choices.
        Returns tuple of (selected choices, indices of correct choices)
        """
        # Separate correct and incorrect choices
        correct_choices = all_choices["correct"]
        incorrect_choices = all_choices["incorrect"]
        
        # Ensure we have enough choices
        if len(correct_choices) < correct_count:
            correct_count = len(correct_choices)
        
        if len(incorrect_choices) < (3 - correct_count):
            # Not enough incorrect choices, adjust correct_count
            incorrect_sample_count = len(incorrect_choices)
            correct_count = 3 - incorrect_sample_count
        else:
            incorrect_sample_count = 3 - correct_count
        
        # Select random correct and incorrect choices
        selected_correct = random.sample(correct_choices, correct_count)
        selected_incorrect = random.sample(incorrect_choices, incorrect_sample_count)
        
        # Combine and shuffle
        all_selected = selected_correct + selected_incorrect
        random.shuffle(all_selected)
        
        # Find indices of correct choices in the shuffled list
        correct_indices = [i for i, choice in enumerate(all_selected) if choice in selected_correct]
        
        return all_selected, correct_indices
    
    def _init_rivermeet_problems(self) -> Dict:
        """Initialize the Rivermeet NPC problems"""
        return {
            "Rivermeet": {
                "Mayor Thadrick Goldvein": [
                    {
                        "problem": "The mayor is hosting a foreign dignitary, but he's worried his lack of etiquette will embarrass the town.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Persuasion",
                                    "text": "Offer to act as the mayor's advisor during the dignitary's visit.",
                                    "skill_dc": 12,
                                    "success_outcome": "Your diplomatic expertise helps the mayor navigate the complex social situation. The dignitary is impressed by Rivermeet's hospitality and leadership.",
                                    "failure_outcome": "Your advice causes a cultural misunderstanding. The dignitary takes offense at what they perceive as rudeness, damaging relations with their homeland."
                                },
                                {
                                    "skill": "History",
                                    "text": "Research the dignitary's culture and prepare a briefing for the mayor.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your thorough research allows the mayor to impress the dignitary with his knowledge of their customs. The visit becomes a great success for Rivermeet.",
                                    "failure_outcome": "Your research contains critical errors about the dignitary's culture. The mayor unknowingly commits several grave insults, ruining the diplomatic visit."
                                },
                                {
                                    "skill": "Performance",
                                    "text": "Arrange entertainment that will distract from any social blunders.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your spectacular entertainment captivates the dignitary. They're so impressed by the cultural showcase that they hardly notice the mayor's occasional faux pas.",
                                    "failure_outcome": "Your entertainment choice is considered offensive in the dignitary's culture. They leave early, and rumors spread about Rivermeet's insensitivity."
                                },
                                {
                                    "skill": "Deception",
                                    "text": "Create a cover story about the mayor being ill and offer to stand in for him.",
                                    "skill_dc": 15,
                                    "success_outcome": "You successfully impersonate an official representative and charm the dignitary completely. The mayor is relieved and rewards your quick thinking.",
                                    "failure_outcome": "Your deception is discovered, embarrassing both you and the mayor. The dignitary takes it as an insult that the mayor didn't meet them personally."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest the mayor cancel the meeting, claiming urgent town business.",
                                    "outcome": "The dignitary takes great offense at the last-minute cancellation. Relations with their homeland suffer, potentially affecting trade for Rivermeet."
                                },
                                {
                                    "text": "Tell the mayor to 'just be himself' without any preparation.",
                                    "outcome": "Without proper guidance, the mayor commits numerous social blunders. The dignitary leaves with a poor impression of Rivermeet's leadership."
                                },
                                {
                                    "text": "Spike the dignitary's drink to make them too intoxicated to notice etiquette errors.",
                                    "outcome": "Your plan backfires horribly when the dignitary's food taster becomes ill. You're accused of attempted poisoning, causing a diplomatic incident."
                                },
                                {
                                    "text": "Suggest hiring actors to pretend to be town officials instead.",
                                    "outcome": "The poorly rehearsed actors are quickly exposed as frauds. The dignitary is insulted by this deception and leaves immediately."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "Tax records have gone missing and Mayor Goldvein suspects foul play.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Investigation",
                                    "text": "Examine the records office for clues about the missing documents.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your careful investigation reveals that the records were misfiled rather than stolen. You recover all the missing documents, earning the mayor's gratitude.",
                                    "failure_outcome": "You overlook crucial evidence and come to incorrect conclusions. The records remain missing, and suspicion falls on innocent townspeople."
                                },
                                {
                                    "skill": "Insight",
                                    "text": "Interview the clerk who last handled the records to determine if they're hiding something.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your perceptive questioning reveals that the clerk accidentally spilled ink on the records and hid them out of fear. The records are recovered with minimal damage.",
                                    "failure_outcome": "You misread the clerk's nervous behavior as guilt when they were actually innocent. The true culprit remains at large while suspicion falls on the wrong person."
                                },
                                {
                                    "skill": "Sleight of Hand",
                                    "text": "Search the mayor's office when he's not looking - perhaps he misplaced them himself.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your discreet search discovers the records tucked inside a book the mayor had been reading. You return them without embarrassing him, earning his private thanks.",
                                    "failure_outcome": "The mayor catches you going through his private papers. He accuses you of being the thief, damaging your reputation in Rivermeet."
                                },
                                {
                                    "skill": "Perception",
                                    "text": "Carefully observe the records room to spot anything out of place.",
                                    "skill_dc": 12,
                                    "success_outcome": "Your keen eye notices a corner of parchment sticking out from behind a bookshelf. The missing records had slipped behind it during cleaning.",
                                    "failure_outcome": "You miss obvious clues despite your careful observation. The records remain missing, and the mayor loses faith in your abilities."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Accuse the mayor's political rival publicly without evidence.",
                                    "outcome": "Your baseless accusation creates a scandal. The mayor distances himself from you, and his rival threatens legal action for defamation."
                                },
                                {
                                    "text": "Suggest creating new records from memory instead of finding the originals.",
                                    "outcome": "Recreating tax records without accurate information causes chaos. Several citizens are incorrectly taxed, leading to protests outside the town hall."
                                },
                                {
                                    "text": "Recommend hiring an expensive specialist from another city to find the records.",
                                    "outcome": "The specialist takes a large advance payment then disappears with the money. The mayor holds you partially responsible for the wasted town funds."
                                },
                                {
                                    "text": "Suggest that this is a sign from the gods to abolish taxes altogether.",
                                    "outcome": "The mayor is appalled by your suggestion. He questions your judgment and asks you to stay away from town administrative matters in the future."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "The mayor needs to decide which of two influential families should receive the contract to rebuild the town bridge.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Persuasion",
                                    "text": "Convince both families to work together on the project and share the credit.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your diplomatic approach brings the feuding families together. The bridge is built stronger with their combined expertise, and public opinion of both families improves.",
                                    "failure_outcome": "Your attempt to mediate backfires as the families become even more competitive. The project is delayed as they refuse to cooperate in any way."
                                },
                                {
                                    "skill": "Investigation",
                                    "text": "Research both families' previous work to find objective criteria for the decision.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your thorough research reveals that one family has superior experience with bridge building. The mayor makes a decision based on merit rather than politics.",
                                    "failure_outcome": "Your research misses critical flaws in one family's previous projects. When the mayor awards them the contract based on your recommendation, the other family publicly reveals these issues."
                                },
                                {
                                    "skill": "Deception",
                                    "text": "Tell each family that the other has agreed to certain compromises, facilitating an agreement.",
                                    "skill_dc": 16,
                                    "success_outcome": "Your clever manipulations lead both families to believe they've outmaneuvered the other. By the time they realize what's happened, the contract is signed and cooperation is established.",
                                    "failure_outcome": "Your lies are quickly discovered when the families compare notes. Both now distrust the mayor and you, making future town projects even more difficult."
                                },
                                {
                                    "skill": "Insight",
                                    "text": "Speak with family members privately to understand their true motivations beyond money.",
                                    "skill_dc": 13,
                                    "success_outcome": "You discover that one family cares more about prestige while the other needs the financial security. You broker a deal where one gets prominent credit while the other receives better payment terms.",
                                    "failure_outcome": "You misinterpret the families' true motives, leading to a proposal that offends both parties. The conflict intensifies, and the bridge project stalls indefinitely."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest awarding the contract to an outside company to avoid choosing between the families.",
                                    "outcome": "Both families unite against the outsider and sabotage their work. The bridge project fails, and the town's economy suffers."
                                },
                                {
                                    "text": "Advise the mayor to flip a coin to make the decision completely random.",
                                    "outcome": "The 'random' approach is seen as dismissive of both families' qualifications. They lose respect for the mayor, and political tensions in town escalate."
                                },
                                {
                                    "text": "Recommend the mayor take bribes from both families and give the contract to the highest bidder.",
                                    "outcome": "Word of the corruption spreads quickly. The mayor's reputation is ruined, and a town investigation is launched into his previous dealings."
                                },
                                {
                                    "text": "Suggest postponing the bridge project until the next mayor's term.",
                                    "outcome": "The delay causes significant economic harm to Rivermeet. Citizens who depend on the bridge for their livelihoods blame the mayor for his indecision."
                                }
                            ]
                        }
                    }
                ],
                "Sister Maribel": [
                    {
                        "problem": "The temple's holy relic has been stolen, and Sister Maribel is desperate to recover it before the high priest returns.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Investigation",
                                    "text": "Search the temple grounds methodically for clues about the thief.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your thorough investigation reveals footprints and a torn piece of cloth. Following these clues leads you to a local collector of religious artifacts who bought the relic not knowing it was stolen.",
                                    "failure_outcome": "Despite your efforts, you overlook crucial evidence. The high priest returns before you can recover the relic, and Sister Maribel faces serious consequences."
                                },
                                {
                                    "skill": "Religion",
                                    "text": "Perform a ritual to divine the location of the sacred object.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your devout ritual produces a vision showing the relic hidden in the hollow of an old tree just outside town. You recover it and return it before anyone notices it was missing.",
                                    "failure_outcome": "The ritual backfires due to an error in your performance. The temple guardian spirits are offended, causing minor supernatural disturbances throughout the temple."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Spread word that returning the relic anonymously will bring divine blessing.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your inspiring message about forgiveness and blessing reaches the thief. The relic appears mysteriously on the temple doorstep the next morning.",
                                    "failure_outcome": "Your message is misinterpreted as offering a reward, bringing numerous false claims and counterfeit relics from opportunists hoping for payment."
                                },
                                {
                                    "skill": "Perception",
                                    "text": "Keep watch near the temple to see if the thief returns to the scene.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your vigilance pays off when you notice a suspicious figure examining the temple's side entrance at night. You follow them to their hideout and recover the relic.",
                                    "failure_outcome": "You spend several fruitless nights watching the wrong areas. The high priest returns, discovers the theft, and Sister Maribel is removed from her position."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest replacing the relic with a convincing fake until the real one can be found.",
                                    "outcome": "The high priest immediately recognizes the forgery upon his return. Sister Maribel is disciplined for attempting to deceive him and cover up the theft."
                                },
                                {
                                    "text": "Accuse another temple acolyte without evidence to deflect suspicion.",
                                    "outcome": "Your false accusation creates discord within the temple. The accused acolyte is deeply hurt, and Sister Maribel's reputation suffers when the truth eventually emerges."
                                },
                                {
                                    "text": "Advise Sister Maribel to deny any knowledge of the relic's existence.",
                                    "outcome": "The high priest is bewildered by her strange behavior. When he presents records clearly mentioning the relic, her deception is exposed, making the situation much worse."
                                },
                                {
                                    "text": "Suggest blaming the theft on a fictional group of traveling bandits.",
                                    "outcome": "The town guard takes the bandit threat seriously and wastes resources searching the surrounding area. When no bandits are found, questions turn back to the temple's security practices."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "Sister Maribel needs to perform a healing ritual for a dying child but lacks a rare herb required for the ceremony.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Nature",
                                    "text": "Search the nearby forest for a substitute herb with similar properties.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your knowledge of plants helps you identify a rare fungus with properties similar to the needed herb. The adapted ritual works, and the child begins to recover.",
                                    "failure_outcome": "The substitute plant you choose has unexpected side effects. While the child's original illness improves, new complications arise from your herbal mistake."
                                },
                                {
                                    "skill": "Medicine",
                                    "text": "Modify the ritual to work without the herb by strengthening other components.",
                                    "skill_dc": 16,
                                    "success_outcome": "Your medical expertise allows you to recalibrate the ritual ingredients. The modified ceremony successfully heals the child, earning Sister Maribel's profound gratitude.",
                                    "failure_outcome": "Your modifications unbalance the ritual's energy. Though you manage to stabilize the child, their recovery will be much slower than expected."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Appeal to local merchants and herbalists to check their inventory for the rare herb.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your heartfelt plea moves a reclusive herbalist to reveal they've been growing the rare herb as an experiment. They donate the needed amount to save the child.",
                                    "failure_outcome": "Despite your efforts, you fail to find anyone with the herb. Time is wasted in the search, and Sister Maribel must attempt the ritual with inadequate substitutes."
                                },
                                {
                                    "skill": "Arcana",
                                    "text": "Assist Sister Maribel in channeling additional magical energy to compensate for the missing herb.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your arcane knowledge helps Sister Maribel amplify the ritual's power. The ceremony succeeds despite the missing ingredient, and the child makes a miraculous recovery.",
                                    "failure_outcome": "The unstable magical energies you help channel spiral out of control. Though the child survives, the magical backlash temporarily damages the temple's sacred space."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest abandoning the ritual and using conventional medicine instead.",
                                    "outcome": "Conventional treatments have already failed, which is why the ritual was needed. The child's condition deteriorates while Sister Maribel desperately tries to find an alternative."
                                },
                                {
                                    "text": "Recommend delaying the ritual until the herb can be ordered from another town.",
                                    "outcome": "The child's condition is too critical to wait. They pass away before the herb can arrive, leaving Sister Maribel devastated by the preventable loss."
                                },
                                {
                                    "text": "Suggest using an obviously incorrect substitute, like a common kitchen spice.",
                                    "outcome": "The inappropriate substitute causes the ritual to fail spectacularly. The temple is filled with noxious smoke, and the child must be moved, further complicating their condition."
                                },
                                {
                                    "text": "Advise Sister Maribel to keep the missing ingredient a secret from the child's parents.",
                                    "outcome": "The parents discover the deception and lose trust in the temple's healing abilities. They remove their child from Sister Maribel's care entirely."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "Sister Maribel discovers evidence of corruption involving temple donations, but doesn't know who to trust with the information.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Investigation",
                                    "text": "Quietly gather more evidence before taking action.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your discreet investigation uncovers a comprehensive trail of evidence linking a senior temple administrator to the missing funds. With this solid proof, reforms are implemented without damaging the temple's reputation.",
                                    "failure_outcome": "Your investigation is noticed, and the culprits destroy key evidence before you can secure it. Without sufficient proof, the corruption continues unpunished."
                                },
                                {
                                    "skill": "Insight",
                                    "text": "Observe the temple staff to determine who might be trustworthy and knowledgeable about the accounts.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your people-reading skills help you identify an honest senior priest with accounting experience. Together, you discreetly address the corruption and recover most of the misappropriated funds.",
                                    "failure_outcome": "You misjudge someone's character badly, confiding in a person involved in the corruption. They alert the other culprits, and evidence quickly disappears."
                                },
                                {
                                    "skill": "Deception",
                                    "text": "Set up a false financial report to see who tries to alter it.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your clever trap works perfectly. The culprit attempts to modify your false report, revealing their identity. Sister Maribel can now take appropriate action with certainty.",
                                    "failure_outcome": "Your deception is transparent and raises suspicions. The corrupt individuals realize they're being investigated and become much more careful, making the real evidence harder to find."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Convince Sister Maribel to approach the high priest directly with what she knows.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your encouragement gives Sister Maribel the confidence to present her concerns to the high priest. He takes the matter seriously, launching a formal investigation that resolves the issue with minimal scandal.",
                                    "failure_outcome": "Your approach backfires when the high priest dismisses the concerns as speculative. The corrupt individuals are now warned and cover their tracks thoroughly."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest ignoring the problem to avoid temple scandal.",
                                    "outcome": "The corruption grows worse over time. When eventually discovered, the scandal is far more damaging, and Sister Maribel is implicated for knowing but remaining silent."
                                },
                                {
                                    "text": "Recommend posting public notices about the missing donations around town.",
                                    "outcome": "The public accusations without proper evidence create a crisis of faith in the community. Temple attendance drops sharply, and many stop giving donations entirely."
                                },
                                {
                                    "text": "Advise confronting all temple staff together to see who acts guilty.",
                                    "outcome": "The public confrontation creates division and distrust among the temple staff. The guilty parties maintain their innocence, and temple functions are disrupted by the internal conflict."
                                },
                                {
                                    "text": "Suggest taking the temple funds yourself for safekeeping until the culprit is found.",
                                    "outcome": "Your questionable suggestion makes Sister Maribel suspicious of your motives. She distances herself from you and decides to handle the matter without your help."
                                }
                            ]
                        }
                    }
                ],
                "Garrick the Unseen": [
                    {
                        "problem": "Garrick's secret hideout has been discovered by the town guard, and he needs to relocate his collection of 'acquired' valuables quickly.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Stealth",
                                    "text": "Help Garrick move his treasures under the cover of night, avoiding guard patrols.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your stealthy guidance helps Garrick transport his collection to a new location without being seen. He rewards you with a valuable item from his collection.",
                                    "failure_outcome": "You misjudge the guard patrol routes, leading Garrick into an encounter with the night watch. He escapes, but most of his valuable collection is confiscated."
                                },
                                {
                                    "skill": "Deception",
                                    "text": "Create a distraction that will draw the town guard away from Garrick's hideout temporarily.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your clever ruse about suspicious activity near the town gate successfully diverts the guards' attention. Garrick moves his collection unnoticed and considers you a valuable ally.",
                                    "failure_outcome": "Your unconvincing story raises the guards' suspicions rather than diverting them. They increase security around Garrick's hideout, making the situation worse."
                                },
                                {
                                    "skill": "Sleight of Hand",
                                    "text": "Disguise the valuables as ordinary objects that can be moved openly without suspicion.",
                                    "skill_dc": 16,
                                    "success_outcome": "Your exceptional skills transform jewels into buttons, gold cups into tarnished cookware, and paintings into common fabric. The disguised treasures are moved in plain sight without raising any suspicion.",
                                    "failure_outcome": "Your disguises are too obvious. A guard notices a poorly concealed valuable, leading to questions about the unusual items you're transporting through town."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Convince a local merchant to store the items temporarily as legitimate inventory.",
                                    "skill_dc": 13,
                                    "success_outcome": "You persuade a sympathetic merchant to store the collection as 'imported goods' awaiting transport. The arrangement works perfectly, and Garrick rewards your social skills.",
                                    "failure_outcome": "The merchant seems to agree but immediately reports the suspicious request to the town guard. Garrick barely escapes when they come to investigate."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest Garrick turn himself in and claim the items were family heirlooms.",
                                    "outcome": "Garrick's extensive criminal record makes his story completely unbelievable. He's imprisoned, and his collection is confiscated. He blames you for the terrible advice."
                                },
                                {
                                    "text": "Recommend hiding the valuables in the town well until the search dies down.",
                                    "outcome": "The heavy items damage the well's mechanism, contaminating the town's water supply. An investigation leads back to you and Garrick as the culprits."
                                },
                                {
                                    "text": "Propose setting fire to another building as a major distraction.",
                                    "outcome": "The fire spreads more quickly than anticipated, damaging multiple buildings. You're identified as the arsonist, facing serious criminal charges and the town's anger."
                                },
                                {
                                    "text": "Advise burying the treasure in the town cemetery temporarily.",
                                    "outcome": "Your nighttime digging activity is noticed by the cemetery caretaker. The guard is alerted, and they set up an ambush, waiting for you to return to the site."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "Garrick has been framed for a theft he didn't commit, and the evidence against him looks convincing.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Investigation",
                                    "text": "Examine the crime scene to find evidence that might clear Garrick's name.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your careful investigation discovers overlooked evidence that contradicts the official account. You find footprints that couldn't be Garrick's and a distinctive tool mark from a rival thief's signature method.",
                                    "failure_outcome": "Your investigation fails to find anything useful, and you accidentally contaminate the crime scene. The town guard asks you to leave and treats Garrick with even more suspicion."
                                },
                                {
                                    "skill": "Insight",
                                    "text": "Question witnesses to find inconsistencies in their accounts.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your perceptive questioning reveals that the main witness was bribed to implicate Garrick. When confronted privately, they confess the truth to you, clearing Garrick's name.",
                                    "failure_outcome": "The witnesses become defensive under your questioning. They report your 'intimidation' to the guard, making you look like Garrick's accomplice rather than his ally."
                                },
                                {
                                    "skill": "Sleight of Hand",
                                    "text": "Discreetly plant evidence that would establish Garrick's alibi for the time of the theft.",
                                    "skill_dc": 16,
                                    "success_outcome": "You skillfully place evidence showing Garrick was elsewhere during the crime. When discovered, this 'overlooked' evidence creates reasonable doubt about his involvement.",
                                    "failure_outcome": "You're caught planting false evidence, which only makes Garrick look more guilty and implicates you in obstructing justice."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Appeal to the victim directly, explaining that Garrick is being framed and offering to find the real culprit.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your sincere appeal convinces the victim to delay pressing charges. This gives you time to uncover the truth and identify the real thief, vindicating Garrick.",
                                    "failure_outcome": "The victim is unmoved by your pleas and becomes suspicious of your motives. They report your 'threatening behavior' to the town guard, complicating matters further."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest Garrick flee town immediately to avoid prosecution.",
                                    "outcome": "Garrick's escape is seen as an admission of guilt. He becomes a wanted criminal throughout the region, unable to return to Rivermeet for the foreseeable future."
                                },
                                {
                                    "text": "Recommend breaking into the guard station to steal the evidence against him.",
                                    "outcome": "The break-in is discovered immediately. The increased security and attention make Garrick's situation significantly worse, and you're now wanted for questioning as well."
                                },
                                {
                                    "text": "Advise Garrick to bribe the town judge before the trial.",
                                    "outcome": "The judge is known for their integrity and is deeply offended by the bribe attempt. They impose the maximum possible sentence on Garrick when he's found guilty."
                                },
                                {
                                    "text": "Suggest finding someone else to confess to the crime in Garrick's place.",
                                    "outcome": "The false confession is quickly exposed as a lie, adding the serious charge of obstructing justice to Garrick's alleged crimes."
                                }
                            ]
                        }
                    },
                    {
                        "problem": "Garrick has information about a planned heist but needs help determining if the target is too heavily guarded.",
                        "choices": {
                            "correct": [
                                {
                                    "skill": "Stealth",
                                    "text": "Scout the location carefully to assess guard patterns and security measures.",
                                    "skill_dc": 16,
                                    "success_outcome": "Your meticulous observation reveals a flaw in the guard rotation. You identify a perfect 10-minute window when the approach is minimally guarded. Garrick is impressed with your skill.",
                                    "failure_outcome": "You're spotted lurking around the location. The guards increase security as a result, and Garrick's contact abandons the plan, blaming him for the failed reconnaissance."
                                },
                                {
                                    "skill": "Deception",
                                    "text": "Pose as a potential client to gain access to the building and observe security from inside.",
                                    "skill_dc": 15,
                                    "success_outcome": "Your convincing persona as a wealthy merchant earns you a tour of the establishment. You gather crucial information about internal security that makes Garrick's plan significantly safer.",
                                    "failure_outcome": "Your story has inconsistencies that raise suspicion. You're asked detailed questions you can't answer, forcing a hasty exit and leaving Garrick without the needed information."
                                },
                                {
                                    "skill": "Perception",
                                    "text": "Watch the building from various public locations to map out guard positions.",
                                    "skill_dc": 14,
                                    "success_outcome": "Your careful observation from different vantage points creates a complete picture of the security arrangements. You even notice a hidden entrance that would be perfect for Garrick's purposes.",
                                    "failure_outcome": "You miss critical details about the patrol schedule. The information you provide to Garrick is dangerously incomplete, potentially leading him into a well-guarded area."
                                },
                                {
                                    "skill": "Persuasion",
                                    "text": "Strike up a friendly conversation with one of the guards to learn about their security protocols.",
                                    "skill_dc": 13,
                                    "success_outcome": "Your casual conversation with a guard yields surprising insights. They openly complain about understaffing on certain nights and reveal which areas have weaker surveillance.",
                                    "failure_outcome": "The guard becomes suspicious of your specific questions about security. They report the conversation to their superior, increasing vigilance around the building."
                                }
                            ],
                            "incorrect": [
                                {
                                    "text": "Suggest creating a distraction by setting off an alarm at a different location.",
                                    "outcome": "The false alarm puts all guards in the area on high alert. Security is tightened everywhere, making Garrick's planned heist even more dangerous."
                                },
                                {
                                    "text": "Recommend bribing random guards for information without knowing who can be trusted.",
                                    "outcome": "You approach an incorruptible guard who reports the bribe attempt immediately. The town guard sets up a sting operation, hoping to catch Garrick in the act."
                                },
                                {
                                    "text": "Advise Garrick to proceed without reconnaissance, trusting his skills to overcome any obstacles.",
                                    "outcome": "Without proper planning, Garrick walks into a heavily guarded area. He barely escapes and suffers an injury that will take weeks to heal."
                                },
                                {
                                    "text": "Propose disguising yourselves as guards to infiltrate the location.",
                                    "outcome": "The authentic-looking uniforms you procure have distinctive markings you didn't notice. Real guards immediately identify you as impostors, resulting in a dangerous chase through town."
                                }
                            ]
                        }
                    }
                ],
"The Village Blacksmith": [
    {
        "problem": "The blacksmith's forge has broken down on the day several important orders are due.",
        "choices": {
            "correct": [
                {
                    "skill": "Athletics",
                    "text": "Help repair the heavy forge components with your physical strength. (Requires: Athletics check)",
                    "skill_dc": 0,
                    "success_outcome": "Your muscle power proves invaluable as you help lift and reset the collapsed forge structure. The blacksmith is able to complete all orders on time."
                },
                {
                    "skill": "Investigation",
                    "text": "Examine the forge to determine the exact cause of the breakdown. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "You discover a cracked support beam that's causing the entire structure to fail. Once identified, the fix is relatively simple."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince nearby craftspeople to lend their tools and expertise. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your diplomatic plea brings the community together. Several artisans arrive with tools and helping hands, turning a disaster into a village-wide repair party."
                },
                {
                    "skill": "Deception",
                    "text": "Distract the waiting customers with elaborate tales while others fix the forge. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your entertaining stories keep the customers happily distracted in the front room, completely unaware of the frantic repairs happening in the back."
                },
                {
                    "skill": "Arcana",
                    "text": "Apply magical knowledge to temporarily enhance the failing forge. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "Your makeshift magical enhancements create a surprising increase in forge efficiency. The blacksmith completes all orders in record time."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest the blacksmith claim their tools were stolen to explain the delays. (Requires: Deception check)",
                    "outcome": "The transparent lie spreads through the village quickly. No one believes the story, and the blacksmith loses several loyal customers who feel insulted by the deception."
                },
                {
                    "text": "Recommend using green, unseasoned wood as emergency forge fuel. (Requires: Survival check)",
                    "outcome": "The wet wood creates enormous amounts of smoke that fills the smithy. The coughing, teary-eyed blacksmith has to evacuate the building for hours, further delaying all work."
                },
                {
                    "text": "Advise doubling prices for the customers who seem most desperate. (Requires: Insight check)",
                    "outcome": "The opportunistic price gouging infuriates customers. Word spreads quickly, and several people cancel their orders entirely, taking their business to the next town."
                },
                {
                    "text": "Suggest using explosives to quickly clear the forge blockage. (Requires: Demolition check)",
                    "outcome": "The excessive force devastates the entire forge setup. What was a simple repair becomes a complete rebuild, closing the smithy for weeks."
                },
                {
                    "text": "Propose blaming the forge's breakdown on a competitor's sabotage. (Requires: Performance check)",
                    "outcome": "The baseless accusation creates a bitter feud between craftspeople who previously had good relations. The blacksmith is ostracized by the crafting community when the lie is discovered."
                }
            ]
        }
    },
    {
        "problem": "The blacksmith needs a rare metal component that's only available in a dangerous nearby mine.",
        "choices": {
            "correct": [
                {
                    "skill": "Athletics",
                    "text": "Offer to venture into the mine yourself to retrieve the component. (Requires: Athletics check)",
                    "skill_dc": 0,
                    "success_outcome": "Your physical prowess allows you to navigate the treacherous mine shafts and extract the rare metal safely. The blacksmith is impressed by your bravery."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince local miners to share their knowledge and spare materials. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your friendly approach wins over the gruff miners. They not only provide the needed component but offer to supply the blacksmith regularly at a fair price."
                },
                {
                    "skill": "Insight",
                    "text": "Suggest an alternative, more common material that could be adapted for the same purpose. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your clever material substitution works perfectly. The blacksmith is able to create an even better final product using your innovative approach."
                },
                {
                    "skill": "Survival",
                    "text": "Scout a safer route into the abandoned section of the mine. (Requires: Survival check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful exploration reveals a forgotten side tunnel that provides safe access to the resource. The blacksmith hires you as a guide for future expeditions."
                },
                {
                    "skill": "History",
                    "text": "Research old mining records to locate forgotten deposits of the material. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your research uncovers detailed maps showing a small but accessible deposit much closer to town. The blacksmith rewards your scholarly approach with a discount on future items."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest stealing the component from a rival blacksmith's supplies. (Requires: Sleight of Hand check)",
                    "outcome": "The theft is immediately discovered and traced back to your blacksmith. The resulting scandal and fines cost far more than simply purchasing the component legitimately."
                },
                {
                    "text": "Recommend hiring inexperienced locals for a dangerous mining expedition. (Requires: Intimidation check)",
                    "outcome": "The poorly prepared mining party suffers several injuries in a minor cave-in. The blacksmith must pay for their medical care and compensation, draining all their savings."
                },
                {
                    "text": "Advise using magical illusions to disguise cheaper metals as the rare component. (Requires: Arcana check)",
                    "outcome": "The magical fakery is discovered by the very first customer, a minor noble with magical training. They spread word of the fraudulent craftsmanship, severely damaging the blacksmith's reputation."
                },
                {
                    "text": "Propose kidnapping a mining expert to force them to help. (Requires: Stealth check)",
                    "outcome": "The kidnapping attempt fails spectacularly. Town guards arrest you and the blacksmith as co-conspirators, shutting down the smithy pending a full investigation."
                },
                {
                    "text": "Suggest claiming the finished products contain the rare metal without actually using it. (Requires: Deception check)",
                    "outcome": "Customers quickly notice the inferior quality of the supposedly premium goods. Refund demands pour in, and the blacksmith becomes known for dishonest business practices."
                }
            ]
        }
    },
    {
        "problem": "The blacksmith's apprentice has accidentally created a bizarre magical effect in a weapon being forged.",
        "choices": {
            "correct": [
                {
                    "skill": "Arcana",
                    "text": "Analyze the magical properties to understand the unexpected enchantment. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "You identify the accidental enchantment as a rare and valuable magic effect. The blacksmith can now reproduce it intentionally, creating a popular new line of specialty weapons."
                },
                {
                    "skill": "Investigation",
                    "text": "Examine the forging process to determine exactly what caused the effect. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful observation reveals that a combination of special ore and the apprentice's unique hammering rhythm created the magical resonance. The process can now be standardized."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince the apprentice to demonstrate exactly what they did to recreate the effect. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your encouraging approach helps the nervous apprentice overcome their fear of punishment. They successfully recreate the process, revealing a valuable new smithing technique."
                },
                {
                    "skill": "History",
                    "text": "Research ancient forging techniques that might explain the magical occurrence. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your knowledge uncovers references to a forgotten dwarven technique accidentally rediscovered by the apprentice. The blacksmith can now market these items as 'rediscovered ancient magic'."
                },
                {
                    "skill": "Performance",
                    "text": "Create a compelling story about the weapon's 'intentional' magical properties to attract buyers. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your dramatic tale of the weapon's magical origins spreads throughout the region. Collectors and adventurers flock to the smithy, willing to pay premium prices for these 'legendary' items."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest hiding the magical effect and selling it as a normal weapon. (Requires: Deception check)",
                    "outcome": "The unsuspecting buyer is surprised when the weapon's magic activates during combat. The uncontrolled effect causes significant collateral damage, resulting in a lawsuit against the blacksmith."
                },
                {
                    "text": "Recommend smashing the enchanted weapon and melting it down immediately. (Requires: Athletics check)",
                    "outcome": "The attempt to destroy the magically-infused metal releases the unstable energy all at once. The resulting explosion damages the forge and injures both the blacksmith and apprentice."
                },
                {
                    "text": "Advise firing the apprentice for dangerous magical experimentation. (Requires: Intimidation check)",
                    "outcome": "The talented apprentice is quickly hired by a rival blacksmith, taking the accidental discovery with them. They become famous for their magical weapons while your blacksmith's business struggles."
                },
                {
                    "text": "Propose charging customers to touch the magical weapon as a good luck charm. (Requires: Performance check)",
                    "outcome": "During the improvised 'lucky touches' event, the unstable enchantment discharges unexpectedly. Several villagers suffer magical burns, and authorities shut down the smithy pending investigation."
                },
                {
                    "text": "Suggest claiming the gods blessed the weapon as a divine sign. (Requires: Religion check)",
                    "outcome": "The local temple takes great offense at the false religious claims. They declare the smithy blasphemous, and devout villagers refuse to patronize the business."
                }
            ]
        }
    }
],
"The Traveling Merchant": [
    {
        "problem": "The merchant's wagon wheel has broken on a dangerous stretch of road far from town.",
        "choices": {
            "correct": [
                {
                    "skill": "Athletics",
                    "text": "Use your strength to help lift the wagon while repairs are made. (Requires: Athletics check)",
                    "skill_dc": 0,
                    "success_outcome": "Your impressive strength keeps the heavy wagon stable during the delicate repair process. The merchant is back on the road quickly and safely."
                },
                {
                    "skill": "Survival",
                    "text": "Find suitable wood in the nearby forest to fashion a temporary replacement wheel. (Requires: Survival check)",
                    "skill_dc": 0,
                    "success_outcome": "Your wilderness knowledge helps you locate the perfect fallen branch with just the right curvature. Your improvised wheel holds until the next town."
                },
                {
                    "skill": "Sleight of Hand",
                    "text": "Make precise, delicate repairs to the damaged wheel components. (Requires: Sleight of Hand check)",
                    "skill_dc": 0,
                    "success_outcome": "Your dexterous fingers manage to bind the splintered wood and bent metal back into a functional wheel. The merchant is impressed by your unexpected handiness."
                },
                {
                    "skill": "Performance",
                    "text": "Keep watch for bandits while entertaining the merchant during the delay. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your engaging stories and songs keep spirits high during the repairs. The merchant is so appreciative that they offer you a significant discount on their wares."
                },
                {
                    "skill": "Animal Handling",
                    "text": "Calm the merchant's anxious draft animals during the repair process. (Requires: Animal Handling check)",
                    "skill_dc": 0,
                    "success_outcome": "Your soothing presence keeps the nervous horses from causing further damage to the wagon. The repair process proceeds smoothly thanks to your animal management."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest abandoning the heavy merchandise to lighten the wagon's load. (Requires: Persuasion check)",
                    "outcome": "The merchant loses most of their valuable inventory to weather damage and theft after abandoning it by the roadside. Their business suffers a devastating financial setback."
                },
                {
                    "text": "Recommend using magical levitation rather than fixing the wheel. (Requires: Arcana check)",
                    "outcome": "Your amateur magical attempt backfires spectacularly. The wagon briefly hovers before crashing down hard, breaking another wheel and damaging the axle."
                },
                {
                    "text": "Advise continuing to drive on the broken wheel until reaching town. (Requires: Deception check)",
                    "outcome": "The continued travel on the damaged wheel destroys the axle completely. What was a simple repair becomes a complete wagon rebuild, stranding the merchant for weeks."
                },
                {
                    "text": "Propose stealing a wheel from another traveler's vehicle. (Requires: Sleight of Hand check)",
                    "outcome": "The theft attempt is spotted by a passing patrol of guards. Both you and the merchant are arrested for highway robbery, and the wagon and goods are impounded."
                },
                {
                    "text": "Suggest setting up shop right there on the roadside until help arrives. (Requires: Persuasion check)",
                    "outcome": "The isolated location attracts bandits rather than customers. The merchant loses their inventory in a robbery that could have been avoided by focusing on repairs."
                }
            ]
        }
    },
    {
        "problem": "The merchant discovers that a valuable item in their inventory is actually a clever counterfeit.",
        "choices": {
            "correct": [
                {
                    "skill": "Investigation",
                    "text": "Examine the fake to identify where it came from and who created it. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful analysis reveals distinctive crafting techniques that point to a known forgery ring. The merchant can now alert authorities and avoid future scams."
                },
                {
                    "skill": "Insight",
                    "text": "Help determine which supplier sold the counterfeit to prevent future fraud. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your perceptive questioning helps the merchant remember suspicious behavior from one particular supplier. They can now avoid this unreliable source."
                },
                {
                    "skill": "Arcana",
                    "text": "Detect any magical properties used to disguise the item's true nature. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "You discover subtle illusion magic making the fake appear more valuable. With this knowledge, the merchant can check other inventory items for similar enchantments."
                },
                {
                    "skill": "Deception",
                    "text": "Help create a clever sales pitch to sell the item as an 'authentic reproduction.' (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your creative marketing approach turns potential disaster into opportunity. By honestly labeling it as a quality reproduction, the merchant still makes a profit without resorting to fraud."
                },
                {
                    "skill": "Persuasion",
                    "text": "Negotiate with the original seller for compensation or replacement. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your diplomatic approach convinces the supplier that making amends is better than risking their reputation. They provide an authentic replacement at no additional cost."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest selling the counterfeit to an unsuspecting customer at full price. (Requires: Deception check)",
                    "outcome": "The fraudulent sale is quickly discovered when the buyer has the item appraised. The merchant's reputation is severely damaged, and they face legal consequences for knowingly selling counterfeits."
                },
                {
                    "text": "Recommend creating more convincing forgeries to sell alongside authentic items. (Requires: Forgery check)",
                    "outcome": "The merchant's turn to deliberate fraud results in arrest when a customer with magical detection abilities reports them to authorities. Their inventory is confiscated and business license revoked."
                },
                {
                    "text": "Advise destroying the fake and denying ever having possessed it. (Requires: Sleight of Hand check)",
                    "outcome": "The hasty destruction is witnessed by a customer who misinterprets it as the merchant hiding evidence of broader fraud. Rumors spread, severely damaging business."
                },
                {
                    "text": "Propose magically enhancing the fake to pass most inspection methods. (Requires: Arcana check)",
                    "outcome": "Your magical tampering triggers a security enchantment placed by the original forger. The resulting magical backlash transforms the entire inventory into worthless replicas."
                },
                {
                    "text": "Suggest threatening the supplier with violence if they don't compensate for the fake. (Requires: Intimidation check)",
                    "outcome": "The supplier reports the threats to local authorities. The merchant faces harassment charges and is banned from several market towns along their regular route."
                }
            ]
        }
    },
    {
        "problem": "The merchant needs to sell their inventory quickly after learning of a much better opportunity in a distant city.",
        "choices": {
            "correct": [
                {
                    "skill": "Performance",
                    "text": "Create an entertaining street performance to draw a crowd of potential customers. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your lively entertainment attracts a huge crowd to the merchant's impromptu 'going out of business' sale. The entire inventory sells out by sundown."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince local shopkeepers to purchase the inventory at wholesale prices. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your negotiation skills help strike a fair bulk deal with several local shops. The merchant makes a decent profit while saving time and effort."
                },
                {
                    "skill": "Deception",
                    "text": "Create a sense of urgency by hinting the items may be banned soon. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your carefully worded rumors about upcoming trade restrictions create a buying frenzy. The technically truthful 'limited time availability' doubles the merchant's sales speed."
                },
                {
                    "skill": "Insight",
                    "text": "Identify which items to discount heavily and which will sell regardless. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your strategic pricing maximizes profit while ensuring everything sells quickly. The merchant makes more than expected despite the rushed sales."
                },
                {
                    "skill": "Investigation",
                    "text": "Research local needs to determine where specific items would be most valuable. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your market research reveals perfect buyers for specialty items - the local alchemist desperately needs exotic components, while the mayor seeks gifts for an upcoming festival."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest drastically slashing all prices to sell everything immediately. (Requires: Commerce check)",
                    "outcome": "The extreme discounts attract bargain hunters who spread word of the desperate sale. The merchant sells everything but at such a loss that they can't afford the journey to their new opportunity."
                },
                {
                    "text": "Recommend starting a rumor that the merchandise is stolen to create excitement. (Requires: Deception check)",
                    "outcome": "The rumor works too well - town guards investigate the 'stolen goods' claim, impounding the entire inventory pending a lengthy investigation that ruins the merchant's opportunity."
                },
                {
                    "text": "Advise holding a gambling event where purchases come with a chance to win the entire inventory. (Requires: Sleight of Hand check)",
                    "outcome": "The improvised gambling operation violates local laws. Authorities shut down the event, fine the merchant heavily, and confiscate much of the remaining inventory as penalty."
                },
                {
                    "text": "Propose claiming the items have magical properties they don't actually possess. (Requires: Arcana check)",
                    "outcome": "Several customers test the supposedly magical items and discover the fraudulent claims. They demand refunds and report the merchant to local authorities for magical fraud."
                },
                {
                    "text": "Suggest hiring local children to aggressively pressure visitors into making purchases. (Requires: Persuasion check)",
                    "outcome": "The overzealous children's tactics anger townsfolk and visitors alike. Complaints reach the town council, who force the merchant to cease operations immediately."
                }
            ]
        }
    }
],
"The Tavern Keeper": [
    {
        "problem": "The tavern is nearly empty during what should be the busiest festival of the year.",
        "choices": {
            "correct": [
                {
                    "skill": "Performance",
                    "text": "Offer to provide special entertainment to draw in festival-goers. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your exceptional performance becomes the talk of the festival. People pack the tavern to standing room only, and the keeper offers you a regular gig with good pay."
                },
                {
                    "skill": "Brewing",
                    "text": "Help create a unique festival drink special that can't be found elsewhere. (Requires: Brewing check)",
                    "skill_dc": 0,
                    "success_outcome": "Your creative 'Festival Spirit' cocktail becomes an instant hit. People line up outside just to try the colorful, delicious concoction that perfectly captures the festive mood."
                },
                {
                    "skill": "Investigation",
                    "text": "Discover why customers are avoiding the tavern specifically. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "You uncover that a rival spread rumors about cleanliness issues. After publicly disproving these claims, customers return in force, often expressing their support."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince festival performers to use the tavern as their official gathering spot. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your networking brings various jugglers, musicians, and dancers to use the tavern as their home base. Their presence attracts steady crowds of admirers and fellow performers."
                },
                {
                    "skill": "Deception",
                    "text": "Start an intriguing rumor about a celebrity secretly visiting the tavern tonight. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your carefully crafted rumor works perfectly - crowds come to spot the supposed celebrity, and end up staying for the great atmosphere and service even after realizing it was just gossip."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest watering down drinks to cut costs during the slow period. (Requires: Sleight of Hand check)",
                    "outcome": "Regular patrons immediately notice the diluted drinks and spread word through the festival. The tavern develops a reputation for cheating customers that persists long after the event."
                },
                {
                    "text": "Recommend physically blocking the entrance to competing establishments. (Requires: Athletics check)",
                    "outcome": "The obvious sabotage is quickly noticed by town guards. The tavern keeper faces fines for unfair business practices and public nuisance charges."
                },
                {
                    "text": "Advise drastically cutting prices to undercut all competition. (Requires: Persuasion check)",
                    "outcome": "The tavern fills with the rowdiest, most frugal festival-goers who order minimal drinks while causing maximum damage. The keeper loses money on every customer while driving away better clientele."
                },
                {
                    "text": "Propose hiring people to stage exciting bar fights to attract attention. (Requires: Performance check)",
                    "outcome": "The fake fight turns into a real brawl that destroys furniture and inventory. The town guard temporarily closes the tavern for promoting disorderly conduct during the festival."
                },
                {
                    "text": "Suggest spreading rumors that other taverns are serving tainted alcohol. (Requires: Deception check)",
                    "outcome": "The malicious rumor is traced back to your tavern keeper. Furious competitors file formal complaints, and festival organizers direct visitors to avoid the 'unethical establishment'."
                }
            ]
        }
    },
    {
        "problem": "A valuable family heirloom was stolen from above the tavern's fireplace during a busy evening.",
        "choices": {
            "correct": [
                {
                    "skill": "Investigation",
                    "text": "Carefully examine the scene and question patrons who were nearby. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your thorough investigation identifies a suspicious traveling merchant who left abruptly. Tracking them down, you recover the heirloom before they could leave town."
                },
                {
                    "skill": "Perception",
                    "text": "Review the evening's events to identify when the theft occurred. (Requires: Perception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful recollection pinpoints the exact moment during a staged distraction. This leads directly to the culprits, who are caught with the heirloom in their possession."
                },
                {
                    "skill": "Persuasion",
                    "text": "Appeal to customers' goodwill for information about the theft. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your heartfelt plea moves several patrons to share crucial observations they had been hesitant to mention. Their combined accounts lead directly to the thief."
                },
                {
                    "skill": "Insight",
                    "text": "Determine which regular customers were acting strangely that evening. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your people-reading skills identify a usually-broke patron who was unusually generous with drinks. Confronted privately, they confess and return the heirloom."
                },
                {
                    "skill": "Deception",
                    "text": "Announce a fictional unique property of the heirloom that makes it dangerous to possess. (Requires: Deception check)",
                    "skill_dc": 0, 
                    "success_outcome": "Your creative story about the 'cursed' heirloom spreads quickly. The superstitious thief secretly returns it overnight, fearing the invented supernatural consequences."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest accusing the most suspicious-looking patron without evidence. (Requires: Intimidation check)",
                    "outcome": "The falsely accused customer is an influential merchant who takes great offense. They spread word of the tavern's hostile treatment, severely damaging its reputation."
                },
                {
                    "text": "Recommend hiring a dubious 'curse-caster' to hex the unknown thief. (Requires: Arcana check)",
                    "outcome": "The theatrical curse ritual spooks many regular customers who fear being accidentally affected. Business drops sharply while the actual thief remains unidentified."
                },
                {
                    "text": "Advise replacing the heirloom with a replica and pretending nothing happened. (Requires: Deception check)",
                    "outcome": "The tavern keeper's family immediately notices the obvious fake. Their public argument about the deception embarrasses the keeper and reveals the theft to everyone."
                },
                {
                    "text": "Propose randomly searching all customers entering the tavern for the next week. (Requires: Intimidation check)",
                    "outcome": "The invasive searches drive away nearly all customers. Word spreads about the unpleasant treatment, and business suffers for months afterward."
                },
                {
                    "text": "Suggest publicly offering a reward larger than the heirloom's actual value. (Requires: Persuasion check)",
                    "outcome": "The excessive reward attracts dozens of opportunists with fake information and fraudulent 'found' items. The tavern keeper wastes time and money pursuing false leads."
                }
            ]
        }
    },
    {
        "problem": "Health inspectors are coming tomorrow, but the tavern's kitchen is in terrible condition.",
        "choices": {
            "correct": [
                {
                    "skill": "Athletics",
                    "text": "Lead an intensive physical cleaning effort of the entire kitchen. (Requires: Athletics check)",
                    "skill_dc": 0,
                    "success_outcome": "Your energetic scrubbing transforms the grimy kitchen. The inspectors are impressed by the spotless conditions and even compliment the tavern keeper on their high standards."
                },
                {
                    "skill": "Nature",
                    "text": "Use natural remedies to eliminate pests and odors quickly. (Requires: Nature check)",
                    "skill_dc": 0,
                    "success_outcome": "Your herbal mixtures and natural pest deterrents work remarkably well. The kitchen is fresh and vermin-free by morning, easily passing inspection."
                },
                {
                    "skill": "Persuasion",
                    "text": "Convince experienced kitchen staff from other establishments to help with the cleanup. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your networking brings several professional cooks after their shifts end. Their combined expertise transforms the kitchen while teaching the staff better maintenance techniques."
                },
                {
                    "skill": "Alchemy",
                    "text": "Create effective cleaning solutions using available tavern ingredients. (Requires: Alchemy check)",
                    "skill_dc": 0,
                    "success_outcome": "Your improvised cleaning mixtures cut through years of grease and grime with surprising efficiency. The kitchen practically sparkles by morning."
                },
                {
                    "skill": "Deception",
                    "text": "Rearrange the kitchen to hide problem areas while highlighting the cleanest sections. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your strategic reorganization emphasizes the kitchen's strengths. The inspector focuses on the improved areas and offers only minor recommendations rather than violations."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest bribing the health inspector to overlook the violations. (Requires: Persuasion check)",
                    "outcome": "The inspector is known for their integrity and reports the bribery attempt to authorities. The tavern now faces corruption charges in addition to health violations."
                },
                {
                    "text": "Recommend using strong magic to create an illusion of cleanliness. (Requires: Illusion check)",
                    "outcome": "Inspectors carry enchanted items specifically designed to detect magical deception. The attempted trickery results in immediate closure of the tavern and substantial fines."
                },
                {
                    "text": "Advise spreading rumors that the inspector is corrupt to discredit their findings. (Requires: Deception check)",
                    "outcome": "The baseless accusations are easily disproven and traced back to the tavern. The insulted inspector conducts an especially thorough examination, finding every possible violation."
                },
                {
                    "text": "Propose serving the inspector food prepared off-premises while claiming it's from the kitchen. (Requires: Sleight of Hand check)",
                    "outcome": "The deception is discovered when the inspector insists on watching meal preparation. This attempted fraud results in immediate license suspension."
                },
                {
                    "text": "Suggest temporarily closing the kitchen claiming a water leak that needs repair. (Requires: Deception check)",
                    "outcome": "The inspector has the authority to examine the premises regardless of operational status. Finding the kitchen deliberately closed for inspection results in automatic failure and fines."
                }
            ]
        }
    }
],
"The Town Healer": [
    {
        "problem": "The healer's supply of a crucial medicinal herb has run out during a seasonal illness outbreak.",
        "choices": {
            "correct": [
                {
                    "skill": "Nature",
                    "text": "Identify local alternatives that could serve the same medicinal purpose. (Requires: Nature check)",
                    "skill_dc": 0,
                    "success_outcome": "Your botanical knowledge reveals a common local plant with similar properties. The substitute works almost as well as the original herb, saving many patients."
                },
                {
                    "skill": "Survival",
                    "text": "Lead an expedition to remote areas where the herb might still be growing. (Requires: Survival check)",
                    "skill_dc": 0,
                    "success_outcome": "Your wilderness skills lead the search party to a hidden valley where the herb grows abundantly. The fresh supply is more potent than usual, treating patients more effectively."
                },
                {
                    "skill": "Medicine",
                    "text": "Help develop a new treatment protocol that requires less of the rare herb. (Requires: Medicine check)",
                    "skill_dc": 0,
                    "success_outcome": "Your medical insight creates a more efficient preparation method that stretches the remaining supply. The healer adopts your technique permanently for its superiority."
                },
                {
                    "skill": "Persuasion",
                    "text": "Organize a town-wide effort to check home gardens for the medicinal plant. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your community organizing reveals several households growing the herb as ornamental plants. Their combined donations provide enough medicine for all who need it."
                },
                {
                    "skill": "Arcana",
                    "text": "Devise a minor enchantment to enhance the potency of the remaining herbs. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "Your magical enhancement significantly increases the effectiveness of the limited supply. The healer asks you to teach them this valuable technique for future shortages."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest using a deceptive placebo and telling patients it's real medicine. (Requires: Deception check)",
                    "outcome": "The fake treatment fails to help genuinely ill people, and several patients develop serious complications. When the deception is discovered, the healer's reputation is severely damaged."
                },
                {
                    "text": "Recommend dramatically increasing prices to ration the remaining supply. (Requires: Persuasion check)",
                    "outcome": "The price gouging during a public health crisis creates outrage. Poor families can't afford treatment, and several children become seriously ill, turning the community against the healer."
                },
                {
                    "text": "Advise stealing supplies from a neighboring town's healer. (Requires: Stealth check)",
                    "outcome": "The theft is quickly traced back to your town's healer. Relations between the communities deteriorate, and the healer faces criminal charges as well as professional disgrace."
                },
                {
                    "text": "Propose using a potentially toxic substitute that looks similar. (Requires: Nature check)",
                    "outcome": "The dangerous substitute causes severe reactions in several patients. Two elderly villagers die from complications, and the healer may face manslaughter charges for the negligent treatment."
                },
                {
                    "text": "Suggest claiming that common water blessed with fake rituals has healing properties. (Requires: Religion check)",
                    "outcome": "The 'blessed water' treatment fails completely. When patients discover the deception, the healer is accused of dangerous religious fraud and medical malpractice."
                }
            ]
        }
    },
    {
        "problem": "The healer has been accused of using forbidden magic after a patient made a miraculous recovery.",
        "choices": {
            "correct": [
                {
                    "skill": "Medicine",
                    "text": "Demonstrate the scientific principles behind the impressive recovery. (Requires: Medicine check)",
                    "skill_dc": 0,
                    "success_outcome": "Your clear explanation of the medical techniques used convinces authorities that no forbidden magic was involved. The healer's methods are recognized as innovative rather than illegal."
                },
                {
                    "skill": "Persuasion",
                    "text": "Gather testimonials from other patients who benefited from similar treatments. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your collected testimonials demonstrate a consistent pattern of successful but non-magical healing. Public opinion shifts strongly in the healer's favor."
                },
                {
                    "skill": "Investigation",
                    "text": "Research the patient's case to find natural explanations for their recovery. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your thorough investigation discovers the patient was simultaneously taking a rare herbal supplement from another source. This combination, not magic, explains the remarkable results."
                },
                {
                    "skill": "Religion",
                    "text": "Involve local religious authorities to verify the recovery was blessed but not forbidden. (Requires: Religion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your theological approach gains the support of respected religious leaders. Their endorsement that the healing was divinely approved silences accusations of dark magic."
                },
                {
                    "skill": "Insight",
                    "text": "Identify who started the rumors and why they might target the healer. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your investigation reveals a rival healer as the source of the accusations. When confronted with evidence of their manipulation, they publicly retract their claims."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest bribing officials to drop the investigation quickly. (Requires: Persuasion check)",
                    "outcome": "The attempted bribe is seen as an admission of guilt. The healer now faces corruption charges in addition to the original accusations, with increased scrutiny from higher authorities."
                },
                {
                    "text": "Recommend threatening accusers with curses to frighten them into silence. (Requires: Intimidation check)",
                    "outcome": "The threats of magical retaliation are taken as confirmation that the healer dabbles in forbidden arts. This dramatically worsens the situation and may lead to formal charges."
                },
                {
                    "text": "Advise claiming the patient was never actually sick to begin with. (Requires: Deception check)",
                    "outcome": "Multiple witnesses contradict this obvious lie, destroying the healer's credibility. This apparent dishonesty convinces many that the other accusations must also be true."
                },
                {
                    "text": "Propose fleeing town until the controversy dies down. (Requires: Stealth check)",
                    "outcome": "The sudden disappearance is seen as admission of guilt. The healer's property is seized, and they are officially branded a dark magic practitioner, unable to return or practice elsewhere."
                },
                {
                    "text": "Suggest publicly demonstrating 'more powerful' magic to intimidate accusers. (Requires: Arcana check)",
                    "outcome": "The magical display confirms everyone's worst fears about forbidden practices. The healer is immediately arrested and their clinic permanently closed by authorities."
                }
            ]
        }
    },
    {
        "problem": "The healer must treat a patient with an unknown illness that doesn't respond to standard remedies.",
        "choices": {
            "correct": [
                {
                    "skill": "Medicine",
                    "text": "Analyze the unusual symptoms to determine the true nature of the illness. (Requires: Medicine check)",
                    "skill_dc": 0,
                    "success_outcome": "Your medical analysis identifies a rare condition caused by exposure to an exotic fungus. With the correct diagnosis, treatment is straightforward and effective."
                },
                {
                    "skill": "History",
                    "text": "Research old medical texts for records of similar symptom patterns. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your scholarly investigation uncovers accounts of a similar outbreak fifty years ago, including the successful treatment methodology that saved patients."
                },
                {
                    "skill": "Investigation",
                    "text": "Trace the patient's recent activities and contacts to find the illness source. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your detective work discovers the patient recently returned from trading with a foreign merchant selling rare teas. This crucial information leads to identifying the exotic illness."
                },
                {
                    "skill": "Nature",
                    "text": "Examine environmental factors that might be causing or worsening the condition. (Requires: Nature check)",
                    "skill_dc": 0,
                    "success_outcome": "Your environmental assessment identifies a rare toxic pollen as the cause. Once the patient is moved away from the contaminated area, their condition improves rapidly."
                },
                {
                    "skill": "Persuasion",
                    "text": "Contact healers from other regions who might have encountered this illness. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your networking connects the healer with a traveling physician who recognizes the symptoms immediately. Their experienced guidance leads to a swift and complete recovery."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest using aggressive bloodletting to purge the unknown illness. (Requires: Medicine check)",
                    "outcome": "The already weakened patient deteriorates rapidly after the bloodletting. Their condition becomes critical, and the treatment must be reversed immediately to prevent death."
                },
                {
                    "text": "Recommend using untested, experimental potions out of desperation. (Requires: Alchemy check)",
                    "outcome": "The unstable concoction causes severe side effects including temporary blindness and delirium. The patient's family threatens legal action for the reckless treatment."
                },
                {
                    "text": "Advise telling the patient nothing can be done to prevent panic. (Requires: Deception check)",
                    "outcome": "The abandoned patient seeks help from a questionable back-alley 'healer' who administers dangerous substances. Their condition worsens dramatically under this fraudulent care."
                },
                {
                    "text": "Propose using forbidden necromantic magic to fight death at any cost. (Requires: Arcana check)",
                    "outcome": "The dark magic temporarily improves symptoms but corrupts the patient's life force. They become dependent on continued magical treatments with increasingly disturbing side effects."
                },
                {
                    "text": "Suggest isolating the patient in case the unknown illness is demonic possession. (Requires: Religion check)",
                    "outcome": "The isolation and lack of proper medical care allows the actual disease to progress unchecked. Religious stigma attaches to the patient and their family, causing lasting social harm."
                }
            ]
        }
    }
],
"The Mysterious Fortune Teller": [
    {
        "problem": "The fortune teller's prophetic crystal has been stolen the night before an important noble consultation.",
        "choices": {
            "correct": [
                {
                    "skill": "Investigation",
                    "text": "Search the fortune teller's tent for clues about the thief. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful examination reveals distinctive footprints and a dropped personal item that leads directly to the culprit – a jealous rival fortune teller from the next town."
                },
                {
                    "skill": "Deception",
                    "text": "Help create an impressive alternative divination method before the noble arrives. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your improvised tea leaf reading ceremony actually impresses the noble more than the standard crystal ball would have. They request this 'exclusive' technique for all future readings."
                },
                {
                    "skill": "Persuasion",
                    "text": "Spread word that returning the crystal will bring good fortune, while keeping it brings a curse. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your convincing warnings about the crystal's 'protective curses' frighten the thief into returning it anonymously before dawn. The fortune teller is ready for the noble's appointment."
                },
                {
                    "skill": "Arcana",
                    "text": "Create a temporary magical link to the stolen crystal to continue using its power. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "Your magical workaround not only allows the reading to proceed but also creates a tracking link to the crystal's location. The fortune teller recovers it immediately after the noble's visit."
                },
                {
                    "skill": "Performance",
                    "text": "Help stage a dramatic 'vision' explaining that spirits commanded a change in divination methods. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your theatrical performance so impresses the noble that they're convinced the spirits intervened specifically to give them a more accurate reading. They leave a generous additional payment."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest using an ordinary glass orb and pretending it's the special crystal. (Requires: Deception check)",
                    "outcome": "The noble has seen the famous crystal before and immediately notices the substitution. Furious at the attempted deception, they publicly denounce the fortune teller as a fraud."
                },
                {
                    "text": "Recommend accusing the noble's servant of stealing the crystal. (Requires: Intimidation check)",
                    "outcome": "The false accusation infuriates the noble, whose trusted servant has been with them for decades. They use their influence to have the fortune teller banned from practicing in the region."
                },
                {
                    "text": "Advise claiming that the crystal shattered during a particularly dark vision about the noble. (Requires: Deception check)",
                    "outcome": "The superstitious noble is terrified by the implied doom prophecy. They cancel all business in town and spread rumors about a curse, damaging the town's economy and the fortune teller's reputation."
                },
                {
                    "text": "Propose using mind-affecting magic to make the noble believe they received a reading. (Requires: Enchantment check)",
                    "outcome": "The noble's personal mage detects the enchantment attempt immediately. Using magic to manipulate a noble is a serious crime, resulting in the fortune teller's arrest."
                },
                {
                    "text": "Suggest hiring a local child to claim they saw the noble's rival stealing the crystal. (Requires: Persuasion check)",
                    "outcome": "The child's obviously coached testimony falls apart under basic questioning. The transparent attempt to frame the noble's rival creates a political scandal that reflects terribly on the fortune teller."
                }
            ]
        }
    },
    {
        "problem": "The fortune teller has foreseen a genuine disaster, but previous false alarms have made townsfolk skeptical.",
        "choices": {
            "correct": [
                {
                    "skill": "Persuasion",
                    "text": "Help present the vision with compelling details that distinguish it from past predictions. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your articulate explanation of why this vision differs from previous ones convinces key town leaders. They implement precautionary measures that save many lives when the disaster occurs."
                },
                {
                    "skill": "Investigation",
                    "text": "Look for current signs that might corroborate elements of the prophesied disaster. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your research discovers early warning signs already visible that support the prediction - unusual animal migrations, water level changes, or structural weaknesses that confirm the coming danger."
                },
                {
                    "skill": "History",
                    "text": "Research if similar disasters have happened in the region's past. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your historical knowledge uncovers records of a similar disaster generations ago with the same preliminary signs. This documented precedent convinces skeptics to take precautions."
                },
                {
                    "skill": "Insight",
                    "text": "Identify which respected community members would be most receptive to the warning. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your people-reading skills identify the town's most pragmatic elder who, once convinced, rallies others to prepare. Their influence is crucial in overcoming general skepticism."
                },
                {
                    "skill": "Nature",
                    "text": "Analyze natural indicators that might validate the fortune teller's vision. (Requires: Nature check)",
                    "skill_dc": 0,
                    "success_outcome": "Your environmental assessment identifies confirming signs in animal behavior and plant conditions that scientific minds respect. This evidence bridges the gap between mysticism and observable fact."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest creating a fake minor disaster to prove the fortune teller's credibility. (Requires: Deception check)",
                    "outcome": "The staged incident goes out of control, causing real damage and injuries. When the deception is discovered, the fortune teller is held liable for the harm and faces criminal charges."
                },
                {
                    "text": "Recommend making the prediction increasingly extreme and frightening to force attention. (Requires: Intimidation check)",
                    "outcome": "The exaggerated doomsaying creates widespread panic that disrupts normal town functions. When the actual disaster is less apocalyptic than described, the fortune teller is permanently branded a fearmonger."
                },
                {
                    "text": "Advise keeping the prediction secret except for the wealthiest citizens who can pay for warning. (Requires: Persuasion check)",
                    "outcome": "The selective warning is discovered and viewed as exploitative and immoral. The excluded townspeople are furious that their lives were valued less than others."
                },
                {
                    "text": "Propose using illusion magic to show terrifying visions of the disaster to skeptics. (Requires: Illusion check)",
                    "outcome": "The magical manipulation is considered a serious ethical violation. Religious authorities condemn the fortune teller for using fear magic, and protective wards are placed to block further 'magical coercion'."
                },
                {
                    "text": "Suggest claiming the gods will punish anyone who doesn't heed the warning. (Requires: Religion check)",
                    "outcome": "The religious authorities take offense at the presumptuous claim of speaking for the gods. They publicly denounce the fortune teller as a blasphemer, destroying any remaining credibility."
                }
            ]
        }
    },
    {
        "problem": "During a reading, the fortune teller accidentally reveals a client's deeply guarded secret, causing a scandal.",
        "choices": {
            "correct": [
                {
                    "skill": "Persuasion",
                    "text": "Help the fortune teller make a sincere public apology for the breach of trust. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your guidance creates an apology so genuine and heartfelt that public opinion shifts to sympathy. Many view the fortune teller as admirably accountable for an honest mistake."
                },
                {
                    "skill": "Deception",
                    "text": "Create confusion about what was actually revealed by introducing alternative interpretations. (Requires: Deception check)",
                    "skill_dc": 0,
                    "success_outcome": "Your clever reframing suggests multiple possible meanings for the revelation. The ambiguity successfully defuses the scandal as people debate what was actually meant."
                },
                {
                    "skill": "Performance",
                    "text": "Stage a demonstration showing how visions can be easily misinterpreted. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your educational performance about divination's ambiguities convinces onlookers that the 'secret' was likely a misunderstanding. Public curiosity shifts to how fortune telling actually works."
                },
                {
                    "skill": "Insight",
                    "text": "Help the fortune teller understand the client's true feelings to make proper amends. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your perceptive advice helps the fortune teller address the client's actual concerns rather than assumed ones. The personalized approach to reconciliation successfully repairs the relationship."
                },
                {
                    "skill": "Intimidation",
                    "text": "Convince rumormongers that spreading the secret further will bring misfortune. (Requires: Intimidation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your ominous warnings about the karmic consequences of gossip effectively suppress further spread of the secret. The scandal gradually fades as people become reluctant to discuss it."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest accusing the client of planting the information to create a scandal. (Requires: Deception check)",
                    "outcome": "The false counter-accusation enrages the already-wounded client. They use their considerable social connections to ensure the fortune teller is completely boycotted in the region."
                },
                {
                    "text": "Recommend offering free readings to anyone who forgets about the scandal. (Requires: Persuasion check)",
                    "outcome": "The transparent bribe attempt appears desperate and guilty. Worse, dozens claim free readings while continuing to spread the gossip, costing the fortune teller significant income."
                },
                {
                    "text": "Advise using minor memory-affecting magic on witnesses to the revelation. (Requires: Enchantment check)",
                    "outcome": "The unethical magical tampering is detected by a witness with protective amulets. Unauthorized memory manipulation is a serious crime, resulting in magical authorities investigating the fortune teller."
                },
                {
                    "text": "Propose spreading equally scandalous rumors about other prominent citizens as distraction. (Requires: Deception check)",
                    "outcome": "The malicious rumors are quickly traced back to the fortune teller. This deliberate attack on innocent people's reputations destroys any public sympathy and may result in multiple defamation claims."
                },
                {
                    "text": "Suggest fleeing town immediately and setting up shop elsewhere under a new identity. (Requires: Stealth check)",
                    "outcome": "The hasty disappearance confirms guilt in everyone's minds. Stories of the scandal follow to neighboring towns, preceding the fortune teller's arrival and ruining their fresh start."
                }
            ]
        }
    }
],
"The Retired Adventurer": [
    {
        "problem": "The retired adventurer's trophy from their greatest quest has been stolen from their home.",
        "choices": {
            "correct": [
                {
                    "skill": "Investigation",
                    "text": "Search for clues around the adventurer's home about the thief's identity. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your careful examination reveals distinctive bootprints and an unusual lock-picking technique. These clues lead directly to a notorious collectibles thief operating in the region."
                },
                {
                    "skill": "Persuasion",
                    "text": "Ask around town for information about suspicious visitors or recent trophy sales. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your friendly inquiries lead to a traveling merchant who was recently offered the trophy for sale. Their detailed description helps identify and track down the thief."
                },
                {
                    "skill": "Athletics",
                    "text": "Offer to help the adventurer personally track down and confront the thief. (Requires: Athletics check)",
                    "skill_dc": 0,
                    "success_outcome": "Your physical prowess proves essential when you locate the thief attempting to cross a treacherous ravine with the stolen trophy. Your pursuit and capture become a tale worth telling."
                },
                {
                    "skill": "Insight",
                    "text": "Determine who might have both motive and opportunity to steal this specific item. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your psychological analysis narrows the suspects to a jealous rival from the adventurer's past. A confrontation with this specific person quickly leads to the trophy's recovery."
                },
                {
                    "skill": "Survival",
                    "text": "Track the thief through town and into the surrounding wilderness. (Requires: Survival check)",
                    "skill_dc": 0,
                    "success_outcome": "Your exceptional tracking abilities follow the thief's trail to their remote hideout. You recover not only the adventurer's trophy but several other stolen valuables from around town."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest accusing the adventurer's estranged family member without evidence. (Requires: Intimidation check)",
                    "outcome": "The false accusation permanently damages an already strained family relationship. The actual thief remains free while an innocent relative suffers public humiliation."
                },
                {
                    "text": "Recommend claiming the trophy was never stolen but sold to cover gambling debts. (Requires: Deception check)",
                    "outcome": "The rumors about financial problems and dishonesty spread quickly. The adventurer's reputation is severely damaged, and the true thief is never pursued."
                },
                {
                    "text": "Advise hiring a questionable 'curse-caster' to magically punish the unknown thief. (Requires: Arcana check)",
                    "outcome": "The shady magic practitioner takes a substantial payment and performs a useless ritual. The trophy remains missing, and the adventurer has wasted money on a fraudulent service."
                },
                {
                    "text": "Propose breaking into the homes of all suspicious neighbors to search for the trophy. (Requires: Stealth check)",
                    "outcome": "The illegal searches are quickly discovered. The adventurer faces multiple charges of breaking and entering, destroying their standing in the community."
                },
                {
                    "text": "Suggest creating a replica and pretending it was never stolen. (Requires: Crafting check)",
                    "outcome": "The obvious fake doesn't match the detailed descriptions the adventurer has shared for years. The deception is immediately noticed, making the adventurer appear pathetic and desperate."
                }
            ]
        }
    },
    {
        "problem": "The adventurer has been challenged to prove their legendary tales by a skeptical bard collecting stories.",
        "choices": {
            "correct": [
                {
                    "skill": "History",
                    "text": "Research independent accounts that corroborate the adventurer's famous exploits. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your scholarly research uncovers official records, witness accounts, and royal commendations that verify key adventures. The bard is impressed by this thorough documentation."
                },
                {
                    "skill": "Performance",
                    "text": "Help the adventurer tell their stories more convincingly with dramatic flair. (Requires: Performance check)",
                    "skill_dc": 0,
                    "success_outcome": "Your coaching transforms the adventurer's dry recounting into captivating narratives filled with vivid details. The bard is thoroughly convinced by the authentic emotion and specific details."
                },
                {
                    "skill": "Persuasion",
                    "text": "Find witnesses from the adventurer's past who can verify their accomplishments. (Requires: Persuasion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your networking locates several former companions who happily confirm the adventures and even add details the modest retiree omitted. Their testimony thoroughly satisfies the bard."
                },
                {
                    "skill": "Medicine",
                    "text": "Examine the adventurer's scars and injuries that match their harrowing tales. (Requires: Medicine check)",
                    "skill_dc": 0,
                    "success_outcome": "Your medical knowledge confirms that specific scars precisely match the injuries described in the tales. This physical evidence convinces the bard of the stories' authenticity."
                },
                {
                    "skill": "Insight",
                    "text": "Help identify which aspects of the tales the bard finds least believable and address them. (Requires: Insight check)",
                    "skill_dc": 0,
                    "success_outcome": "Your perceptive reading of the bard's reactions helps focus the verification efforts on specific doubtful points. This targeted approach efficiently resolves all the bard's skepticism."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest threatening the bard to stop their questioning and leave town. (Requires: Intimidation check)",
                    "outcome": "The intimidation backfires completely. The bard writes a popular ballad about 'The Fraud of Rivermeet' that permanently damages the adventurer's reputation throughout the region."
                },
                {
                    "text": "Recommend bribing the bard to write flattering, exaggerated accounts. (Requires: Persuasion check)",
                    "outcome": "The bard appears to accept but actually writes an exposé about the attempted bribery. The published account portrays the adventurer as desperate to maintain a facade of false glory."
                },
                {
                    "text": "Advise creating fake 'evidence' like doctored trophies or forged commendations. (Requires: Forgery check)",
                    "outcome": "The experienced bard easily identifies the forgeries. The attempted deception becomes the centerpiece of their new story about fraudulent heroes manipulating public admiration."
                },
                {
                    "text": "Propose using magic to make the bard more gullible and accepting of the stories. (Requires: Enchantment check)",
                    "outcome": "The magical tampering is detected by the bard's protective amulet - standard equipment for those who interview powerful figures. This unethical tactic becomes the focus of a damaging exposé."
                },
                {
                    "text": "Suggest staging a fake monster attack for the adventurer to heroically thwart. (Requires: Deception check)",
                    "outcome": "The poorly executed charade falls apart when a participant accidentally reveals the plan. The public mockery that follows is worse than any skepticism the adventurer faced before."
                }
            ]
        }
    },
    {
        "problem": "The retired adventurer's nightmares about an ancient evil are becoming reality as strange phenomena occur in town.",
        "choices": {
            "correct": [
                {
                    "skill": "Arcana",
                    "text": "Analyze the magical nature of the phenomena to determine their cause. (Requires: Arcana check)",
                    "skill_dc": 0,
                    "success_outcome": "Your magical expertise identifies a dormant psychic link between the adventurer and a defeated enemy that's gradually reactivating. With this knowledge, the connection can be safely severed."
                },
                {
                    "skill": "History",
                    "text": "Research the ancient evil from historical records to find its weaknesses. (Requires: History check)",
                    "skill_dc": 0,
                    "success_outcome": "Your scholarly investigation uncovers crucial information about the entity that was missing from the adventurer's knowledge. This historical insight provides the key to resolving the supernatural events."
                },
                {
                    "skill": "Investigation",
                    "text": "Examine the pattern of strange occurrences for clues about what's happening. (Requires: Investigation check)",
                    "skill_dc": 0,
                    "success_outcome": "Your systematic analysis reveals the phenomena follow a specific sequence that matches an ancient ritual of return. Understanding the pattern allows you to disrupt the process before completion."
                },
                {
                    "skill": "Religion",
                    "text": "Consult with religious authorities about spiritual protections against ancient evils. (Requires: Religion check)",
                    "skill_dc": 0,
                    "success_outcome": "Your theological approach secures help from diverse faith leaders who combine their blessings in a powerful protection ritual. Their combined spiritual strength successfully repels the supernatural threat."
                },
                {
                    "skill": "Survival",
                    "text": "Track the supernatural phenomena to their source location. (Requires: Survival check)",
                    "skill_dc": 0,
                    "success_outcome": "Your keen tracking identifies a pattern in the manifestations that leads to a forgotten shrine beneath the town. Sealing this magical focal point immediately ends the disturbances."
                }
            ],
            "incorrect": [
                {
                    "text": "Suggest ignoring the nightmares and phenomena as mere coincidence. (Requires: Insight check)",
                    "outcome": "The neglected supernatural threat grows stronger each day. Within a week, violent manifestations begin causing physical harm to townspeople, with the adventurer bearing moral responsibility for the inaction."
                },
                {
                    "text": "Recommend the adventurer leave town to draw the evil presence away. (Requires: Deception check)",
                    "outcome": "The established magical connection is unaffected by distance. The phenomena intensify in the adventurer's absence with no one present who understands their significance or how to fight them."
                },
                {
                    "text": "Advise conducting an amateur exorcism ritual found in an old book. (Requires: Religion check)",
                    "outcome": "The improperly performed ritual actually strengthens the supernatural presence by acknowledging and feeding it attention. The manifestations immediately become more frequent and dangerous."
                },
                {
                    "text": "Propose publicly blaming a marginalized town resident for causing the phenomena. (Requires: Deception check)",
                    "outcome": "The baseless accusation creates a witch hunt atmosphere that divides the town when unity is needed most. The actual supernatural threat grows unchecked while resources are wasted persecuting an innocent."
                },
                {
                    "text": "Suggest using forbidden magic to fight the ancient evil directly. (Requires: Arcana check)",
                    "outcome": "The dangerous magical attempt backfires catastrophically, creating a direct conduit for the ancient evil to manifest physically. What was a gradual, creeping threat becomes an immediate crisis."
                }
            ]
        }
    }
]



            }
        }