# RAG Scripts

Convenient shell scripts for vectorising code chunks and storing in vector databases.

---

## Quick Start

### PostgreSQL (pgvector)

```bash
# Use defaults (chunks_output.json, table: code_embeddings, batch: 25)
./vectorise_pgvector.sh

# Specify chunks file
./vectorise_pgvector.sh my_chunks.json

# Full options
./vectorise_pgvector.sh chunks_output.json code_embeddings 25 --clear
```

### Amazon S3 Vectors

```bash
# Minimal (S3 bucket required)
./vectorise_s3.sh my-code-vectors

# Specify chunks file
./vectorise_s3.sh my-code-vectors my_chunks.json

# Full options
./vectorise_s3.sh my-code-vectors chunks_output.json code_embeddings 25 --clear
```

---

## Scripts

### `vectorise_pgvector.sh`

Vectorise and store in PostgreSQL with pgvector extension.

**Syntax:**
```bash
./vectorise_pgvector.sh [chunks_file] [table_name] [batch_size] [--clear]
```

**Parameters:**
- `chunks_file` - Path to chunks JSON file (default: `chunks_output.json`)
- `table_name` - PostgreSQL table name (default: `code_embeddings`)
- `batch_size` - Number of chunks per batch (default: `25`)
- `--clear` - Clear existing data before inserting (optional)

**Examples:**

```bash
# Use all defaults
./vectorise_pgvector.sh

# Custom chunks file
./vectorise_pgvector.sh my_chunks.json

# Custom table name
./vectorise_pgvector.sh chunks_output.json my_embeddings

# Custom batch size
./vectorise_pgvector.sh chunks_output.json code_embeddings 50

# Clear existing data
./vectorise_pgvector.sh chunks_output.json code_embeddings 25 --clear
```

**Requirements:**
- PostgreSQL running with pgvector extension
- Environment variables set in `.env`:
  ```bash
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=vectordb
  DB_USER=postgres
  DB_PASSWORD=your-password
  ```

---

### `vectorise_s3.sh`

Vectorise and store in Amazon S3 Vectors (serverless).

**Syntax:**
```bash
./vectorise_s3.sh <s3_bucket> [chunks_file] [index_name] [batch_size] [--clear]
```

**Parameters:**
- `s3_bucket` - S3 bucket name (required, auto-created if doesn't exist)
- `chunks_file` - Path to chunks JSON file (default: `chunks_output.json`)
- `index_name` - Vector index name (default: `code_embeddings`)
- `batch_size` - Number of chunks per batch (default: `25`)
- `--clear` - Clear existing vectors before inserting (optional)

**Examples:**

```bash
# Minimal (bucket auto-created)
./vectorise_s3.sh my-code-vectors

# Custom chunks file
./vectorise_s3.sh my-code-vectors my_chunks.json

# Custom index name
./vectorise_s3.sh my-code-vectors chunks_output.json my_index

# Custom batch size
./vectorise_s3.sh my-code-vectors chunks_output.json code_embeddings 50

# Clear existing vectors
./vectorise_s3.sh my-code-vectors chunks_output.json code_embeddings 25 --clear
```

**Requirements:**
- AWS credentials configured
- Environment variables set in `.env`:
  ```bash
  AWS_REGION=ap-southeast-2
  AWS_ACCESS_KEY_ID=your-access-key
  AWS_SECRET_ACCESS_KEY=your-secret-key
  ```
- IAM permissions:
  - `s3:CreateBucket` (for auto-creation)
  - `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`
  - `s3:ListBucket`, `s3:HeadBucket`

---

## Comparison

| Feature | `vectorise_pgvector.sh` | `vectorise_s3.sh` |
|---------|------------------------|-------------------|
| **Infrastructure** | PostgreSQL server | Serverless (S3) |
| **Setup** | Requires DB setup | Bucket auto-created |
| **Scalability** | DB instance limited | Unlimited |
| **Cost** | Fixed (DB instance) | Pay-per-request |
| **Speed** | Very fast (HNSW) | Good (serverless) |

---

## Underlying Python Script

Both shell scripts call `vectorise_and_store.py` with different options:

```bash
# Direct Python usage (if needed)
python3 vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --vector-store {pgvector|s3} \
    --table-name code_embeddings \
    --batch-size 25 \
    [--s3-bucket my-bucket]  # Required for S3
    [--clear]                # Optional
```

---

## Environment Setup

Create a `.env` file in the project root:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vectordb
DB_USER=postgres
DB_PASSWORD=your-password

# AWS (for both Bedrock and S3 Vectors)
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

---

## Troubleshooting

### PostgreSQL Connection Failed

```
❌ Database connection failed: could not connect to server
```

**Solution:**
```bash
# Start PostgreSQL
brew services start postgresql@14

# Verify it's running
psql -U postgres -c "SELECT version();"
```

### S3 Access Denied

```
❌ Access denied to bucket my-code-vectors. Check IAM permissions.
```

**Solution:**
- Verify AWS credentials in `.env`
- Check IAM policy includes `s3:CreateBucket`, `s3:PutObject`, etc.
- Test credentials: `aws s3 ls`

### Chunks File Not Found

```
❌ No chunks to process
```

**Solution:**
- Check file path is correct
- Generate chunks first using `chunk_code.sh`
- Verify JSON format is valid

---

## Related Documentation

- [PostgreSQL Vector Store](../docs/PGVECTOR_STORE.md)
- [S3 Vector Store](../docs/S3_VECTOR_STORE.md)
- [Bedrock Embeddings](../docs/BEDROCK_EMBEDDINGS.md)

---

**Last Updated:** 2025-10-16
