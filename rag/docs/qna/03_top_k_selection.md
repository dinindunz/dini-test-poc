# Top-K Selection Strategy

[← Back to Documentation Index](../README.md)

**Navigation:** [← Previous: Metadata Role](./02_metadata_role.md) | [Next: Metadata in Embeddings →](./04_metadata_in_embeddings.md)

---

Vector search determines which chunks to send by calculating cosine similarity between the query embedding and all chunk embeddings, then returning only the top K most relevant results (e.g., top 5). Here's how it works in detail:

### 🎯 How Vector Search Works

**Query:**

"Generate the code for java hello world springboot application"

#### Step 1: Query → Embedding

```python
query = "Generate the code for java hello world springboot application"
query_embedding = bedrock.generate(query)  # [0.34, -0.12, 0.88, ...]
```

#### Step 2: Find TOP K Most Similar Chunks

```python
results = vector_store.similarity_search(
    query_embedding=query_embedding,
    top_k=5  # ⚠️ Only get 5 MOST RELEVANT chunks, not all 29!
)
```

#### Step 3: Database Calculates Similarity for ALL Chunks

Database calculates cosine similarity between query and all 29 chunks:

```
Chunk 1 (Application.java):        similarity = 0.92 ⭐ HIGHLY RELEVANT
Chunk 2 (SampleController.java):   similarity = 0.88 ⭐ HIGHLY RELEVANT
Chunk 3 (SampleService.java):      similarity = 0.85 ⭐ HIGHLY RELEVANT
Chunk 4 (SampleRepository.java):   similarity = 0.82 ⭐ HIGHLY RELEVANT
Chunk 5 (SampleResponse.java):     similarity = 0.78 ⭐ HIGHLY RELEVANT
Chunk 6 (api.swagger.yaml):        similarity = 0.65
Chunk 7 (build.gradle):            similarity = 0.55
Chunk 8 (README section 1):        similarity = 0.45
Chunk 9 (README section 2):        similarity = 0.42
...
Chunk 29 (README section 19):      similarity = 0.15 ❌ NOT RELEVANT
```

#### Step 4: Return ONLY Top 5

```python
# Only these 5 chunks are sent to LLM:
[
    {
        "content": "@SpringBootApplication\npublic class Application {...}",
        "metadata": {"file_path": "Application.java", "type": "class"},
        "similarity": 0.92
    },
    {
        "content": "@RestController\npublic class SampleController {...}",
        "metadata": {"file_path": "SampleController.java", "type": "class"},
        "similarity": 0.88
    },
    {
        "content": "@Service\npublic class SampleService {...}",
        "metadata": {"file_path": "SampleService.java", "type": "class"},
        "similarity": 0.85
    },
    {
        "content": "@Repository\npublic class SampleRepository {...}",
        "metadata": {"file_path": "SampleRepository.java", "type": "class"},
        "similarity": 0.82
    },
    {
        "content": "public record SampleResponse(String message) {...}",
        "metadata": {"file_path": "SampleResponse.java", "type": "class"},
        "similarity": 0.78
    }
]
```

### 📊 Why Only Top K?

#### 1. Token Limits 🚫

```
LLM Context Window: 8,000 tokens
29 chunks × 200 tokens/chunk = 5,800 tokens (too much!)
5 chunks × 200 tokens/chunk = 1,000 tokens (perfect!)
```

#### 2. Relevance 🎯

```
Highly relevant chunks (0.8-1.0): Useful for LLM
Moderately relevant (0.5-0.8): Maybe useful
Low relevance (0.0-0.5): Just noise, confuses LLM
```

#### 3. Cost 💰

```
All 29 chunks: $0.05 per query
Top 5 chunks:  $0.01 per query
Savings: 80%!
```

#### 4. Quality ✨

```
More context ≠ Better response
Too much context = LLM gets confused

Best practice: 3-10 most relevant chunks
```

### 🔧 Configurable Top K

When you build the retrieval agent, you can adjust:

```python
# Very specific query - need fewer examples
results = vector_search(query, top_k=3)

# Broad query - need more context
results = vector_search(query, top_k=10)

# Complex query - need comprehensive context
results = vector_search(query, top_k=15)
```

### 📈 Similarity Score Examples

**Query:** "Spring Boot hello world application"

Top results:

```
✅ Application.java (main class)          - 0.92 (sent to LLM)
✅ SampleController.java                  - 0.88 (sent to LLM)
✅ SampleService.java                     - 0.85 (sent to LLM)
✅ SampleRepository.java                  - 0.82 (sent to LLM)
✅ SampleResponse.java                    - 0.78 (sent to LLM)
❌ build.gradle (dependencies)            - 0.55 (NOT sent)
❌ api.swagger.yaml (API spec)            - 0.45 (NOT sent)
❌ README "Prerequisites" section         - 0.25 (NOT sent)
❌ README "Next steps" section            - 0.15 (NOT sent)
```

**Query:** "How to configure Gradle build"

Top results:

```
✅ build.gradle (full config)             - 0.95 (sent to LLM)
✅ build.gradle (dependencies)            - 0.90 (sent to LLM)
✅ README "Build instructions" section    - 0.75 (sent to LLM)
❌ Application.java                       - 0.35 (NOT sent)
❌ SampleController.java                  - 0.30 (NOT sent)
```

### 🎯 Sample Specific Case

For "generate java hello world springboot application":

**What WILL be sent to LLM (top 5):**

1. ✅ Application.java - Main Spring Boot entry point
2. ✅ SampleController.java - REST controller example
3. ✅ SampleService.java - Service layer example
4. ✅ SampleRepository.java - Repository layer example
5. ✅ SampleResponse.java - DTO example

**What WON'T be sent (lower similarity):**

6. ❌ api.swagger.yaml sections (not code)
7. ❌ build.gradle sections (build config, not app code)
8. ❌ README sections 1-19 (documentation, not code)

### 💡 Summary

| Aspect                  | Reality                      |
|-------------------------|------------------------------|
| Total chunks vectorised | 29 chunks                    |
| Chunks searched         | ALL 29 (for similarity calc) |
| Chunks sent to LLM      | Only TOP 5 most relevant     |
| Chunks ignored          | 24 chunks (low similarity)   |

**Key Point:** Vector search is about selective retrieval based on semantic relevance, not dumping everything into the LLM! 🎯
