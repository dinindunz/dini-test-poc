# How Vector Search Works

[← Back to Documentation Index](../README.md)

**Navigation:** [Next: Metadata Role →](./02_metadata_role.md)

---

## Question


How an agent searches for content for a user query.

An agent searches by converting the user query into an embedding vector and performing semantic similarity search against stored code embeddings. Here is the complete workflow:

  🔍 How Vector Search Works

  Step 1: User asks a question

  User: "Create a Spring Boot hello world application"

  Step 2: Convert query to embedding (vector)

  # Agent converts user query to same vector format
  query = "Create a Spring Boot hello world application"
  query_embedding = bedrock.generate(query)  # Returns [0.23, 0.11, -0.45, ...]

  Step 3: Search for similar vectors in database

  # Find chunks with similar embeddings (semantic similarity)
  results = vector_store.similarity_search(
      query_embedding=query_embedding,
      top_k=5,  # Get top 5 most relevant chunks
      metadata_filter={"file_type": "java"}  # Optional: filter by metadata
  )

  Step 4: Database returns ranked results

  results = [
      {
          "id": 42,
          "content": "Type: class\n@SpringBootApplication\npublic class Application {...}",
          "metadata": {
              "module": "01_dini_java17-quickstart-helloworld",
              "file_path": "Application.java",
              "file_type": "java",
              "type": "class",
              "package": "com.example.hello.world"
          },
          "similarity": 0.92  # Very similar!
      },
      {
          "id": 43,
          "content": "Type: class\n@RestController\npublic class SampleController {...}",
          "metadata": {...},
          "similarity": 0.88
      },
      ...
  ]

  Step 5: Agent builds context from results

  context = ""
  for result in results:
      context += f"File: {result['metadata']['file_path']}\n"
      context += f"{result['content']}\n\n"

  Step 6: Agent sends to LLM with context

  prompt = f"""
  You are a Spring Boot expert. Use the following code examples to help answer the question.


  Question: {user_query}

  Generate a complete Spring Boot application based on the examples.
  """

  response = llm.generate(prompt)

  📊 How Each Column Is Used

  | Column    | Purpose                          | Example Usage                         |
  |-----------|----------------------------------|---------------------------------------|
  | embedding | Find semantically similar chunks | WHERE embedding <=> query_vector      |
  | content   | Provide code/context to LLM      | Included in prompt as examples        |
  | metadata  | Filter & organize results        | WHERE metadata->>'file_type' = 'java' |

  🔧 Practical Example

  User Query:

  "How do I create a REST controller in Spring Boot?"

  Vector Search Query:

  SELECT id, content, metadata,
         1 - (embedding <=> '[query_embedding_vector]') as similarity
  FROM code_embeddings
  WHERE metadata->>'file_type' = 'java'  -- Filter: only Java files
    AND metadata->>'type' = 'class'      -- Filter: only classes
  ORDER BY embedding <=> '[query_embedding_vector]'  -- Sort by similarity
  LIMIT 5;

  Retrieved Chunks:

  [
    {
      "content": "@RestController\n@RequestMapping(\"/api/hello\")\npublic class SampleController {...}",
      "metadata": {"file_type": "java", "type": "class", "layer": "controller"},
      "similarity": 0.94
    },
    {
      "content": "@Service\npublic class SampleService {...}",
      "metadata": {"file_type": "java", "type": "class", "layer": "service"},
      "similarity": 0.78
    }
  ]

  Agent's Prompt to LLM:

  Here are relevant code examples from your codebase:

  Example 1 (similarity: 0.94):
  File: SampleController.java
  @RestController
  @RequestMapping("/api/hello")
  public class SampleController {
      @GetMapping
      public SampleResponse getHelloWorld() { ... }
  }

  Example 2 (similarity: 0.78):
  File: SampleService.java
  @Service
  public class SampleService { ... }

  Question: How do I create a REST controller in Spring Boot?

  LLM Response:

  To create a REST controller in Spring Boot, use @RestController annotation:

  @RestController
  @RequestMapping("/api/yourpath")
  public class YourController {
      @GetMapping
      public ResponseType getMethod() {
          // your logic
      }
  }

  🎯 Why This Works

  Embeddings (Semantic Search)

  - Traditional search: Matches keywords only
    - Query: "REST API endpoint" ❌ Won't find "controller"
  - Vector search: Understands meaning
    - Query: "REST API endpoint" ✅ Finds "controller", "service", "endpoint"

  Metadata (Smart Filtering)

  # Example filters
  filter={"file_type": "java"}           # Only Java files
  filter={"type": "class"}               # Only class definitions
  filter={"layer": "controller"}         # Only controller layer
  filter={"module": "quickstart"}        # Only from specific module

  Content (Context for LLM)

  - Provides actual code examples
  - Shows patterns and structure
  - Enables LLM to generate similar, working code

  🔄 Complete Workflow Diagram

  User Query
      ↓
  [Convert to embedding]
      ↓
  [Search vector DB] ← Uses: embeddings (similarity) + metadata (filters)
      ↓
  [Retrieve top K chunks] → Returns: content + metadata + similarity score
      ↓
  [Build context from content]
      ↓
  [Send to LLM with context]
      ↓
  Agent Response

  This is called RAG (Retrieval Augmented Generation) - the agent retrieves relevant code, then generates a response based on that context! 🚀


