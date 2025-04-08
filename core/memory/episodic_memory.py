from typing import Dict, List, Any, Optional
import time
import uuid

class EpisodicMemory:
    """
    Episodic memory system for recent experiences.
    Stores interactions and events with temporal context.
    """
    
    def __init__(self, storage, embedding_provider):
        """
        Initialize episodic memory.
        
        Args:
            storage: ChromaDB storage instance
            embedding_provider: Text embedding provider
        """
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.memory_type = 'episodic'
    
    def add_memory(self, memory_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add a new episodic memory.
        
        Args:
            memory_id: Unique ID for the memory
            text: Text content describing the experience
            metadata: Additional metadata
            
        Returns:
            ID of the added memory
        """
        # Generate embedding
        embedding = self.embedding_provider.embed_text(text)
        
        # Ensure timestamp is in metadata
        if 'timestamp' not in metadata:
            metadata['timestamp'] = time.time()
        
        # Ensure importance is in metadata
        if 'importance' not in metadata:
            metadata['importance'] = 0.5  # Default importance
        
        # Store in database
        self.storage.add(
            memory_type=self.memory_type,
            id=memory_id,
            text=text,
            metadata=metadata,
            embedding=embedding
        )
        
        return memory_id
    
    def log_interaction(self, 
                      text: str, 
                      user_id: Optional[str] = None,
                      importance: float = 0.5,
                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an interaction as an episodic memory.
        
        Args:
            text: Description of the interaction
            user_id: ID of the user involved (if any)
            importance: Importance score (0-1)
            context: Additional context (channel, command, etc.)
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'memory_type': 'interaction'
        }
        
        # Add user ID if provided
        if user_id:
            metadata['user_id'] = user_id
        
        # Add context if provided
        if context:
            metadata.update(context)
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def log_event(self, 
                text: str, 
                event_type: str,
                importance: float = 0.5,
                context: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an event as an episodic memory.
        
        Args:
            text: Description of the event
            event_type: Type of event
            importance: Importance score (0-1)
            context: Additional context
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'memory_type': 'event',
            'event_type': event_type
        }
        
        # Add context if provided
        if context:
            metadata.update(context)
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific episodic memory by ID.
        
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
        Update an existing episodic memory.
        
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
        Delete an episodic memory.
        
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
        Search for episodic memories based on semantic similarity.
        
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
        Get all episodic memories, optionally filtered by metadata.
        
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
    
    def get_recent_memories(self, 
                          hours: float = 24.0, 
                          limit: int = 100,
                          min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get recent episodic memories within a time window.
        
        Args:
            hours: Time window in hours
            limit: Maximum number of results
            min_importance: Minimum importance score
            
        Returns:
            List of recent memories
        """
        # Calculate cutoff time
        cutoff_time = time.time() - (hours * 3600)
        
        # Create filter
        filter_metadata = {
            "timestamp": {"$gte": cutoff_time}
        }
        
        if min_importance > 0:
            filter_metadata["importance"] = {"$gte": min_importance}
        
        # Get memories
        memories = self.get_all_memories(limit, filter_metadata)
        
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.get("metadata", {}).get("timestamp", 0), reverse=True)
        
        return memories
    
    def get_user_interactions(self, 
                            user_id: str, 
                            limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent interactions with a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of interactions
        """
        # Create filter
        filter_metadata = {
            "user_id": user_id,
            "memory_type": "interaction"
        }
        
        # Get memories
        memories = self.get_all_memories(limit, filter_metadata)
        
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.get("metadata", {}).get("timestamp", 0), reverse=True)
        
        return memories
    
    def get_events_by_type(self, 
                         event_type: str, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get events of a specific type.
        
        Args:
            event_type: Type of event
            limit: Maximum number of results
            
        Returns:
            List of events
        """
        # Create filter
        filter_metadata = {
            "memory_type": "event",
            "event_type": event_type
        }
        
        # Get memories
        memories = self.get_all_memories(limit, filter_metadata)
        
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.get("metadata", {}).get("timestamp", 0), reverse=True)
        
        return memories
    
    def summarize_recent_activity(self, hours: float = 24.0, limit: int = 10) -> str:
        """
        Generate a summary of recent activities.
        
        Args:
            hours: Time window in hours
            limit: Maximum number of events to include
            
        Returns:
            Summary text
        """
        # Get recent memories
        recent_memories = self.get_recent_memories(hours, limit, 0.3)
        
        if not recent_memories:
            return "No significant activity in the specified time period."
        
        # Generate summary
        summary = f"Recent activity in the past {hours} hours:\n\n"
        
        for i, memory in enumerate(recent_memories, 1):
            timestamp = memory.get("metadata", {}).get("timestamp", 0)
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            
            summary += f"{i}. [{time_str}] {memory['text']}\n"
        
        return summary