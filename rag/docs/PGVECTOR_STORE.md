# PostgreSQL Vector Store Module

**Module:** `core/pgvector_store.py`

[← Back to Documentation Index](./README.md)

---

## Overview

The `PgVectorStore` class provides a complete vector database implementation using PostgreSQL with the pgvector extension. It handles schema creation, embedding storage, similarity search, and metadata filtering for code retrieval systems.

## Features

- ✅ PostgreSQL with pgvector extension integration
- ✅ HNSW indexing for fast similarity search
- ✅ Cosine distance similarity metric
- ✅ JSONB metadata storage and filtering
- ✅ Batch insertion support
- ✅ Context manager support (with statement)
- ✅ Configurable table names
- ✅ Verbose query debugging mode

## Class: `PgVectorStore`

### Initialisation

```python
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig

# Create database config
config = DatabaseConfig()

# Initialise vector store
vector_store = PgVectorStore(
    config=config,
    table_name="code_embeddings"  # Optional, default: "embeddings"
)

# Connect to database
vector_store.connect()
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `DatabaseConfig` | *Required* | Database configuration object |
| `table_name` | `str` | `"embeddings"` | Name of the table to store embeddings |

## Methods

### `connect()`

Establish database connection and register pgvector types.

**Returns:** None

**Example:**

```python
vector_store = PgVectorStore(config=config, table_name="code_embeddings")
vector_store.connect()
# Output: ✅ Connected to PostgreSQL database: vectordb
```

### `initialise_schema(dimension: int = 1536)`

Create database schema with pgvector extension, table, and HNSW index.

**Parameters:**
- `dimension` (int): Vector dimension (default: 1536 for OpenAI, use 1024 for Titan v2)

**Creates:**
1. `vector` extension (if not exists)
2. Table with columns: `id`, `content`, `embedding`, `metadata`, `created_at`
3. HNSW index on `embedding` column with cosine distance

**Example:**

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator

# Get dimension from embedding model
embedder = BedrockEmbeddingGenerator()
dimension = embedder.get_dimension()  # 1024 for Titan v2

# Initialise schema
vector_store.initialise_schema(dimension=dimension)
# Output: ✅ Schema initialised for table: code_embeddings
```

**SQL Generated:**

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table
CREATE TABLE IF NOT EXISTS code_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create HNSW index (cosine distance)
CREATE INDEX IF NOT EXISTS code_embeddings_embedding_idx
ON code_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### `insert_embedding(content: str, embedding: List[float], metadata: Optional[Dict] = None) -> int`

Insert a single embedding into the database.

**Parameters:**
- `content` (str): Text content to store
- `embedding` (List[float]): Vector embedding
- `metadata` (Optional[Dict]): Metadata dictionary (stored as JSONB)

**Returns:**
- `int`: ID of the inserted record

**Example:**

```python
# Insert code chunk
content = """Type: class
Layer: controller
Class: SampleController
Annotations: @RestController, @RequestMapping("/api/hello")

@RestController
@RequestMapping("/api/hello")
public class SampleController {
    @GetMapping
    public String hello() {
        return "Hello World";
    }
}"""

embedding = embedder.generate(content)

metadata = {
    "file_type": "java",
    "layer": "controller",
    "class_name": "SampleController",
    "annotations": ["@RestController", "@RequestMapping"]
}

record_id = vector_store.insert_embedding(content, embedding, metadata)
print(f"✅ Inserted embedding with ID: {record_id}")
# Output: ✅ Inserted embedding with ID: 42
```

### `insert_embeddings_batch(records: List[Tuple[str, List[float], Optional[Dict]]]) -> List[int]`

Insert multiple embeddings in a single batch operation (more efficient).

**Parameters:**
- `records` (List[Tuple]): List of (content, embedding, metadata) tuples

**Returns:**
- `List[int]`: List of inserted record IDs

**Example:**

```python
# Prepare batch records
records = [
    (
        "Type: class\n@RestController\nclass UserController {...}",
        embedder.generate("..."),
        {"file_type": "java", "layer": "controller"}
    ),
    (
        "Type: class\n@Service\nclass UserService {...}",
        embedder.generate("..."),
        {"file_type": "java", "layer": "service"}
    ),
    (
        "Type: class\n@Repository\nclass UserRepository {...}",
        embedder.generate("..."),
        {"file_type": "java", "layer": "repository"}
    )
]

# Batch insert
record_ids = vector_store.insert_embeddings_batch(records)
print(f"✅ Inserted {len(record_ids)} embeddings: {record_ids}")
# Output: ✅ Inserted 3 embeddings: [43, 44, 45]
```

### `similarity_search(query_embedding: List[float], top_k: int = 5, metadata_filter: Optional[Dict] = None, verbose: bool = False) -> List[Dict]`

Perform semantic similarity search using cosine distance.

**Parameters:**
- `query_embedding` (List[float]): Query vector embedding
- `top_k` (int): Number of results to return (default: 5)
- `metadata_filter` (Optional[Dict]): Filter by metadata fields (e.g., `{"layer": "controller"}`)
- `verbose` (bool): Print SQL query and search strategy (default: False)

**Returns:**
- `List[Dict]`: List of results with keys:
  - `id` (int): Record ID
  - `content` (str): Stored content
  - `metadata` (dict): Stored metadata
  - `embedding` (List[float]): Vector embedding
  - `similarity` (float): Cosine similarity score (0.0 to 1.0, higher is better)

**Example 1: Basic Semantic Search**

```python
# Query: "Find REST controllers"
query = "Find REST controllers"
query_embedding = embedder.generate(query)

results = vector_store.similarity_search(
    query_embedding=query_embedding,
    top_k=5
)

for result in results:
    print(f"ID: {result['id']}")
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Metadata: {result['metadata']}\n")
```

**Output:**

```
ID: 42
Similarity: 0.8934
Content: Type: class
Layer: controller
Class: SampleController
Annotations: @RestController...
Metadata: {'file_type': 'java', 'layer': 'controller', 'class_name': 'SampleController'}

ID: 38
Similarity: 0.8621
Content: Type: class
Layer: controller
Class: UserController...
Metadata: {'file_type': 'java', 'layer': 'controller', 'class_name': 'UserController'}
```

**Example 2: Hybrid Search (Semantic + Metadata Filter)**

```python
# Query: "authentication logic" + filter by service layer
query = "authentication logic"
query_embedding = embedder.generate(query)

results = vector_store.similarity_search(
    query_embedding=query_embedding,
    top_k=3,
    metadata_filter={"layer": "service"}  # Only service layer
)

for result in results:
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Class: {result['metadata']['class_name']}")
    print(f"Layer: {result['metadata']['layer']}\n")
```

**Output:**

```
Similarity: 0.9123
Class: AuthenticationService
Layer: service

Similarity: 0.8745
Class: UserService
Layer: service
```

**Example 3: Verbose Mode (Debug SQL)**

```python
results = vector_store.similarity_search(
    query_embedding=query_embedding,
    top_k=5,
    metadata_filter={"layer": "controller"},
    verbose=True  # Show SQL query
)
```

**Output:**

```
======================================================================
🔎 SQL QUERY
======================================================================

                SELECT id, content, metadata, embedding,
                       1 - (embedding <=> %s) as similarity
                FROM code_embeddings
 WHERE metadata->>'layer' = %s ORDER BY embedding <=> %s LIMIT %s

📋 Query Parameters:
  - Vector dimension: 1024
  - Top K: 5
  - Metadata filters: {'layer': 'controller'}

💡 Search Strategy:
  - Semantic Search: Using cosine similarity (embedding <=> vector)
  - Distance Operator: '<=' (cosine distance)
  - Similarity Metric: 1 - cosine_distance (higher = more similar)
  - Lexical Filter: JSONB metadata filtering on ['layer']
======================================================================
```

### `delete_by_id(record_id: int)`

Delete a record by its ID.

**Parameters:**
- `record_id` (int): Record ID to delete

**Returns:** None

**Example:**

```python
vector_store.delete_by_id(42)
print("✅ Record 42 deleted")
```

### `delete_all()`

Delete all records from the table.

**Returns:** None

**Example:**

```python
vector_store.delete_all()
print("✅ All records deleted")
```

### `get_count() -> int`

Get the total number of records in the table.

**Returns:**
- `int`: Number of records

**Example:**

```python
count = vector_store.get_count()
print(f"Total embeddings: {count}")
# Output: Total embeddings: 127
```

### `close()`

Close the database connection.

**Returns:** None

**Example:**

```python
vector_store.close()
# Output: ✅ Database connection closed
```

## Context Manager Support

The class supports Python's context manager protocol (`with` statement):

```python
from core.config import DatabaseConfig
from core.pgvector_store import PgVectorStore

config = DatabaseConfig()

# Automatically connects and closes
with PgVectorStore(config=config, table_name="code_embeddings") as store:
    store.initialise_schema(dimension=1024)

    # Insert data
    store.insert_embedding(content, embedding, metadata)

    # Search
    results = store.similarity_search(query_embedding, top_k=5)

# Connection automatically closed when exiting 'with' block
```

## Complete Usage Example

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig

# 1. Setup
config = DatabaseConfig()
embedder = BedrockEmbeddingGenerator()

# 2. Initialise vector store
with PgVectorStore(config=config, table_name="code_embeddings") as store:
    # 3. Create schema
    dimension = embedder.get_dimension()
    store.initialise_schema(dimension=dimension)

    # 4. Insert code chunks
    code_chunks = [
        {
            "content": "Type: class\n@RestController\nclass UserController {...}",
            "metadata": {"file_type": "java", "layer": "controller"}
        },
        {
            "content": "Type: class\n@Service\nclass UserService {...}",
            "metadata": {"file_type": "java", "layer": "service"}
        }
    ]

    for chunk in code_chunks:
        embedding = embedder.generate(chunk["content"])
        record_id = store.insert_embedding(
            chunk["content"],
            embedding,
            chunk["metadata"]
        )
        print(f"✅ Inserted: {record_id}")

    # 5. Search
    query = "Find user management code"
    query_embedding = embedder.generate(query)

    results = store.similarity_search(
        query_embedding=query_embedding,
        top_k=3
    )

    # 6. Display results
    print(f"\n🔍 Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Similarity: {result['similarity']:.4f}")
        print(f"   Layer: {result['metadata']['layer']}")
        print(f"   Content preview: {result['content'][:80]}...\n")
```

## Distance Metrics

### Cosine Distance (`<=>` operator)

Measures directional similarity (angle between vectors), ignoring magnitude.

**Formula:**
```
cosine_distance = 1 - (A · B) / (||A|| × ||B||)
similarity = 1 - cosine_distance
```

**Why Cosine for Code Search:**
- Code chunks vary in length (short utility vs long controller)
- Semantic meaning matters, not text length
- Bedrock Titan embeddings are normalised (designed for cosine)

**Range:**
- Distance: 0.0 (identical) to 2.0 (opposite)
- Similarity: 0.0 (opposite) to 1.0 (identical)

## HNSW Index Parameters

**Configured in `initialise_schema()`:**

```sql
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
```

**Parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `m` | 16 | Number of bi-directional links per node (higher = better accuracy, more memory) |
| `ef_construction` | 64 | Candidates explored during index build (higher = better quality, slower build) |

**For larger codebases (10k+ chunks):**

```sql
WITH (m = 24, ef_construction = 100)  -- Medium
WITH (m = 32, ef_construction = 128)  -- Large
```

See [pgvector Indexing Strategies](./qna/06_pgvector_indexing.md) for details.

## Metadata Filtering

Metadata is stored as JSONB and can be queried with PostgreSQL's JSON operators:

**Example Filters:**

```python
# Single field
{"layer": "controller"}

# Multiple fields (AND condition)
{"layer": "service", "file_type": "java"}

# Filter by annotation presence (requires custom SQL)
# metadata @> '{"annotations": ["@RestController"]}'
```

**SQL Generated:**

```sql
-- Single filter
WHERE metadata->>'layer' = 'controller'

-- Multiple filters
WHERE metadata->>'layer' = 'service' AND metadata->>'file_type' = 'java'
```

## Performance Considerations

### Batch Insertion

Use `insert_embeddings_batch()` for multiple embeddings:

```python
# ❌ Slow: Individual inserts
for chunk in chunks:
    store.insert_embedding(chunk["content"], chunk["embedding"], chunk["metadata"])

# ✅ Fast: Batch insert
records = [(c["content"], c["embedding"], c["metadata"]) for c in chunks]
store.insert_embeddings_batch(records)
```

## Error Handling

```python
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig

config = DatabaseConfig()
store = PgVectorStore(config=config)

try:
    store.connect()
    store.initialise_schema(dimension=1024)
except Exception as e:
    print(f"❌ Error: {e}")
    # Handle connection or schema errors
```

**Common Errors:**

1. **Extension Not Installed:**
   ```
   psycopg2.errors.UndefinedFile: could not open extension control file
   ```
   **Solution:** Install pgvector: `CREATE EXTENSION vector;`

2. **Dimension Mismatch:**
   ```
   psycopg2.errors.DatatypeMismatch: expected 1024 dimensions, got 1536
   ```
   **Solution:** Match `initialise_schema(dimension=...)` with embedding model dimension

3. **Table Exists:**
   - `CREATE TABLE IF NOT EXISTS` prevents errors on re-run
   - Schema is idempotent (safe to run multiple times)

## Best Practices

1. **Use Context Manager:** Ensures connection is closed properly
2. **Batch Insertion:** Use `insert_embeddings_batch()` for efficiency
3. **Match Dimensions:** Ensure schema dimension matches embedding model
4. **Index Before Bulk Load:** Create index AFTER inserting large datasets (faster)
5. **Metadata Design:** Store searchable fields in metadata (layer, file_type, etc.)
6. **Verbose Mode:** Use `verbose=True` during development to debug queries

## Related Documentation

- [Database Configuration](./CONFIG.md) - PostgreSQL connection setup
- [Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md) - Generating embeddings
- [pgvector Indexing](./qna/06_pgvector_indexing.md) - HNSW vs IVFFlat
- [Metadata in Embeddings](./qna/04_metadata_in_embeddings.md) - What to include

---

**Module Location:** `core/pgvector_store.py`
**Dependencies:** `psycopg2`, `pgvector`, `numpy`
**PostgreSQL Extension Required:** `pgvector`

---

**Last Updated**: 2025-10-16
