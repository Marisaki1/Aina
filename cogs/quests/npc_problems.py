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
                ]
            }
        }