# Bedrock Embeddings Module

**Module:** `core/bedrock_embeddings.py`

[← Back to Documentation Index](./README.md)

---

## Overview

The `BedrockEmbeddingGenerator` class provides a Python interface for generating text embeddings using Amazon Bedrock's Titan embedding models. It handles AWS authentication, API calls, and batch processing of text inputs.

## Features

- ✅ Support for multiple Titan embedding models
- ✅ Batch processing with configurable batch sizes
- ✅ Normalised embeddings for cosine similarity
- ✅ Error handling with fallback strategies
- ✅ Multiple model dimension support

## Class: `BedrockEmbeddingGenerator`

### Initialisation

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator

# Using environment variables (recommended)
embedder = BedrockEmbeddingGenerator()

# With explicit configuration
embedder = BedrockEmbeddingGenerator(
    model_id="amazon.titan-embed-text-v2:0",
    region="ap-southeast-2",
)
```

## Methods

### `generate(text: str, normalize: bool = True) -> List[float]`

Generate an embedding vector for a single text input.

**Parameters:**
- `text` (str): Input text to embed
- `normalize` (bool): Whether to normalise the embedding vector (default: `True`)

**Returns:**
- `List[float]`: Embedding vector (1024-dimensional for Titan v2)

**Example:**

```python
embedder = BedrockEmbeddingGenerator()

# Generate embedding for a code snippet
code = "@RestController\npublic class SampleController { ... }"
embedding = embedder.generate(code)

print(f"Embedding dimension: {len(embedding)}")
# Output: Embedding dimension: 1024

print(f"First 5 values: {embedding[:5]}")
# Output: First 5 values: [-0.097, 0.009, 0.025, -0.050, 0.034]
```

### `generate_batch(texts: List[str], normalize: bool = True, batch_size: int = 25) -> List[List[float]]`

Generate embeddings for multiple texts in batches.

**Parameters:**
- `texts` (List[str]): List of input texts to embed
- `normalize` (bool): Whether to normalise embeddings (default: `True`)
- `batch_size` (int): Number of texts to process at once (default: `25`)

**Returns:**
- `List[List[float]]`: List of embedding vectors

**Example:**

```python
embedder = BedrockEmbeddingGenerator()

# Batch generate embeddings
texts = [
    "Type: class\n@RestController\npublic class SampleController {...}",
    "Type: class\n@Service\npublic class SampleService {...}",
    "Type: class\n@Repository\npublic class SampleRepository {...}"
]

embeddings = embedder.generate_batch(texts, batch_size=25)

print(f"Generated {len(embeddings)} embeddings")
# Output: Generated 3 embeddings

for i, emb in enumerate(embeddings):
    print(f"Text {i+1}: dimension={len(emb)}, first value={emb[0]:.4f}")
```

**Error Handling:**

If embedding generation fails for a text, a zero vector is returned as fallback:

```python
# If an error occurs
# Output: ❌ Failed to generate embedding for text (index 5): Connection timeout
# Returns: [0.0, 0.0, 0.0, ..., 0.0]  (1024 zeros)
```

### `get_dimension() -> int`

Get the embedding dimension for the current model.

**Returns:**
- `int`: Embedding dimension

**Supported Models:**

| Model ID | Dimension |
|----------|-----------|
| `amazon.titan-embed-text-v1` | 1536 |
| `amazon.titan-embed-text-v2:0` | 1024 |
| `amazon.titan-embed-image-v1` | 1024 |

**Example:**

```python
embedder = BedrockEmbeddingGenerator(model_id="amazon.titan-embed-text-v2:0")
dim = embedder.get_dimension()

print(f"Model dimension: {dim}")
# Output: Model dimension: 1024
```

## Complete Usage Example

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from pathlib import Path

# Initialise embedder
embedder = BedrockEmbeddingGenerator(
    model_id="amazon.titan-embed-text-v2:0",
    region="ap-southeast-2"
)

# Single text embedding
text = "How do I create a REST controller in Spring Boot?"
query_embedding = embedder.generate(text)

print(f"Query embedding dimension: {len(query_embedding)}")
print(f"Query embedding sample: {query_embedding[:5]}")

# Batch embeddings for code chunks
code_chunks = [
    "Type: class\nLayer: controller\n@RestController\npublic class UserController {...}",
    "Type: class\nLayer: service\n@Service\npublic class UserService {...}",
    "Type: class\nLayer: repository\n@Repository\npublic class UserRepository {...}"
]

embeddings = embedder.generate_batch(code_chunks, batch_size=10)

print(f"\nGenerated {len(embeddings)} embeddings")
for i, emb in enumerate(embeddings):
    print(f"Chunk {i+1}: {len(emb)}-dimensional vector")

# Get model dimension
dimension = embedder.get_dimension()
print(f"\nModel embedding dimension: {dimension}")
```

**Output:**

```
Query embedding dimension: 1024
Query embedding sample: [-0.079, -0.009, 0.016, -0.017, 0.012]

Generated 3 embeddings
Chunk 1: 1024-dimensional vector
Chunk 2: 1024-dimensional vector
Chunk 3: 1024-dimensional vector

Model embedding dimension: 1024
```

## Integration with Vector Store

Typically used with `PgVectorStore` for storing and searching embeddings:

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig

# Setup
embedder = BedrockEmbeddingGenerator()
db_config = DatabaseConfig()
vector_store = PgVectorStore(config=db_config, table_name="code_embeddings")
vector_store.connect()
vector_store.initialise_schema(dimension=embedder.get_dimension())

# Vectorise and store
content = "Type: class\n@RestController\npublic class HelloController {...}"
embedding = embedder.generate(content)
metadata = {"file_type": "java", "layer": "controller"}

record_id = vector_store.insert_embedding(content, embedding, metadata)
print(f"Stored embedding with ID: {record_id}")

# Search
query = "Show me REST controller examples"
query_embedding = embedder.generate(query)
results = vector_store.similarity_search(query_embedding, top_k=5)

for result in results:
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Content: {result['content'][:100]}...")
```

## Error Handling

The module handles common errors gracefully:

```python
try:
    embedding = embedder.generate("Some text")
except Exception as e:
    print(f"Error: {e}")
    # Handle error (retry, log, etc.)
```

## Performance Considerations

### Batch Size

- **Default:** 25 texts per batch
- **Recommended:** 10-50 for most use cases
- **Large datasets:** Use smaller batches (10-25) to avoid rate limits

```python
# For large datasets
embeddings = embedder.generate_batch(
    texts=large_text_list,
    batch_size=10  # Smaller batch to avoid throttling
)
```

### Normalisation

- **Default:** `normalize=True` (recommended for cosine similarity)
- Normalised vectors have unit length (magnitude = 1.0)
- Essential for accurate cosine similarity calculations

## Best Practices

1. **Batch Processing:** Use `generate_batch()` for multiple texts (more efficient)
2. **Normalisation:** Keep `normalize=True` for vector search use cases
3. **Model Selection:** Use `amazon.titan-embed-text-v2:0` for code embeddings (1024-dim, faster)

## Related Documentation

- [Database Configuration](./CONFIG.md) - PostgreSQL connection setup
- [Vector Store](./PGVECTOR_STORE.md) - Storing and searching embeddings
- [Metadata Fields](./METADATA_FIELDS.md) - Metadata schema for code chunks

---

**Module Location:** `core/bedrock_embeddings.py`
**Dependencies:** `boto3`, `python-dotenv`

---

**Last Updated**: 2025-10-16