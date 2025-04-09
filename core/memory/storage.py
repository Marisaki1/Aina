import os
import numpy as np
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Callable, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# For backwards compatibility - aliasing QdrantStorage as ChromaDBStorage
# This helps existing imports continue to work
ChromaDBStorage = None  # This will be redefined after QdrantStorage is defined

class QdrantStorage:
    """Interface to Qdrant for vector storage and retrieval."""
    
    def __init__(self, 
                 url: str = "localhost",
                 port: int = 6333,
                 embedding_function: Optional[Callable] = None):
        """
        Initialize Qdrant storage.
        
        Args:
            url: URL for Qdrant server
            port: Port for Qdrant server
            embedding_function: Function to convert text to embeddings
        """
        self.url = url
        self.port = port
        self.embedding_function = embedding_function
        
        # Initialize client
        self.client = QdrantClient(url=url, port=port)
        
        # Memory types and their collection names
        self.memory_types = {
            "core": "core_memories",
            "episodic": "episodic_memories",
            "semantic": "semantic_memories",
            "personal": "personal_memories"
        }
        
        # Initialize ID mapping storage
        self.id_mapping = {}
        self._load_id_mappings()
        
        # Initialize collections
        self._initialize_collections()
        
        print(f"✅ Qdrant initialized at {url}:{port}")
    
    def _load_id_mappings(self):
        """Load existing ID mappings from file."""
        mapping_file = "data/aina/id_mappings.json"
        try:
            if os.path.exists(mapping_file):
                import json
                with open(mapping_file, 'r') as f:
                    self.id_mapping = json.load(f)
                print(f"  ✓ Loaded {len(self.id_mapping)} ID mappings")
        except Exception as e:
            print(f"  ⚠️ Could not load ID mappings: {e}")
            self.id_mapping = {}
    
    def _save_id_mappings(self):
        """Save ID mappings to file."""
        mapping_file = "data/aina/id_mappings.json"
        try:
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            import json
            with open(mapping_file, 'w') as f:
                json.dump(self.id_mapping, f, indent=2)
        except Exception as e:
            print(f"  ⚠️ Could not save ID mappings: {e}")
    
    def _convert_id(self, id_string: str) -> str:
        """
        Convert string ID to Qdrant-compatible ID.
        Qdrant accepts UUIDs or unsigned integers.
        
        Args:
            id_string: Original string ID
            
        Returns:
            Qdrant-compatible ID
        """
        # If it's already a UUID or a number, use it directly
        if self._is_valid_uuid(id_string) or id_string.isdigit():
            return id_string
        
        # Check if we have a mapping for this ID
        if id_string in self.id_mapping:
            return self.id_mapping[id_string]
        
        # Generate a new UUID
        qdrant_id = str(uuid.uuid4())
        
        # Store the mapping
        self.id_mapping[id_string] = qdrant_id
        
        # Save the updated mappings
        self._save_id_mappings()
        
        return qdrant_id
    
    def _reverse_id(self, qdrant_id: str) -> str:
        """
        Convert Qdrant ID back to original ID.
        
        Args:
            qdrant_id: Qdrant ID
            
        Returns:
            Original ID if found, otherwise the Qdrant ID
        """
        # Check if this ID is in our mappings
        for original_id, mapped_id in self.id_mapping.items():
            if mapped_id == qdrant_id:
                return original_id
        
        # If not found, return the Qdrant ID
        return qdrant_id
    
    def _is_valid_uuid(self, id_string: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(str(id_string))
            return True
        except ValueError:
            return False
    
    def _initialize_collections(self):
        """Initialize or get existing collections for each memory type."""
        # Default to a common embedding size
        embedding_dim = 384
        
        # Try to determine embedding dimension from a test embedding if available
        if self.embedding_function is not None:
            try:
                test_embedding = self.embedding_function(["test"])
                
                # Handle different return types
                if isinstance(test_embedding, list):
                    if len(test_embedding) > 0:
                        if isinstance(test_embedding[0], list):
                            # Case: list of lists of floats
                            embedding_dim = len(test_embedding[0])
                        elif isinstance(test_embedding[0], (float, int)):
                            # Case: list of floats (single embedding)
                            embedding_dim = len(test_embedding)
                elif isinstance(test_embedding, np.ndarray):
                    # Case: numpy array
                    if test_embedding.ndim == 2:
                        embedding_dim = test_embedding.shape[1]
                    else:
                        embedding_dim = test_embedding.shape[0]
                
                print(f"  ✓ Detected embedding dimension: {embedding_dim}")
            except Exception as e:
                print(f"  ⚠️ Could not determine embedding dimension: {e}")
                print(f"  ✓ Using default dimension: {embedding_dim}")
            
        for memory_type, collection_name in self.memory_types.items():
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                print(f"  ✓ Collection '{collection_name}' created")
            else:
                print(f"  ✓ Collection '{collection_name}' already exists")
    
    def add(self, 
            memory_type: str, 
            id: str, 
            text: str, 
            metadata: Dict[str, Any] = None,
            embedding: Optional[List[float]] = None) -> str:
        """
        Add a document to the specified memory collection.
        
        Args:
            memory_type: Type of memory ('core', 'episodic', 'semantic', 'personal')
            id: Unique ID for the document
            text: Text content
            metadata: Additional metadata
            embedding: Pre-computed embedding (optional)
            
        Returns:
            ID of the added document
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert ID to Qdrant-compatible format
        qdrant_id = self._convert_id(id)
        
        # Generate embedding if not provided
        if embedding is None and self.embedding_function is not None:
            try:
                raw_embedding = self.embedding_function([text])
                
                # Process different embedding formats
                if isinstance(raw_embedding, list):
                    if len(raw_embedding) > 0:
                        if isinstance(raw_embedding[0], list):
                            # Case: list of lists of floats
                            embedding = raw_embedding[0]
                        elif isinstance(raw_embedding[0], (float, int)):
                            # Case: list of floats (single embedding)
                            embedding = raw_embedding
                elif isinstance(raw_embedding, np.ndarray):
                    # Case: numpy array
                    if raw_embedding.ndim == 2:
                        embedding = raw_embedding[0].tolist()
                    else:
                        embedding = raw_embedding.tolist()
            except Exception as e:
                print(f"❌ Error generating embedding: {e}")
                # Create a zero vector as fallback
                collection_info = self.client.get_collection(collection_name)
                vector_size = collection_info.config.params.vector_size
                embedding = [0.0] * vector_size
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Store original ID in metadata for reference
        metadata["original_id"] = id
        
        # Add text to metadata for retrieval
        payload = {
            "text": text,
            **metadata
        }
        
        # Add point to collection
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=qdrant_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            if "is not a valid point ID" in str(e):
                # Try with a UUID as a fallback
                uuid_id = str(uuid.uuid4())
                print(f"  ⚠️ Using UUID {uuid_id} as fallback")
                self.id_mapping[id] = uuid_id
                self._save_id_mappings()
                
                self.client.upsert(
                    collection_name=collection_name,
                    points=[
                        PointStruct(
                            id=uuid_id,
                            vector=embedding,
                            payload=payload
                        )
                    ]
                )
        
        return id  # Return the original ID
    
    def get(self, memory_type: str, id: str) -> Dict[str, Any]:
        """Retrieve a document by ID from the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert ID to Qdrant-compatible format
        qdrant_id = self._convert_id(id)
        
        # Get point from collection
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=[qdrant_id],
                with_vectors=True
            )
        except Exception as e:
            print(f"❌ Error retrieving document: {e}")
            # Try to search by original_id in metadata
            filter_condition = models.FieldCondition(
                key="original_id",
                match=models.MatchValue(value=id)
            )
            
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                filter=filter_condition,
                limit=1,
                with_vectors=True
            )[0]
            
            if scroll_result:
                # Found it via metadata search
                point = scroll_result[0]
                
                # Update the mapping for future use
                self.id_mapping[id] = point.id
                self._save_id_mappings()
                
                # Format result
                return {
                    "id": id,  # Return original ID
                    "text": point.payload.get("text", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "text" and k != "original_id"},
                    "embedding": point.vector
                }
            else:
                return None  # Not found
        
        if not result:
            return None
        
        point = result[0]
        
        # Format result
        return {
            "id": id,  # Return original ID
            "text": point.payload.get("text", ""),
            "metadata": {k: v for k, v in point.payload.items() if k != "text" and k != "original_id"},
            "embedding": point.vector
        }
    
    def update(self, 
              memory_type: str, 
              id: str, 
              text: Optional[str] = None, 
              metadata: Optional[Dict[str, Any]] = None,
              embedding: Optional[List[float]] = None) -> bool:
        """
        Update a document in the specified memory collection.
        
        Args:
            memory_type: Type of memory
            id: Document ID to update
            text: New text content (if None, won't update)
            metadata: New metadata (if None, won't update)
            embedding: New embedding (if None, won't update)
            
        Returns:
            Success status
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert ID to Qdrant-compatible format
        qdrant_id = self._convert_id(id)
        
        try:
            # Get existing document if we need partial update
            existing = None
            if text is None or (metadata is None and embedding is None):
                existing = self.get(memory_type, id)
                if not existing:
                    return False
            
            # Prepare update
            payload = {}
            
            # Update text if provided
            if text is not None:
                payload["text"] = text
            elif existing:
                payload["text"] = existing["text"]
            
            # Add original ID to metadata
            payload["original_id"] = id
            
            # Update metadata if provided
            if metadata is not None:
                for key, value in metadata.items():
                    payload[key] = value
            elif existing:
                for key, value in existing["metadata"].items():
                    payload[key] = value
            
            # Generate new embedding if text changed and no embedding provided
            if text is not None and embedding is None and self.embedding_function is not None:
                try:
                    raw_embedding = self.embedding_function([text])
                    
                    # Process different embedding formats
                    if isinstance(raw_embedding, list):
                        if len(raw_embedding) > 0:
                            if isinstance(raw_embedding[0], list):
                                # Case: list of lists of floats
                                embedding = raw_embedding[0]
                            elif isinstance(raw_embedding[0], (float, int)):
                                # Case: list of floats (single embedding)
                                embedding = raw_embedding
                    elif isinstance(raw_embedding, np.ndarray):
                        # Case: numpy array
                        if raw_embedding.ndim == 2:
                            embedding = raw_embedding[0].tolist()
                        else:
                            embedding = raw_embedding.tolist()
                except Exception as e:
                    print(f"❌ Error generating embedding for update: {e}")
                    if existing and existing.get("embedding"):
                        embedding = existing["embedding"]
            
            # Use existing embedding if none provided
            if embedding is None and existing:
                embedding = existing["embedding"]
            
            # Update point
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=qdrant_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
                
            return True
        except Exception as e:
            print(f"❌ Error updating document: {e}")
            return False
    
    def delete(self, memory_type: str, id: str) -> bool:
        """Delete a document from the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert ID to Qdrant-compatible format
        qdrant_id = self._convert_id(id)
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[qdrant_id]
                )
            )
            return True
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False
    
    def search_by_text(self, 
                      memory_type: str, 
                      query_text: str, 
                      limit: int = 10,
                      filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents by text.
        
        Args:
            memory_type: Type of memory
            query_text: Text to search for
            limit: Maximum number of results
            filter: Metadata filter
            
        Returns:
            List of matching documents with similarity scores
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Generate embedding for query
        if self.embedding_function is None:
            raise ValueError("Embedding function is required for text search")
        
        # Get query vector with error handling
        try:
            raw_embedding = self.embedding_function([query_text])
            
            # Process different embedding formats
            if isinstance(raw_embedding, list):
                if len(raw_embedding) > 0:
                    if isinstance(raw_embedding[0], list):
                        # Case: list of lists of floats
                        query_vector = raw_embedding[0]
                    elif isinstance(raw_embedding[0], (float, int)):
                        # Case: list of floats (single embedding)
                        query_vector = raw_embedding
            elif isinstance(raw_embedding, np.ndarray):
                # Case: numpy array
                if raw_embedding.ndim == 2:
                    query_vector = raw_embedding[0].tolist()
                else:
                    query_vector = raw_embedding.tolist()
        except Exception as e:
            print(f"❌ Error generating query embedding: {e}")
            # Create a zero vector as fallback
            collection_info = self.client.get_collection(collection_name)
            vector_size = collection_info.config.params.vector_size
            query_vector = [0.0] * vector_size
            
        # Convert filter to Qdrant format if provided
        qdrant_filter = None
        if filter:
            qdrant_filter = self._convert_filter(filter)
        
        # Search by vector
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True
        )
        
        # Format results
        formatted_results = []
        for result in results:
            # Get original ID if possible
            original_id = result.payload.get("original_id", result.id)
            
            formatted_results.append({
                "id": original_id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text" and k != "original_id"},
                "similarity": result.score
            })
        
        return formatted_results
    
    def search_by_vector(self, 
                        memory_type: str, 
                        query_vector: List[float], 
                        limit: int = 10,
                        filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents by vector.
        
        Args:
            memory_type: Type of memory
            query_vector: Vector to search for
            limit: Maximum number of results
            filter: Metadata filter
            
        Returns:
            List of matching documents with similarity scores
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert filter to Qdrant format if provided
        qdrant_filter = None
        if filter:
            qdrant_filter = self._convert_filter(filter)
        
        # Search by vector
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True
        )
        
        # Format results
        formatted_results = []
        for result in results:
            # Get original ID if possible
            original_id = result.payload.get("original_id", result.id)
            
            formatted_results.append({
                "id": original_id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text" and k != "original_id"},
                "similarity": result.score
            })
        
        return formatted_results
    
    def search_by_metadata(self, 
                          memory_type: str, 
                          filter: Dict[str, Any], 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata.
        
        Args:
            memory_type: Type of memory
            filter: Metadata filter
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Convert filter to Qdrant format
        qdrant_filter = self._convert_filter(filter)
        
        # Search by filter
        results = self.client.scroll(
            collection_name=collection_name,
            filter=qdrant_filter,
            limit=limit,
            with_payload=True
        )[0]  # scroll returns a tuple (results, offset)
        
        # Format results
        formatted_results = []
        for result in results:
            # Get original ID if possible
            original_id = result.payload.get("original_id", result.id)
            
            formatted_results.append({
                "id": original_id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text" and k != "original_id"}
            })
        
        return formatted_results
    
    def get_all(self, memory_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all documents from the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Get all documents
        results = self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True
        )[0]  # scroll returns a tuple (results, offset)
        
        # Format results
        formatted_results = []
        for result in results:
            # Get original ID if possible
            original_id = result.payload.get("original_id", result.id)
            
            formatted_results.append({
                "id": original_id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text" and k != "original_id"}
            })
        
        return formatted_results
    
    def count(self, memory_type: str) -> int:
        """Get the number of documents in the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Get collection info
        collection_info = self.client.get_collection(collection_name)
        
        return collection_info.vectors_count
    
    def clear(self, memory_type: str) -> bool:
        """Clear all documents from the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        try:
            # Delete collection
            self.client.delete_collection(collection_name)
            
            # Recreate collection
            embedding_dim = 384  # default
            if self.embedding_function is not None:
                try:
                    raw_embedding = self.embedding_function(["test"])
                    
                    # Process different embedding formats
                    if isinstance(raw_embedding, list):
                        if len(raw_embedding) > 0:
                            if isinstance(raw_embedding[0], list):
                                # Case: list of lists of floats
                                embedding_dim = len(raw_embedding[0])
                            elif isinstance(raw_embedding[0], (float, int)):
                                # Case: list of floats (single embedding)
                                embedding_dim = len(raw_embedding)
                    elif isinstance(raw_embedding, np.ndarray):
                        # Case: numpy array
                        if raw_embedding.ndim == 2:
                            embedding_dim = raw_embedding.shape[1]
                        else:
                            embedding_dim = raw_embedding.shape[0]
                except Exception:
                    pass
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            return True
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")
            return False
    
    def backup(self, memory_type: str, backup_path: str) -> bool:
        """
        Backup a memory collection.
        
        Args:
            memory_type: Type of memory
            backup_path: Path to backup directory
            
        Returns:
            Success status
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Get all documents
            documents = self.get_all(memory_type, limit=100000)
            
            # Save to file
            import json
            with open(os.path.join(backup_path, f"{collection_name}.json"), 'w') as f:
                json.dump(documents, f, indent=2)
            
            # Also save ID mappings
            with open(os.path.join(backup_path, "id_mappings.json"), 'w') as f:
                json.dump(self.id_mapping, f, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Error backing up collection: {e}")
            return False
    
    def restore(self, memory_type: str, backup_path: str) -> bool:
        """
        Restore a memory collection from backup.
        
        Args:
            memory_type: Type of memory
            backup_path: Path to backup directory
            
        Returns:
            Success status
        """
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        backup_file = os.path.join(backup_path, f"{collection_name}.json")
        
        if not os.path.exists(backup_file):
            print(f"⚠️ Backup file not found: {backup_file}")
            return False
        
        try:
            # Clear existing collection
            self.clear(memory_type)
            
            # Load documents from file
            import json
            with open(backup_file, 'r') as f:
                documents = json.load(f)
            
            # Load ID mappings if available
            mapping_file = os.path.join(backup_path, "id_mappings.json")
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    self.id_mapping.update(json.load(f))
            
            # Restore documents
            for doc in documents:
                # Skip if missing required fields
                if "id" not in doc or "text" not in doc:
                    continue
                
                # Extract fields
                original_id = doc["id"]
                text = doc["text"]
                metadata = doc.get("metadata", {})
                
                # Generate embedding if needed
                embedding = None
                if "embedding" in doc:
                    embedding = doc["embedding"]
                elif self.embedding_function is not None:
                    try:
                        raw_embedding = self.embedding_function([text])
                        
                        # Process different embedding formats
                        if isinstance(raw_embedding, list):
                            if len(raw_embedding) > 0:
                                if isinstance(raw_embedding[0], list):
                                    # Case: list of lists of floats
                                    embedding = raw_embedding[0]
                                elif isinstance(raw_embedding[0], (float, int)):
                                    # Case: list of floats (single embedding)
                                    embedding = raw_embedding
                        elif isinstance(raw_embedding, np.ndarray):
                            # Case: numpy array
                            if raw_embedding.ndim == 2:
                                embedding = raw_embedding[0].tolist()
                            else:
                                embedding = raw_embedding.tolist()
                    except Exception as e:
                        print(f"❌ Error generating embedding for restore: {e}")
                
                # Add to collection
                self.add(
                    memory_type=memory_type,
                    id=original_id,
                    text=text,
                    metadata=metadata,
                    embedding=embedding
                )
            
            return True
        except Exception as e:
            print(f"❌ Error restoring collection: {e}")
            return False
    
    def _convert_filter(self, filter_dict: Dict[str, Any]) -> models.Filter:
        """Convert filter dictionary to Qdrant filter."""
        conditions = []
        
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                # Handle operators like $eq, $gt, $lt, etc.
                for op, op_value in value.items():
                    if op == "$eq":
                        conditions.append(models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=op_value)
                        ))
                    elif op == "$ne":
                        conditions.append(models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=op_value),
                            match_value=False
                        ))
                    elif op == "$gt":
                        conditions.append(models.FieldCondition(
                            key=key,
                            range=models.Range(gt=op_value)
                        ))
                    elif op == "$gte":
                        conditions.append(models.FieldCondition(
                            key=key,
                            range=models.Range(gte=op_value)
                        ))
                    elif op == "$lt":
                        conditions.append(models.FieldCondition(
                            key=key,
                            range=models.Range(lt=op_value)
                        ))
                    elif op == "$lte":
                        conditions.append(models.FieldCondition(
                            key=key,
                            range=models.Range(lte=op_value)
                        ))
                    elif op == "$in":
                        if isinstance(op_value, list):
                            conditions.append(models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=op_value)
                            ))
            else:
                # Simple equality
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                ))
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return models.Filter(
            must=conditions
        )

# For backwards compatibility - Make ChromaDBStorage class an alias of QdrantStorage
ChromaDBStorage = QdrantStorage