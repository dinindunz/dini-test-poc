# Claude Code Session Logs

**Purpose:** Track all modifications, decisions, and context from Claude Code sessions to enable seamless continuation if session is lost.

**Last Updated:** 2025-10-15

---

## Session 2: S3 Vector Store Implementation (2025-10-15)

### Tasks Completed

#### 1. Created S3 Vector Store Module
**Goal:** Implement Amazon S3 Vectors as an alternative to pgvector

**Files Created:**
- `rag/core/s3_vector_store.py` (365 lines)

**Implementation Details:**
- `S3VectorStore` class with full API implementation
- Methods implemented:
  - `connect()` - Verify S3 bucket access
  - `initialise_schema(dimension, distance_metric)` - Configure vector index
  - `insert_embedding(content, embedding, metadata)` - Insert single vector using `put_vectors()` API
  - `insert_embeddings_batch(records)` - Batch insert using `put_vectors()` API
  - `similarity_search(query_embedding, top_k, metadata_filter, verbose)` - Search using `query_vectors()` API
  - `delete_by_key(vector_key)` - Delete vector by key
  - `delete_all()` - Delete all vectors in index
  - `get_count()` - Count vectors in index
  - Context manager support (`with` statement)

**Key Features:**
- PutVectors API for insertion (single and batch)
- QueryVectors API for similarity search with metadata filtering
- Cosine and Euclidean distance metrics
- Automatic AWS credential management from environment
- Serverless architecture (no database to manage)

**Vector Data Structure:**
```python
{
    "key": "chunk-id",
    "data": {"float32": [0.1, 0.2, ...]},  # 1024-dim embedding
    "metadata": {
        "chunk_id": "...",
        "file_type": "java",
        "layer": "controller",
        "content": "..."
    }
}
```

#### 2. Updated vectorise_and_store.py Script
**Goal:** Add support for choosing between pgvector and S3 vectors

**Files Modified:**
- `rag/scripts/vectorise_and_store.py`

**Changes:**
- Imported `S3VectorStore` module
- Updated `vectorise_and_store()` function signature:
  - Added `vector_store_type` parameter ("pgvector" or "s3")
  - Added `s3_bucket_name` parameter
- Added vector store selection logic with if/else:
  ```python
  if vector_store_type == "pgvector":
      vector_store = PgVectorStore(...)
  elif vector_store_type == "s3":
      vector_store = S3VectorStore(...)
  ```
- Added command-line arguments:
  - `--vector-store {pgvector|s3}` (default: pgvector)
  - `--s3-bucket BUCKET_NAME` (required for S3)

**Usage Examples:**

pgvector:
```bash
python rag/scripts/vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store pgvector
```

S3 Vectors:
```bash
python rag/scripts/vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store s3 \
    --s3-bucket my-code-vectors \
    --batch-size 25
```

#### 3. Created S3 Vector Store Documentation
**Goal:** Comprehensive documentation for S3 vector store module

**Files Created:**
- `docs/S3_VECTOR_STORE.md` (644 lines)

**Documentation Includes:**
- Overview and features
- Class initialisation and all methods with examples
- PutVectors and QueryVectors API documentation
- Environment variable setup
- S3 bucket creation and IAM permissions
- Distance metrics (cosine vs euclidean)
- Comparison table: S3 Vectors vs pgvector
- When to use each vector store
- Metadata handling
- Performance considerations
- Cost analysis
- Error handling and troubleshooting
- Best practices
- API methods summary table

**Files Modified:**
- `docs/README.md` - Added S3 Vector Store to Core Modules section
- Updated document structure diagram

---

## Key Technical Decisions (Session 2)

### 1. S3 Vectors as Alternative to pgvector
**Decision:** Implement S3 Vectors as a pluggable alternative
**Rationale:**
- Serverless architecture (no database management)
- Unlimited scalability with S3
- Pay-per-request pricing model
- Same interface as pgvector for easy switching
- Suitable for AWS-native architectures

### 2. Unified Interface for Vector Stores
**Decision:** Both `PgVectorStore` and `S3VectorStore` implement the same methods
**Rationale:**
- Easy to switch between vector stores
- Existing code (vectorise_and_store.py) works with both
- Consistent API experience
- Future vector stores can follow the same pattern

**Common Interface:**
```python
- connect()
- initialise_schema(dimension)
- insert_embedding(content, embedding, metadata)
- insert_embeddings_batch(records)
- similarity_search(query_embedding, top_k, metadata_filter, verbose)
- delete_all()
- get_count()
- close()
```

### 3. Batch Operations with PutVectors API
**Decision:** Use native PutVectors API for batch insertion
**Rationale:**
- Single API call for multiple vectors (more efficient)
- Reduced latency compared to sequential inserts
- Better cost efficiency (fewer API requests)
- Follows AWS best practices

---

## File Modifications Summary (Session 2)

### Created (New Files)
| File | Size | Purpose |
|------|------|---------|
| `rag/core/s3_vector_store.py` | ~365 lines | S3 vector store implementation |
| `docs/S3_VECTOR_STORE.md` | 644 lines | S3 vector store documentation |

### Modified
| File | Changes |
|------|---------|
| `rag/scripts/vectorise_and_store.py` | Added S3 vector store support, new CLI arguments |
| `docs/README.md` | Added S3 Vector Store to Core Modules, updated structure |

---

## Environment Configuration (Session 2)

### S3 Vectors (Additional)
```bash
# Same AWS credentials as Bedrock
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SESSION_TOKEN=your-session-token  # Optional

# S3 bucket for vectors (specify via CLI --s3-bucket)
```

### S3 Bucket Setup
```bash
# Create S3 bucket
aws s3 mb s3://my-code-vectors --region ap-southeast-2

# Verify bucket
aws s3 ls s3://my-code-vectors

# List vectors in index
aws s3 ls s3://my-code-vectors/code_embeddings/
```

---

## Common Commands Reference (Session 2)

### S3 Vector Store Usage
```bash
# Vectorise and store in S3
python rag/scripts/vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store s3 \
    --s3-bucket my-code-vectors \
    --table-name code_embeddings \
    --batch-size 25 \
    --clear

# Vectorise and store in pgvector (default)
python rag/scripts/vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store pgvector \
    --table-name code_embeddings
```

### Python Usage (S3 Vectors)
```python
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.s3_vector_store import S3VectorStore

# Setup
embedder = BedrockEmbeddingGenerator()
bucket_name = "my-code-vectors"

# Initialise S3 vector store
with S3VectorStore(bucket_name=bucket_name, index_name="code_embeddings") as store:
    dimension = embedder.get_dimension()  # 1024 for Titan v2
    store.initialise_schema(dimension=dimension, distance_metric="cosine")

    # Insert
    content = "Type: class\n@RestController\nclass HelloController {...}"
    embedding = embedder.generate(content)
    metadata = {"chunk_id": "hc-001", "file_type": "java", "layer": "controller"}
    vector_key = store.insert_embedding(content, embedding, metadata)

    # Search
    query = "Find REST controllers"
    query_embedding = embedder.generate(query)
    results = store.similarity_search(
        query_embedding=query_embedding,
        top_k=5,
        metadata_filter={"layer": "controller"},
        verbose=True
    )
```

---

## Code Module Relationships (Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  DatabaseConfig      │  ← Environment variables (.env)
│  (config.py)         │  ← Connection parameters
└──────────┬───────────┘
           │
           │ provides config to
           │
           ↓
┌──────────────────────┐     ┌──────────────────────────────┐
│  BedrockEmbedding    │     │  PgVectorStore               │
│  Generator           │────→│  (pgvector_store.py)         │
│  (bedrock_          │ embeddings │                        │
│   embeddings.py)     │     │  - PostgreSQL + pgvector     │
│                      │     │  - HNSW indexing             │
│  - generate()        │     │  - SQL-based search          │
│  - generate_batch()  │     └──────────────────────────────┘
│  - get_dimension()   │
└──────────────────────┘     ┌──────────────────────────────┐
           │                  │  S3VectorStore               │
           │                  │  (s3_vector_store.py)        │
           └─────────────────→│                              │
                embeddings    │  - Amazon S3 Vectors         │
                              │  - PutVectors/QueryVectors   │
                              │  - Serverless                │
                              └──────────────────────────────┘
```

**Integration Flow (S3 Vectors):**
1. `BedrockEmbeddingGenerator` generates embeddings (1024-dim)
2. `S3VectorStore` initialises with bucket name and index name
3. `initialise_schema()` configures dimension and distance metric
4. Embeddings inserted with `insert_embedding()` or `insert_embeddings_batch()`
   - Uses `put_vectors()` API
   - Stores in S3 bucket under `{index_name}/{vector_key}`
5. Query embedding generated with `BedrockEmbeddingGenerator.generate()`
6. Search with `similarity_search()` using `query_vectors()` API
   - Supports metadata filtering
   - Returns top-K results with similarity scores

---

## Session 1: Q&A Documentation Restructuring (2025-10-14)

### Tasks Completed

#### 1. Updated Q&A Response Openings
**Goal:** Make Q&A responses more direct (remove "Great question!" openings)

**Files Modified:**
- `docs/Q&A.md` (6 opening responses updated)

**Changes:**
- Updated opening sentences to directly answer questions
- Example: "Tree-sitter works with **source code text**, not compiled binaries."
- Preserved all original content

#### 2. Added Weighted Vector Boosting Q&A
**Goal:** Add comprehensive content about weighted vector boosting

**Files Modified:**
- `docs/Q&A.md` (added Question 7)

**Content Added:**
- 4 approaches to weighted boosting:
  1. Metadata-based reranking (recommended)
  2. Query-time embedding manipulation
  3. Hybrid scoring (semantic + lexical)
  4. Database-level boost factors
- Full code examples for each approach
- Practical use cases and before/after comparisons

#### 3. Restructured Q&A Documentation
**Goal:** Create navigable multi-file structure for growing Q&A content

**Files Created:**
- `docs/README.md` - Main navigation hub
- `docs/qna/01_vector_search_workflow.md`
- `docs/qna/02_metadata_role.md`
- `docs/qna/03_top_k_selection.md`
- `docs/qna/04_metadata_in_embeddings.md`
- `docs/qna/05_tree_sitter_parsing.md`
- `docs/qna/06_pgvector_indexing.md`
- `docs/qna/07_weighted_boosting.md`
- `docs/RESTRUCTURING_SUMMARY.md`

**Structure Created:**
```
docs/
├── README.md                          # Main navigation
├── Q&A.md                            # Original (kept as backup)
└── qna/                              # Individual Q&A files
    ├── 01_vector_search_workflow.md
    ├── 02_metadata_role.md
    ├── 03_top_k_selection.md
    ├── 04_metadata_in_embeddings.md
    ├── 05_tree_sitter_parsing.md
    ├── 06_pgvector_indexing.md
    └── 07_weighted_boosting.md
```

**Navigation Added:**
- Each file has Previous/Next/Back to Index links
- Main README serves as central hub
- All content preserved (no deletions)

#### 4. Applied Proper Markdown Formatting
**Goal:** Format Q&A files with proper headings, code blocks, etc.

**Files Modified:**
- All 7 Q&A files in `docs/qna/`
- `docs/FORMATTING_SUMMARY.md` (created)

**Formatting Applied:**
- Proper code blocks with language tags (```python, ```sql, ```java)
- Converted indented sections to proper headings (###, ####)
- Maintained Australian English spelling
- 100% content preservation

#### 5. Removed Q&A Format Headers
**Goal:** Simplify format by removing "## Question" and "## Answer" headers

**Files Modified:**
- All 7 Q&A files in `docs/qna/`

**Changes:**
- Removed section headers
- Content flows directly after navigation
- Simplified structure: Title → Navigation → Content

#### 6. Created Core Module Documentation
**Goal:** Create comprehensive documentation for three core Python modules

**Files Created:**
- `docs/BEDROCK_EMBEDDINGS.md` (9.2KB)
- `docs/CONFIG.md` (7.5KB)
- `docs/PGVECTOR_STORE.md` (16KB)

**Files Modified:**
- `docs/README.md` (added Core Modules section with links)

**Documentation Includes:**

**BEDROCK_EMBEDDINGS.md:**
- `BedrockEmbeddingGenerator` class documentation
- Methods: `generate()`, `generate_batch()`, `get_dimension()`
- Constructor parameters and environment variables
- Usage examples (single text, batch, integration)
- Error handling
- Supported models (Titan v1/v2)
- Best practices

**CONFIG.md:**
- `DatabaseConfig` class documentation
- Constructor parameters
- Properties: `connection_string`, `connection_params`
- Environment variable setup
- Usage examples with psycopg2
- Multiple database connections
- Error handling
- Best practices

**PGVECTOR_STORE.md:**
- `PgVectorStore` class documentation
- Methods:
  - `connect()`
  - `initialise_schema(dimension)`
  - `insert_embedding(content, embedding, metadata)`
  - `insert_embeddings_batch(records)`
  - `similarity_search(query_embedding, top_k, metadata_filter, verbose)`
  - `delete_by_id(record_id)`
  - `delete_all()`
  - `get_count()`
  - `close()`
- Context manager support (`with` statement)
- HNSW index parameters explained
- Distance metrics (cosine vs euclidean)
- Metadata filtering examples
- Hybrid search (semantic + metadata)
- Performance considerations
- Verbose mode for debugging SQL queries
- Error handling
- Best practices

---

## Key Technical Decisions

### 1. HNSW Index Configuration
**Decision:** Use HNSW with `m=16, ef_construction=64`
**Rationale:**
- High accuracy for code search (small-to-medium datasets)
- Fast queries
- No training phase needed
- Better than IVFFlat for <10k chunks

**Reference:** `docs/qna/06_pgvector_indexing.md`

### 2. Cosine Distance for Similarity
**Decision:** Use cosine distance (`vector_cosine_ops`)
**Rationale:**
- Code chunks vary in length
- Semantic meaning matters, not magnitude
- Bedrock Titan embeddings are normalised
- Direction-based similarity

**Reference:** `docs/qna/06_pgvector_indexing.md`, `docs/PGVECTOR_STORE.md`

### 3. Rich Metadata in Embeddings
**Decision:** Include annotations, class names, layers in embedded content
**Rationale:**
- Improves semantic search accuracy (20-40%)
- Spring Boot annotations define architectural roles
- Hybrid search capability (semantic + metadata filter)
- Industry best practice (LangChain, LlamaIndex)

**Reference:** `docs/qna/04_metadata_in_embeddings.md`

### 4. Metadata-based Reranking for Boosting
**Decision:** Use post-retrieval metadata-based reranking (Approach #1)
**Rationale:**
- Flexible (easy to adjust boost factors)
- Transparent (original similarity + boost visible)
- Query-specific (different queries can use different boosts)
- No database schema changes needed

**Reference:** `docs/qna/07_weighted_boosting.md`

---

## Code Module Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  DatabaseConfig      │  ← Environment variables (.env)
│  (config.py)         │  ← Connection parameters
└──────────┬───────────┘
           │
           │ provides config to
           │
           ↓
┌──────────────────────┐     ┌──────────────────────────────┐
│  BedrockEmbedding    │     │  PgVectorStore               │
│  Generator           │────→│  (pgvector_store.py)         │
│  (bedrock_          │ embeddings │                        │
│   embeddings.py)     │     │  - Schema creation           │
│                      │     │  - Insert embeddings         │
│  - generate()        │     │  - Similarity search         │
│  - generate_batch()  │     │  - Metadata filtering        │
│  - get_dimension()   │     │  - HNSW indexing            │
└──────────────────────┘     └──────────────────────────────┘
           │                            │
           │ Titan v2                  │ PostgreSQL + pgvector
           │ 1024-dim                  │ Cosine similarity
           ↓                            ↓
    [0.1, 0.2, ...]              [stored vectors]
```

**Integration Flow:**
1. `DatabaseConfig` loads connection parameters
2. `PgVectorStore` uses config to connect to PostgreSQL
3. `BedrockEmbeddingGenerator` generates embeddings (1024-dim)
4. `PgVectorStore.initialise_schema()` creates table with correct dimension
5. Embeddings inserted with `insert_embedding()` or `insert_embeddings_batch()`
6. Query embedding generated with `BedrockEmbeddingGenerator.generate()`
7. Search with `PgVectorStore.similarity_search()` using cosine similarity

---

## File Modifications Summary

### Created (New Files)
| File | Size | Purpose |
|------|------|---------|
| `docs/README.md` | 3.0KB | Main navigation hub |
| `docs/qna/01_vector_search_workflow.md` | - | Vector search workflow explanation |
| `docs/qna/02_metadata_role.md` | - | Metadata vs content |
| `docs/qna/03_top_k_selection.md` | - | Top-K selection |
| `docs/qna/04_metadata_in_embeddings.md` | - | Metadata in embeddings tradeoffs |
| `docs/qna/05_tree_sitter_parsing.md` | - | Tree-sitter AST parsing |
| `docs/qna/06_pgvector_indexing.md` | - | HNSW vs IVFFlat indexing |
| `docs/qna/07_weighted_boosting.md` | - | Weighted vector boosting |
| `docs/RESTRUCTURING_SUMMARY.md` | - | Restructuring documentation |
| `docs/FORMATTING_SUMMARY.md` | - | Formatting documentation |
| `docs/BEDROCK_EMBEDDINGS.md` | 9.2KB | Bedrock embeddings module docs |
| `docs/CONFIG.md` | 7.5KB | Database config module docs |
| `docs/PGVECTOR_STORE.md` | 16KB | Vector store module docs |

### Modified
| File | Changes |
|------|---------|
| `docs/Q&A.md` | Updated 6 opening responses, added Question 7 (weighted boosting) |
| `docs/README.md` | Added Core Modules section, updated document structure |

### Preserved (Backups)
| File | Status |
|------|--------|
| `docs/Q&A.md` | Kept as backup (original content) |

---

## Environment Configuration

### Required Environment Variables

**PostgreSQL Database:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vectordb
DB_USER=postgres
DB_PASSWORD=your-secure-password
```

**AWS Bedrock:**
```bash
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SESSION_TOKEN=your-session-token  # Optional
```

**File:** `.env` (project root)

---

## Common Commands Reference

### Database Setup
```bash
# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb vectordb

# Connect to database
psql vectordb

# Install pgvector extension
psql vectordb -c "CREATE EXTENSION vector;"
```

### Python Usage
```python
from core.config import DatabaseConfig
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.pgvector_store import PgVectorStore

# Setup
config = DatabaseConfig()
embedder = BedrockEmbeddingGenerator()

# Initialise vector store
with PgVectorStore(config=config, table_name="code_embeddings") as store:
    dimension = embedder.get_dimension()  # 1024 for Titan v2
    store.initialise_schema(dimension=dimension)

    # Insert
    content = "Type: class\n@RestController\nclass HelloController {...}"
    embedding = embedder.generate(content)
    metadata = {"file_type": "java", "layer": "controller"}
    record_id = store.insert_embedding(content, embedding, metadata)

    # Search
    query = "Find REST controllers"
    query_embedding = embedder.generate(query)
    results = store.similarity_search(
        query_embedding=query_embedding,
        top_k=5,
        metadata_filter={"layer": "controller"}
    )
```

---

## Key Implementation Details

### Embedding Content Format
**Format:**
```
Type: class
Layer: controller
Class: SampleController
Annotations: @RestController, @RequestMapping("/api/hello")
Package: com.example.demo

[actual code content]
```

**Rationale:** Rich metadata in content improves semantic search

### Metadata Schema
**Fields:**
```json
{
    "file_type": "java",
    "layer": "controller",
    "class_name": "SampleController",
    "annotations": ["@RestController", "@RequestMapping"],
    "package": "com.example.demo",
    "chunk_id": "unique-id",
    "line_start": 10,
    "line_end": 25
}
```

**Reference:** `docs/METADATA_FIELDS.md`

### Vector Dimensions
- **Titan v1:** 1536 dimensions
- **Titan v2:** 1024 dimensions (current)
- **Titan Image:** 1024 dimensions

**Always match:** `initialise_schema(dimension=embedder.get_dimension())`

---

## Troubleshooting Guide

### Connection Failed
```
psycopg2.OperationalError: could not connect to server
```
**Solution:** Start PostgreSQL: `brew services start postgresql@14`

### Extension Not Found
```
could not open extension control file
```
**Solution:** Install pgvector: `CREATE EXTENSION vector;`

### Dimension Mismatch
```
expected 1024 dimensions, got 1536
```
**Solution:** Match schema dimension with embedding model dimension

### AWS Credentials Error
```
Unable to locate credentials
```
**Solution:** Set environment variables in `.env` file

---

## Next Steps / Future Enhancements

### Potential Improvements
1. **Reranking Module:** Implement metadata-based reranking as separate module
2. **Query Intent Detection:** Auto-adjust boost factors based on query intent
3. **Metadata Expansion:** Add more fields (HTTP methods, security annotations)
4. **Connection Pooling:** Add for production workloads
5. **Batch Delete:** Add `delete_by_metadata()` method
6. **Similarity Threshold:** Filter results by minimum similarity score
7. **Hybrid Search:** Combine with lexical search (BM25)

### Documentation Gaps
- Usage guide for `vectorise_and_store.py`
- End-to-end RAG workflow example
- Integration with LLM for retrieval
- Chunking strategy documentation

---

## Session Continuation Instructions

### If Session is Lost

1. **Review this file** to understand what's been completed
2. **Check git status** to see uncommitted changes
3. **Reference module docs** in `docs/` for current state
4. **Key context:**
   - All Q&A content split into 7 individual files
   - Core module documentation completed (3 files)
   - Original content 100% preserved (no deletions)
   - Australian English spelling used throughout

### Important Files to Check
- `docs/README.md` - Current navigation structure
- `docs/qna/` - All Q&A content
- `docs/BEDROCK_EMBEDDINGS.md` - Embeddings module
- `docs/CONFIG.md` - Database config module
- `docs/PGVECTOR_STORE.md` - Vector store module
- `rag/core/` - Implementation code

### Current State
- ✅ Q&A documentation restructured and formatted
- ✅ Core module documentation completed
- ✅ Navigation system in place
- ✅ All original content preserved

---

## User Preferences

### Must Follow
1. **Never remove original content** - preserve 100%
2. **Australian English spelling** - optimise, analyse, behaviour, colour, etc.
3. **Proper markdown formatting** - headings, code blocks with language tags
4. **Code comments in Australian English**

### Communication Style
- Direct answers (no "Great question!" openings)
- Practical code examples
- Clear explanations with visual diagrams where helpful
- Cross-references to related documentation

---

**End of Session Log**

---

## Appendix: Command History

```bash
# Q&A restructuring
awk '...' Q&A.md  # Split by separator
cat navigation.txt 01.md > 01_vector_search_workflow.md

# File verification
ls -lh docs/qna/
grep -n "^#" docs/qna/*.md

# Module documentation
cat rag/core/bedrock_embeddings.py
cat rag/core/config.py
cat rag/core/pgvector_store.py
```

---

**Note:** This session log should be updated at the end of each session to maintain continuity.
