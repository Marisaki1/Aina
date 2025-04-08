import os
import shutil
import chromadb
from typing import Dict, List, Any, Optional, Callable, Union

class ChromaDBStorage:
    """Interface to ChromaDB for vector storage and retrieval."""
    
    def __init__(self, 
                 base_path: str = "data/aina/memories",
                 embedding_function: Optional[Callable] = None):
        """
        Initialize ChromaDB storage.
        
        Args:
            base_path: Base directory for ChromaDB collections
            embedding_function: Function to convert text to embeddings
        """
        self.base_path = base_path
        self.embedding_function = embedding_function
        
        # Create directories
        os.makedirs(base_path, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(path=base_path)
        
        # Initialize collections dictionary
        self.collections = {}
        
        # Memory types and their collection names
        self.memory_types = {
            "core": "core_memories",
            "episodic": "episodic_memories",
            "semantic": "semantic_memories",
            "personal": "personal_memories"
        }
        
        # Initialize collections
        self._initialize_collections()
        
        print(f"✅ ChromaDB initialized at {base_path}")
    
    def _initialize_collections(self):
        """Initialize or get existing collections for each memory type."""
        for memory_type, collection_name in self.memory_types.items():
            try:
                # Try to get existing collection
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                self.collections[memory_type] = collection
            except Exception:
                # Create new collection if it doesn't exist
                collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                self.collections[memory_type] = collection
                
            print(f"  ✓ Collection '{collection_name}' ready")
    
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Add document
        if embedding is not None:
            collection.add(
                ids=[id],
                documents=[text],
                metadatas=[metadata] if metadata else None,
                embeddings=[embedding]
            )
        else:
            collection.add(
                ids=[id],
                documents=[text],
                metadatas=[metadata] if metadata else None
            )
        
        return id
    
    def get(self, memory_type: str, id: str) -> Dict[str, Any]:
        """Retrieve a document by ID from the specified memory collection."""
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Get document
        result = collection.get(ids=[id], include=["documents", "metadatas", "embeddings"])
        
        if not result["ids"]:
            return None
        
        # Format result
        return {
            "id": result["ids"][0],
            "text": result["documents"][0],
            "metadata": result["metadatas"][0] if result["metadatas"] else {},
            "embedding": result["embeddings"][0] if "embeddings" in result and result["embeddings"] else None
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        try:
            # Update document
            if text is not None and embedding is not None:
                collection.update(
                    ids=[id],
                    documents=[text],
                    metadatas=[metadata] if metadata else None,
                    embeddings=[embedding]
                )
            elif text is not None:
                collection.update(
                    ids=[id],
                    documents=[text],
                    metadatas=[metadata] if metadata else None
                )
            elif metadata is not None:
                # Get existing document if only updating metadata
                existing = self.get(memory_type, id)
                if existing:
                    collection.update(
                        ids=[id],
                        metadatas=[metadata]
                    )
                else:
                    return False
            else:
                return False  # Nothing to update
                
            return True
        except Exception as e:
            print(f"❌ Error updating document: {e}")
            return False
    
    def delete(self, memory_type: str, id: str) -> bool:
        """Delete a document from the specified memory collection."""
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        try:
            collection.delete(ids=[id])
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Search by text
        results = collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                    "similarity": 1.0 - min(1.0, results["distances"][0][i]) if "distances" in results else 0.0
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Search by vector
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                    "similarity": 1.0 - min(1.0, results["distances"][0][i]) if "distances" in results else 0.0
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Search by metadata
        results = collection.get(
            where=filter,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        # Format results
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
        
        return formatted_results
    
    def get_all(self, memory_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all documents from the specified memory collection."""
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        # Get all documents
        results = collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        # Format results
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
        
        return formatted_results
    
    def count(self, memory_type: str) -> int:
        """Get the number of documents in the specified memory collection."""
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection = self.collections[memory_type]
        
        return collection.count()
    
    def clear(self, memory_type: str) -> bool:
        """Clear all documents from the specified memory collection."""
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_name = self.memory_types[memory_type]
        
        try:
            # Delete collection
            self.client.delete_collection(collection_name)
            
            # Recreate collection
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            self.collections[memory_type] = collection
            
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
        if memory_type not in self.collections:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        collection_path = os.path.join(self.base_path, self.memory_types[memory_type])
        if not os.path.exists(collection_path):
            print(f"⚠️ Collection path not found: {collection_path}")
            return False
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy collection directory
            shutil.copytree(collection_path, os.path.join(backup_path, self.memory_types[memory_type]))
            
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
        
        backup_collection_path = os.path.join(backup_path, self.memory_types[memory_type])
        if not os.path.exists(backup_collection_path):
            print(f"⚠️ Backup collection not found: {backup_collection_path}")
            return False
        
        try:
            # Clear existing collection
            self.clear(memory_type)
            
            # Copy backup collection directory
            collection_path = os.path.join(self.base_path, self.memory_types[memory_type])
            if os.path.exists(collection_path):
                shutil.rmtree(collection_path)
            
            shutil.copytree(backup_collection_path, collection_path)
            
            # Reinitialize collection
            self.collections[memory_type] = self.client.get_collection(
                name=self.memory_types[memory_type],
                embedding_function=self.embedding_function
            )
            
            return True
        except Exception as e:
            print(f"❌ Error restoring collection: {e}")
            return False