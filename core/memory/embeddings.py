import os
import torch
from typing import List, Union, Callable, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingProvider:
    """Provides text embedding functionality for memory system."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding provider.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            # Check if CUDA is available
            if torch.cuda.is_available():
                device = "cuda"
                print(f"✅ Using GPU for embeddings: {torch.cuda.get_device_name(0)}")
            else:
                device = "cpu"
                print("⚠️ No GPU detected, using CPU for embeddings")
            
            # Create models directory if it doesn't exist
            os.makedirs("models/embeddings", exist_ok=True)
            
            print(f"🔄 Loading embedding model '{self.model_name}'...")
            self.model = SentenceTransformer(
                self.model_name, 
                cache_folder="models/embeddings",
                device=device
            )
            print(f"✅ Embedding model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            self.model = None
    
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Single string or list of strings to embed
            
        Returns:
            List of embeddings (one per text)
        """
        if self.model is None:
            try:
                self._initialize_model()
            except Exception as e:
                print(f"❌ Cannot generate embeddings, model failed to load: {e}")
                if isinstance(text, list):
                    # Return zero vectors with correct dimension
                    return [[0.0] * 384 for _ in range(len(text))]
                else:
                    return [0.0] * 384
        
        try:
            # Ensure text is a list
            if isinstance(text, str):
                text = [text]
            
            # Generate embeddings
            with torch.no_grad():
                embeddings = self.model.encode(text, convert_to_numpy=True)
            
            # Convert numpy arrays to lists for JSON serialization
            result = embeddings.tolist()
            
            # If only one text was provided, return just that embedding
            if len(result) == 1 and isinstance(text, list) and len(text) == 1:
                return result[0]
            
            return result
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            if len(text) > 1:
                return [[0.0] * 384 for _ in range(len(text))]
            else:
                return [0.0] * 384
    
    def get_embedding_function(self) -> Callable:
        """
        Get a function that can be used as a ChromaDB embedding function.
        
        Returns:
            Function that takes a list of strings and returns embeddings
        """
        def embedding_function(texts: List[str]) -> List[List[float]]:
            return self.embed_text(texts)
        
        return embedding_function
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure the result is between 0 and 1
        return float(max(0.0, min(1.0, similarity)))
    
    def batch_similarities(self, query_embedding: List[float], target_embeddings: List[List[float]]) -> List[float]:
        """
        Calculate similarities between a query embedding and multiple target embeddings.
        
        Args:
            query_embedding: Query embedding vector
            target_embeddings: List of target embedding vectors
            
        Returns:
            List of similarity scores
        """
        if not query_embedding or not target_embeddings:
            return [0.0] * len(target_embeddings) if target_embeddings else []
        
        # Convert to numpy arrays
        query_vec = np.array(query_embedding)
        target_vecs = np.array(target_embeddings)
        
        # Normalize query vector
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return [0.0] * len(target_embeddings)
        query_vec = query_vec / query_norm
        
        # Normalize target vectors
        target_norms = np.linalg.norm(target_vecs, axis=1, keepdims=True)
        target_norms[target_norms == 0] = 1.0  # Avoid division by zero
        target_vecs = target_vecs / target_norms
        
        # Calculate cosine similarities
        similarities = np.dot(target_vecs, query_vec)
        
        # Ensure results are between 0 and 1
        similarities = np.clip(similarities, 0.0, 1.0)
        
        return similarities.tolist()