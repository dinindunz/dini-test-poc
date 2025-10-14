# Weighted Vector Boosting

[← Back to Documentation Index](../README.md)

**Navigation:** [← Previous: pgvector Indexing](./06_pgvector_indexing.md)

---

What are the approaches to apply weights or boost certain vectors to prioritise specific code chunks in search results?

You can apply metadata-based reranking after retrieval to boost similarity scores based on chunk characteristics (layer, file type, annotations, etc.). This allows you to prioritise controller classes over DTOs, or Java code over documentation, without re-vectorising. Here are the main approaches:

### Approaches to Weight Vectors in RAG

#### 1. Metadata-based Reranking (Post-Retrieval Boosting) ⭐ Recommended

After retrieving results, boost scores based on metadata:

```python
def rerank_results(results: List[Dict], boost_config: Dict) -> List[Dict]:
    """
    Rerank results by applying metadata-based score boosting

    Args:
        results: Retrieved chunks with similarity scores
        boost_config: {"layer": {"controller": 1.5, "service": 1.2}, ...}
    """
    for result in results:
        original_score = result['similarity']
        boost_multiplier = 1.0

        # Boost by layer
        if 'layer' in result['metadata']:
            layer = result['metadata']['layer']
            boost_multiplier *= boost_config.get('layer', {}).get(layer, 1.0)

        # Boost by file type
        if 'file_type' in result['metadata']:
            file_type = result['metadata']['file_type']
            boost_multiplier *= boost_config.get('file_type', {}).get(file_type, 1.0)

        # Apply boost
        result['boosted_similarity'] = original_score * boost_multiplier

    # Re-sort by boosted score
    return sorted(results, key=lambda x: x['boosted_similarity'], reverse=True)
```

**Usage:**

```python
# Search for "authentication logic"
results = vector_store.similarity_search(query_embedding, top_k=20)

# Boost service layer and Java files
boost_config = {
    "layer": {"service": 1.5, "controller": 1.2, "repository": 1.1},
    "file_type": {"java": 1.3, "swagger": 0.8}
}

reranked = rerank_results(results, boost_config)[:5]  # Take top 5 after boosting
```

#### 2. Query-time Embedding Manipulation

Modify the query embedding to bias towards certain semantic spaces:

```python
def apply_query_bias(query_embedding: List[float], bias_vector: List[float], alpha: float = 0.2):
    """
    Blend query embedding with bias vector

    Args:
        query_embedding: Original query vector
        bias_vector: Direction to bias towards (e.g., average of all controller embeddings)
        alpha: Bias strength (0.0 = no bias, 1.0 = full bias)
    """
    import numpy as np

    query = np.array(query_embedding)
    bias = np.array(bias_vector)

    # Weighted combination
    biased_query = (1 - alpha) * query + alpha * bias

    # Normalise to unit vector (for cosine similarity)
    biased_query = biased_query / np.linalg.norm(biased_query)

    return biased_query.tolist()
```

#### 3. Hybrid Scoring (Semantic + Lexical)

Combine vector similarity with keyword/metadata exact matching:

```python
def hybrid_score(
    semantic_score: float,
    metadata_matches: int,
    semantic_weight: float = 0.7,
    metadata_weight: float = 0.3
) -> float:
    """
    Combine semantic similarity with metadata matching

    Example:
        semantic_score = 0.85 (cosine similarity)
        metadata_matches = 2 (matches "java" and "controller")
        -> hybrid_score = 0.7*0.85 + 0.3*0.67 = 0.595 + 0.201 = 0.796
    """
    # Normalise metadata matches (assume max 3 fields can match)
    metadata_score = min(metadata_matches / 3.0, 1.0)

    return semantic_weight * semantic_score + metadata_weight * metadata_score
```

#### 4. Store Pre-computed Boost Factors (Database-level)

Add a `boost_factor` column to the database:

```sql
ALTER TABLE code_embeddings ADD COLUMN boost_factor FLOAT DEFAULT 1.0;

-- Boost important chunks
UPDATE code_embeddings
SET boost_factor = 1.5
WHERE metadata->>'layer' = 'controller';

UPDATE code_embeddings
SET boost_factor = 1.3
WHERE metadata->>'file_type' = 'java';

-- Query with boost
SELECT
    id,
    content,
    metadata,
    (1 - (embedding <=> %s)) * boost_factor as weighted_similarity
FROM code_embeddings
ORDER BY weighted_similarity DESC
LIMIT 5;
```

### Recommended Implementation for Code Search

**Approach #1 (Metadata-based Reranking)** is recommended because:

1. ✅ **Flexible**: Easy to adjust boost factors without re-vectorising
2. ✅ **Transparent**: Can see original similarity + boost separately
3. ✅ **Query-specific**: Different queries can use different boost strategies
4. ✅ **No DB changes**: Works with existing schema

**Example for Spring Boot code search:**

```python
# In your retrieval tool
def retrieve_with_boosting(
    query: str,
    top_k: int = 5,
    layer_preference: Optional[str] = None
):
    # 1. Get more results than needed
    results = vector_store.similarity_search(
        query_embedding=generate_embedding(query),
        top_k=top_k * 3  # Over-retrieve
    )

    # 2. Apply context-aware boosting
    boost_config = {
        "layer": {
            "controller": 1.3,  # Boost REST controllers
            "service": 1.2,     # Slightly boost services
            "dto": 0.9          # De-boost DTOs
        },
        "file_type": {
            "java": 1.2,        # Boost Java code
            "swagger": 1.0,     # Neutral for API specs
            "markdown": 0.8     # De-boost docs
        }
    }

    # 3. User can override layer preference
    if layer_preference:
        boost_config["layer"][layer_preference] = 1.5

    # 4. Rerank and return top K
    reranked = rerank_results(results, boost_config)
    return reranked[:top_k]
```

### Practical Example: Before vs After Boosting

**Query:** "Show me authentication logic"

**Before Boosting (Pure Semantic Search):**

```
1. AuthService.java         - similarity: 0.92
2. README (Auth section)    - similarity: 0.88  ⚠️ Documentation ranks high
3. AuthController.java      - similarity: 0.85
4. auth-config.yaml         - similarity: 0.82  ⚠️ Config ranks high
5. AuthRepository.java      - similarity: 0.78
```

**After Boosting (Java 1.3x, Service layer 1.5x, Markdown 0.8x):**

```
1. AuthService.java         - boosted: 1.20 (0.92 × 1.3 × 1.5)  ✅ Service + Java
2. AuthController.java      - boosted: 1.11 (0.85 × 1.3)        ✅ Java code
3. AuthRepository.java      - boosted: 1.01 (0.78 × 1.3)        ✅ Java code
4. README (Auth section)    - boosted: 0.70 (0.88 × 0.8)        ⬇️ Docs de-boosted
5. auth-config.yaml         - boosted: 0.82 (0.82 × 1.0)        → Neutral
```

**Result:** Java service classes now rank higher than documentation!

### Use Cases

#### Use Case 1: Prioritise Architectural Layers

```python
# User asks about business logic
boost_config = {
    "layer": {
        "service": 1.5,      # Business logic (highest priority)
        "controller": 1.2,   # API layer
        "repository": 1.1,   # Data access
        "dto": 0.9           # Data transfer objects (lower priority)
    }
}
```

#### Use Case 2: Prioritise Code Over Docs

```python
# User wants implementation examples
boost_config = {
    "file_type": {
        "java": 1.4,         # Implementation code (highest)
        "swagger": 1.1,      # API specs (medium)
        "markdown": 0.7,     # Documentation (lower)
        "yaml": 0.8          # Configuration (lower)
    }
}
```

#### Use Case 3: Context-aware Boosting

```python
# Detect query intent and adjust boosts
if "REST API" in query or "endpoint" in query:
    boost_config["layer"]["controller"] = 1.8  # Prioritise controllers
elif "database" in query or "data access" in query:
    boost_config["layer"]["repository"] = 1.8  # Prioritise repositories
elif "business logic" in query:
    boost_config["layer"]["service"] = 1.8     # Prioritise services
```

### Comparison of Approaches

| Approach | Flexibility | Performance | DB Changes | Use Case |
|----------|------------|-------------|------------|----------|
| **Metadata Reranking** | ⭐⭐⭐ High | ⚡⚡ Good | ✅ None | General purpose, query-specific |
| **Query Bias** | ⭐⭐ Medium | ⚡⚡⚡ Excellent | ✅ None | Pre-filter towards semantic space |
| **Hybrid Scoring** | ⭐⭐ Medium | ⚡⚡ Good | ✅ None | Combine semantic + exact matching |
| **DB Boost Column** | ⭐ Low | ⚡⚡⚡ Excellent | ❌ Schema change | Static, global boosts |

### Key Principles

1. **Over-retrieve, then rerank**: Fetch 3-5x more results than needed, then boost and trim
2. **Multiplicative boosts**: Use 1.0-2.0 range (1.0 = neutral, 1.5 = 50% boost, 0.8 = 20% de-boost)
3. **Context-aware**: Adjust boosts based on query intent or user preferences
4. **Transparent scoring**: Keep original similarity alongside boosted score for debugging

### Summary

**Recommended approach for your RAG system:**
- Use **Approach #1: Metadata-based Reranking**
- Over-retrieve results (e.g., top_k=20)
- Apply boost multipliers based on layer, file_type, annotations
- Re-sort by boosted scores
- Return final top K results

**Benefits:**
- No database schema changes
- Flexible per-query tuning
- Transparent (can see original + boosted scores)
- Easy to experiment with different boost strategies

This gives you fine-grained control over search result prioritisation whilst maintaining the power of semantic search! 🎯
