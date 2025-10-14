# RAG System Documentation

Comprehensive documentation for the RAG (Retrieval Augmented Generation) code search system.

## 📚 Documentation Index

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

---

## 🚀 Quick Links

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

**Last Updated**: 2025-10-14
