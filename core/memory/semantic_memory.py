from typing import Dict, List, Any, Optional
import time
import uuid

class SemanticMemory:
    """
    Semantic memory system for long-term conceptual knowledge.
    Stores facts, concepts, and general information.
    """
    
    def __init__(self, storage, embedding_provider):
        """
        Initialize semantic memory.
        
        Args:
            storage: ChromaDB storage instance
            embedding_provider: Text embedding provider
        """
        self.storage = storage
        self.embedding_provider = embedding_provider
        self.memory_type = 'semantic'
    
    def add_memory(self, memory_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add a new semantic memory.
        
        Args:
            memory_id: Unique ID for the memory
            text: Text content describing the knowledge
            metadata: Additional metadata
            
        Returns:
            ID of the added memory
        """
        # Generate embedding
        embedding = self.embedding_provider.embed_text(text)
        
        # Ensure timestamp is in metadata
        if 'timestamp' not in metadata:
            metadata['timestamp'] = time.time()
        
        # Ensure category is in metadata
        if 'category' not in metadata:
            metadata['category'] = 'general'
        
        # Store in database
        self.storage.add(
            memory_type=self.memory_type,
            id=memory_id,
            text=text,
            metadata=metadata,
            embedding=embedding
        )
        
        return memory_id
    
    def store_fact(self, 
                 text: str, 
                 category: str = 'general',
                 source: Optional[str] = None,
                 importance: float = 0.5,
                 tags: Optional[List[str]] = None) -> str:
        """
        Store a factual piece of information.
        
        Args:
            text: Fact text
            category: Knowledge category
            source: Source of the information
            importance: Importance score (0-1)
            tags: Related tags
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'category': category,
            'memory_subtype': 'fact'
        }
        
        # Add source if provided
        if source:
            metadata['source'] = source
        
        # Add tags if provided
        if tags:
            metadata['tags'] = tags
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def store_concept(self, 
                    text: str, 
                    concept_name: str,
                    category: str = 'general',
                    importance: float = 0.6,
                    related_concepts: Optional[List[str]] = None,
                    tags: Optional[List[str]] = None) -> str:
        """
        Store a concept definition or explanation.
        
        Args:
            text: Concept explanation text
            concept_name: Name of the concept
            category: Knowledge category
            importance: Importance score (0-1)
            related_concepts: List of related concept names
            tags: Related tags
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'category': category,
            'memory_subtype': 'concept',
            'concept_name': concept_name
        }
        
        # Add related concepts if provided
        if related_concepts:
            metadata['related_concepts'] = related_concepts
        
        # Add tags if provided
        if tags:
            metadata['tags'] = tags
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def store_rule(self, 
                 text: str, 
                 rule_name: str,
                 category: str = 'rules',
                 importance: float = 0.7,
                 tags: Optional[List[str]] = None) -> str:
        """
        Store a rule or guideline.
        
        Args:
            text: Rule description text
            rule_name: Name of the rule
            category: Knowledge category
            importance: Importance score (0-1)
            tags: Related tags
            
        Returns:
            ID of the created memory
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        metadata = {
            'timestamp': time.time(),
            'importance': importance,
            'category': category,
            'memory_subtype': 'rule',
            'rule_name': rule_name
        }
        
        # Add tags if provided
        if tags:
            metadata['tags'] = tags
        
        # Store the memory
        return self.add_memory(memory_id, text, metadata)
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific semantic memory by ID.
        
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
        Update an existing semantic memory.
        
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
        Delete a semantic memory.
        
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
        Search for semantic memories based on semantic similarity.
        
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
        Get all semantic memories, optionally filtered by metadata.
        
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
        Get semantic memories by category.
        
        Args:
            category: Category to filter by
            limit: Maximum number of results
            
        Returns:
            List of memories
        """
        filter_metadata = {"category": category}
        return self.get_all_memories(limit, filter_metadata)
    
    def get_by_tags(self, tags: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get semantic memories by tags.
        
        Args:
            tags: List of tags to filter by (any match)
            limit: Maximum number of results
            
        Returns:
            List of memories
        """
        # Note: This is a simplification, actual implementation would depend on
        # how ChromaDB supports array filtering
        memories = []
        
        for tag in tags:
            filter_metadata = {"tags": {"$eq": tag}}
            memories.extend(self.get_all_memories(limit, filter_metadata))
        
        # Remove duplicates
        unique_memories = {}
        for memory in memories:
            if memory["id"] not in unique_memories:
                unique_memories[memory["id"]] = memory
        
        # Convert back to list and limit
        result = list(unique_memories.values())
        if limit > 0:
            result = result[:limit]
        
        return result
    
    def get_concepts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all concept memories.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of concept memories
        """
        filter_metadata = {"memory_subtype": "concept"}
        return self.get_all_memories(limit, filter_metadata)
    
    def get_facts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all fact memories.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of fact memories
        """
        filter_metadata = {"memory_subtype": "fact"}
        return self.get_all_memories(limit, filter_metadata)
    
    def get_rules(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all rule memories.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of rule memories
        """
        filter_metadata = {"memory_subtype": "rule"}
        return self.get_all_memories(limit, filter_metadata)