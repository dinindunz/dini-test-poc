# pgvector Indexing Strategies

[← Back to Documentation Index](../README.md)

**Navigation:** [← Previous: Tree-sitter Parsing](./05_tree_sitter_parsing.md) | [Next: Weighted Boosting →](./07_weighted_boosting.md)

---

Explain pgvector indexing strategies: IVFFlat vs HNSW, and which is best for code search

HNSW (Hierarchical Navigable Small World) is best for code search due to its high accuracy and fast queries for small-to-medium datasets, while IVFFlat is better for very large datasets (100k+ vectors). Here's a detailed comparison:

### Index Strategy 1: IVFFlat (Inverted File with Flat Search)

**SQL:**

```sql
CREATE INDEX ON code_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**How it works:**

1. **Clustering Phase** (index build):
   - Divides all vectors into 100 clusters (like neighbourhoods)
   - Each vector assigned to nearest cluster centroid

2. **Search Phase** (query time):
   - Find closest cluster(s) to query vector
   - Search ALL vectors within that cluster exhaustively

**Visual:**

```
Query: [0.2, 0.3, 0.4]
       ↓
Find nearest cluster → Cluster 42
       ↓
Scan all vectors in Cluster 42 exhaustively
       ↓
Return top K results
```

**Parameters:**
- `lists = 100`: Number of clusters to create
  - Rule of thumb: `lists = rows / 1000` for large datasets
  - More lists = finer partitioning = faster search, slower build

**Trade-offs:**
- ✅ Fast for very large datasets (millions of vectors)
- ✅ Lower memory usage
- ❌ **Approximate results** (might miss true nearest neighbour)
- ❌ Requires training/clustering phase
- ❌ Not optimal for small datasets (<100k vectors)

---

### Index Strategy 2: HNSW (Hierarchical Navigable Small World)

**SQL:**

```sql
CREATE INDEX ON code_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**How it works:**

Multi-layer graph structure (like a highway system):

```
Layer 2 (highways):     A -------- B

Layer 1 (main roads):   A -- C -- B -- D
                        |    |    |    |
Layer 0 (local):        A-C-E-F-B-G-D-H-I...
```

**Search Process:**
1. Start at top layer (sparse, long jumps)
2. Navigate to closest node
3. Descend to next layer (denser connections)
4. Refine search until bottom layer
5. Return top K results

**Parameters:**
- `m = 16`: Number of bi-directional links per node
  - Higher M = more connections = better accuracy, more memory
  - Default and recommended: 16

- `ef_construction = 64`: Candidates explored during index build
  - Higher = slower build, better quality graph
  - Recommended: 64-128 for code search

**Trade-offs:**
- ✅ **Excellent recall** (very accurate approximate search)
- ✅ Fast queries after building
- ✅ No training phase needed
- ✅ Works great for small to large datasets
- ❌ Slower to build than IVFFlat
- ❌ Higher memory usage

---

### Distance Metrics

#### Cosine Distance (`vector_cosine_ops`)

Measures directional similarity, ignoring magnitude:

```
similarity = 1 - cosine_distance

Vector A: [0.1, 0.2, 0.3]  (short code snippet)
Vector B: [0.3, 0.6, 0.9]  (long code snippet, same direction)

Cosine similarity: 1.0 (identical direction, different magnitude)
```

**Best for:** Text/code embeddings where length varies

#### Euclidean Distance (`vector_l2_ops`)

Measures straight-line distance, magnitude-sensitive:

```
distance = sqrt((A[0]-B[0])² + (A[1]-B[1])² + ...)

Vector A: [0.1, 0.2, 0.3]
Vector B: [0.3, 0.6, 0.9]

L2 distance: 0.693 (penalised for magnitude difference)
```

**Best for:** Image embeddings, magnitude matters

---

### Side-by-Side Comparison

| Aspect | IVFFlat + Cosine | HNSW + Cosine |
|--------|------------------|---------------|
| **Structure** | Clusters (neighbourhoods) | Multi-layer graph (highways) |
| **Search** | Find cluster → scan all | Navigate graph layers |
| **Build Speed** | ⚡ Fast | 🐢 Slower |
| **Query Speed** | 🚀 Good | 🚀🚀 Excellent |
| **Accuracy** | ~Good (tunable) | ⭐ Excellent |
| **Memory** | 💾 Lower | 💾💾 Higher |
| **Best for** | 100k+ vectors | 100 - 1M vectors |

---

### Why We Chose HNSW + Cosine for Code Search

**Your use case:**
- Vectorising codebase (Spring Boot Java)
- Current: ~30 chunks, expected growth: 1k-10k chunks
- Need: High accuracy code retrieval

**Reasons for HNSW:**

#### 1. High Accuracy is Critical

```
Query: "authentication middleware"

You need to find:
✅ Auth filter classes
✅ JWT validation methods
✅ Security config

Not acceptable to miss:
❌ The actual AuthenticationFilter
```

#### 2. Dataset Size is Small-to-Medium

- IVFFlat optimal for 100k+ vectors
- Your codebase: likely < 10k chunks
- HNSW handles this range perfectly

#### 3. No Training Phase

- IVFFlat requires clustering (rebuild when data changes)
- HNSW builds incrementally (add vectors anytime)

#### 4. Fast Queries

- HNSW navigates graph layers efficiently
- Critical for interactive code search

**Reasons for Cosine:**

#### 1. Code Length Varies

```
Short utility:
def add(a, b):
    return a + b

Long controller:
@RestController
public class SampleController {
    // ... 50 lines of code ...
}
```

With cosine: Both compared by semantic meaning
With L2: Long snippet penalised for length

#### 2. Bedrock Titan Embeddings

- Titan embeddings are normalised
- Designed for cosine similarity

#### 3. Semantic Search

- Query: "REST endpoint handler"
- Should match: `@RestController` classes
- Direction matters, not magnitude

---

### Current Implementation

**In `pgvector_store.py:64`:**

```python
CREATE INDEX IF NOT EXISTS code_embeddings_embedding_idx
ON code_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
```

**What this means:**
- Uses HNSW graph structure
- Cosine distance for similarity
- Each node connects to 16 neighbours
- Explores 64 candidates during build

---

### If Your Codebase Grows

**Small (<10k chunks):** Current settings perfect

```sql
WITH (m = 16, ef_construction = 64)
```

**Medium (10k-50k chunks):** Increase quality

```sql
WITH (m = 24, ef_construction = 100)
```

**Large (50k+ chunks):** Maximum accuracy

```sql
WITH (m = 32, ef_construction = 128)
```

**Very large (1M+ chunks):** Consider IVFFlat

```sql
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000)
```

---

### Summary

**Best practice for code search:**
- ✅ Use **HNSW** (accurate, fast, no training)
- ✅ Use **Cosine distance** (length-invariant, semantic)
- ✅ Parameters: `m = 16, ef_construction = 64` (proven defaults)
- ✅ Scale up parameters as codebase grows

**Your current setup is optimal for code vectorisation!** 🚀


