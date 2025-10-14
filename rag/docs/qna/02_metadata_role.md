# Metadata Role in Vector Search

[← Back to Documentation Index](../README.md)

**Navigation:** [← Previous: Vector Search Workflow](./01_vector_search_workflow.md) | [Next: Top-K Selection →](./03_top_k_selection.md)

---

## Question

What is the role of metadata here? Only content is vectorised.

Metadata serves as structured filters for pre-filtering and post-filtering search results, while only content gets vectorised for semantic similarity. Here's the distinct role of each:

  🎯 Clear Separation of Concerns

  Content (Vectorised) ✅

  content = "Type: class\n@RestController\npublic class SampleController {...}"
  embedding = bedrock.generate(content)  # [0.23, 0.11, -0.45, ...]
  Role: Semantic similarity matching

  Metadata (NOT Vectorised) ❌

  metadata = {
      "file_type": "java",
      "module": "quickstart",
      "type": "class",
      "layer": "controller"
  }
  Role: Filtering, organization, attribution

  🔍 Why Keep Metadata Separately?

  1. Pre-filtering (Performance)

  # BAD: Search all 10,000 chunks, then filter
  results = vector_search(query)  # Search 10,000 embeddings
  filtered = [r for r in results if r.metadata['file_type'] == 'java']

  # GOOD: Filter first, then search smaller set
  results = vector_search(query, filter={"file_type": "java"})  # Search only 2,000 Java chunks

  2. Post-filtering (Precision)

  # Get semantically similar chunks
  results = vector_search("create REST endpoint", top_k=20)

  # Then filter by exact criteria
  controller_examples = [r for r in results if r.metadata['layer'] == 'controller']

  3. Attribution & Context (Transparency)

  # Tell user WHERE the code came from
  for result in results:
      print(f"Found in: {result.metadata['file_path']}")
      print(f"Module: {result.metadata['module']}")
      print(f"Type: {result.metadata['type']}")

  4. Faceted Search (Hybrid Approach)

  # Combine semantic search + structured filters
  results = vector_search(
      query="authentication logic",
      filter={
          "file_type": "java",      # Must be Java
          "layer": "service",        # Must be service layer
          "module": "auth-module"    # Must be from auth module
      }
  )

  📊 Real-World Example

  Scenario: "Show me REST controllers"

  Without Metadata (Bad) ❌

  # Search all chunks for "REST controller"
  results = vector_search("REST controller", top_k=10)

  # Results might include:
  # - Service classes (similar semantically but wrong layer)
  # - YAML configs mentioning "controller"
  # - Documentation about controllers
  # - Non-controller Java files

  With Metadata (Good) ✅

  # Semantic search + metadata filter
  results = vector_search(
      query="REST controller",
      filter={
          "file_type": "java",
          "type": "class",
          "layer": "controller"  # EXACT filter
      }
  )

  # Results are ONLY actual controller classes!

  🎪 Metadata Use Cases

  Use Case 1: Module Isolation

  # Only search within specific project
  filter={"module": "01_dini_java17-quickstart-helloworld"}

  Use Case 2: File Type Selection

  # User asks: "Show me the API spec"
  filter={"file_type": "swagger"}

  # User asks: "Show me the build config"
  filter={"file_type": "gradle"}

  Use Case 3: Layer-based Retrieval

  # User asks: "How do I structure my service layer?"
  filter={"layer": "service"}

  # User asks: "Show me repository examples"
  filter={"layer": "repository"}

  Use Case 4: Reranking & Scoring

  # Get similar chunks
  results = vector_search(query, top_k=20)

  # Boost score for specific file types
  for result in results:
      if result.metadata['file_type'] == 'java':
          result.score *= 1.2  # Prefer Java examples
      if result.metadata['layer'] == 'controller':
          result.score *= 1.5  # Prefer controllers

  🔬 SQL Query Breakdown

  SELECT
      content,           -- For LLM context
      metadata,          -- For filtering & attribution
      embedding <=> query_vector as distance  -- For similarity ranking
  FROM code_embeddings
  WHERE
      -- Metadata filters (exact match, fast!)
      metadata->>'file_type' = 'java'
      AND metadata->>'layer' = 'controller'
  ORDER BY
      -- Vector similarity (semantic search)
      embedding <=> query_vector
  LIMIT 5;

  ⚡ Performance Benefit

  ❌ Without metadata filtering:
  Vector search: 10,000 chunks → 2.5 seconds
  Post-filter: 10,000 → 50 results

  ✅ With metadata filtering:
  Pre-filter: 10,000 → 500 chunks (metadata index)
  Vector search: 500 chunks → 0.3 seconds
  Results: 50 results

  Speed improvement: 8x faster! 🚀

  🎯 Summary

  | Aspect      | Content (Vectorised)               | Metadata (Not Vectorised) |
  |-------------|------------------------------------|---------------------------|
  | Purpose     | Semantic similarity                | Exact filtering           |
  | Search type | Fuzzy/semantic                     | Precise/structured        |
  | Example     | "REST endpoint" finds "controller" | file_type == "java"       |
  | Speed       | Slower (vector math)               | Faster (index lookup)     |
  | Use         | "What is it about?"                | "Where is it from?"       |

  Analogy:
  - Embedding = Google search (finds similar meaning)
  - Metadata = Advanced filters (file type, date, site, etc.)

  Both together = Powerful hybrid search! 🎉


