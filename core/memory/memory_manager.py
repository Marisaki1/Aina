import os
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import uuid

from .embeddings import EmbeddingProvider
from .storage import QdrantStorage

class MemoryManager:
    """
    Central manager for all memory systems.
    Orchestrates interactions between different memory types.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the memory manager.
        
        Args:
            config_path: Path to memory configuration file
        """
        # Initialize default configuration
        self.config = {
            "qdrant_url": "localhost",
            "qdrant_port": 6333,
            "embedding_model": "all-MiniLM-L6-v2",
            "importance_threshold": 0.5,
            "recency_weight": 0.3,
            "relevance_weight": 0.5,
            "importance_weight": 0.2,
            "max_results": 10
        }
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                print(f"✅ Loaded memory configuration from {config_path}")
            except Exception as e:
                print(f"❌ Error loading memory configuration: {e}")
        
        # Create necessary directories
        os.makedirs("data/aina/reflections/daily", exist_ok=True)
        os.makedirs("data/aina/reflections/weekly", exist_ok=True)
        os.makedirs("data/aina/backups", exist_ok=True)

        # Add embedding cache
        self.embedding_cache = {}
        self.cache_size_limit = 1000  # Cache at most 1000 embeddings
        
        # FIRST: Initialize embedding provider
        self.embedding_provider = EmbeddingProvider(
            model_name=self.config["embedding_model"]
        )

        # SECOND: Set memory manager reference for caching
        self.embedding_provider.set_memory_manager(self)
        
        # THIRD: Initialize storage with embedding function
        self.storage = QdrantStorage(
            url=self.config["qdrant_url"],
            port=self.config["qdrant_port"],
            embedding_function=self.embedding_provider.get_embedding_function()
        )
        
        # Memory module instances (will be initialized as needed)
        self._core_memory = None
        self._episodic_memory = None
        self._semantic_memory = None
        self._personal_memory = None
        self._reflection = None
        
        print("✅ Memory Manager initialized with embedding cache")
        
    @property
    def core_memory(self):
        """Lazy-loaded core memory module."""
        if self._core_memory is None:
            from .core_memory import CoreMemory
            self._core_memory = CoreMemory(self.storage, self.embedding_provider)
        return self._core_memory
    
    @property
    def episodic_memory(self):
        """Lazy-loaded episodic memory module."""
        if self._episodic_memory is None:
            from .episodic_memory import EpisodicMemory
            self._episodic_memory = EpisodicMemory(self.storage, self.embedding_provider)
        return self._episodic_memory
    
    @property
    def semantic_memory(self):
        """Lazy-loaded semantic memory module."""
        if self._semantic_memory is None:
            from .semantic_memory import SemanticMemory
            self._semantic_memory = SemanticMemory(self.storage, self.embedding_provider)
        return self._semantic_memory
    
    @property
    def personal_memory(self):
        """Lazy-loaded personal memory module."""
        if self._personal_memory is None:
            from .personal_memory import PersonalMemory
            self._personal_memory = PersonalMemory(self.storage, self.embedding_provider)
        return self._personal_memory
    
    @property
    def reflection(self):
        """Lazy-loaded reflection module."""
        if self._reflection is None:
            from .reflection import Reflection
            self._reflection = Reflection(self, self.storage, self.embedding_provider)
        return self._reflection
    
    def store_memory(self, 
                    text: str, 
                    memory_type: str, 
                    metadata: Optional[Dict[str, Any]] = None,
                    importance: Optional[float] = None,
                    user_id: Optional[str] = None) -> str:
        """
        Store a memory in the appropriate memory system.
        
        Args:
            text: The text content of the memory
            memory_type: Type of memory ('core', 'episodic', 'semantic', 'personal')
            metadata: Additional metadata for the memory
            importance: Importance score (0-1)
            user_id: User ID for personal memories
            
        Returns:
            ID of the stored memory
        """
        if not text or not memory_type:
            raise ValueError("Text and memory_type are required")
        
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not provided
        if 'timestamp' not in metadata:
            metadata['timestamp'] = time.time()
        
        # Add importance score if provided
        if importance is not None:
            metadata['importance'] = importance
        
        # Add user_id for personal memories
        if memory_type == 'personal' and user_id:
            metadata['user_id'] = user_id
        
        # Route to the appropriate memory system
        if memory_type == 'core':
            return self.core_memory.add_memory(memory_id, text, metadata)
        elif memory_type == 'episodic':
            return self.episodic_memory.add_memory(memory_id, text, metadata)
        elif memory_type == 'semantic':
            return self.semantic_memory.add_memory(memory_id, text, metadata)
        elif memory_type == 'personal':
            if not user_id:
                raise ValueError("user_id is required for personal memories")
            return self.personal_memory.add_memory(memory_id, text, metadata)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def retrieve_memory(self, memory_type: str, memory_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_type: Type of memory
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory object
        """
        # Route to the appropriate memory system
        if memory_type == 'core':
            return self.core_memory.get_memory(memory_id)
        elif memory_type == 'episodic':
            return self.episodic_memory.get_memory(memory_id)
        elif memory_type == 'semantic':
            return self.semantic_memory.get_memory(memory_id)
        elif memory_type == 'personal':
            return self.personal_memory.get_memory(memory_id)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def update_memory(self, 
                     memory_type: str, 
                     memory_id: str, 
                     text: Optional[str] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_type: Type of memory
            memory_id: ID of the memory to update
            text: New text content (if None, won't update)
            metadata: New metadata (if None, won't update)
            
        Returns:
            Success status
        """
        # Route to the appropriate memory system
        if memory_type == 'core':
            return self.core_memory.update_memory(memory_id, text, metadata)
        elif memory_type == 'episodic':
            return self.episodic_memory.update_memory(memory_id, text, metadata)
        elif memory_type == 'semantic':
            return self.semantic_memory.update_memory(memory_id, text, metadata)
        elif memory_type == 'personal':
            return self.personal_memory.update_memory(memory_id, text, metadata)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def delete_memory(self, memory_type: str, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_type: Type of memory
            memory_id: ID of the memory to delete
            
        Returns:
            Success status
        """
        # Route to the appropriate memory system
        if memory_type == 'core':
            return self.core_memory.delete_memory(memory_id)
        elif memory_type == 'episodic':
            return self.episodic_memory.delete_memory(memory_id)
        elif memory_type == 'semantic':
            return self.semantic_memory.delete_memory(memory_id)
        elif memory_type == 'personal':
            return self.personal_memory.delete_memory(memory_id)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def search_memories(self, 
                       query: str, 
                       memory_types: Union[str, List[str]] = 'all',
                       limit: int = 10,
                       filter_metadata: Optional[Dict[str, Any]] = None,
                       user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for memories across memory systems.
        
        Args:
            query: Search query text
            memory_types: Type(s) of memory to search, 'all' for all types
            limit: Maximum number of results per memory type
            filter_metadata: Filter results by metadata
            user_id: User ID for filtering personal memories
            
        Returns:
            List of matching memories with scores
        """
        results = []
        
        # Determine which memory types to search
        if memory_types == 'all':
            memory_types = ['core', 'episodic', 'semantic', 'personal']
        elif isinstance(memory_types, str):
            memory_types = [memory_types]
        
        # Generate embedding for query
        query_embedding = self.embedding_provider.embed_text(query)
        
        # Search each memory type
        for memory_type in memory_types:
            # Add user_id filter for personal memories
            type_filter = filter_metadata.copy() if filter_metadata else {}
            if memory_type == 'personal' and user_id:
                type_filter['user_id'] = user_id
            
            # Get results
            if memory_type == 'core':
                type_results = self.core_memory.search_memories(query, limit, type_filter)
            elif memory_type == 'episodic':
                type_results = self.episodic_memory.search_memories(query, limit, type_filter)
            elif memory_type == 'semantic':
                type_results = self.semantic_memory.search_memories(query, limit, type_filter)
            elif memory_type == 'personal':
                if not user_id and not type_filter.get('user_id'):
                    # Skip personal memories if no user_id is provided
                    continue
                type_results = self.personal_memory.search_memories(query, limit, type_filter)
            else:
                continue
            
            # Add memory type to results
            for result in type_results:
                result['memory_type'] = memory_type
            
            results.extend(type_results)
        
        # Sort by similarity
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Limit total results
        if limit > 0:
            results = results[:limit]
        
        return results
    
    def retrieve_all_memories(self, 
                            memory_type: str, 
                            limit: int = 1000,
                            filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all memories of a specific type.
        
        Args:
            memory_type: Type of memory
            limit: Maximum number of results
            filter_metadata: Filter by metadata
            
        Returns:
            List of memories
        """
        # Route to the appropriate memory system
        if memory_type == 'core':
            return self.core_memory.get_all_memories(limit, filter_metadata)
        elif memory_type == 'episodic':
            return self.episodic_memory.get_all_memories(limit, filter_metadata)
        elif memory_type == 'semantic':
            return self.semantic_memory.get_all_memories(limit, filter_metadata)
        elif memory_type == 'personal':
            return self.personal_memory.get_all_memories(limit, filter_metadata)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
    
    def get_user_memories(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all memories related to a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of memories
        """
        # Get personal memories for the user
        personal_memories = self.personal_memory.get_user_memories(user_id, limit)
        
        # Get episodic memories that mention the user
        episodic_filter = {'user_id': user_id}
        episodic_memories = self.episodic_memory.get_all_memories(limit, episodic_filter)
        
        # Combine and sort by timestamp (most recent first)
        all_memories = personal_memories + episodic_memories
        all_memories.sort(key=lambda x: x.get('metadata', {}).get('timestamp', 0), reverse=True)
        
        return all_memories[:limit]
    
    def trigger_reflection(self, reflection_type: str = 'daily') -> Dict[str, Any]:
            """
            Trigger a reflection process to consolidate and analyze memories.
            
            Args:
                reflection_type: Type of reflection ('daily' or 'weekly')
                
            Returns:
                Reflection result
            """
            try:
                return self.reflection.create_reflection(reflection_type)
            except Exception as e:
                print(f"Error creating reflection: {e}")
                # Return a minimal reflection object in case of error
                return {
                    "type": reflection_type,
                    "timestamp": time.time(),
                    "summary": f"Error creating reflection: {str(e)}",
                    "insights": [],
                    "memory_count": 0
                }
    
    def backup_memories(self, backup_path: Optional[str] = None) -> bool:
        """
        Backup all memory collections.
        
        Args:
            backup_path: Path to backup directory (default: data/aina/backups/YYYY-MM-DD)
            
        Returns:
            Success status
        """
        # Create default backup path if not provided
        if not backup_path:
            date_str = time.strftime("%Y-%m-%d")
            backup_path = f"data/aina/backups/{date_str}"
        
        os.makedirs(backup_path, exist_ok=True)
        
        success = True
        for memory_type in ['core', 'episodic', 'semantic', 'personal']:
            type_success = self.storage.backup(memory_type, backup_path)
            success = success and type_success
        
        if success:
            print(f"✅ Successfully backed up all memories to {backup_path}")
        else:
            print(f"⚠️ Some errors occurred during backup to {backup_path}")
        
        return success
    
    def restore_memories(self, backup_path: str) -> bool:
        """
        Restore all memory collections from backup.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            Success status
        """
        if not os.path.exists(backup_path):
            print(f"❌ Backup path not found: {backup_path}")
            return False
        
        success = True
        for memory_type in ['core', 'episodic', 'semantic', 'personal']:
            type_success = self.storage.restore(memory_type, backup_path)
            success = success and type_success
        
        if success:
            print(f"✅ Successfully restored all memories from {backup_path}")
        else:
            print(f"⚠️ Some errors occurred during restore from {backup_path}")
        
        return success