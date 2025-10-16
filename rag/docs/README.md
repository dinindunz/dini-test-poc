# RAG System Documentation

Comprehensive documentation for the RAG (Retrieval Augmented Generation) code search system.

## 📚 Documentation Index

### Core Modules
- **[Bedrock Embeddings](./BEDROCK_EMBEDDINGS.md)**
  Generate text embeddings using Amazon Bedrock Titan models

- **[Database Configuration](./CONFIG.md)**
  PostgreSQL connection setup and environment configuration

- **[PostgreSQL Vector Store](./PGVECTOR_STORE.md)**
  Store and search embeddings using PostgreSQL with pgvector

- **[S3 Vector Store](./S3_VECTOR_STORE.md)**
  Store and search embeddings using Amazon S3 Vectors

### Core Concepts
1. **[How Vector Search Works](./qna/01_vector_search_workflow.md)**
   Understanding how agents search for content using embeddings and semantic similarity

2. **[Metadata vs Content](./qna/02_metadata_role.md)**
   The role of metadata in filtering and organising search results

3. **[Top-K Selection](./qna/03_top_k_selection.md)**
   How vector search determines which code chunks to send to the LLM

### Implementation Details
4. **[Metadata in Embeddings](./qna/04_metadata_in_embeddings.md)**
   Should rich metadata be included in vectorised content? Tradeoffs explained

5. **[Tree-sitter Parsing](./qna/05_tree_sitter_parsing.md)**
   Understanding AST parsing with source code vs compiled binaries

6. **[pgvector Indexing Strategies](./qna/06_pgvector_indexing.md)**
   IVFFlat vs HNSW - which is best for code search?

### Advanced Techniques
7. **[Weighted Vector Boosting](./qna/07_weighted_boosting.md)**
   Applying weights to prioritise specific code chunks in search results

8. **[S3 Vectors Metadata Limitations](./qna/08_s3_vectors_metadata_limits.md)**
   Understanding and working with S3 Vectors' 10-key and 2048-byte metadata limits

---

## 🚀 Quick Links

- [Vectorisation Scripts](../scripts/README.md) - Shell scripts for easy vectorisation
- [Metadata Fields Reference](./METADATA_FIELDS.md)
- [Strands Usage Guide](./STRANDS_USAGE.md)

---

## 📖 How to Use This Documentation

Each Q&A document follows this structure:
- **Question**: Clear, specific question
- **Quick Answer**: Direct answer in the opening paragraph
- **Detailed Explanation**: In-depth explanation with examples
- **Code Examples**: Practical implementation snippets
- **Visual Diagrams**: Where applicable

---

## 🔄 Navigation Tips

- Use the **Documentation Index** above to jump to specific topics
- Each document is self-contained and can be read independently
- Code examples are provided in Python with SQL where relevant
- All examples use Australian English spelling

---

## 📝 Document Structure

```
docs/
├── README.md                          # This file (main navigation)
├── BEDROCK_EMBEDDINGS.md              # Bedrock Titan embeddings module
├── CONFIG.md                          # Database configuration module
├── PGVECTOR_STORE.md                  # PostgreSQL vector store module
├── S3_VECTOR_STORE.md                 # Amazon S3 vector store module
├── METADATA_FIELDS.md                 # Metadata schema reference
├── STRANDS_USAGE.md                   # Strands framework usage
└── qna/                               # Q&A documents by topic
    ├── 01_vector_search_workflow.md
    ├── 02_metadata_role.md
    ├── 03_top_k_selection.md
    ├── 04_metadata_in_embeddings.md
    ├── 05_tree_sitter_parsing.md
    ├── 06_pgvector_indexing.md
    ├── 07_weighted_boosting.md
    └── 08_s3_vectors_metadata_limits.md
```

---

**Last Updated**: 2025-10-16
