# cogs/quests/llm_manager.py
import asyncio
from cogs.conversation.llm_core import LLMManager as CoreLLMManager

class LLMManager(CoreLLMManager):
    """
    LLM Manager for quests that extends the core LLM implementation
    with quest-specific functionality and async support.
    """
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from the LLM model asynchronously.
        
        Args:
            prompt: The input prompt for the model
            **kwargs: Additional parameters for generation
            
        Returns:
            The generated text response
        """
        try:
            # Using run_in_executor to make synchronous code async
            loop = asyncio.get_event_loop()
            
            # Get user_id from kwargs or use a default for quest system
            user_id = kwargs.pop("user_id", "quest_system")
            
            # Get system prompt from kwargs or use a quest-specific one
            system_prompt = kwargs.pop("system_prompt", 
                "You are a fantasy quest generator. Create engaging scenarios with choices and outcomes.")
            
            # Use the parent class's get_response method
            response = await loop.run_in_executor(
                None, 
                self.get_response,
                user_id,
                prompt,
                system_prompt
            )
            
            return response
            
        except Exception as e:
            print(f"Error generating text: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """
        Provide a fallback response if the model fails.
        """
        if "Random Encounter" in prompt:
            # Battle scenario
            return """
            Scenario:
            You encounter a pack of wolves circling around you, their eyes gleaming with hunger in the moonlight.
            
            Choices:
            1. Try to run away at full speed
            2. Stand your ground and make yourself look bigger
            3. Throw your rations away from you as a distraction
            
            Outcomes:
            1. ❌ The wolves are faster than you and quickly surround you, resulting in several painful bites.
            2. ✅ Your confident stance and loud shouts confuse the wolves. The pack leader hesitates, then retreats with the others following. You find a small treasure they were guarding. Gain 175 XP and 30 Gold!
            3. ❌ The wolves take your food but still consider you prey. They approach even more aggressively now.
            """
        else:
            # Normal scenario
            return """
            Scenario:
            You find an old chest partially buried beneath some roots near a stream. It appears to be locked.
            
            Choices:
            1. Break the lock with your weapon
            2. Examine the lock carefully for traps before attempting to pick it
            3. Try to pry the chest open with force
            
            Outcomes:
            1. ❌ Your weapon strikes the lock and triggers a hidden mechanism! A small dart flies out and grazes your arm, causing a painful sting.
            2. ✅ Your careful examination reveals a tiny needle trap which you safely disarm. The lock opens with a satisfying click, revealing 45 gold coins and a small gemstone. Gain 200 XP for your caution!
            3. ❌ As you apply force, the chest's hinges break awkwardly, damaging some of the contents inside. Several valuable items are now ruined.
            """