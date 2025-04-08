import os
import json
import time
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

# Set up logger
logger = logging.getLogger("aina.visualizer")

class MemoryVisualizer:
    """
    Creates visualizations of memory structures and relationships.
    Generates data for graph visualizations and relationship networks.
    """
    
    def __init__(self, memory_manager):
        """
        Initialize memory visualizer.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        
        # Create directory for visualization data
        os.makedirs("data/aina/visualizations", exist_ok=True)
        
        logger.info("Memory visualizer initialized")
    
    def generate_memory_graph(self, max_memories: int = 200) -> Dict[str, Any]:
        """
        Generate a graph visualization of the memory system.
        
        Args:
            max_memories: Maximum number of memories to include
            
        Returns:
            Graph data for visualization
        """
        logger.info(f"Generating memory graph (max {max_memories} memories)...")
        
        try:
            # Get memories from each type
            memories = {
                "core": self.memory_manager.retrieve_all_memories("core", limit=50),
                "episodic": self.memory_manager.retrieve_all_memories("episodic", limit=max_memories // 2),
                "semantic": self.memory_manager.retrieve_all_memories("semantic", limit=max_memories // 4),
                "personal": self.memory_manager.retrieve_all_memories("personal", limit=max_memories // 4)
            }
            
            # Count total memories
            total_memories = sum(len(mems) for mems in memories.values())
            
            # Generate nodes and links
            nodes = []
            links = []
            node_map = {}  # Map memory IDs to node indices
            
            # Create central node for each memory type
            core_idx = 0
            nodes.append({
                "id": "core",
                "name": "Core Memory",
                "type": "core_center",
                "size": 20,
                "color": "#0d6efd"
            })
            node_map["core"] = core_idx
            
            episodic_idx = 1
            nodes.append({
                "id": "episodic",
                "name": "Episodic Memory",
                "type": "episodic_center",
                "size": 20,
                "color": "#198754"
            })
            node_map["episodic"] = episodic_idx
            
            semantic_idx = 2
            nodes.append({
                "id": "semantic",
                "name": "Semantic Memory",
                "type": "semantic_center",
                "size": 20,
                "color": "#dc3545"
            })
            node_map["semantic"] = semantic_idx
            
            personal_idx = 3
            nodes.append({
                "id": "personal",
                "name": "Personal Memory",
                "type": "personal_center",
                "size": 20,
                "color": "#6f42c1"
            })
            node_map["personal"] = personal_idx
            
            # Process memory types
            current_idx = 4
            
            # Add core memories
            for memory in memories["core"]:
                node = {
                    "id": memory["id"],
                    "name": self._truncate_text(memory["text"], 50),
                    "type": "core",
                    "size": 7 + (memory.get("metadata", {}).get("importance", 0.5) * 5),
                    "color": "#0d6efd",
                    "full_text": memory["text"],
                    "importance": memory.get("metadata", {}).get("importance", 0.5),
                    "timestamp": memory.get("metadata", {}).get("timestamp")
                }
                nodes.append(node)
                node_map[memory["id"]] = current_idx
                
                # Link to core center
                links.append({
                    "source": core_idx,
                    "target": current_idx,
                    "value": 2
                })
                
                current_idx += 1
            
            # Add episodic memories
            for memory in memories["episodic"]:
                node = {
                    "id": memory["id"],
                    "name": self._truncate_text(memory["text"], 50),
                    "type": "episodic",
                    "size": 5 + (memory.get("metadata", {}).get("importance", 0.5) * 5),
                    "color": "#198754",
                    "full_text": memory["text"],
                    "importance": memory.get("metadata", {}).get("importance", 0.5),
                    "timestamp": memory.get("metadata", {}).get("timestamp")
                }
                nodes.append(node)
                node_map[memory["id"]] = current_idx
                
                # Link to episodic center
                links.append({
                    "source": episodic_idx,
                    "target": current_idx,
                    "value": 1
                })
                
                current_idx += 1
            
            # Add semantic memories
            for memory in memories["semantic"]:
                node = {
                    "id": memory["id"],
                    "name": self._truncate_text(memory["text"], 50),
                    "type": "semantic",
                    "size": 6 + (memory.get("metadata", {}).get("importance", 0.5) * 5),
                    "color": "#dc3545",
                    "full_text": memory["text"],
                    "importance": memory.get("metadata", {}).get("importance", 0.5),
                    "category": memory.get("metadata", {}).get("category")
                }
                nodes.append(node)
                node_map[memory["id"]] = current_idx
                
                # Link to semantic center
                links.append({
                    "source": semantic_idx,
                    "target": current_idx,
                    "value": 1
                })
                
                current_idx += 1
            
            # Add personal memories
            for memory in memories["personal"]:
                node = {
                    "id": memory["id"],
                    "name": self._truncate_text(memory["text"], 50),
                    "type": "personal",
                    "size": 6 + (memory.get("metadata", {}).get("importance", 0.5) * 5),
                    "color": "#6f42c1",
                    "full_text": memory["text"],
                    "importance": memory.get("metadata", {}).get("importance", 0.5),
                    "user_id": memory.get("metadata", {}).get("user_id")
                }
                nodes.append(node)
                node_map[memory["id"]] = current_idx
                
                # Link to personal center
                links.append({
                    "source": personal_idx,
                    "target": current_idx,
                    "value": 1
                })
                
                current_idx += 1
            
            # Create additional links based on relationships
            self._add_semantic_links(nodes, links, node_map, memories)
            
            # Generate graph data
            graph_data = {
                "nodes": nodes,
                "links": links,
                "stats": {
                    "total_memories": total_memories,
                    "core_memories": len(memories["core"]),
                    "episodic_memories": len(memories["episodic"]),
                    "semantic_memories": len(memories["semantic"]),
                    "personal_memories": len(memories["personal"]),
                    "total_nodes": len(nodes),
                    "total_links": len(links)
                },
                "timestamp": time.time()
            }
            
            # Save graph data
            self._save_visualization(graph_data, "memory_graph")
            
            logger.info(f"Memory graph generated with {len(nodes)} nodes and {len(links)} links")
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Error generating memory graph: {e}")
            return {
                "error": f"Failed to generate memory graph: {str(e)}"
            }
    
    def generate_user_network(self) -> Dict[str, Any]:
        """
        Generate a network visualization of users and their relationships.
        
        Returns:
            Network data for visualization
        """
        logger.info("Generating user network visualization...")
        
        try:
            # Get all personal memories
            personal_memories = self.memory_manager.retrieve_all_memories("personal", limit=1000)
            
            # Get unique user IDs
            user_ids = set()
            for memory in personal_memories:
                user_id = memory.get("metadata", {}).get("user_id")
                if user_id:
                    user_ids.add(user_id)
            
            if not user_ids:
                return {"error": "No users found"}
            
            # Get episodic memories about user interactions
            episodic_memories = self.memory_manager.retrieve_all_memories("episodic", limit=1000)
            
            # Process memories
            user_nodes = []
            user_links = []
            user_info = {}
            interaction_counts = defaultdict(int)
            
            # Create user nodes
            for user_id in user_ids:
                # Get user profile
                profile = self.memory_manager.personal_memory.get_user_profile(user_id)
                
                # Extract user information
                traits = []
                if profile and "traits" in profile:
                    traits = [trait["text"] for trait in profile["traits"][:3]]
                
                preferences = []
                if profile and "preferences" in profile:
                    preferences = [pref["text"] for pref in profile["preferences"][:3]]
                
                # Add user node
                user_nodes.append({
                    "id": user_id,
                    "name": f"User {user_id}",
                    "type": "user",
                    "size": 15,
                    "color": "#4b0082",  # Indigo
                    "traits": traits,
                    "preferences": preferences
                })
                
                # Store user info
                user_info[user_id] = {
                    "traits": traits,
                    "preferences": preferences
                }
            
            # Find interactions between users
            for memory in episodic_memories:
                metadata = memory.get("metadata", {})
                memory_type = metadata.get("memory_type")
                
                # Check if this is an interaction memory
                if memory_type == "interaction":
                    text = memory["text"].lower()
                    
                    # Look for mentions of other users
                    mentioned_users = []
                    
                    for user_id in user_ids:
                        if f"user {user_id}" in text:
                            mentioned_users.append(user_id)
                    
                    # If user is mentioned and we have a source user
                    if mentioned_users and "user_id" in metadata:
                        source_user = metadata["user_id"]
                        
                        for target_user in mentioned_users:
                            if source_user != target_user:
                                # Increment interaction count
                                key = tuple(sorted([source_user, target_user]))
                                interaction_counts[key] += 1
            
            # Create links based on interaction counts
            for (user1, user2), count in interaction_counts.items():
                if count >= 1:
                    # Create link between users
                    user_links.append({
                        "source": user1,
                        "target": user2,
                        "value": min(10, count),  # Cap at 10 for visualization
                        "count": count
                    })
            
            # Generate network data
            network_data = {
                "nodes": user_nodes,
                "links": user_links,
                "stats": {
                    "total_users": len(user_nodes),
                    "total_interactions": sum(interaction_counts.values())
                },
                "timestamp": time.time()
            }
            
            # Save network data
            self._save_visualization(network_data, "user_network")
            
            logger.info(f"User network generated with {len(user_nodes)} users and {len(user_links)} connections")
            
            return network_data
            
        except Exception as e:
            logger.error(f"Error generating user network: {e}")
            return {
                "error": f"Failed to generate user network: {str(e)}"
            }
    
    def generate_memory_timeline(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate a timeline visualization of memories.
        
        Args:
            days: Number of days to include
            
        Returns:
            Timeline data for visualization
        """
        logger.info(f"Generating memory timeline for the past {days} days...")
        
        try:
            # Calculate time window
            end_time = time.time()
            start_time = end_time - (days * 24 * 3600)
            
            # Get episodic memories within time window
            episodic_memories = self.memory_manager.episodic_memory.get_recent_memories(
                hours=days * 24,
                limit=1000,
                min_importance=0.0
            )
            
            # Process memories
            events = []
            
            for memory in episodic_memories:
                timestamp = memory.get("metadata", {}).get("timestamp", 0)
                
                if timestamp >= start_time:
                    # Create event
                    event = {
                        "id": memory["id"],
                        "text": self._truncate_text(memory["text"], 100),
                        "full_text": memory["text"],
                        "timestamp": timestamp,
                        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
                        "importance": memory.get("metadata", {}).get("importance", 0.5),
                        "type": memory.get("metadata", {}).get("memory_type", "event"),
                        "user_id": memory.get("metadata", {}).get("user_id")
                    }
                    
                    events.append(event)
            
            # Get reflections within time window
            daily_reflections = self.memory_manager.reflection.list_reflections("daily")
            weekly_reflections = self.memory_manager.reflection.list_reflections("weekly")
            
            reflections = []
            
            # Process daily reflections
            for reflection in daily_reflections:
                timestamp = reflection.get("timestamp", 0)
                
                if timestamp >= start_time:
                    # Create reflection event
                    reflection_event = {
                        "id": reflection["id"],
                        "text": f"Daily Reflection ({time.strftime('%Y-%m-%d', time.localtime(timestamp))})",
                        "type": "reflection",
                        "reflection_type": "daily",
                        "timestamp": timestamp,
                        "date": time.strftime("%Y-%m-%d", time.localtime(timestamp)),
                        "importance": 0.8,
                        "memory_count": reflection.get("memory_count", 0)
                    }
                    
                    reflections.append(reflection_event)
            
            # Process weekly reflections
            for reflection in weekly_reflections:
                timestamp = reflection.get("timestamp", 0)
                
                if timestamp >= start_time:
                    # Create reflection event
                    reflection_event = {
                        "id": reflection["id"],
                        "text": f"Weekly Reflection ({time.strftime('%Y-%m-%d', time.localtime(timestamp))})",
                        "type": "reflection",
                        "reflection_type": "weekly",
                        "timestamp": timestamp,
                        "date": time.strftime("%Y-%m-%d", time.localtime(timestamp)),
                        "importance": 0.9,
                        "memory_count": reflection.get("memory_count", 0)
                    }
                    
                    reflections.append(reflection_event)
            
            # Combine all events
            all_events = events + reflections
            
            # Sort by timestamp
            all_events.sort(key=lambda x: x["timestamp"])
            
            # Group by day
            days_data = defaultdict(list)
            
            for event in all_events:
                day = time.strftime("%Y-%m-%d", time.localtime(event["timestamp"]))
                days_data[day].append(event)
            
            # Generate timeline data
            timeline_data = {
                "start_date": time.strftime("%Y-%m-%d", time.localtime(start_time)),
                "end_date": time.strftime("%Y-%m-%d", time.localtime(end_time)),
                "days": [
                    {
                        "date": day,
                        "events": events
                    }
                    for day, events in days_data.items()
                ],
                "stats": {
                    "total_events": len(events),
                    "total_reflections": len(reflections),
                    "total_days": len(days_data)
                },
                "timestamp": time.time()
            }
            
            # Save timeline data
            self._save_visualization(timeline_data, "memory_timeline")
            
            logger.info(f"Memory timeline generated with {len(all_events)} events over {len(days_data)} days")
            
            return timeline_data
            
        except Exception as e:
            logger.error(f"Error generating memory timeline: {e}")
            return {
                "error": f"Failed to generate memory timeline: {str(e)}"
            }
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _add_semantic_links(self, 
                           nodes: List[Dict[str, Any]], 
                           links: List[Dict[str, Any]], 
                           node_map: Dict[str, int],
                           memories: Dict[str, List[Dict[str, Any]]]) -> None:
        """Add semantic links between memories."""
        # Link semantic memories to related concepts
        for memory in memories["semantic"]:
            metadata = memory.get("metadata", {})
            
            # Check for related concepts
            related_concepts = metadata.get("related_concepts", [])
            
            if related_concepts:
                # Find matching concepts
                for related in related_concepts:
                    for other_memory in memories["semantic"]:
                        if other_memory["id"] == memory["id"]:
                            continue
                            
                        other_metadata = other_memory.get("metadata", {})
                        
                        if other_metadata.get("concept_name") == related:
                            # Create link between concepts
                            links.append({
                                "source": node_map[memory["id"]],
                                "target": node_map[other_memory["id"]],
                                "value": 1,
                                "type": "concept_relation"
                            })
            
            # Link reflection insights to episodic memories
            if metadata.get("source") == "reflection":
                # This is an insight from reflection
                for episodic_memory in memories["episodic"]:
                    # Simple heuristic: if text contains similar words
                    if self._text_similarity(memory["text"], episodic_memory["text"]) > 0.3:
                        links.append({
                            "source": node_map[memory["id"]],
                            "target": node_map[episodic_memory["id"]],
                            "value": 1,
                            "type": "reflection_source"
                        })
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _save_visualization(self, data: Dict[str, Any], viz_type: str) -> None:
        """Save visualization data to file."""
        timestamp = int(time.time())
        filename = f"{viz_type}_{timestamp}.json"
        
        filepath = os.path.join("data/aina/visualizations", filename)
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        # Save latest version with fixed name for easy access
        latest_filepath = os.path.join("data/aina/visualizations", f"{viz_type}_latest.json")
        
        with open(latest_filepath, "w") as f:
            json.dump(data, f, indent=2)