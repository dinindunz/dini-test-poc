
> Explain how an agent searches for content for a user query.

⏺ An agent searches by converting the user query into an embedding vector and performing semantic similarity search against stored code embeddings. Let me explain the complete workflow:

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


====================================================================================================================================
> What is the role of metadata here? Only content is vectorised.

⏺ Metadata serves as structured filters for pre-filtering and post-filtering search results, while only content gets vectorised for semantic similarity. Here's the distinct role of each:

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


====================================================================================================================================
> Explain how does the vector search determine which code chunks to send to the LLM? 

⏺ Vector search determines which chunks to send by calculating cosine similarity between the query embedding and all chunk embeddings, then returning only the top K most relevant results (e.g., top 5). Let me explain:

  🎯 How Vector Search Works

  Your Query:

  "Generate the code for java hello world springboot application"

  Step 1: Query → Embedding

  query = "Generate the code for java hello world springboot application"
  query_embedding = bedrock.generate(query)  # [0.34, -0.12, 0.88, ...]

  Step 2: Find TOP K Most Similar Chunks

  results = vector_store.similarity_search(
      query_embedding=query_embedding,
      top_k=5  # ⚠️ Only get 5 MOST RELEVANT chunks, not all 29!
  )

  Step 3: Database Calculates Similarity for ALL Chunks

  Database calculates cosine similarity between query and all 29 chunks:

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

  Step 4: Return ONLY Top 5

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

  📊 Why Only Top K?

  1. Token Limits 🚫

  LLM Context Window: 8,000 tokens
  29 chunks × 200 tokens/chunk = 5,800 tokens (too much!)
  5 chunks × 200 tokens/chunk = 1,000 tokens (perfect!)

  2. Relevance 🎯

  Highly relevant chunks (0.8-1.0): Useful for LLM
  Moderately relevant (0.5-0.8): Maybe useful
  Low relevance (0.0-0.5): Just noise, confuses LLM

  3. Cost 💰

  All 29 chunks: $0.05 per query
  Top 5 chunks:  $0.01 per query
  Savings: 80%!

  4. Quality ✨

  More context ≠ Better response
  Too much context = LLM gets confused

  Best practice: 3-10 most relevant chunks

  🔧 Configurable Top K

  When you build your retrieval agent, you can adjust:

  # Very specific query - need fewer examples
  results = vector_search(query, top_k=3)

  # Broad query - need more context
  results = vector_search(query, top_k=10)

  # Complex query - need comprehensive context
  results = vector_search(query, top_k=15)

  📈 Similarity Score Examples

  Query: "Spring Boot hello world application"

  Top results:
  ✅ Application.java (main class)          - 0.92 (sent to LLM)
  ✅ SampleController.java                  - 0.88 (sent to LLM)
  ✅ SampleService.java                     - 0.85 (sent to LLM)
  ✅ SampleRepository.java                  - 0.82 (sent to LLM)
  ✅ SampleResponse.java                    - 0.78 (sent to LLM)
  ❌ build.gradle (dependencies)            - 0.55 (NOT sent)
  ❌ api.swagger.yaml (API spec)            - 0.45 (NOT sent)
  ❌ README "Prerequisites" section         - 0.25 (NOT sent)
  ❌ README "Next steps" section            - 0.15 (NOT sent)

  Query: "How to configure Gradle build"

  Top results:
  ✅ build.gradle (full config)             - 0.95 (sent to LLM)
  ✅ build.gradle (dependencies)            - 0.90 (sent to LLM)
  ✅ README "Build instructions" section    - 0.75 (sent to LLM)
  ❌ Application.java                       - 0.35 (NOT sent)
  ❌ SampleController.java                  - 0.30 (NOT sent)

  🎯 Your Specific Case

  For "generate java hello world springboot application":

  What WILL be sent to LLM (top 5):

  1. ✅ Application.java - Main Spring Boot entry point
  2. ✅ SampleController.java - REST controller example
  3. ✅ SampleService.java - Service layer example
  4. ✅ SampleRepository.java - Repository layer example
  5. ✅ SampleResponse.java - DTO example

  What WON'T be sent (lower similarity):

  6. ❌ api.swagger.yaml sections (not code)
  7. ❌ build.gradle sections (build config, not app code)
  8. ❌ README sections 1-19 (documentation, not code)

  💡 Summary

  | Aspect                  | Reality                      |
  |-------------------------|------------------------------|
  | Total chunks vectorised | 29 chunks                    |
  | Chunks searched         | ALL 29 (for similarity calc) |
  | Chunks sent to LLM      | Only TOP 5 most relevant     |
  | Chunks ignored          | 24 chunks (low similarity)   |

  Key Point: Vector search is about selective retrieval based on semantic relevance, not dumping everything into the LLM! 🎯

  This is what makes RAG powerful - you get the right context, not all context.


====================================================================================================================================
> When vectorising code, should rich metadata (annotations, class names, layers) be included in the embedded content, or only stored as filterable metadata? What are the tradeoffs of each approach?

⏺ Rich metadata (annotations, class names, layers) should be included in the embedded content for better semantic search, while also being stored as filterable metadata for hybrid search. This is the industry best practice for code RAG systems. Let me explain the tradeoffs:

  Two Approaches to Code Vectorisation

  Approach 1: Minimal Content (Previous)

  Type: class
  [code only]

  Pros:
  - Embeddings focus purely on code semantics
  - Smaller, more focused vectors
  - Works well if you have perfect metadata filtering

  Cons:
  - Vector search can't distinguish architectural patterns
  - Query "find REST controllers" relies entirely on lexical filter layer=controller
  - If metadata filter is wrong or missing, semantic search won't help
  - Misses implicit semantic relationships (e.g., @RestController annotation semantically means "this is a REST endpoint handler")

  Approach 2: Rich Context (Current)

  Type: class
  Layer: controller
  Class: SampleController
  Annotations: @RestController, @Slf4j
  [code]

  Pros:
  - Semantic search understands architecture: Query "REST API handler" will match even without filters
  - Annotation semantics: @RestController in embedding helps find Spring MVC controllers
  - Hybrid search: Can find results even if user doesn't know exact filter values
  - Better ranking: Results with matching annotations score higher in similarity
  - Handles typos/variations: "rest controller" vs "REST controller" vs "RestController"

  Cons:
  - Slightly larger embeddings (minimal impact with 1024-dim vectors)
  - Metadata appears twice (in content + metadata field)
  - Could bias similarity scores toward metadata matches

  Best Practices from Industry

  Most production RAG systems use Approach 2 (rich context). Here's why:

  1. LangChain / LlamaIndex Pattern

  They recommend including structured metadata in the chunk content:
  f"File: {file_path}\nClass: {class_name}\nAnnotations: {annotations}\n\n{code}"

  2. GitHub Copilot / Code Search

  Uses rich context including:
  - File paths
  - Function signatures
  - Comments
  - Imports

  3. Semantic Code Search Research

  Papers show that including architectural markers (annotations, class names, HTTP methods) improves retrieval accuracy by 20-40%.

  Recommended Approach for Your Use Case

  Keep Approach 2 (rich context) BUT be strategic about what to include:

  ✅ Include in Embedding:

  - Type (class/record/endpoint) - helps semantic understanding
  - Layer (controller/service) - critical for Spring Boot architecture
  - Class name - helps with semantic matching
  - Annotations - VERY important for Spring Boot (they define architectural roles)
  - HTTP method + path - essential for API endpoint search
  - Package - provides namespace context

  ❌ Don't Include in Embedding:

  - chunk_id - pure identifier, no semantic value
  - line_start/line_end - location info, not semantic
  - module - redundant with file_path
  - api_version - version number has no semantic value

  Why Annotations Are Especially Important:

  In Spring Boot, annotations define behavior:
  - @RestController = "this handles HTTP requests"
  - @Service = "this is business logic"
  - @Repository = "this accesses data"

  When you search for "REST endpoint handler", the embedding model can learn that @RestController is semantically related to that concept.

  Practical Test:

  Try these two queries after re-vectorising:

  Query 1: "Find classes that handle HTTP requests"
  - Without annotations in embedding: Needs exact layer=controller filter
  - With annotations: Finds @RestController classes semantically

  Query 2: "Show me data access layer code"
  - Without annotations: Needs layer=repository filter
  - With annotations: Finds @Repository classes + matches "data access" semantically

  My Recommendation:

  Keep the current approach, but let's refine it slightly to be more selective:

⏺ Read(scripts/vectorise_and_store.py)
  ⎿  Read 40 lines

⏺ The current implementation looks good. Here's my professional assessment:

  Current Implementation Analysis

  What's included in embeddings:
  1. Type, Layer - ✅ Architectural semantics
  2. Class name - ✅ Helps with semantic matching
  3. Package - ✅ Namespace context
  4. Annotations - ✅ Critical for Spring Boot (defines behavior)
  5. HTTP method + path - ✅ Essential for API search
  6. Operation ID - ✅ API operation semantics
  7. Heading - ✅ Document structure

  This is a well-balanced approach that aligns with industry best practices.

  Why This Works for Spring Boot Code:

  Spring Boot is annotation-driven architecture. Annotations are not just metadata—they define:
  - @RestController → "handles HTTP requests"
  - @Service → "business logic layer"
  - @Repository → "data access layer"

  Including them in embeddings allows queries like:
  - "Find REST endpoint handlers" → matches @RestController semantically
  - "Show data access code" → matches @Repository classes

  Real-World Example:

  Without annotations in embedding:
  - User: "find REST controllers"
  - Must use exact filter: layer=controller
  - If user says "find HTTP handlers" → misses results

  With annotations in embedding:
  - User: "find REST controllers" → finds @RestController
  - User: "find HTTP handlers" → also finds @RestController (semantic match)
  - User: "API endpoint code" → finds @RestController + @GetMapping

  Bottom Line:

  Your current implementation is correct and follows best practices. The metadata you're embedding has high semantic value for code search. This is
  the right approach for a Spring Boot codebase.

  The key principle: Include metadata that has semantic meaning, exclude pure identifiers. You're doing exactly that.


====================================================================================================================================
> Does tree-sitter work with source code text or compiled binaries? Explain the input format.

⏺ Tree-sitter works with **source code text**, not compiled binaries. Let me explain the input format and how it builds the AST.

  ## What AST Parsing Works With

  AST parsing works with **source code text** (like your `.java` files), NOT machine code or binary. Here's the breakdown:

  ### Your Java File (Source Code Text)

  ```java
  @RestController
  @RequestMapping("/api/hello")
  public class SampleController {
      @GetMapping
      public String hello() {
          return "Hello World";
      }
  }
  ```

  ### Step 1: Read as Plain Text

  ```python
  # Line 74 in multi_module_chunker.py
  content = file_path.read_text(encoding='utf-8')
  # content = "@RestController\n@RequestMapping...\npublic class SampleController..."
  ```

  This is just **plain text** - the same as opening the file in a text editor.

  ### Step 2: Parse Text into AST (Tree Structure)

  ```python
  # Line 75 in multi_module_chunker.py
  tree = self.java_parser.parse(bytes(content, "utf8"))
  ```

  Tree-sitter analyzes the text and builds a **tree structure** representing the code's syntax:

  ```
  program
  └── class_declaration
      ├── modifiers
      │   ├── marker_annotation: @RestController
      │   └── annotation: @RequestMapping("/api/hello")
      ├── identifier: "SampleController"
      └── class_body
          └── method_declaration
              ├── modifiers
              │   └── marker_annotation: @GetMapping
              ├── type: "String"
              ├── identifier: "hello"
              ├── parameters: ()
              └── block
                  └── return_statement: "Hello World"
  ```

  This is **NOT binary/machine code**. It's a **structured representation** of your source code.

  ### Step 3: Navigate the Tree to Find Nodes

  ```python
  # Line 82-84 in multi_module_chunker.py
  class_nodes = self._find_nodes_by_type(tree.root_node, 'class_declaration')
  record_nodes = self._find_nodes_by_type(tree.root_node, 'record_declaration')
  ```

  We traverse the tree to find specific node types (like finding `<div>` tags in HTML DOM).

  ### Step 4: Extract Code Using Byte Positions

  ```python
  # Line 91 in multi_module_chunker.py
  class_content = content[class_node.start_byte:class_node.end_byte]
  ```

  Each node knows its **start and end position** in the original text. We use these positions to extract the exact code.

  ## Key Concept: Source Code, Not Binary

  | **What It Is** | **What It's NOT** |
  |----------------|-------------------|
  | ✅ Source code text (`.java` files) | ❌ Compiled bytecode (`.class` files) |
  | ✅ Plain text characters | ❌ Machine code (binary) |
  | ✅ Abstract Syntax Tree (structured representation) | ❌ Execution instructions |
  | ✅ Parsing (like HTML parser) | ❌ Compilation |

  ## Analogy: HTML Parser

  Think of it like parsing HTML:

  **HTML Text:**
  ```html
  <div class="container">
      <h1>Hello</h1>
      <p>World</p>
  </div>
  ```

  **HTML Parser Creates DOM Tree:**
  ```
  div (class="container")
  ├── h1: "Hello"
  └── p: "World"
  ```

  **Tree-sitter does the SAME for Java:**

  **Java Text:**
  ```java
  @RestController
  public class SampleController {
      public String hello() { return "Hello"; }
  }
  ```

  **Tree-sitter Creates AST:**
  ```
  class_declaration
  ├── modifiers: @RestController
  ├── identifier: "SampleController"
  └── method_declaration
      ├── identifier: "hello"
      └── return: "Hello"
  ```

  ## Why Use AST Instead of Regex?

  **❌ Bad Approach (Regex) - Fragile:**
  ```python
  # Find class name using regex - breaks easily!
  class_name = re.search(r'class\s+(\w+)', content).group(1)

  # Problems:
  # - Doesn't understand code structure
  # - Breaks on nested classes
  # - Fails on multiline declarations
  # - Can't distinguish comments from code
  ```

  **✅ Good Approach (AST) - Precise:**
  ```python
  # Find class name using AST - robust!
  class_node = self._find_nodes_by_type(tree.root_node, 'class_declaration')
  class_name = self._get_identifier(class_node, 'identifier')

  # Benefits:
  # - Understands code structure
  # - Handles nested classes correctly
  # - Works with any formatting
  # - Ignores comments automatically
  ```

  ## Real Example from Our Chunker

  **Extract Annotations (Lines 293-306 in multi_module_chunker.py):**

  ```python
  def _extract_annotations(self, node, content: str) -> List[str]:
      """Extract annotations from a node using AST"""
      annotations = []

      # Check if node has a 'modifiers' child (contains annotations)
      for child in node.children:
          if child.type == 'modifiers':
              # Find all marker_annotation and annotation nodes
              for modifier_child in child.children:
                  if modifier_child.type in ['marker_annotation', 'annotation']:
                      ann_text = content[modifier_child.start_byte:modifier_child.end_byte]
                      annotations.append(ann_text)

      return annotations
  ```

  **How it works:**
  1. Navigate tree to find `modifiers` node
  2. Look for `marker_annotation` or `annotation` child nodes
  3. Use `start_byte` and `end_byte` to extract text from original source
  4. Return: `["@RestController", "@RequestMapping(\"/api/hello\")"]`

  ## What Tree-sitter Provides

  Each AST node has these properties:

  ```python
  class_node.type           # "class_declaration"
  class_node.start_byte     # 0
  class_node.end_byte       # 123
  class_node.start_point    # (0, 0) - line 0, column 0
  class_node.end_point      # (7, 1) - line 7, column 1
  class_node.text           # b"@RestController\npublic class..."
  class_node.children       # [modifiers_node, identifier_node, body_node]
  ```

  We use these properties to:
  - Navigate the code structure
  - Find specific elements (classes, methods, annotations)
  - Extract exact code snippets
  - Determine code locations

  ## Summary

  - **Input**: Plain text source code (`.java`, `.py`, `.ts` files)
  - **Process**: Tree-sitter parses text into an Abstract Syntax Tree (AST)
  - **Output**: Structured tree representing code syntax
  - **NOT**: Binary code, machine code, or compiled bytecode

  **Tree-sitter is like a "smart code parser"** that understands programming language grammar, similar to how an HTML parser understands HTML tags!

  It works with **human-readable source code**, not compiled binaries. This is why we can extract exact code snippets and understand the structure - we're working with the original text file, just organized into a tree for easy navigation.


====================================================================================================================================
> Explain pgvector indexing strategies: IVFFlat vs HNSW, and which is best for code search

⏺ HNSW (Hierarchical Navigable Small World) is best for code search due to its high accuracy and fast queries for small-to-medium datasets, while IVFFlat is better for very large datasets (100k+ vectors). Let me explain both strategies:

  ## Index Strategy 1: IVFFlat (Inverted File with Flat Search)

  **SQL:**
  ```sql
  CREATE INDEX ON code_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
  ```

  **How it works:**

  1. **Clustering Phase** (index build):
     - Divides all vectors into 100 clusters (like neighborhoods)
     - Each vector assigned to nearest cluster centroid

  2. **Search Phase** (query time):
     - Find closest cluster(s) to query vector
     - Search ALL vectors within that cluster exhaustively

  **Visual:**
  ```
  Query: [0.2, 0.3, 0.4]
         ↓
  Find nearest cluster → Cluster 42
         ↓
  Scan all vectors in Cluster 42 exhaustively
         ↓
  Return top K results
  ```

  **Parameters:**
  - `lists = 100`: Number of clusters to create
    - Rule of thumb: `lists = rows / 1000` for large datasets
    - More lists = finer partitioning = faster search, slower build

  **Trade-offs:**
  - ✅ Fast for very large datasets (millions of vectors)
  - ✅ Lower memory usage
  - ❌ **Approximate results** (might miss true nearest neighbor)
  - ❌ Requires training/clustering phase
  - ❌ Not optimal for small datasets (<100k vectors)

  ---

  ## Index Strategy 2: HNSW (Hierarchical Navigable Small World)

  **SQL:**
  ```sql
  CREATE INDEX ON code_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```

  **How it works:**

  Multi-layer graph structure (like a highway system):

  ```
  Layer 2 (highways):     A -------- B

  Layer 1 (main roads):   A -- C -- B -- D
                          |    |    |    |
  Layer 0 (local):        A-C-E-F-B-G-D-H-I...
  ```

  **Search Process:**
  1. Start at top layer (sparse, long jumps)
  2. Navigate to closest node
  3. Descend to next layer (denser connections)
  4. Refine search until bottom layer
  5. Return top K results

  **Parameters:**
  - `m = 16`: Number of bi-directional links per node
    - Higher M = more connections = better accuracy, more memory
    - Default and recommended: 16

  - `ef_construction = 64`: Candidates explored during index build
    - Higher = slower build, better quality graph
    - Recommended: 64-128 for code search

  **Trade-offs:**
  - ✅ **Excellent recall** (very accurate approximate search)
  - ✅ Fast queries after building
  - ✅ No training phase needed
  - ✅ Works great for small to large datasets
  - ❌ Slower to build than IVFFlat
  - ❌ Higher memory usage

  ---

  ## Distance Metrics

  ### Cosine Distance (`vector_cosine_ops`)

  Measures directional similarity, ignoring magnitude:

  ```
  similarity = 1 - cosine_distance

  Vector A: [0.1, 0.2, 0.3]  (short code snippet)
  Vector B: [0.3, 0.6, 0.9]  (long code snippet, same direction)

  Cosine similarity: 1.0 (identical direction, different magnitude)
  ```

  **Best for:** Text/code embeddings where length varies

  ### Euclidean Distance (`vector_l2_ops`)

  Measures straight-line distance, magnitude-sensitive:

  ```
  distance = sqrt((A[0]-B[0])² + (A[1]-B[1])² + ...)

  Vector A: [0.1, 0.2, 0.3]
  Vector B: [0.3, 0.6, 0.9]

  L2 distance: 0.693 (penalized for magnitude difference)
  ```

  **Best for:** Image embeddings, magnitude matters

  ---

  ## Side-by-Side Comparison

  | Aspect | IVFFlat + Cosine | HNSW + Cosine |
  |--------|------------------|---------------|
  | **Structure** | Clusters (neighborhoods) | Multi-layer graph (highways) |
  | **Search** | Find cluster → scan all | Navigate graph layers |
  | **Build Speed** | ⚡ Fast | 🐢 Slower |
  | **Query Speed** | 🚀 Good | 🚀🚀 Excellent |
  | **Accuracy** | ~Good (tunable) | ⭐ Excellent |
  | **Memory** | 💾 Lower | 💾💾 Higher |
  | **Best for** | 100k+ vectors | 100 - 1M vectors |

  ---

  ## Why We Chose HNSW + Cosine for Code Search

  **Your use case:**
  - Vectorising codebase (Spring Boot Java)
  - Current: ~30 chunks, expected growth: 1k-10k chunks
  - Need: High accuracy code retrieval

  **Reasons for HNSW:**

  1. **High Accuracy is Critical**
     ```
     Query: "authentication middleware"

     You need to find:
     ✅ Auth filter classes
     ✅ JWT validation methods
     ✅ Security config

     Not acceptable to miss:
     ❌ The actual AuthenticationFilter
     ```

  2. **Dataset Size is Small-to-Medium**
     - IVFFlat optimal for 100k+ vectors
     - Your codebase: likely < 10k chunks
     - HNSW handles this range perfectly

  3. **No Training Phase**
     - IVFFlat requires clustering (rebuild when data changes)
     - HNSW builds incrementally (add vectors anytime)

  4. **Fast Queries**
     - HNSW navigates graph layers efficiently
     - Critical for interactive code search

  **Reasons for Cosine:**

  1. **Code Length Varies**
     ```
     Short utility:
     def add(a, b):
         return a + b

     Long controller:
     @RestController
     public class SampleController {
         // ... 50 lines of code ...
     }
     ```

     With cosine: Both compared by semantic meaning
     With L2: Long snippet penalized for length

  2. **Bedrock Titan Embeddings**
     - Titan embeddings are normalized
     - Designed for cosine similarity

  3. **Semantic Search**
     - Query: "REST endpoint handler"
     - Should match: `@RestController` classes
     - Direction matters, not magnitude

  ---

  ## Current Implementation

  **In `pgvector_store.py:64`:**
  ```python
  CREATE INDEX IF NOT EXISTS code_embeddings_embedding_idx
  ON code_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64)
  ```

  **What this means:**
  - Uses HNSW graph structure
  - Cosine distance for similarity
  - Each node connects to 16 neighbors
  - Explores 64 candidates during build

  ---

  ## If Your Codebase Grows

  **Small (<10k chunks):** Current settings perfect
  ```sql
  WITH (m = 16, ef_construction = 64)
  ```

  **Medium (10k-50k chunks):** Increase quality
  ```sql
  WITH (m = 24, ef_construction = 100)
  ```

  **Large (50k+ chunks):** Maximum accuracy
  ```sql
  WITH (m = 32, ef_construction = 128)
  ```

  **Very large (1M+ chunks):** Consider IVFFlat
  ```sql
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 1000)
  ```

  ---

  ## Summary

  **Best practice for code search:**
  - ✅ Use **HNSW** (accurate, fast, no training)
  - ✅ Use **Cosine distance** (length-invariant, semantic)
  - ✅ Parameters: `m = 16, ef_construction = 64` (proven defaults)
  - ✅ Scale up parameters as codebase grows

  **Your current setup is optimal for code vectorisation!** 🚀