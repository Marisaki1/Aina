from typing import Dict, List, Any, Optional
import time
import uuid

class PersonalMemory:
    """
    Personal memory system for user-specific information.
    Stores preferences, traits, and other information about users.
    """
    
    def __init__(self, storage, embedding_provider):
        """
        Initialize personal memory.
        
        Args:
            storage: ChromaDB storage instance
            embedding_provider: Text embedding provider
        """
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.memory_type = 'personal'
    
    def add_memory(self, memory_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add a new personal memory.
        
        Args:
            memory_id: Unique ID for the memory
            text: Text content describing the user information
            metadata: Additional metadata
            
        Returns:
            ID of the added memory
        """
        # Generate embedding
        embedding = self.embedding_provider.embed_text(text)
        
        # Ensure timestamp is in metadata
        if 'timestamp' not in metadata:
            metadata['timestamp'] = time.time()
        
        # Ensure user_id is in metadata
        if 'user_id' not in metadata:
            raise ValueError("user_id is required for personal memories")
        
        # Store in database
        self.storage.add(
            memory_type=self.memory_type,
            id=memory_id,
            text=text,
            metadata=metadata,
            embedding=embedding
        )
        
        return memory_id
    
    def store_user_info(self, 
                      user_id: str, 
                      text: str, 
                      info_type: str = 'general',
                      importance: float = 0.6) -> str:
        """
        Store general information about a user.
        
        Args:
            user_id: User ID
            text: Information text
            info_type: Type of information
            importance: Importance score (0-1)
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'user_id': user_id,
            'memory_subtype': 'info',
            'info_type': info_type
        }
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def store_user_preference(self, 
                            user_id: str, 
                            text: str, 
                            preference_type: str,
                            importance: float = 0.7) -> str:
        """
        Store a user preference.
        
        Args:
            user_id: User ID
            text: Preference description
            preference_type: Type of preference
            importance: Importance score (0-1)
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'user_id': user_id,
            'memory_subtype': 'preference',
            'preference_type': preference_type
        }
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def store_user_trait(self, 
                       user_id: str, 
                       text: str, 
                       trait_type: str = 'personality',
                       importance: float = 0.6) -> str:
        """
        Store a user trait or characteristic.
        
        Args:
            user_id: User ID
            text: Trait description
            trait_type: Type of trait
            importance: Importance score (0-1)
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'user_id': user_id,
            'memory_subtype': 'trait',
            'trait_type': trait_type
        }
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def store_interaction_summary(self, 
                               user_id: str, 
                               text: str,
                               date: Optional[str] = None,
                               importance: float = 0.8) -> str:
        """
        Store a summary of interactions with a user.
        
        Args:
            user_id: User ID
            text: Summary text
            date: Date of the interaction summary
            importance: Importance score (0-1)
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'user_id': user_id,
            'memory_subtype': 'interaction_summary'
        }
        
        # Add date if provided
        if date:
            metadata['date'] = date
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific personal memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory object or None if not found
        """
        return self.storage.get(self.memory_type, memory_id)
    
    def update_memory(self, 
                     memory_id: str, 
                     text: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing personal memory.
        
        Args:
            memory_id: ID of the memory to update
            text: New text content (if None, won't update)
            metadata: New metadata (if None, won't update)
            
        Returns:
            Success status
        """
        # If nothing to update, return early
        if text is None and metadata is None:
            return False
        
        # Generate new embedding if text is updated
        embedding = None
        if text is not None:
            embedding = self.embedding_provider.embed_text(text)
        
        # Update in database
        return self.storage.update(
            memory_type=self.memory_type,
            id=memory_id,
            text=text,
            metadata=metadata,
            embedding=embedding
        )
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a personal memory.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            Success status
        """
        return self.storage.delete(self.memory_type, memory_id)
    
    def search_memories(self, 
                       query: str, 
                       limit: int = 10,
                       filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for personal memories based on semantic similarity.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            filter_metadata: Filter results by metadata
            
        Returns:
            List of matching memories with similarity scores
        """
        return self.storage.search_by_text(
            memory_type=self.memory_type,
            query_text=query,
            limit=limit,
            filter=filter_metadata
        )
    
    def get_all_memories(self, 
                        limit: int = 100,
                        filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all personal memories, optionally filtered by metadata.
        
        Args:
            limit: Maximum number of results
            filter_metadata: Filter by metadata
            
        Returns:
            List of memories
        """
        if filter_metadata:
            return self.storage.search_by_metadata(
                memory_type=self.memory_type,
                filter=filter_metadata,
                limit=limit
            )
        else:
            return self.storage.get_all(
                memory_type=self.memory_type,
                limit=limit
            )
    
    def get_user_memories(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of memories
        """
        filter_metadata = {"user_id": user_id}
        
        # Get memories
        memories = self.get_all_memories(limit, filter_metadata)
        
        # Sort by importance (most important first)
        memories.sort(key=lambda x: x.get("metadata", {}).get("importance", 0), reverse=True)
        
        return memories
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get a consolidated profile of a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile dictionary
        """
        # Get all memories for the user
        memories = self.get_user_memories(user_id)
        
        # Prepare profile
        profile = {
            "user_id": user_id,
            "preferences": [],
            "traits": [],
            "info": [],
            "interaction_summaries": []
        }
        
        # Categorize memories
        for memory in memories:
            metadata = memory.get("metadata", {})
            memory_subtype = metadata.get("memory_subtype", "info")
            
            if memory_subtype == "preference":
                profile["preferences"].append({
                    "text": memory["text"],
                    "type": metadata.get("preference_type", "general"),
                    "importance": metadata.get("importance", 0.5)
                })
            elif memory_subtype == "trait":
                profile["traits"].append({
                    "text": memory["text"],
                    "type": metadata.get("trait_type", "personality"),
                    "importance": metadata.get("importance", 0.5)
                })
            elif memory_subtype == "interaction_summary":
                profile["interaction_summaries"].append({
                    "text": memory["text"],
                    "date": metadata.get("date", "unknown"),
                    "timestamp": metadata.get("timestamp", 0),
                    "importance": metadata.get("importance", 0.5)
                })
            else:  # info or other
                profile["info"].append({
                    "text": memory["text"],
                    "type": metadata.get("info_type", "general"),
                    "importance": metadata.get("importance", 0.5)
                })
        
        # Sort each category by importance
        profile["preferences"].sort(key=lambda x: x.get("importance", 0), reverse=True)
        profile["traits"].sort(key=lambda x: x.get("importance", 0), reverse=True)
        profile["info"].sort(key=lambda x: x.get("importance", 0), reverse=True)
        profile["interaction_summaries"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return profile
    
    def get_user_summary(self, user_id: str, max_length: int = 500) -> str:
        """
        Generate a text summary of a user based on stored memories.
        
        Args:
            user_id: User ID
            max_length: Maximum length of the summary
            
        Returns:
            Text summary
        """
        profile = self.get_user_profile(user_id)
        
        # Count memories
        total_memories = (
            len(profile["preferences"]) + 
            len(profile["traits"]) + 
            len(profile["info"]) + 
            len(profile["interaction_summaries"])
        )
        
        if total_memories == 0:
            return f"No stored memories about user {user_id}."
        
        # Generate summary text
        summary = f"Summary for user {user_id}:\n\n"
        
        # Add key traits
        if profile["traits"]:
            summary += "Key traits:\n"
            for trait in profile["traits"][:3]:  # Top 3 traits by importance
                summary += f"- {trait['text']}\n"
            summary += "\n"
        
        # Add key preferences
        if profile["preferences"]:
            summary += "Preferences:\n"
            for pref in profile["preferences"][:3]:  # Top 3 preferences by importance
                summary += f"- {pref['text']}\n"
            summary += "\n"
        
        # Add additional information
        if profile["info"]:
            summary += "Additional information:\n"
            for info in profile["info"][:3]:  # Top 3 info items by importance
                summary += f"- {info['text']}\n"
            summary += "\n"
        
        # Add recent interaction summary
        if profile["interaction_summaries"]:
            summary += "Recent interactions:\n"
            for interaction in profile["interaction_summaries"][:1]:  # Most recent interaction
                summary += f"- {interaction['text']}\n"
        
        # Truncate if necessary
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary