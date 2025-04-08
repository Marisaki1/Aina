import os
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

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
        
        # Initialize collections
        self._initialize_collections()
        
        print(f"✅ Qdrant initialized at {url}:{port}")
    
    def _initialize_collections(self):
        """Initialize or get existing collections for each memory type."""
        # Get embedding dimensionality from a test embedding
        # This assumes embedding_function returns a list with dimensions (1, n)
        if self.embedding_function is not None:
            test_embedding = self.embedding_function(["test"])
            if isinstance(test_embedding, list) and len(test_embedding) > 0:
                embedding_dim = len(test_embedding[0])
            else:
                # Default to a common embedding size if we can't determine
                embedding_dim = 384
        else:
            # Default to a common embedding size
            embedding_dim = 384
            
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
        
        # Generate embedding if not provided
        if embedding is None and self.embedding_function is not None:
            embedding = self.embedding_function([text])[0]
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add text to metadata for retrieval
        payload = {
            "text": text,
            **metadata
        }
        
        # Add point to collection
        self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return id
    
    def get(self, memory_type: str, id: str) -> Dict[str, Any]:
        """Retrieve a document by ID from the specified memory collection."""
        if memory_type not in self.memory_types:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        # Get point from collection
        result = self.client.retrieve(
            collection_name=collection_name,
            ids=[id],
            with_vectors=True
        )
        
        if not result:
            return None
        
        point = result[0]
        
        # Format result
        return {
            "id": point.id,
            "text": point.payload.get("text", ""),
            "metadata": {k: v for k, v in point.payload.items() if k != "text"},
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
            
            # Update metadata if provided
            if metadata is not None:
                for key, value in metadata.items():
                    payload[key] = value
            elif existing:
                for key, value in existing["metadata"].items():
                    payload[key] = value
            
            # Generate new embedding if text changed and no embedding provided
            if text is not None and embedding is None and self.embedding_function is not None:
                embedding = self.embedding_function([text])[0]
            
            # Use existing embedding if none provided
            if embedding is None and existing:
                embedding = existing["embedding"]
            
            # Update point
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=id,
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
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[id]
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
            
        query_vector = self.embedding_function([query_text])[0]
        
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
            formatted_results.append({
                "id": result.id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"},
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
            formatted_results.append({
                "id": result.id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"},
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
            formatted_results.append({
                "id": result.id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
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
            formatted_results.append({
                "id": result.id,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
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
                test_embedding = self.embedding_function(["test"])
                if isinstance(test_embedding, list) and len(test_embedding) > 0:
                    embedding_dim = len(test_embedding[0])
            
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
            
            # Restore documents
            for doc in documents:
                # Skip if missing required fields
                if "id" not in doc or "text" not in doc:
                    continue
                
                # Extract fields
                doc_id = doc["id"]
                text = doc["text"]
                metadata = doc.get("metadata", {})
                
                # Generate embedding if needed
                embedding = None
                if "embedding" in doc:
                    embedding = doc["embedding"]
                elif self.embedding_function is not None:
                    embedding = self.embedding_function([text])[0]
                
                # Add to collection
                self.add(
                    memory_type=memory_type,
                    id=doc_id,
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