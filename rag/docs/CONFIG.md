# Database Configuration Module

**Module:** `core/config.py`

[← Back to Documentation Index](./README.md)

---

## Overview

The `DatabaseConfig` class provides a centralised configuration management system for PostgreSQL database connections. It automatically loads connection parameters from environment variables with sensible defaults, making it easy to connect to your vector database.

## Features

- ✅ Automatic environment variable loading via `python-dotenv`
- ✅ Configurable connection parameters (host, port, database, user, password)
- ✅ Connection string generation for SQLAlchemy and psycopg2
- ✅ Dictionary-style connection parameters for psycopg2
- ✅ Default values for local development
- ✅ Secure password handling from environment variables

## Class: `DatabaseConfig`

### Initialisation

```python
from core.config import DatabaseConfig

# Using environment variables (recommended)
config = DatabaseConfig()

# With explicit parameters (overrides env vars)
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="vectordb",
    user="postgres",
    password="your-password"
)
```

### Constructor Parameters

| Parameter | Type | Default | Env Variable | Description |
|-----------|------|---------|--------------|-------------|
| `host` | `str` | `"localhost"` | `DB_HOST` | PostgreSQL server hostname |
| `port` | `int` | `5432` | `DB_PORT` | PostgreSQL server port |
| `database` | `str` | `"vectordb"` | `DB_NAME` | Database name |
| `user` | `str` | `"postgres"` | `DB_USER` | Database user |
| `password` | `str` | `"postgres"` | `DB_PASSWORD` | Database password |

**Priority:** Explicit parameters > Environment variables > Defaults

## Properties

### `connection_string`

Returns a PostgreSQL connection string suitable for SQLAlchemy or psycopg2.

**Returns:**
- `str`: Connection string in format `postgresql://user:password@host:port/database`

**Example:**

```python
config = DatabaseConfig()
conn_string = config.connection_string

print(conn_string)
# Output: postgresql://postgres:postgres@localhost:5432/vectordb

# Use with psycopg2
import psycopg2
conn = psycopg2.connect(conn_string)
```

### `connection_params`

Returns connection parameters as a dictionary for direct use with psycopg2.

**Returns:**
- `dict`: Dictionary with keys: `host`, `port`, `database`, `user`, `password`

**Example:**

```python
config = DatabaseConfig()
params = config.connection_params

print(params)
# Output: {
#     'host': 'localhost',
#     'port': 5432,
#     'database': 'vectordb',
#     'user': 'postgres',
#     'password': 'postgres'
# }

# Use with psycopg2
import psycopg2
conn = psycopg2.connect(**params)
```

## Environment Variables

Create a `.env` file in your project root:

```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vectordb
DB_USER=postgres
DB_PASSWORD=your-secure-password
```

**Security Note:** Never commit `.env` files to version control. Add `.env` to your `.gitignore`.

## Usage Examples

### Example 1: Basic Usage with Environment Variables

```python
from core.config import DatabaseConfig
from core.pgvector_store import PgVectorStore

# Load config from .env file
config = DatabaseConfig()

# Connect to vector store
vector_store = PgVectorStore(config=config, table_name="code_embeddings")
vector_store.connect()

print(f"Connected to {config.database} at {config.host}:{config.port}")
# Output: Connected to vectordb at localhost:5432
```

### Example 2: Override Specific Parameters

```python
from core.config import DatabaseConfig

# Use env vars for most settings, override database name
config = DatabaseConfig(database="my_custom_db")

print(config.connection_string)
# Output: postgresql://postgres:postgres@localhost:5432/my_custom_db
```

### Example 3: Multiple Database Connections

```python
from core.config import DatabaseConfig

# Development database
dev_config = DatabaseConfig(
    host="localhost",
    database="vectordb_dev"
)

# Production database (from env vars)
prod_config = DatabaseConfig(
    host="prod-db.example.com",
    database="vectordb_prod"
)

print(f"Dev: {dev_config.connection_string}")
print(f"Prod: {prod_config.connection_string}")
```

### Example 4: Using with psycopg2

```python
from core.config import DatabaseConfig
import psycopg2

config = DatabaseConfig()

# Method 1: Connection string
conn = psycopg2.connect(config.connection_string)

# Method 2: Connection parameters (equivalent)
conn = psycopg2.connect(**config.connection_params)

# Execute query
cursor = conn.cursor()
cursor.execute("SELECT version();")
version = cursor.fetchone()
print(f"PostgreSQL version: {version[0]}")

conn.close()
```

## Integration with Vector Store

Typical usage with `PgVectorStore`:

```python
from core.config import DatabaseConfig
from core.pgvector_store import PgVectorStore
from core.bedrock_embeddings import BedrockEmbeddingGenerator

# 1. Setup configuration
db_config = DatabaseConfig()

# 2. Initialise vector store
vector_store = PgVectorStore(config=db_config, table_name="code_embeddings")
vector_store.connect()

# 3. Initialise schema
embedder = BedrockEmbeddingGenerator()
dimension = embedder.get_dimension()
vector_store.initialise_schema(dimension=dimension)

# 4. Store embeddings
content = "Type: class\n@RestController\npublic class HelloController {...}"
embedding = embedder.generate(content)
metadata = {"file_type": "java", "layer": "controller"}

record_id = vector_store.insert_embedding(content, embedding, metadata)
print(f"Stored embedding with ID: {record_id}")

# 5. Clean up
vector_store.close()
```

## Default Configuration

If no environment variables are set, the following defaults are used:

```python
{
    'host': 'localhost',
    'port': 5432,
    'database': 'vectordb',
    'user': 'postgres',
    'password': 'postgres'
}
```

**Note:** Default password `"postgres"` is for local development only. Always use strong passwords in production.

## Error Handling

```python
from core.config import DatabaseConfig
import psycopg2

config = DatabaseConfig()

try:
    conn = psycopg2.connect(config.connection_string)
    print("✅ Connected successfully")
except psycopg2.OperationalError as e:
    print(f"❌ Connection failed: {e}")
    # Check:
    # 1. Is PostgreSQL running?
    # 2. Are credentials correct?
    # 3. Is the database created?
    # 4. Is pgvector extension installed?
```

## Related Documentation

- [Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md) - Generating text embeddings
- [Vector Store](./PGVECTOR_STORE.md) - Storing and searching embeddings
- [Metadata Fields](./METADATA_FIELDS.md) - Metadata schema for code chunks

---

**Module Location:** `core/config.py`
**Dependencies:** `python-dotenv`

---

**Last Updated**: 2025-10-16