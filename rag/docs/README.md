# RAG System Documentation

**Code search powered by semantic embeddings and vector similarity**

---

## 🎯 What This System Does

This RAG (Retrieval Augmented Generation) system enables AI agents to search and understand your codebase through three core capabilities:

### 1️⃣ **Chunk** - Break code into semantic units
Parse codebases using tree-sitter AST analysis to extract classes, methods, API definitions, and documentation into meaningful chunks with rich metadata.

**→** [Scripts Guide](./SCRIPTS_GUIDE.md) - Shell scripts for chunking code

### 2️⃣ **Vectorise** - Convert code to embeddings
Transform code chunks into 1024-dimensional vectors using Amazon Bedrock Titan embeddings, then store in PostgreSQL with pgvector for fast similarity search.

**→** [Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md) - Generate embeddings
**→** [Vector Store](./PGVECTOR_STORE.md) - Store and index embeddings

### 3️⃣ **Retrieve** - Search by semantic meaning
Query the vector database using natural language to find relevant code examples. Combine vector similarity with metadata filters for precise results.

**→** [Strands Usage Guide](./STRANDS_USAGE.md) - AI agent integration
**→** [Retrievals Guide](./RETRIEVALS_GUIDE.md) - Retrieval testing and accuracy

---

## 📚 Documentation Index

### Core Modules
- **[Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md)** - Generate text embeddings using Amazon Bedrock Titan models
- **[Database Configuration](./CONFIG.md)** - PostgreSQL connection setup and environment configuration
- **[Vector Store](./PGVECTOR_STORE.md)** - Store and search embeddings using PostgreSQL with pgvector
- **[Scripts Guide](./SCRIPTS_GUIDE.md)** - Shell scripts and Python modules for chunking and vectorisation
- **[Retrievals Guide](./RETRIEVALS_GUIDE.md)** - Testing and iterating on retrieval accuracy
- **[Metadata Fields Reference](./METADATA_FIELDS.md)** - Metadata schema for code chunks
- **[Strands Usage Guide](./STRANDS_USAGE.md)** - Strands agent framework integration

### Core Concepts
1. **[How Vector Search Works](./qna/01_vector_search_workflow.md)** - Understanding semantic similarity search
2. **[Metadata vs Content](./qna/02_metadata_role.md)** - Role of metadata in filtering results
3. **[Top-K Selection](./qna/03_top_k_selection.md)** - Choosing how many results to retrieve

### Implementation Details
4. **[Metadata in Embeddings](./qna/04_metadata_in_embeddings.md)** - What to include in vectorised content
5. **[Tree-sitter Parsing](./qna/05_tree_sitter_parsing.md)** - AST parsing for code chunking
6. **[pgvector Indexing Strategies](./qna/06_pgvector_indexing.md)** - IVFFlat vs HNSW indexing

### Advanced Techniques
7. **[Weighted Vector Boosting](./qna/07_weighted_boosting.md)** - Prioritising specific code chunks in results

---

## 🚀 Quick Start

```bash
# 1. Chunk your code
cd scripts
./chunk_code.sh

# 2. Vectorise and store
./vectorise_data.sh

# 3. Test retrieval
cd ../strands-agent
python strands_example.py
```

**→** See [Scripts Guide](./SCRIPTS_GUIDE.md) for detailed instructions

---

## 📝 Document Structure

```
docs/
├── README.md                          # This file (main navigation)
├── BEDROCK_EMBEDDINGS.md              # Bedrock Titan embeddings module
├── CONFIG.md                          # Database configuration module
├── PGVECTOR_STORE.md                  # PostgreSQL vector store module
├── SCRIPTS_GUIDE.md                   # Scripts and Python modules guide
├── RETRIEVALS_GUIDE.md                # Retrieval testing and iterations
├── METADATA_FIELDS.md                 # Metadata schema reference
├── STRANDS_USAGE.md                   # Strands framework usage
└── qna/                               # Q&A documents by topic
    ├── 01_vector_search_workflow.md
    ├── 02_metadata_role.md
    ├── 03_top_k_selection.md
    ├── 04_metadata_in_embeddings.md
    ├── 05_tree_sitter_parsing.md
    ├── 06_pgvector_indexing.md
    └── 07_weighted_boosting.md
```

---

**Last Updated**: 2025-10-16
