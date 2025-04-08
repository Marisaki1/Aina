import os
import time
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

class ReflectionEnhancer:
    """
    Enhances the memory reflection system using LLM integration.
    Provides deeper insights, pattern recognition, and memory consolidation.
    """
    
    def __init__(self, memory_manager, llm_manager):
        """
        Initialize reflection enhancer.
        
        Args:
            memory_manager: MemoryManager instance
            llm_manager: LLMManager instance
        """
        self.memory_manager = memory_manager
        self.llm_manager = llm_manager
        
        # Create reflection directory if it doesn't exist
        os.makedirs("data/aina/reflections", exist_ok=True)
    
    def generate_enhanced_reflection(self, 
                                   reflection_type: str = 'daily',
                                   max_memories: int = 100) -> Dict[str, Any]:
        """
        Generate an enhanced reflection using the LLM.
        
        Args:
            reflection_type: Type of reflection ('daily' or 'weekly')
            max_memories: Maximum number of memories to consider
            
        Returns:
            Enhanced reflection data
        """
        print(f"🔄 Generating enhanced {reflection_type} reflection...")
        
        # Determine time window based on reflection type
        if reflection_type == 'daily':
            hours = 24.0
            title = "Daily Reflection"
        elif reflection_type == 'weekly':
            hours = 168.0  # 7 days
            title = "Weekly Reflection"
        else:
            raise ValueError(f"Unknown reflection type: {reflection_type}")
        
        # Get recent memories
        episodic_memories = self.memory_manager.episodic_memory.get_recent_memories(
            hours=hours, 
            limit=max_memories,
            min_importance=0.3
        )
        
        # If no memories, return basic reflection
        if not episodic_memories:
            return {
                "type": reflection_type,
                "timestamp": time.time(),
                "title": title,
                "summary": f"No significant memories found in the past {hours/24} days.",
                "insights": [],
                "patterns": [],
                "memory_count": 0
            }
        
        # Create memory text for LLM
        memory_text = self._format_memories_for_llm(episodic_memories)
        
        # Generate reflection using LLM
        reflection_data = self._generate_reflection_with_llm(memory_text, reflection_type)
        
        # Add metadata
        reflection_data["type"] = reflection_type
        reflection_data["timestamp"] = time.time()
        reflection_data["title"] = title
        reflection_data["memory_count"] = len(episodic_memories)
        
        # Save reflection
        self._save_reflection(reflection_data, reflection_type)
        
        # Store insights in semantic memory
        self._store_insights(reflection_data)
        
        return reflection_data
    
    def _format_memories_for_llm(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories as text for the LLM."""
        formatted_text = "Recent memories:\n\n"
        
        for i, memory in enumerate(memories, 1):
            # Get metadata
            timestamp = memory.get("metadata", {}).get("timestamp", 0)
            importance = memory.get("metadata", {}).get("importance", 0.5)
            memory_type = memory.get("metadata", {}).get("memory_type", "general")
            
            # Format timestamp
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format memory
            formatted_text += f"{i}. [{time_str}] (Importance: {importance:.2f}, Type: {memory_type})\n"
            formatted_text += f"   {memory['text']}\n\n"
        
        return formatted_text
    
    def _generate_reflection_with_llm(self, memory_text: str, reflection_type: str) -> Dict[str, Any]:
        """Generate reflection using the LLM."""
        # Create system prompt
        system_prompt = """You are an advanced AI reflection system that analyzes memories and generates insights.
Your task is to analyze the provided memories and create a comprehensive reflection.
Be insightful, thoughtful, and look for patterns, themes, and important information.

Your reflection should include:
1. A concise yet comprehensive summary of the key events and interactions
2. Insightful observations about patterns, preferences, or notable points
3. Identification of recurring themes or elements
4. Recognition of any changes or trends over time
5. Suggestions for areas of focus or improvement

Focus on extracting meaningful insights rather than just summarizing individual memories."""
        
        # Create user prompt
        user_prompt = f"""Please analyze these memories and create a {reflection_type} reflection:

{memory_text}

Please format your response as a JSON object with the following structure:
{{
  "summary": "A comprehensive summary of key events and activities",
  "insights": [
    {{"text": "First insight", "category": "category1", "importance": 0.8}},
    {{"text": "Second insight", "category": "category2", "importance": 0.6}}
  ],
  "patterns": [
    {{"pattern": "Description of pattern", "evidence": "Evidence from memories", "confidence": 0.7}}
  ],
  "themes": ["theme1", "theme2", "theme3"],
  "focus_areas": ["area1", "area2"]
}}

Make sure the JSON is valid and properly formatted."""
        
        try:
            # Get reflection from LLM
            system_prompt = system_prompt.replace("\n", " ")
            response = self.llm_manager.get_response(
                user_id="reflection_system",
                prompt=user_prompt,
                system_prompt=system_prompt,
                interface_type="system",
                context={"reflection_type": reflection_type}
            )
            
            # Extract JSON from response
            json_text = self._extract_json(response)
            
            # Parse JSON
            try:
                reflection_data = json.loads(json_text)
                print("✅ Successfully generated enhanced reflection with LLM")
                return reflection_data
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing reflection JSON: {e}")
                print(f"Raw response: {response}")
                
                # Fallback to basic reflection
                return self._generate_basic_reflection(memory_text, reflection_type)
                
        except Exception as e:
            print(f"❌ Error generating reflection with LLM: {e}")
            
            # Fallback to basic reflection
            return self._generate_basic_reflection(memory_text, reflection_type)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON string from text."""
        # Look for JSON block
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            return text[json_start:json_end+1]
        else:
            # Try to clean up the text
            cleaned_text = text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
                
            # Try again
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                return cleaned_text[json_start:json_end+1]
            
            raise ValueError("Could not extract JSON from LLM response")
    
    def _generate_basic_reflection(self, memory_text: str, reflection_type: str) -> Dict[str, Any]:
        """Generate a basic reflection without LLM."""
        print("⚠️ Falling back to basic reflection generation")
        
        # Create a simple summary
        lines = memory_text.strip().split('\n')
        memory_count = len([line for line in lines if line.strip() and line[0].isdigit()])
        
        summary = f"Analyzed {memory_count} memories from the past "
        summary += "day" if reflection_type == 'daily' else "week"
        
        # Create a simple insight
        insights = [
            {
                "text": f"Activity level: {memory_count} memories recorded.",
                "category": "activity",
                "importance": 0.5
            }
        ]
        
        return {
            "summary": summary,
            "insights": insights,
            "patterns": [],
            "themes": [],
            "focus_areas": []
        }
    
    def _save_reflection(self, reflection_data: Dict[str, Any], reflection_type: str) -> None:
        """Save reflection to file."""
        # Generate file path
        date_str = datetime.fromtimestamp(reflection_data["timestamp"]).strftime("%Y-%m-%d")
        
        if reflection_type == "daily":
            file_path = f"data/aina/reflections/daily/{date_str}.json"
        else:  # weekly
            year_week = datetime.fromtimestamp(reflection_data["timestamp"]).strftime("%Y-W%W")
            file_path = f"data/aina/reflections/weekly/{year_week}.json"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(reflection_data, f, indent=2)
    
    def _store_insights(self, reflection_data: Dict[str, Any]) -> None:
        """Store important insights in semantic memory."""
        if "insights" not in reflection_data:
            return
        
        for insight in reflection_data["insights"]:
            # Only store insights with high importance
            importance = insight.get("importance", 0.5)
            if importance >= 0.6:
                self.memory_manager.semantic_memory.store_fact(
                    text=insight["text"],
                    category="reflection_insight",
                    source="enhanced_reflection",
                    importance=importance,
                    tags=["reflection", insight.get("category", "general")]
                )
        
        # Store patterns if available
        if "patterns" in reflection_data:
            for pattern in reflection_data["patterns"]:
                confidence = pattern.get("confidence", 0.5)
                if confidence >= 0.6:
                    self.memory_manager.semantic_memory.store_concept(
                        text=f"Pattern: {pattern['pattern']}. Evidence: {pattern.get('evidence', 'None')}",
                        concept_name=f"pattern_{int(time.time())}",
                        category="pattern",
                        importance=confidence,
                        tags=["reflection", "pattern"]
                    )
    
    def analyze_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user behavior patterns using LLM.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Analysis results
        """
        # Get user memories
        user_memories = self.memory_manager.get_user_memories(user_id, limit=100)
        
        if not user_memories:
            return {
                "status": "error",
                "message": "No memories found for this user"
            }
        
        # Format memories
        memory_text = self._format_memories_for_llm(user_memories)
        
        # Create system prompt
        system_prompt = """You are an advanced AI behavior analysis system that analyzes user interactions.
Your task is to analyze the provided memories about a user and identify behavior patterns, preferences, and traits.
Be insightful, thoughtful, and look for consistent patterns without making unfounded assumptions.

Your analysis should include:
1. Key personality traits observed
2. User preferences and interests
3. Interaction patterns
4. Potential areas of improvement for the AI's interactions with this user

Focus on evidence-based observations rather than speculation."""
        
        # Create user prompt
        user_prompt = f"""Please analyze these memories about user {user_id} and create a behavior analysis:

{memory_text}

Please format your response as a JSON object with the following structure:
{{
  "traits": [
    {{"trait": "trait description", "evidence": "evidence from memories", "confidence": 0.8}}
  ],
  "preferences": [
    {{"preference": "preference description", "category": "category", "evidence": "evidence", "confidence": 0.7}}
  ],
  "interaction_patterns": [
    {{"pattern": "pattern description", "evidence": "evidence from memories", "significance": 0.6}}
  ],
  "recommendations": [
    {{"recommendation": "how to improve interactions", "reasoning": "reason for recommendation"}}
  ]
}}

Make sure the JSON is valid and properly formatted."""
        
        try:
            # Get analysis from LLM
            system_prompt = system_prompt.replace("\n", " ")
            response = self.llm_manager.get_response(
                user_id="analysis_system",
                prompt=user_prompt,
                system_prompt=system_prompt,
                interface_type="system",
                context={"user_id": user_id}
            )
            
            # Extract JSON from response
            json_text = self._extract_json(response)
            
            # Parse JSON
            try:
                analysis_data = json.loads(json_text)
                analysis_data["status"] = "success"
                
                # Store insights
                self._store_user_insights(user_id, analysis_data)
                
                return analysis_data
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing user analysis JSON: {e}")
                print(f"Raw response: {response}")
                
                return {
                    "status": "error",
                    "message": "Error parsing analysis results",
                    "raw_response": response
                }
                
        except Exception as e:
            print(f"❌ Error generating user analysis: {e}")
            
            return {
                "status": "error",
                "message": f"Error analyzing user behavior: {str(e)}"
            }
    
    def _store_user_insights(self, user_id: str, analysis_data: Dict[str, Any]) -> None:
        """Store user insights in personal memory."""
        # Store traits
        if "traits" in analysis_data:
            for trait in analysis_data["traits"]:
                if trait.get("confidence", 0) >= 0.6:
                    self.memory_manager.personal_memory.store_user_trait(
                        user_id=user_id,
                        text=f"{trait['trait']}. Evidence: {trait.get('evidence', 'None')}",
                        trait_type="personality",
                        importance=trait.get("confidence", 0.6)
                    )
        
        # Store preferences
        if "preferences" in analysis_data:
            for pref in analysis_data["preferences"]:
                if pref.get("confidence", 0) >= 0.6:
                    self.memory_manager.personal_memory.store_user_preference(
                        user_id=user_id,
                        text=f"{pref['preference']}. Evidence: {pref.get('evidence', 'None')}",
                        preference_type=pref.get("category", "general"),
                        importance=pref.get("confidence", 0.6)
                    )
        
        # Store interaction summary
        if "interaction_patterns" in analysis_data:
            patterns_text = "\n".join([
                f"- {pattern['pattern']}" 
                for pattern in analysis_data["interaction_patterns"]
                if pattern.get("significance", 0) >= 0.5
            ])
            
            if patterns_text:
                date_str = datetime.now().strftime("%Y-%m-%d")
                self.memory_manager.personal_memory.store_interaction_summary(
                    user_id=user_id,
                    text=f"Interaction patterns: {patterns_text}",
                    date=date_str,
                    importance=0.8
                )