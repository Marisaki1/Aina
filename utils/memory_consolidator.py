import os
import time
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
import numpy as np
from collections import defaultdict

class MemoryConsolidator:
    """
    Consolidates and optimizes memories by identifying relationships,
    merging similar memories, and generating higher-level concepts.
    """
    
    def __init__(self, memory_manager, embedding_provider):
        """
        Initialize memory consolidator.
        
        Args:
            memory_manager: MemoryManager instance
            embedding_provider: EmbeddingProvider instance
        """
        self.memory_manager = memory_manager
        self.embedding_provider = embedding_provider
        
        # Thresholds
        self.similarity_threshold = 0.85  # Threshold for considering memories similar
        self.merge_threshold = 0.92       # Threshold for merging memories
        self.concept_threshold = 0.75     # Threshold for identifying concepts
        
        # Create log directory
        os.makedirs("data/aina/consolidation", exist_ok=True)
    
    def consolidate_episodic_memories(self, 
                                    days: int = 7, 
                                    min_importance: float = 0.0) -> Dict[str, Any]:
        """
        Consolidate episodic memories, merging similar ones and identifying patterns.
        
        Args:
            days: Number of days to look back
            min_importance: Minimum importance threshold
            
        Returns:
            Consolidation results
        """
        print(f"🔄 Consolidating episodic memories from past {days} days...")
        
        # Get memories to consolidate
        memories = self.memory_manager.episodic_memory.get_recent_memories(
            hours=days * 24, 
            limit=1000,
            min_importance=min_importance
        )
        
        if not memories:
            print("❌ No memories found to consolidate")
            return {
                "status": "error",
                "message": "No memories found to consolidate",
                "merged": 0,
                "archived": 0
            }
        
        # Find similar memory clusters
        clusters = self._cluster_similar_memories(memories)
        
        # Merge clusters
        merged_count = 0
        archived_count = 0
        
        # Process each cluster
        for cluster in clusters:
            if len(cluster) < 2:
                # Skip single-memory clusters
                continue
            
            # Sort cluster by importance
            sorted_cluster = sorted(
                cluster, 
                key=lambda x: x.get("metadata", {}).get("importance", 0),
                reverse=True
            )
            
            # Get primary memory (most important)
            primary_memory = sorted_cluster[0]
            
            # Check for extremely similar memories (above merge threshold)
            merge_candidates = []
            archive_candidates = []
            
            for memory in sorted_cluster[1:]:
                # Calculate similarity between primary memory and this one
                primary_text = primary_memory["text"]
                current_text = memory["text"]
                
                similarity = self._calculate_similarity(primary_text, current_text)
                
                if similarity >= self.merge_threshold:
                    # This is a merge candidate - content is nearly identical
                    merge_candidates.append(memory)
                elif similarity >= self.similarity_threshold:
                    # This is a related memory but different enough to keep separately
                    # Mark for possible archiving
                    archive_candidates.append(memory)
            
            # Merge extremely similar memories
            if merge_candidates:
                merged_count += len(merge_candidates)
                
                # Combine metadata
                self._merge_memories(primary_memory, merge_candidates)
            
            # Consider archiving related but different memories
            if archive_candidates:
                # Only archive if we have enough merged memories
                if len(merge_candidates) >= 2:
                    archived_count += len(archive_candidates)
                    self._archive_memories(archive_candidates)
        
        # Log consolidation results
        consolidation_log = {
            "timestamp": time.time(),
            "days_range": days,
            "total_memories": len(memories),
            "merged_memories": merged_count,
            "archived_memories": archived_count,
            "clusters_found": len(clusters)
        }
        
        # Save log
        log_path = f"data/aina/consolidation/episodic_{int(time.time())}.json"
        with open(log_path, "w") as f:
            json.dump(consolidation_log, f, indent=2)
        
        print(f"✅ Consolidated episodic memories: merged {merged_count}, archived {archived_count}")
        
        return {
            "status": "success",
            "message": f"Consolidated memories: merged {merged_count}, archived {archived_count}",
            "merged": merged_count,
            "archived": archived_count,
            "total": len(memories)
        }
    
    def consolidate_personal_memories(self, 
                                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Consolidate personal memories for a user or all users.
        
        Args:
            user_id: Specific user ID or None for all users
            
        Returns:
            Consolidation results
        """
        print(f"🔄 Consolidating personal memories{' for user ' + user_id if user_id else ''}...")
        
        # Get all personal memories
        if user_id:
            memories = self.memory_manager.personal_memory.get_user_memories(user_id, limit=1000)
        else:
            memories = self.memory_manager.retrieve_all_memories("personal", limit=1000)
        
        if not memories:
            print("❌ No personal memories found to consolidate")
            return {
                "status": "error", 
                "message": "No personal memories found to consolidate",
                "merged": 0
            }
        
        # Group by user ID if no specific user
        if not user_id:
            # Group memories by user
            user_memories = defaultdict(list)
            
            for memory in memories:
                uid = memory.get("metadata", {}).get("user_id")
                if uid:
                    user_memories[uid].append(memory)
            
            # Process each user
            total_merged = 0
            for uid, user_mems in user_memories.items():
                result = self._consolidate_user_personal_memories(uid, user_mems)
                total_merged += result.get("merged", 0)
            
            return {
                "status": "success",
                "message": f"Consolidated personal memories for {len(user_memories)} users",
                "merged": total_merged,
                "users": len(user_memories)
            }
        else:
            # Process single user
            return self._consolidate_user_personal_memories(user_id, memories)
    
    def _consolidate_user_personal_memories(self, 
                                          user_id: str, 
                                          memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate personal memories for a specific user."""
        # Group by memory_subtype
        subtypes = defaultdict(list)
        
        for memory in memories:
            subtype = memory.get("metadata", {}).get("memory_subtype", "info")
            subtypes[subtype].append(memory)
        
        merged_count = 0
        
        # Process each subtype
        for subtype, subtype_memories in subtypes.items():
            # Skip if only a few memories
            if len(subtype_memories) < 3:
                continue
            
            # Find duplicate/conflicting information
            if subtype == "trait":
                # Group by trait_type
                traits = defaultdict(list)
                for memory in subtype_memories:
                    trait_type = memory.get("metadata", {}).get("trait_type", "general")
                    traits[trait_type].append(memory)
                
                # Merge similar traits
                for trait_type, trait_memories in traits.items():
                    clusters = self._cluster_similar_memories(trait_memories)
                    
                    for cluster in clusters:
                        if len(cluster) < 2:
                            continue
                        
                        # Sort by importance and recency
                        sorted_cluster = sorted(
                            cluster,
                            key=lambda x: (
                                x.get("metadata", {}).get("importance", 0),
                                x.get("metadata", {}).get("timestamp", 0)
                            ),
                            reverse=True
                        )
                        
                        # Merge
                        primary = sorted_cluster[0]
                        to_merge = sorted_cluster[1:]
                        self._merge_memories(primary, to_merge)
                        merged_count += len(to_merge)
            
            elif subtype == "preference":
                # Similar approach for preferences
                preferences = defaultdict(list)
                for memory in subtype_memories:
                    pref_type = memory.get("metadata", {}).get("preference_type", "general")
                    preferences[pref_type].append(memory)
                
                for pref_type, pref_memories in preferences.items():
                    clusters = self._cluster_similar_memories(pref_memories)
                    
                    for cluster in clusters:
                        if len(cluster) < 2:
                            continue
                        
                        # Sort by importance and recency
                        sorted_cluster = sorted(
                            cluster,
                            key=lambda x: (
                                x.get("metadata", {}).get("importance", 0),
                                x.get("metadata", {}).get("timestamp", 0)
                            ),
                            reverse=True
                        )
                        
                        # Merge
                        primary = sorted_cluster[0]
                        to_merge = sorted_cluster[1:]
                        self._merge_memories(primary, to_merge)
                        merged_count += len(to_merge)
            
            elif subtype == "info":
                # Group by info_type
                infos = defaultdict(list)
                for memory in subtype_memories:
                    info_type = memory.get("metadata", {}).get("info_type", "general")
                    infos[info_type].append(memory)
                
                for info_type, info_memories in infos.items():
                    clusters = self._cluster_similar_memories(info_memories)
                    
                    for cluster in clusters:
                        if len(cluster) < 2:
                            continue
                        
                        # Sort by importance and recency
                        sorted_cluster = sorted(
                            cluster,
                            key=lambda x: (
                                x.get("metadata", {}).get("importance", 0),
                                x.get("metadata", {}).get("timestamp", 0)
                            ),
                            reverse=True
                        )
                        
                        # Merge
                        primary = sorted_cluster[0]
                        to_merge = sorted_cluster[1:]
                        self._merge_memories(primary, to_merge)
                        merged_count += len(to_merge)
        
        # Log consolidation results
        consolidation_log = {
            "timestamp": time.time(),
            "user_id": user_id,
            "total_memories": len(memories),
            "merged_memories": merged_count
        }
        
        # Save log
        log_path = f"data/aina/consolidation/personal_{user_id}_{int(time.time())}.json"
        with open(log_path, "w") as f:
            json.dump(consolidation_log, f, indent=2)
        
        print(f"✅ Consolidated personal memories for user {user_id}: merged {merged_count}")
        
        return {
            "status": "success",
            "message": f"Consolidated personal memories for user {user_id}",
            "merged": merged_count,
            "total": len(memories)
        }
    
    def extract_concepts(self, min_importance: float = 0.5) -> Dict[str, Any]:
        """
        Extract high-level concepts from episodic memories and store in semantic memory.
        
        Args:
            min_importance: Minimum importance for memories to consider
            
        Returns:
            Extraction results
        """
        print(f"🔄 Extracting concepts from episodic memories...")
        
        # Get episodic memories
        memories = self.memory_manager.retrieve_all_memories("episodic", limit=1000)
        
        # Filter by importance
        memories = [
            m for m in memories 
            if m.get("metadata", {}).get("importance", 0) >= min_importance
        ]
        
        if not memories:
            print("❌ No memories found for concept extraction")
            return {
                "status": "error",
                "message": "No memories found for concept extraction",
                "concepts_extracted": 0
            }
        
        # Get text representations
        texts = [memory["text"] for memory in memories]
        
        # Generate embeddings
        embeddings = self.embedding_provider.embed_text(texts)
        
        # Cluster embeddings
        clusters = self._cluster_by_embeddings(embeddings)
        
        # Extract concepts from each significant cluster
        concepts_extracted = 0
        
        for i, cluster_indices in enumerate(clusters):
            if len(cluster_indices) < 3:
                # Skip small clusters
                continue
            
            # Get cluster memories
            cluster_memories = [memories[idx] for idx in cluster_indices]
            
            # Extract concept name and description
            concept_name, concept_description = self._extract_cluster_concept(cluster_memories)
            
            if concept_name and concept_description:
                # Store concept in semantic memory
                self.memory_manager.semantic_memory.store_concept(
                    text=concept_description,
                    concept_name=concept_name,
                    category="extracted_concept",
                    importance=0.7,
                    related_concepts=[],
                    tags=["extracted", "concept", f"cluster_{i}"]
                )
                
                concepts_extracted += 1
        
        # Log results
        log_data = {
            "timestamp": time.time(),
            "memories_analyzed": len(memories),
            "clusters_found": len(clusters),
            "concepts_extracted": concepts_extracted
        }
        
        log_path = f"data/aina/consolidation/concepts_{int(time.time())}.json"
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)
        
        print(f"✅ Extracted {concepts_extracted} concepts from episodic memories")
        
        return {
            "status": "success",
            "message": f"Extracted {concepts_extracted} concepts from {len(memories)} memories",
            "concepts_extracted": concepts_extracted,
            "memories_analyzed": len(memories)
        }
    
    def _cluster_similar_memories(self, memories: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Cluster similar memories using embeddings."""
        if not memories:
            return []
        
        # Get text representations
        texts = [memory["text"] for memory in memories]
        
        # Generate embeddings
        embeddings = self.embedding_provider.embed_text(texts)
        
        # Cluster embeddings
        cluster_indices = self._cluster_by_embeddings(embeddings)
        
        # Convert indices to memories
        clusters = [[memories[idx] for idx in cluster] for cluster in cluster_indices]
        
        return clusters
    
    def _cluster_by_embeddings(self, embeddings: List[List[float]]) -> List[List[int]]:
        """Cluster embeddings using similarity threshold."""
        if not embeddings:
            return []
        
        # Number of embeddings
        n = len(embeddings)
        
        # Initialize clusters
        clusters = []
        assigned = set()
        
        # Process each embedding
        for i in range(n):
            if i in assigned:
                continue
            
            # Start a new cluster
            cluster = [i]
            assigned.add(i)
            
            # Find similar embeddings
            for j in range(i+1, n):
                if j in assigned:
                    continue
                
                # Calculate similarity
                similarity = self.embedding_provider.calculate_similarity(embeddings[i], embeddings[j])
                
                if similarity >= self.similarity_threshold:
                    cluster.append(j)
                    assigned.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using embeddings."""
        # Generate embeddings
        embedding1 = self.embedding_provider.embed_text(text1)
        embedding2 = self.embedding_provider.embed_text(text2)
        
        # Calculate similarity
        return self.embedding_provider.calculate_similarity(embedding1, embedding2)
    
    def _merge_memories(self, primary_memory: Dict[str, Any], merge_candidates: List[Dict[str, Any]]) -> None:
        """Merge similar memories, keeping the primary memory and removing others."""
        if not merge_candidates:
            return
        
        # Get memory type
        memory_type = primary_memory.get("memory_type", "episodic")
        
        # Update primary memory metadata
        metadata = primary_memory.get("metadata", {}).copy()
        
        # Update importance - increase slightly based on merged memories
        importance = metadata.get("importance", 0.5)
        importance_boost = min(0.2, 0.05 * len(merge_candidates))
        new_importance = min(1.0, importance + importance_boost)
        
        metadata["importance"] = new_importance
        metadata["merged_count"] = metadata.get("merged_count", 0) + len(merge_candidates)
        metadata["merged_ids"] = metadata.get("merged_ids", []) + [m.get("id") for m in merge_candidates]
        metadata["last_consolidated"] = time.time()
        
        # Update primary memory
        self.memory_manager.update_memory(
            memory_type=memory_type,
            memory_id=primary_memory["id"],
            metadata=metadata
        )
        
        # Delete merged memories
        for memory in merge_candidates:
            self.memory_manager.delete_memory(memory_type, memory["id"])
    
    def _archive_memories(self, memories: List[Dict[str, Any]]) -> None:
        """Archive memories by reducing their importance."""
        if not memories:
            return
        
        for memory in memories:
            memory_type = memory.get("memory_type", "episodic")
            
            # Update metadata - reduce importance
            metadata = memory.get("metadata", {}).copy()
            importance = metadata.get("importance", 0.5)
            
            # Reduce importance by 30%
            metadata["importance"] = max(0.1, importance * 0.7)
            metadata["archived"] = True
            metadata["archive_time"] = time.time()
            
            # Update memory
            self.memory_manager.update_memory(
                memory_type=memory_type,
                memory_id=memory["id"],
                metadata=metadata
            )
    
    def _extract_cluster_concept(self, 
                               cluster_memories: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        """Extract a concept name and description from cluster memories."""
        if not cluster_memories:
            return None, None
        
        # Get common words and phrases
        texts = [memory["text"] for memory in cluster_memories]
        
        # Simple approach: find most common words
        # In a production system, this would use NLP techniques
        words = []
        for text in texts:
            words.extend(text.lower().split())
        
        # Count word frequency
        word_counts = defaultdict(int)
        for word in words:
            # Clean word (remove punctuation)
            word = word.strip('.,!?:;()"\'')
            if len(word) > 3:  # Skip short words
                word_counts[word] += 1
        
        # Sort by frequency
        common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Generate concept name from top words
        top_words = [word for word, count in common_words[:3] if count >= len(cluster_memories) * 0.5]
        
        if not top_words:
            return None, None
        
        concept_name = "_".join(top_words)
        
        # Generate concept description
        # Take most important memory as basis
        sorted_memories = sorted(
            cluster_memories,
            key=lambda x: x.get("metadata", {}).get("importance", 0),
            reverse=True
        )
        
        base_text = sorted_memories[0]["text"]
        memory_count = len(cluster_memories)
        
        concept_description = f"Concept extracted from {memory_count} related memories: {base_text}"
        
        return concept_name, concept_description