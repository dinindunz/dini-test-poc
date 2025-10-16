# Scripts Guide

**[← Back to Main Documentation](./README.md)**

Convenient shell scripts and Python modules for chunking code and vectorising with PostgreSQL pgvector.

---

## Quick Start

### 1. Chunk Your Code

```bash
cd scripts
./chunk_code.sh
```

This creates chunked representations of your code in `chunks/chunks_output.json`.

### 2. Vectorise and Store

```bash
./vectorise_data.sh
```

This generates embeddings using Amazon Bedrock Titan and stores them in PostgreSQL with pgvector.

---

## Scripts Overview

### `chunk_code.sh`

Chunks your codebase into semantic units for embedding.

**What it does:**
- Runs the multi-module code chunker
- Processes Java, Swagger/OpenAPI, Markdown, and Gradle files
- Creates structured chunks with metadata
- Outputs to `chunks/chunks_output.json`

**Usage:**
```bash
./chunk_code.sh
```

**Output:**
```
chunks/
├── chunks_output.json   # All chunks (used for vectorisation)
└── chunks_sample.json   # First 10 chunks (for inspection)
```

**Expected Statistics:**
```
============================================================
CHUNKING STATISTICS
============================================================

📦 Chunks per module:
  01_dini_java17-quickstart-helloworld: 29

📄 Chunks per file type:
  gradle: 2
  java: 4
  markdown: 19
  swagger: 4

🏷️  Chunks per type:
  api_endpoint: 1
  api_info: 1
  api_schema: 2
  build_config_full: 1
  class: 4
  dependencies: 1
  documentation: 19

📊 Total chunks: 29
```

---

### `vectorise_data.sh`

Generates embeddings and stores them in PostgreSQL with pgvector.

**What it does:**
- Reads chunks from `chunks/chunks_output.json`
- Generates embeddings using Amazon Bedrock Titan v2 (1024 dimensions)
- Stores embeddings in PostgreSQL with metadata
- Creates pgvector indexes for fast similarity search

**Syntax:**
```bash
./vectorise_data.sh
```

**Configuration:**

The script uses these default settings (edit the script to customise):

```bash
--chunks-file ../chunks/chunks_output.json     # Input chunks
--model-id amazon.titan-embed-text-v2:0        # Bedrock model
--table-name code_embeddings                   # PostgreSQL table
--batch-size 25                                # Chunks per batch
--clear                                        # Clear existing data
```

**Customisation Examples:**

To keep existing data (don't clear):
```bash
python vectorise_and_store.py \
    --chunks-file ../chunks/chunks_output.json \
    --model-id amazon.titan-embed-text-v2:0 \
    --table-name code_embeddings \
    --batch-size 25
```

To use a different table:
```bash
python vectorise_and_store.py \
    --chunks-file ../chunks/chunks_output.json \
    --table-name my_custom_table \
    --batch-size 50 \
    --clear
```

**Expected Output:**
```
🚀 Starting vectorisation and storage process

📂 Loading chunks from: ../chunks/chunks_output.json
✅ Loaded 30 chunks
🤖 Initialising Bedrock Titan embedding generator: amazon.titan-embed-text-v2:0
📊 Embedding dimension: 1024

🗄️  Connecting to PostgreSQL database
✅ Connected to database: vectordb
✅ Database schema initialised: code_embeddings (dimension: 1024)

🗑️  Clearing existing data
✅ Deleted all existing records

⚙️  Processing 30 chunks in batches of 25
Processing batches: 100%|████████████| 2/2 [00:08<00:00,  4.12s/it]

============================================================
📊 VECTORISATION SUMMARY
============================================================
✅ Successfully processed: 30 chunks
⏭️  Skipped (no metadata): 0 chunks
❌ Failed: 0 chunks
📦 Total in database: 30 records
============================================================

✅ Vectorisation complete!
```

---

## Environment Setup

### Prerequisites

1. **PostgreSQL instance with pgvector**
   ```bash
   docker run -d --name pgvector -e POSTGRES_PASSWORD=postgres123 -p 5432:5432 pgvector/pgvector:pg17
   ```

2. **Python Environment**
   ```bash
   pip install -r requirements.txt
   ```

3. **AWS Credentials**
   - Configure AWS profile for Bedrock access
   - Ensure Bedrock Titan model access is enabled

### Environment Variables

Create a `.env` file:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vectordb
DB_USER=postgres
DB_PASSWORD=your-password

# AWS (uses AWS profile, no explicit credentials needed)
AWS_REGION=ap-southeast-2
```

---

## Complete Pipeline

Run the full chunking and vectorisation pipeline:

```bash
# 1. Chunk the code
./chunk_code.sh

# 2. Review the chunks (optional)
cat ../chunks/chunks_sample.json | jq '.[0]'

# 3. Vectorise and store
./vectorise_data.sh
```

**Total Time:** ~10 seconds for 30 chunks (includes embedding generation and database insertion)

---

## Advanced Usage

### Custom Chunking

Edit `chunk_code.sh` to customise the chunking process:

```bash
# Chunk a different directory
python multi_module_chunker.py /path/to/your/code

# Process specific file types only
# (Edit multi_module_chunker.py configuration)
```

### Batch Processing

For large codebases, adjust batch size:

```bash
python vectorise_and_store.py \
    --chunks-file ../chunks/chunks_output.json \
    --batch-size 50 \
    --clear
```

**Batch Size Guidelines:**
- Small projects (<100 chunks): 25
- Medium projects (100-1000 chunks): 50
- Large projects (>1000 chunks): 100

### Incremental Updates

To add new chunks without clearing existing data:

```bash
python vectorise_and_store.py \
    --chunks-file ../chunks/new_chunks.json \
    --batch-size 25
    # No --clear flag
```

---

## Related Documentation

- [Main Documentation](./README.md) - Complete RAG system documentation
- [PostgreSQL Vector Store](./PGVECTOR_STORE.md)
- [Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md)
- [Database Configuration](./CONFIG.md)
- [Metadata Fields Reference](./METADATA_FIELDS.md)

---

## Python Modules

### `multi_module_chunker.py`

Core chunking module that processes multiple code modules.

**Features:**
- Tree-sitter AST parsing for Java files
- Chunks by classes, methods, and records
- Processes Swagger/OpenAPI YAML files
- Processes Markdown documentation
- Processes Gradle build files
- Automatic layer detection (controller, service, repository, etc.)
- Extracts rich metadata (package, annotations, HTTP methods, etc.)

**Direct Usage:**
```bash
python multi_module_chunker.py /path/to/java17
```

**What it chunks:**
| File Type | Chunking Strategy | Metadata Extracted |
|-----------|------------------|-------------------|
| **Java** (.java) | By class/record (if < 300 lines) or by method (if larger) | Package, class name, annotations, layer, imports, HTTP methods, API paths |
| **Swagger** (.yaml, .yml) | By endpoint + schemas separately | HTTP method, API path, operation ID, request/response schemas |
| **Markdown** (.md) | By heading sections | Document name, heading, heading level, code presence |
| **Gradle** (build.gradle) | Full file + dependencies block + plugins block | Java version, Spring Boot version, dependencies, plugins |

**Output:**
- `chunks/chunks_output.json` - All chunks
- `chunks/chunks_sample.json` - First 10 chunks for review

---

### `verify_chunks.py`

Verification tool to ensure all Java files have been chunked.

**Purpose:**
- Compares source Java files with chunked files
- Identifies missing files
- Shows chunk statistics per file
- Validates chunking completeness

**Usage:**
```bash
# Verify chunks for default java17 directory
python verify_chunks.py

# Verify chunks for custom directory
python verify_chunks.py /path/to/your/code
```

**Example Output:**
```
======================================================================
JAVA FILE CHUNK VERIFICATION
======================================================================

📂 Source directory: /Users/dinindu/Projects/GitHub/dini-test-poc/java17
📄 Chunks file: /Users/dinindu/Projects/GitHub/dini-test-poc/chunks/chunks_output.json

✅ Found 5 Java files in source directory
✅ Found 5 Java files in chunks

======================================================================
VERIFICATION RESULTS
======================================================================

✅ SUCCESS: All Java files have been chunked!
   Total files: 5

======================================================================
CHUNKS PER JAVA FILE
======================================================================

📄 SampleController.java (1 chunk)
   Path: 01_dini_java17-quickstart-helloworld/src/main/java/...
   Types: {'class': 1}
   Classes/Records: SampleController

======================================================================
SUMMARY
======================================================================
Total Java files in source: 5
Total Java files chunked: 5
Missing from chunks: 0
Extra in chunks: 0
Total chunks for Java files: 5
```

**Exit Codes:**
- `0` - Success (all files chunked)
- `1` - Failure (missing files)

---

### `vectorise_and_store.py`

Vectorisation module that generates embeddings and stores in PostgreSQL.

**Features:**
- Bedrock Titan embedding generation
- Batch processing with progress bars
- Rich metadata storage
- Configurable batch sizes
- Clear existing data option
- Comprehensive error handling

**Direct Usage:**
```bash
# Basic usage with defaults
python vectorise_and_store.py

# Full configuration
python vectorise_and_store.py \
    --chunks-file ../chunks/chunks_output.json \
    --model-id amazon.titan-embed-text-v2:0 \
    --table-name code_embeddings \
    --batch-size 25 \
    --clear
```

**Arguments:**
- `--chunks-file` - Path to chunks JSON file (default: `chunks_output.json`)
- `--model-id` - Bedrock model ID (default: `amazon.titan-embed-text-v2:0`)
- `--table-name` - PostgreSQL table name (default: `code_embeddings`)
- `--batch-size` - Processing batch size (default: `25`)
- `--clear` - Clear existing data before inserting

**Embedding Content Structure:**

The module prepares rich content for embedding:
```
Type: class
Layer: controller
Class: SampleController
Package: com.example.hello.world.controller
Annotations: @Slf4j, @RestController

[actual code content here]
```

This structured approach improves semantic search accuracy.

---

## Script Locations

```
scripts/
├── chunk_code.sh                # Code chunking shell script
├── vectorise_data.sh            # Vectorisation shell script
├── multi_module_chunker.py      # Core chunking module
├── verify_chunks.py             # Chunk verification tool
└── vectorise_and_store.py       # Vectorisation module
```

---

**Last Updated:** 2025-10-16
