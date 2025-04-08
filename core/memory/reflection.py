import os
import json
import time
from typing import Dict, List, Any, Optional
import uuid

class Reflection:
    """
    Reflection system for memory consolidation and insights.
    Analyzes memories to generate higher-level understanding.
    """
    
    def __init__(self, memory_manager, storage, embedding_provider):
        """
        Initialize reflection system.
        
        Args:
            memory_manager: MemoryManager instance
            storage: ChromaDB storage instance
            embedding_provider: Text embedding provider
        """
        self.memory_manager = memory_manager
        self.storage = storage
        self.embedding_provider = embedding_provider
        
        # Create reflection directories
        os.makedirs("data/aina/reflections/daily", exist_ok=True)
        os.makedirs("data/aina/reflections/weekly", exist_ok=True)
    
    def create_reflection(self, reflection_type: str = 'daily') -> Dict[str, Any]:
        """
        Create a new reflection by analyzing recent memories.
        
        Args:
            reflection_type: Type of reflection ('daily' or 'weekly')
            
        Returns:
            Reflection result
        """
        # Determine time window based on reflection type
        if reflection_type == 'daily':
            hours = 24.0
            max_memories = 100
        elif reflection_type == 'weekly':
            hours = 168.0  # 7 days
            max_memories = 300
        else:
            raise ValueError(f"Unknown reflection type: {reflection_type}")
        
        # Get recent memories to reflect on
        episodic_memories = self.memory_manager.episodic_memory.get_recent_memories(
            hours=hours, 
            limit=max_memories,
            min_importance=0.3
        )
        
        # If no memories, create a simple reflection
        if not episodic_memories:
            reflection = {
                "id": str(uuid.uuid4()),
                "type": reflection_type,
                "timestamp": time.time(),
                "summary": f"No significant memories found in the past {hours/24} days.",
                "insights": [],
                "memory_count": 0
            }
            
            # Save reflection to file
            self._save_reflection(reflection)
            
            return reflection
        
        # Process memories
        sorted_memories = sorted(
            episodic_memories,
            key=lambda x: x.get("metadata", {}).get("importance", 0) * 0.8 + 
                         x.get("metadata", {}).get("timestamp", 0) * 0.2,
            reverse=True
        )
        
        # Extract main events
        main_events = []
        for memory in sorted_memories[:10]:  # Top 10 important/recent memories
            event = {
                "text": memory["text"],
                "timestamp": memory.get("metadata", {}).get("timestamp", 0),
                "importance": memory.get("metadata", {}).get("importance", 0.5)
            }
            main_events.append(event)
        
        # Generate summary and insights
        summary = self._generate_summary(sorted_memories, reflection_type)
        insights = self._generate_insights(sorted_memories, reflection_type)
        
        # Create reflection object
        reflection = {
            "id": str(uuid.uuid4()),
            "type": reflection_type,
            "timestamp": time.time(),
            "summary": summary,
            "insights": insights,
            "main_events": main_events,
            "memory_count": len(episodic_memories)
        }
        
        # Save reflection to file
        self._save_reflection(reflection)
        
        # Add important insights to semantic memory
        self._store_insights(insights)
        
        return reflection
    
    def _generate_summary(self, memories: List[Dict[str, Any]], reflection_type: str) -> str:
        """
        Generate a summary of memories.
        
        Args:
            memories: List of memories to summarize
            reflection_type: Type of reflection
            
        Returns:
            Summary text
        """
        # Simple implementation - in a real system this would use an LLM
        # Here we just concatenate the most important memories
        
        if reflection_type == 'daily':
            summary = "Daily summary of recent experiences:\n\n"
        else:
            summary = "Weekly summary of experiences:\n\n"
        
        # Get top memories by importance
        top_memories = sorted(
            memories,
            key=lambda x: x.get("metadata", {}).get("importance", 0),
            reverse=True
        )[:5]  # Top 5 important memories
        
        for i, memory in enumerate(top_memories, 1):
            timestamp = memory.get("metadata", {}).get("timestamp", 0)
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            importance = memory.get("metadata", {}).get("importance", 0.5)
            
            summary += f"{i}. [{time_str}] (Importance: {importance:.1f}) {memory['text']}\n"
        
        # Add memory count
        summary += f"\nTotal memories analyzed: {len(memories)}"
        
        return summary
    
    def _generate_insights(self, memories: List[Dict[str, Any]], reflection_type: str) -> List[Dict[str, Any]]:
        """
        Generate insights from memories.
        
        Args:
            memories: List of memories to analyze
            reflection_type: Type of reflection
            
        Returns:
            List of insights
        """
        # Simple implementation - in a real system this would use an LLM
        # to generate deeper insights
        
        insights = []
        
        # In a real system, we would use more sophisticated analysis
        # For now, we'll just create a simple insight about activity level
        
        activity_insight = {
            "id": str(uuid.uuid4()),
            "text": f"Activity level: {len(memories)} memories recorded.",
            "category": "activity",
            "importance": 0.5
        }
        insights.append(activity_insight)
        
        # Add user interaction insight if applicable
        user_interactions = {}
        for memory in memories:
            user_id = memory.get("metadata", {}).get("user_id")
            if user_id:
                if user_id not in user_interactions:
                    user_interactions[user_id] = 0
                user_interactions[user_id] += 1
        
        if user_interactions:
            most_active_user = max(user_interactions.items(), key=lambda x: x[1])
            user_insight = {
                "id": str(uuid.uuid4()),
                "text": f"Most interactions were with user {most_active_user[0]} ({most_active_user[1]} interactions).",
                "category": "user_interaction",
                "importance": 0.6
            }
            insights.append(user_insight)
        
        # Add time-based insight
        if memories:
            timestamps = [m.get("metadata", {}).get("timestamp", 0) for m in memories]
            min_time = min(timestamps)
            max_time = max(timestamps)
            
            time_span = max_time - min_time
            time_span_hours = time_span / 3600
            
            if time_span_hours > 0:
                activity_rate = len(memories) / time_span_hours
                
                time_insight = {
                    "id": str(uuid.uuid4()),
                    "text": f"Activity rate: {activity_rate:.2f} memories per hour over {time_span_hours:.1f} hours.",
                    "category": "time_analysis",
                    "importance": 0.5
                }
                insights.append(time_insight)
        
        return insights
    
    def _store_insights(self, insights: List[Dict[str, Any]]) -> None:
        """
        Store important insights in semantic memory.
        
        Args:
            insights: List of insights to store
        """
        for insight in insights:
            # Only store insights with high importance
            if insight.get("importance", 0) >= 0.6:
                self.memory_manager.semantic_memory.store_fact(
                    text=insight["text"],
                    category="reflection_insight",
                    source="reflection",
                    importance=insight["importance"],
                    tags=["reflection", insight.get("category", "general")]
                )
    
    def _save_reflection(self, reflection: Dict[str, Any]) -> None:
        """
        Save reflection to file.
        
        Args:
            reflection: Reflection data
        """
        # Determine file path
        date_str = time.strftime("%Y-%m-%d", time.localtime(reflection["timestamp"]))
        
        if reflection["type"] == "daily":
            file_path = f"data/aina/reflections/daily/{date_str}.json"
        else:  # weekly
            year_week = time.strftime("%Y-W%W", time.localtime(reflection["timestamp"]))
            file_path = f"data/aina/reflections/weekly/{year_week}.json"
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(reflection, f, indent=2)
    
    def get_latest_reflection(self, reflection_type: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        Get the latest reflection of specified type.
        
        Args:
            reflection_type: Type of reflection ('daily' or 'weekly')
            
        Returns:
            Latest reflection or None if not found
        """
        if reflection_type == 'daily':
            reflection_dir = "data/aina/reflections/daily"
        else:  # weekly
            reflection_dir = "data/aina/reflections/weekly"
        
        if not os.path.exists(reflection_dir):
            return None
        
        # List reflection files
        reflection_files = [f for f in os.listdir(reflection_dir) if f.endswith('.json')]
        
        if not reflection_files:
            return None
        
        # Sort files by name (which includes date)
        reflection_files.sort(reverse=True)
        
        # Load latest reflection
        latest_file = os.path.join(reflection_dir, reflection_files[0])
        
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading reflection file {latest_file}: {e}")
            return None
    
    def get_reflection(self, reflection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific reflection by ID.
        
        Args:
            reflection_id: Reflection ID
            
        Returns:
            Reflection data or None if not found
        """
        # Search in daily reflections
        daily_dir = "data/aina/reflections/daily"
        if os.path.exists(daily_dir):
            for file_name in os.listdir(daily_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(daily_dir, file_name)
                    try:
                        with open(file_path, 'r') as f:
                            reflection = json.load(f)
                            if reflection.get("id") == reflection_id:
                                return reflection
                    except Exception:
                        continue
        
        # Search in weekly reflections
        weekly_dir = "data/aina/reflections/weekly"
        if os.path.exists(weekly_dir):
            for file_name in os.listdir(weekly_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(weekly_dir, file_name)
                    try:
                        with open(file_path, 'r') as f:
                            reflection = json.load(f)
                            if reflection.get("id") == reflection_id:
                                return reflection
                    except Exception:
                        continue
        
        return None
    
    def list_reflections(self, reflection_type: str = 'daily', limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent reflections of specified type.
        
        Args:
            reflection_type: Type of reflection ('daily' or 'weekly')
            limit: Maximum number of reflections to return
            
        Returns:
            List of reflection metadata
        """
        if reflection_type == 'daily':
            reflection_dir = "data/aina/reflections/daily"
        else:  # weekly
            reflection_dir = "data/aina/reflections/weekly"
        
        if not os.path.exists(reflection_dir):
            return []
        
        # List reflection files
        reflection_files = [f for f in os.listdir(reflection_dir) if f.endswith('.json')]
        
        if not reflection_files:
            return []
        
        # Sort files by name (which includes date)
        reflection_files.sort(reverse=True)
        
        # Limit number of files
        reflection_files = reflection_files[:limit]
        
        # Load reflections
        reflections = []
        for file_name in reflection_files:
            file_path = os.path.join(reflection_dir, file_name)
            try:
                with open(file_path, 'r') as f:
                    reflection = json.load(f)
                    # Add just the metadata, not the full content
                    reflections.append({
                        "id": reflection.get("id"),
                        "type": reflection.get("type"),
                        "timestamp": reflection.get("timestamp"),
                        "memory_count": reflection.get("memory_count"),
                        "file_name": file_name
                    })
            except Exception as e:
                print(f"❌ Error loading reflection file {file_path}: {e}")
        
        return reflections