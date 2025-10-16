# Amazon S3 Vector Store Module

**Module:** `rag/core/s3_vector_store.py`

[← Back to Documentation Index](./README.md)

---

## Overview

The `S3VectorStore` class provides a vector database implementation using Amazon S3 Vectors. It offers an alternative to PostgreSQL/pgvector for storing and searching code embeddings, with the benefits of S3's scalability and serverless architecture.

## Features

- ✅ Amazon S3 Vectors integration
- ✅ PutVectors API for insertion (single and batch)
- ✅ QueryVectors API for similarity search
- ✅ Cosine and Euclidean distance metrics
- ✅ Metadata storage and filtering
- ✅ Batch insertion support
- ✅ Context manager support (with statement)
- ✅ Automatic AWS credential management
- ✅ Serverless architecture (no database to manage)

## Documentation Reference

- [S3 Vectors Getting Started Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-getting-started.html)

## Class: `S3VectorStore`

### Initialisation

```python
from core.s3_vector_store import S3VectorStore

# Using environment variables (recommended)
vector_store = S3VectorStore(
    bucket_name="my-vector-bucket",
    index_name="code_embeddings"
)

# With explicit AWS credentials
vector_store = S3VectorStore(
    bucket_name="my-vector-bucket",
    index_name="code_embeddings",
    region="ap-southeast-2",
    aws_access_key_id="your-key",
    aws_secret_access_key="your-secret"
)

# Connect and initialise
vector_store.connect()
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket_name` | `str` | *Required* | S3 bucket name for vector storage |
| `index_name` | `str` | `"code_embeddings"` | Name of the vector index |
| `region` | `str` | `"ap-southeast-2"` | AWS region (from `AWS_REGION` env var) |
| `aws_access_key_id` | `str` | `None` | AWS access key (from `AWS_ACCESS_KEY_ID` env var) |
| `aws_secret_access_key` | `str` | `None` | AWS secret key (from `AWS_SECRET_ACCESS_KEY` env var) |
| `aws_session_token` | `str` | `None` | AWS session token (from `AWS_SESSION_TOKEN` env var) |

## Methods

### `connect()`

Verify S3 bucket access and create bucket if it doesn't exist.

**Returns:** None

**Behaviour:**
- If bucket exists: Verifies access and connects
- If bucket doesn't exist: Automatically creates it in the configured region
- If access denied: Raises error with permission guidance

**Example:**

```python
vector_store = S3VectorStore(bucket_name="my-vector-bucket")
vector_store.connect()
```

**Output (Bucket Exists):**
```
✅ Connected to S3 bucket: my-vector-bucket
```

**Output (Bucket Created):**
```
⚠️  Bucket my-vector-bucket doesn't exist. Creating...
✅ Created S3 bucket: my-vector-bucket in region ap-southeast-2
```

**Errors:**
```python
# If access denied (403)
# Output: ❌ Access denied to bucket my-vector-bucket. Check IAM permissions.

# If bucket creation fails
# Output: ❌ Failed to create S3 bucket: <error details>
```

**IAM Permissions Required:**
- `s3:HeadBucket` - Check if bucket exists
- `s3:CreateBucket` - Create bucket if it doesn't exist
- `s3:ListBucket` - List bucket contents

### `initialise_schema(dimension: int = 1536, distance_metric: str = "cosine")`

Configure vector index parameters.

**Parameters:**
- `dimension` (int): Vector dimension (default: 1536, use 1024 for Titan v2)
- `distance_metric` (str): Distance metric - "cosine" or "euclidean" (default: "cosine")

**Returns:** None

**Note:** S3 Vectors creates indexes automatically on first vector insertion.

**Example:**

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator

# Get dimension from embedding model
embedder = BedrockEmbeddingGenerator()
dimension = embedder.get_dimension()  # 1024 for Titan v2

# Initialise schema
vector_store.initialise_schema(dimension=dimension, distance_metric="cosine")
```

**Output:**
```
✅ S3 Vector index configured: code_embeddings
   Dimension: 1024
   Distance metric: cosine
   Index will be created on first vector insertion
```

### `insert_embedding(content: str, embedding: List[float], metadata: Optional[Dict] = None) -> str`

Insert a single embedding into S3 Vectors using the PutVectors API.

**Parameters:**
- `content` (str): Text content (stored in metadata)
- `embedding` (List[float]): Vector embedding
- `metadata` (Optional[Dict]): Metadata dictionary

**Returns:**
- `str`: Vector key (unique identifier)

**API Used:** `put_vectors(vectorBucketName, indexName, vectors)`

**Example:**

```python
# Insert code chunk
content = """Type: class
Layer: controller
Class: SampleController
Annotations: @RestController

@RestController
public class SampleController {
    @GetMapping
    public String hello() {
        return "Hello";
    }
}"""

embedding = embedder.generate(content)

metadata = {
    "chunk_id": "sample-controller-001",
    "file_type": "java",
    "layer": "controller",
    "class_name": "SampleController"
}

vector_key = vector_store.insert_embedding(content, embedding, metadata)
print(f"✅ Inserted with key: {vector_key}")
# Output: ✅ Inserted with key: sample-controller-001
```

**Vector Data Structure:**
```python
{
    "key": "sample-controller-001",
    "data": {"float32": [0.1, 0.2, 0.3, ...]},  # 1024-dim embedding
    "metadata": {
        "chunk_id": "sample-controller-001",
        "file_type": "java",
        "layer": "controller",
        "class_name": "SampleController",
        "content": "Type: class\n..."
    }
}
```

**Key Generation:**
- If `chunk_id` is in metadata, it's used as the vector key
- Otherwise, a UUID is generated automatically

### `insert_embeddings_batch(records: List[Tuple[str, List[float], Optional[Dict]]]) -> List[str]`

Insert multiple embeddings in a single batch operation using the PutVectors API.

**Parameters:**
- `records` (List[Tuple]): List of (content, embedding, metadata) tuples

**Returns:**
- `List[str]`: List of vector keys

**API Used:** `put_vectors(vectorBucketName, indexName, vectors=[...])`

**Example:**

```python
# Prepare batch records
records = [
    (
        "Type: class\n@RestController\nclass UserController {...}",
        embedder.generate("..."),
        {"chunk_id": "user-controller-001", "layer": "controller"}
    ),
    (
        "Type: class\n@Service\nclass UserService {...}",
        embedder.generate("..."),
        {"chunk_id": "user-service-001", "layer": "service"}
    )
]

# Batch insert (single API call)
vector_keys = vector_store.insert_embeddings_batch(records)
print(f"✅ Inserted {len(vector_keys)} vectors")
# Output: ✅ Inserted 2 vectors
```

**Performance:**
- Batch insertion uses a single PutVectors API call
- More efficient than multiple individual inserts
- Recommended for large datasets

### `similarity_search(query_embedding: List[float], top_k: int = 5, metadata_filter: Optional[Dict] = None, verbose: bool = False) -> List[Dict]`

Perform semantic similarity search using S3 Vectors QueryVectors API.

**Parameters:**
- `query_embedding` (List[float]): Query vector embedding
- `top_k` (int): Number of results to return (default: 5)
- `metadata_filter` (Optional[Dict]): Filter by metadata fields (e.g., `{"layer": "controller"}`)
- `verbose` (bool): Print query details (default: False)

**Returns:**
- `List[Dict]`: List of results with keys:
  - `id` (str): Vector key
  - `content` (str): Stored content
  - `metadata` (dict): Stored metadata
  - `embedding` (List[float]): Vector embedding
  - `similarity` (float): Similarity score

**API Used:** `query_vectors(vectorBucketName, indexName, queryVector, topK, filter)`

**Example:**

```python
# Query: "Find REST controllers"
query = "Find REST controllers"
query_embedding = embedder.generate(query)

# Search with metadata filter
results = vector_store.similarity_search(
    query_embedding=query_embedding,
    top_k=5,
    metadata_filter={"layer": "controller"},
    verbose=True
)

# Process results
for result in results:
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Class: {result['metadata']['class_name']}")
    print(f"Content: {result['content'][:100]}...\n")
```

**Output:**

```
======================================================================
🔎 S3 VECTOR SEARCH
======================================================================
  - Index: code_embeddings
  - Top K: 5
  - Distance metric: cosine
  - Metadata filters: {'layer': 'controller'}
======================================================================

Similarity: 0.8934
Class: SampleController
Content: Type: class
Layer: controller
Class: SampleController...

Similarity: 0.8621
Class: UserController
Content: Type: class
Layer: controller
Class: UserController...
```

### `delete_by_key(vector_key: str)`

Delete a vector by its key.

**Parameters:**
- `vector_key` (str): Vector key to delete

**Returns:** None

**Example:**

```python
vector_store.delete_by_key("sample-controller-001")
# Output: ✅ Deleted vector: sample-controller-001
```

### `delete_all()`

Delete all vectors from the index.

**Returns:** None

**Warning:** This deletes all objects with the index prefix!

**Example:**

```python
vector_store.delete_all()
# Output: ✅ Deleted 127 vectors from index: code_embeddings
```

### `get_count() -> int`

Get the total number of vectors in the index.

**Returns:**
- `int`: Number of vectors

**Example:**

```python
count = vector_store.get_count()
print(f"Total vectors: {count}")
# Output: Total vectors: 127
```

### `close()`

Close the vector store.

**Returns:** None

**Example:**

```python
vector_store.close()
# Output: ✅ S3 Vector Store closed
```

## Environment Variables

Create a `.env` file in your project root:

```bash
# .env

# AWS Configuration (same as Bedrock)
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_SESSION_TOKEN=your-session-token  # Optional
```

## Complete Usage Example

```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.s3_vector_store import S3VectorStore

# 1. Setup
embedder = BedrockEmbeddingGenerator()
bucket_name = "my-code-vectors"

# 2. Initialise S3 vector store (bucket auto-created if needed)
with S3VectorStore(bucket_name=bucket_name, index_name="code_embeddings") as store:
    # 3. Configure schema
    dimension = embedder.get_dimension()
    store.initialise_schema(dimension=dimension, distance_metric="cosine")

    # 4. Insert code chunks
    code_chunks = [
        {
            "content": "Type: class\n@RestController\nclass UserController {...}",
            "metadata": {"chunk_id": "uc-001", "file_type": "java", "layer": "controller"}
        },
        {
            "content": "Type: class\n@Service\nclass UserService {...}",
            "metadata": {"chunk_id": "us-001", "file_type": "java", "layer": "service"}
        }
    ]

    for chunk in code_chunks:
        embedding = embedder.generate(chunk["content"])
        vector_key = store.insert_embedding(
            chunk["content"],
            embedding,
            chunk["metadata"]
        )
        print(f"✅ Inserted: {vector_key}")

    # 5. Check count
    total = store.get_count()
    print(f"\n📦 Total vectors stored: {total}")
```

**Output (Bucket Auto-Created):**
```
⚠️  Bucket my-code-vectors doesn't exist. Creating...
✅ Created S3 bucket: my-code-vectors in region ap-southeast-2
✅ S3 Vector index configured: code_embeddings
   Dimension: 1024
   Distance metric: cosine
✅ Inserted: uc-001
✅ Inserted: us-001

📦 Total vectors stored: 2
✅ S3 Vector Store closed
```

**Output (Bucket Already Exists):**
```
✅ Connected to S3 bucket: my-code-vectors
✅ S3 Vector index configured: code_embeddings
   Dimension: 1024
   Distance metric: cosine
✅ Inserted: uc-001
✅ Inserted: us-001

📦 Total vectors stored: 2
✅ S3 Vector Store closed
```

## Using with vectorise_and_store.py Script

```bash
# Vectorise and store in S3 Vectors
python rag/scripts/vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store s3 \
    --s3-bucket my-code-vectors \
    --table-name code_embeddings \
    --batch-size 25 \
    --clear
```

**Arguments:**
- `--vector-store s3`: Use S3 Vectors instead of pgvector
- `--s3-bucket`: S3 bucket name (required for S3)
- `--table-name`: Index name (default: code_embeddings)
- `--clear`: Delete existing vectors before inserting

## S3 Bucket Setup

### Automatic Bucket Creation

The S3VectorStore automatically creates the bucket if it doesn't exist when you call `connect()`. No manual setup required!

```python
# Bucket will be created automatically if it doesn't exist
vector_store = S3VectorStore(bucket_name="my-code-vectors", region="ap-southeast-2")
vector_store.connect()
# Output: ✅ Created S3 bucket: my-code-vectors in region ap-southeast-2
```

### Manual Bucket Creation (Optional)

If you prefer to create the bucket manually:

```bash
# Using AWS CLI
aws s3 mb s3://my-code-vectors --region ap-southeast-2

# Verify bucket exists
aws s3 ls s3://my-code-vectors
```

### Required IAM Permissions

Ensure your IAM user/role has these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:HeadBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-code-vectors",
                "arn:aws:s3:::my-code-vectors/*"
            ]
        }
    ]
}
```

**Key Permissions:**
- `s3:CreateBucket` - Required for automatic bucket creation
- `s3:HeadBucket` - Check if bucket exists
- `s3:PutObject` - Insert vectors
- `s3:GetObject` - Retrieve vectors for search
- `s3:DeleteObject` - Delete vectors
- `s3:ListBucket` - Count vectors and list operations

## Distance Metrics

### Cosine Distance (Recommended for Code)

Measures directional similarity (angle between vectors).

**Use Cases:**
- Code embeddings (varying lengths)
- Semantic similarity
- Text search

**Formula:**
```
cosine_similarity = (A · B) / (||A|| × ||B||)
```

### Euclidean Distance

Measures straight-line distance.

**Use Cases:**
- Image embeddings
- Magnitude-sensitive comparisons

**Formula:**
```
euclidean_distance = sqrt((A[0]-B[0])² + (A[1]-B[1])² + ...)
```

## Comparison: S3 Vectors vs pgvector

| Aspect | S3 Vectors | pgvector |
|--------|-----------|----------|
| **Infrastructure** | Serverless (no DB to manage) | Requires PostgreSQL server |
| **Scalability** | Unlimited (S3 scalability) | Limited by DB instance |
| **Cost** | Pay per request + storage | Fixed DB instance cost |
| **Query Speed** | Good (serverless latency) | Very fast with HNSW |
| **Setup** | Simple (just S3 bucket) | Requires PostgreSQL + pgvector extension |
| **Maturity** | Production-ready | Production-ready |
| **Search API** | QueryVectors (boto3) | SQL-based (mature) |
| **Indexing** | Automatic | Manual (HNSW/IVFFlat) |
| **Metadata** | Flexible (dict values) | JSONB (rich querying) |
| **Batch Operations** | Native PutVectors API | execute_values() |

## When to Use S3 Vectors

✅ **Use S3 Vectors when:**
- You want serverless architecture
- You need unlimited scalability
- You prefer pay-per-request pricing
- You're already using AWS ecosystem
- You want simple setup (no DB management, bucket auto-created)
- You want zero infrastructure maintenance

❌ **Use pgvector when:**
- You need production-ready solution now
- You require advanced metadata querying (JSONB)
- You want proven performance (HNSW indexing)
- You need complex filtering
- Sub-10ms query latency is critical

## Metadata Limitations

**S3 Vectors:**
- Metadata values must be strings
- Nested objects converted to strings
- Filtering capabilities limited (preview)

**Example:**

```python
# Metadata is converted to strings
metadata = {
    "chunk_id": "uc-001",
    "layer": "controller",  # Stored as "controller"
    "line_start": 10,       # Stored as "10" (string)
    "annotations": ["@RestController", "@RequestMapping"]  # Stored as string repr
}
```

## Performance Considerations

### Batch Insertion

Currently, `insert_embeddings_batch()` inserts vectors sequentially. This can be optimised when S3 Vectors batch API is available.

**Current Speed:**
- 100 vectors: ~10-20 seconds
- 1000 vectors: ~2-3 minutes

### Storage Costs

S3 Vectors pricing (subject to change):
- Storage: ~$0.023 per GB/month
- PUT requests: ~$0.005 per 1000 requests
- GET requests: ~$0.0004 per 1000 requests

**Example for 10,000 code chunks:**
- Vector size: 1024 floats × 4 bytes = 4KB per vector
- Total storage: 10,000 × 4KB = 40MB
- Monthly cost: 40MB × $0.023/GB ≈ $0.001/month (negligible)

## Error Handling

```python
from core.s3_vector_store import S3VectorStore

vector_store = S3VectorStore(bucket_name="my-bucket")

try:
    vector_store.connect()
    vector_store.initialise_schema(dimension=1024)
    # ... insert operations ...
except Exception as e:
    print(f"❌ Error: {e}")
```

**Common Errors:**

1. **Access Denied (Bucket Creation):**
   ```
   ❌ Access denied to bucket my-code-vectors. Check IAM permissions.
   ```
   **Solution:** Add `s3:CreateBucket` permission to your IAM policy

2. **Access Denied (Operations):**
   ```
   ❌ Failed to insert vector: An error occurred (AccessDenied)
   ```
   **Solution:** Check IAM permissions for S3 operations (PutObject, GetObject, etc.)

3. **Dimension Mismatch:**
   ```
   ValueError: Embedding dimension mismatch: expected 1024, got 1536
   ```
   **Solution:** Match schema dimension with embedding model

4. **Invalid Bucket Name:**
   ```
   ❌ Failed to create S3 bucket: An error occurred (InvalidBucketName)
   ```
   **Solution:** Bucket names must be 3-63 characters, lowercase, no underscores

## Best Practices

1. **Use chunk_id:** Always provide `chunk_id` in metadata for deterministic keys
2. **Batch Operations:** Use `insert_embeddings_batch()` for efficiency (single API call)
3. **Cost Optimisation:** Use S3 lifecycle policies to archive old vectors
4. **Monitoring:** Enable S3 request metrics to track API usage and costs
5. **Error Handling:** Wrap API calls in try-except blocks for resilience
6. **Metadata Design:** Store searchable fields in metadata for filtering

## API Methods Summary

| Method | API Used | Purpose |
|--------|----------|---------|
| `insert_embedding()` | `put_vectors()` | Insert single vector |
| `insert_embeddings_batch()` | `put_vectors()` | Insert multiple vectors (batch) |
| `similarity_search()` | `query_vectors()` | Semantic similarity search |
| `delete_by_key()` | `delete_vectors()` | Delete vector by key |
| `delete_all()` | S3 `delete_objects()` | Delete all vectors |
| `get_count()` | S3 `list_objects_v2()` | Count vectors |

## Related Documentation

- [Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md) - Generating embeddings
- [pgvector Store](./PGVECTOR_STORE.md) - Alternative vector store
- [AWS S3 Vectors Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-getting-started.html)

---

**Module Location:** `rag/core/s3_vector_store.py`
**Dependencies:** `boto3`, `python-dotenv`
**AWS Service:** Amazon S3 Vectors
**Status:** Production-ready
