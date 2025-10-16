# S3 Vectors Metadata Limitations

**Question**: What are the metadata limitations in Amazon S3 Vectors, and how do we handle them?

---

## Quick Answer

Amazon S3 Vectors has strict metadata constraints:

1. **Maximum 10 metadata keys** per vector
2. **Filterable metadata limited to 2048 bytes** total
3. **Non-filterable metadata** can be larger but cannot be used in queries

These limitations require careful metadata design to balance searchability with content storage.

---

## The Two Key Limitations

### 1. Maximum 10 Metadata Keys

**Error Message:**
```
ValidationException: Invalid record for key 'xxx': Metadata object must have at most 10 keys
```

**Cause:**
- Each vector can only have up to 10 metadata keys
- This includes both filterable and non-filterable keys
- Content stored as metadata counts toward this limit

**Solution:**
- Prioritise essential fields for filtering
- Store only the most important metadata
- Example priority order:
  1. `content` (the actual text)
  2. `chunk_id` (unique identifier)
  3. `file_path` (source file)
  4. `layer` (architectural layer)
  5. `type` (code element type)
  6. `class_name` (class identifier)
  7. `module` (module/package)
  8. `package` (package name)
  9. `file_type` (file extension)
  10. `line_start` (starting line number)

---

### 2. Filterable Metadata Size Limit (2048 Bytes)

**Error Message:**
```
ValidationException: Invalid record for key 'xxx': Filterable metadata must have at most 2048 bytes
```

**Cause:**
- Filterable metadata (fields you can query on) has a 2048-byte limit
- Large content fields exceed this limit
- File paths and other text fields contribute to the byte count

**Solution:**
- Mark large fields as **non-filterable** using `nonFilterableMetadataKeys`
- Non-filterable fields don't count toward the 2048-byte limit
- Non-filterable fields are returned in search results but cannot be used in filters

---

## Implementation Example

### Creating Index with Non-Filterable Keys

```python
from core.s3_vector_store import S3VectorStore

# Initialise S3 vector store
store = S3VectorStore(
    bucket_name='my-code-vectors',
    index_name='code-embeddings'
)

store.connect()

# Create index with 'content' as non-filterable
# This is done automatically in initialise_schema()
store.initialise_schema(
    dimension=1024,  # Titan v2 dimension
    distance_metric='cosine'
)
```

**Behind the scenes:**
```python
vectors_client.create_index(
    vectorBucketName='my-code-vectors',
    indexName='code-embeddings',
    dataType='float32',
    dimension=1024,
    distanceMetric='cosine',
    metadataConfiguration={
        'nonFilterableMetadataKeys': ['content']  # Content won't count toward 2048-byte limit
    }
)
```

---

### Metadata Selection Strategy

Our implementation prioritises metadata fields:

```python
# Prepare metadata - S3 Vectors has a 10-key limit
vector_metadata = {
    "content": content,        # Non-filterable (large)
    "chunk_id": vector_key     # Filterable (small)
}

# Add essential filterable fields (max 10 total keys)
essential_fields = [
    "file_path",    # Source file location
    "layer",        # Architectural layer (controller, service, etc.)
    "type",         # Code element type (class, method, etc.)
    "class_name",   # Class identifier
    "module",       # Module/package name
    "package",      # Package identifier
    "file_type",    # File extension
    "line_start"    # Starting line number
]

for field in essential_fields:
    if field in metadata and len(vector_metadata) < 10:
        vector_metadata[field] = metadata[field]
```

---

## What Can You Filter On?

### Filterable Fields (Can Use in Queries)

These fields are **small enough** and **marked as filterable**:

- `chunk_id` - Unique identifier
- `file_path` - Source file path
- `layer` - Architectural layer (e.g., "controller", "service")
- `type` - Code element type (e.g., "class", "method")
- `class_name` - Class name
- `module` - Module/package name
- `package` - Package identifier
- `file_type` - File extension (e.g., "java", "py")
- `line_start` - Starting line number

### Non-Filterable Fields (Returned But Not Queryable)

- `content` - The actual code/text (too large for filtering)

**Example Query with Filter:**
```python
results = store.similarity_search(
    query_embedding=embedding,
    top_k=5,
    metadata_filter={
        "layer": "controller",
        "type": "class"
    }
)
```

---

## Troubleshooting

### Error: "Metadata object must have at most 10 keys"

**Problem**: Too many metadata fields

**Solutions**:
1. Review which fields are essential
2. Remove less important fields from metadata
3. Consider combining related fields (e.g., `file_path` includes directory info)

---

### Error: "Filterable metadata must have at most 2048 bytes"

**Problem**: Filterable metadata too large (usually due to `content` field)

**Solutions**:
1. **Delete and recreate index** with proper configuration:
   ```bash
   python scripts/delete_index.py
   ./scripts/vectorise_s3.sh dini-code-vectors
   ```

2. Mark large fields as non-filterable in index configuration
3. Reduce content size if needed (though content should be non-filterable)

**Important**: Once an index is created, you **cannot change** its metadata configuration. You must delete and recreate it.

---

## Comparison: S3 Vectors vs pgvector

| Feature | S3 Vectors | pgvector |
|---------|-----------|----------|
| **Metadata Keys** | Max 10 | Unlimited |
| **Filterable Size** | 2048 bytes | Unlimited |
| **Non-Filterable** | Supported | N/A (all filterable) |
| **Schema Changes** | Requires index recreation | Flexible with ALTER TABLE |
| **Best For** | Simple metadata, large scale | Rich metadata, complex queries |

---

## Best Practices

### 1. Plan Metadata Fields Upfront
- S3 Vectors requires index deletion to change metadata configuration
- Choose your 10 fields carefully
- Prioritise fields you'll actually filter on

### 2. Mark Large Fields as Non-Filterable
- `content` should always be non-filterable
- Any field > 200 bytes should be non-filterable
- Non-filterable fields are still returned in results

### 3. Use Concise Field Values
- Keep file paths relative, not absolute
- Use short enums for `layer` ("ctrl" vs "controller")
- Use abbreviations where appropriate

### 4. Test with Sample Data First
- Calculate metadata size: `len(json.dumps(metadata).encode('utf-8'))`
- Ensure total filterable metadata < 2048 bytes
- Verify you're using ≤ 10 keys

---

## Code Example: Checking Metadata Size

```python
import json

def check_metadata_size(metadata: dict, non_filterable_keys: list):
    """Check if metadata fits S3 Vectors limits"""

    # Check key count
    key_count = len(metadata)
    if key_count > 10:
        print(f"❌ Too many keys: {key_count} (max 10)")
        return False

    # Check filterable metadata size
    filterable_metadata = {
        k: v for k, v in metadata.items()
        if k not in non_filterable_keys
    }

    filterable_size = len(json.dumps(filterable_metadata).encode('utf-8'))
    if filterable_size > 2048:
        print(f"❌ Filterable metadata too large: {filterable_size} bytes (max 2048)")
        return False

    print(f"✅ Metadata valid: {key_count} keys, {filterable_size} filterable bytes")
    return True

# Example usage
metadata = {
    "content": "class MyController { ... }",  # Non-filterable
    "chunk_id": "01_app_controller_0",
    "file_path": "src/main/java/com/example/MyController.java",
    "layer": "controller",
    "type": "class",
    "class_name": "MyController"
}

check_metadata_size(metadata, non_filterable_keys=['content'])
```

---

## Related Documentation

- [S3 Vector Store Module](../S3_VECTOR_STORE.md)
- [Metadata vs Content](./02_metadata_role.md)
- [Metadata Fields Reference](../METADATA_FIELDS.md)

---

**Last Updated**: 2025-10-16
