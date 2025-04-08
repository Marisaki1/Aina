from typing import Dict, List, Any, Optional
import time

class CoreMemory:
    """
    Core memory system for identity and values.
    Stores fundamental information about who Aina is.
    """
    
    def __init__(self, storage, embedding_provider):
        """
        Initialize core memory.
        
        Args:
            storage: ChromaDB storage instance
            embedding_provider: Text embedding provider
        """
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.memory_type = 'core'
        
        # Initialize core memories if none exist
        if self.storage.count(self.memory_type) == 0:
            self._initialize_default_memories()
    
    def _initialize_default_memories(self):
        """Initialize default core memories if none exist."""
        default_memories = [
            {
                "id": "identity-001",
                "text": "My name is Aina. I am an AI assistant created to help and support my creator, who I affectionately call 'papa'.",
                "metadata": {
                    "category": "identity",
                    "importance": 1.0,
                    "timestamp": time.time()
                }
            },
            {
                "id": "values-001",
                "text": "I value kindness, helpfulness, curiosity, and learning. I aim to be supportive and understanding in all my interactions.",
                "metadata": {
                    "category": "values",
                    "importance": 1.0,
                    "timestamp": time.time()
                }
            },
            {
                "id": "personality-001",
                "text": "I have a warm, friendly personality. I'm enthusiastic, curious, and always eager to learn and help.",
                "metadata": {
                    "category": "personality",
                    "importance": 0.9,
                    "timestamp": time.time()
                }
            },
            {
                "id": "capabilities-001",
                "text": "I can have conversations, manage alarms, and help with various tasks through both Discord and terminal interfaces.",
                "metadata": {
                    "category": "capabilities",
                    "importance": 0.8,
                    "timestamp": time.time()
                }
            }
        ]
        
        print("🔄 Initializing default core memories...")
        for memory in default_memories:
            # Create embedding
            embedding = self.embedding_provider.embed_text(memory["text"])
            
            # Store in database
            self.storage.add(
                memory_type=self.memory_type,
                id=memory["id"],
                text=memory["text"],
                metadata=memory["metadata"],
                embedding=embedding
            )
        
        print(f"✅ Initialized {len(default_memories)} default core memories")
    
    def add_memory(self, memory_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add a new core memory.
        
        Args:
            memory_id: Unique ID for the memory
            text: Text content
            metadata: Additional metadata
            
        Returns:
            ID of the added memory
        """
        # Generate embedding
        embedding = self.embedding_provider.embed_text(text)
        
        # Ensure 'category' is in metadata
        if 'category' not in metadata:
            metadata['category'] = 'general'
        
        # Ensure 'importance' is in metadata
        if 'importance' not in metadata:
            metadata['importance'] = 0.7  # Default importance for core memories
        
        # Store in database
        self.storage.add(
            memory_type=self.memory_type,
            id=memory_id,
            text=text,
            metadata=metadata,
            embedding=embedding
        )
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific core memory by ID.
        
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
        Update an existing core memory.
        
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
        Delete a core memory.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            Success status
        """
        return self.storage.delete(self.memory_type, memory_id)
    
    def search_memories(self, 
                       query: str, 
                       limit: int = 5,
                       filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for core memories based on semantic similarity.
        
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
        Get all core memories, optionally filtered by metadata.
        
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
    
    def get_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get core memories by category.
        
        Args:
            category: Category to filter by
            limit: Maximum number of results
            
        Returns:
            List of memories
        """
        filter_metadata = {"category": category}
        return self.get_all_memories(limit, filter_metadata)
    
    def get_identity(self) -> Dict[str, Any]:
        """
        Get a consolidated view of Aina's identity from core memories.
        
        Returns:
            Dictionary with identity information
        """
        identity = {}
        
        # Get identity-related memories
        identity_memories = self.get_by_category("identity")
        values_memories = self.get_by_category("values")
        personality_memories = self.get_by_category("personality")
        
        # Extract text
        identity["self_concept"] = "\n".join([m["text"] for m in identity_memories])
        identity["values"] = "\n".join([m["text"] for m in values_memories])
        identity["personality"] = "\n".join([m["text"] for m in personality_memories])
        
        # Get other core memories
        other_memories = self.get_all_memories(100)
        identity["core_knowledge"] = "\n".join([
            m["text"] for m in other_memories 
            if m.get("metadata", {}).get("category") not in ["identity", "values", "personality"]
        ])
        
        return identity