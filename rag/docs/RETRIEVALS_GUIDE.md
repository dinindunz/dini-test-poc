# Retrievals Guide

**[← Back to Main Documentation](./README.md)**

Testing and iterating on retrieval accuracy with metadata enhancements.

---

## 📋 Overview

This guide documents the evolution of our retrieval system through iterative testing. Each iteration demonstrates how changes to metadata storage and embedding content impact search accuracy and filtering capabilities.

The retrievals folder contains detailed records of each iteration, including:
- Full context and commit information
- Vectorised content structure
- Metadata stored in the database
- Complete test outputs with SQL queries
- Key improvements and issues identified

---

## 🔄 Iterations

### Iteration One: Basic Vectorisation

**File:** [`../retrievals/iteration_one.md`](../retrievals/iteration_one.md)

**Focus:** Minimal chunk content with basic metadata

**Key Characteristics:**
- Embedded content: `Type: class\n[code only]`
- Basic metadata fields only
- Missing: layer, class_name, annotations, chunk_id

**Critical Issue:**
- ❌ Filter by `layer=controller` returned **0 results**
- Metadata fields weren't being stored in the database
- Limited semantic search due to sparse embedded content

**Lesson Learned:** Metadata must be explicitly stored to enable filtering

---

### Iteration Two: Metadata Enhancement

**File:** [`../retrievals/iteration_two.md`](../retrievals/iteration_two.md)

**Focus:** Enriched vectorisation with comprehensive metadata

**Key Improvements:**
- Embedded content includes: Type, Layer, Class, Package, Annotations
- Comprehensive metadata: Core + Java + API + Docs fields
- All metadata fields properly stored in JSONB column

**Success Metrics:**
- ✅ Filter by `layer=controller` returned **1 result** (SampleController)
- ✅ Successful metadata filtering with pgvector
- ✅ Better semantic search due to richer embedded content

**Lesson Learned:** Rich metadata in both embeddings and database storage enables accurate hybrid search

---

## 📊 Comparison

| Aspect | Iteration One | Iteration Two |
|--------|---------------|---------------|
| **Embedded Content** | `Type: class\n[code]` | `Type, Layer, Class, Package, Annotations\n[code]` |
| **Metadata Storage** | Basic fields only | Core + Java + API + Docs fields |
| **Layer Filter** | ❌ 0 results | ✅ 1 result (correct) |
| **Semantic Search** | Limited context | Enhanced context |
| **Hybrid Search** | Not functional | ✅ Functional |

---

## 🎯 Key Takeaways

### 1. Metadata is Critical
Storing rich metadata enables precise filtering alongside semantic search. Without it, you can't filter by architectural layer, class name, or other structural attributes.

### 2. Hybrid Search = Vector + Metadata
The best results come from combining:
- **Semantic similarity** (vector embeddings)
- **Lexical filtering** (JSONB metadata queries)

### 3. Embed the Context
Including metadata in the embedded content (Type, Layer, Package, etc.) improves semantic search by providing context to the embedding model.

---

## 🔍 Testing Approach

Each iteration follows this pattern:

1. **Vectorise** code chunks with specific metadata strategy
2. **Store** embeddings and metadata in PostgreSQL pgvector
3. **Test** retrieval with various queries and filters
4. **Document** complete output including SQL queries
5. **Analyse** results and identify improvements
6. **Iterate** with enhanced approach

---

## 📁 Detailed Iteration Files

For complete test outputs, SQL queries, and comprehensive analysis:

- [Iteration One: Basic Vectorisation](../retrievals/iteration_one.md)
- [Iteration Two: Metadata Enhancement](../retrievals/iteration_two.md)

Each file contains:
- Full context and commit SHA
- Vectorised content structure
- Metadata schema stored
- Complete strands_example.py output
- SQL queries with results
- Key improvements and issues

---

## 🚀 Running Your Own Tests

To test retrieval with the current codebase:

```bash
cd strands-agent
python strands_example.py
```

This will:
1. Connect to your PostgreSQL vector store
2. Run test queries with various filters
3. Display results with similarity scores
4. Show SQL queries being executed

---

## 📚 Related Documentation

- [Main Documentation](./README.md) - Complete RAG system documentation
- [Scripts Guide](./SCRIPTS_GUIDE.md) - Chunking and vectorisation pipeline
- [Metadata Fields Reference](./METADATA_FIELDS.md) - Complete metadata schema
- [PostgreSQL Vector Store](./PGVECTOR_STORE.md) - Vector storage implementation
- [Strands Usage Guide](./STRANDS_USAGE.md) - Agent framework integration

---

**Last Updated:** 2025-10-16
