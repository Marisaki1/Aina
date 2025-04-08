# Aina Memory System

This document describes the memory architecture for Aina, the AI assistant with persistent memory.

## Overview

Aina's memory system is designed to retain information across conversations and provide a more personalized and human-like interaction experience. The system has four main memory types:

1. **Core Memory** - Identity, values, and fundamental knowledge about Aina
2. **Episodic Memory** - Recent experiences and interactions
3. **Semantic Memory** - Long-term knowledge and facts
4. **Personal Memory** - User-specific information and preferences

## Architecture

The memory system is built around ChromaDB for vector storage and retrieval. Text is embedded using sentence-transformers to enable semantic search and similarity.

### Components

- **MemoryManager**: Central orchestration of all memory types
- **ChromaDBStorage**: Interface to ChromaDB for persistence
- **EmbeddingProvider**: Text embedding using sentence-transformers
- **Memory Type Modules**: Specialized modules for each memory type
- **Reflection**: Memory consolidation and analysis

## Memory Types

### Core Memory

Core memory contains fundamental information about Aina's identity, values, and capabilities. This includes:

- Self-concept and identity
- Values and principles
- Personality traits
- Core capabilities

Core memories have high importance scores and are prioritized during retrieval.

### Episodic Memory

Episodic memory stores recent experiences and interactions with users. This includes:

- Conversations with users
- Events and system activities
- Command executions and responses
- Important moments

Episodic memories are time-sensitive and gradually decay in importance over time.

### Semantic Memory

Semantic memory stores factual information and knowledge. This includes:

- Facts learned from conversations
- Conceptual knowledge
- Rules and guidelines
- World knowledge

Semantic memory is organized by categories and tags for efficient retrieval.

### Personal Memory

Personal memory stores user-specific information. This includes:

- User preferences and traits
- User interaction patterns
- Important facts about users
- User-specific instructions or rules

Personal memories are associated with specific user IDs.

## Reflection System

The reflection system periodically analyzes memories to:

1. Consolidate related memories
2. Generate insights about users and interactions
3. Identify patterns and important information
4. Create summaries of recent activity

Reflections occur daily and weekly, generating new semantic memories from insights.

## Implementation Details

### Data Storage

- ChromaDB is used for vector storage and similarity search
- Memories are stored in four collections (one per memory type)
- Each memory includes text, metadata, and vector embeddings
- File-based storage with JSON for reflections and configuration

### Embedding

- Sentence transformers (all-MiniLM-L6-v2) for text embedding
- GPU acceleration when available
- 384-dimensional embedding vectors
- Cosine similarity for retrieval

### Optimization

- Lazy loading of models and components
- CUDA acceleration for embeddings
- Efficient vector search with filters
- Memory importance scoring for prioritization

## Usage

### Storing Memories

```python
# Store a personal memory about a user
memory_id = memory_manager.store_memory(
    text="The user likes chocolate ice cream",
    memory_type="personal",
    metadata={
        "user_id": "123456789",
        "importance": 0.7,
        "category": "preference" 
    }
)
```

### Retrieving Memories

```python
# Search across all memory types
memories = memory_manager.search_memories(
    query="What does the user like?",
    memory_types=["personal", "episodic"],
    user_id="123456789",
    limit=5
)
```

### Memory Reflection

```python
# Trigger a daily reflection
reflection = memory_manager.trigger_reflection("daily")
```

## Configuration

Memory system behavior can be configured through the `data/aina/config/memory_config.json` file:

```json
{
  "base_memory_path": "data/aina/memories",
  "embedding_model": "all-MiniLM-L6-v2",
  "importance_threshold": 0.5,
  "recency_weight": 0.3,
  "relevance_weight": 0.5,
  "importance_weight": 0.2,
  "max_results": 10
}
```

## Directory Structure

```
data/aina/
├── memories/            # ChromaDB memory collections
│   ├── core/            # Core identity memories
│   ├── episodic/        # Recent experiences
│   ├── semantic/        # Long-term knowledge
│   └── personal/        # User-specific memories
├── reflections/         # Periodic memory analysis
│   ├── daily/           # Daily summaries
│   └── weekly/          # Weekly memory consolidation
├── config/
│   ├── personality.json # Aina's personality settings
│   └── memory_config.json # Memory thresholds & settings
└── backups/             # Backup storage for memories
```

## Integration with LLM

The memory system integrates with the LLM through:

1. **Context enhancement**: Relevant memories are included in the prompt
2. **Memory creation**: Important information from conversations is stored
3. **User profiles**: User information influences responses
4. **Reflection**: Insights guide future interactions

## Hardware Optimization

The memory system is optimized for the RTX 4070 Super with:

- GPU acceleration for embeddings
- Efficient batch processing
- Optimized vector operations
- Appropriate memory usage for VRAM limitations