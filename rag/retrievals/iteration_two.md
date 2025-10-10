# Iteration Two - After Metadata Enhancement

**Context:** Enriched vectorisation with comprehensive metadata
**Commit:** a74674b309ad062d00b976dc1a8a03a551e0d55c
**Vectorised Content:**
```
Type: class
Layer: controller
Class: SampleController
Package: com.example.hello.world.controller
Annotations: @Slf4j, @RestController, @RequiredArgsConstructor, @RequestMapping("/api/hello")
[code]
```

**Metadata Stored:**
- Core: `module`, `file_path`, `file_type`, `type`, `layer`, `chunk_id`
- Java: `class_name`, `package`, `annotations`
- API: `http_method`, `api_path`, `operation_id`, `schema_name`
- Docs: `document_name`, `heading`, `heading_level`

**Key Improvements:**
- Metadata filter `layer=controller` now returns **1 result** (SampleController)
- Content includes architectural context (layer, annotations, class name)
- Better semantic search due to richer embedded content

---

➜ python strands_example.py                

============================================================
Example 3: Using filters
============================================================
I'll search for Java controller class examples to show you how REST controllers are structured in this codebase.
Tool #1: retrieve_code_examples

======================================================================
🔍 RETRIEVAL TOOL EXECUTION
======================================================================
📝 Query: REST controller classes
🔢 Top K: 7
🔧 Filters: file_type=java, module=None, layer=controller, class_name=None, http_method=None

⚙️  Initialising components...
✅ Connected to PostgreSQL database: postgres
✅ Connected to vector database

🧮 Generating query embedding...
✅ Query vector dimension: 1024
📊 Query vector sample (first 5 values): [-0.079744853079319, -0.009282239712774754, 0.016573728993535042, -0.0173997413367033, 0.01244961004704237]

🔍 Applying metadata filters: {'file_type': 'java', 'layer': 'controller'}

🔎 Searching vector database...

======================================================================
🔎 SQL QUERY
======================================================================

                SELECT id, content, metadata, embedding,
                       1 - (embedding <=> %s) as similarity
                FROM code_embeddings
             WHERE metadata->>'file_type' = %s AND metadata->>'layer' = %s ORDER BY embedding <=> %s LIMIT %s

📋 Query Parameters:
  - Vector dimension: 1024
  - Top K: 7
  - Metadata filters: {'file_type': 'java', 'layer': 'controller'}

💡 Search Strategy:
  - Semantic Search: Using cosine similarity (embedding <=> vector)
  - Distance Operator: '<=' (cosine distance)
  - Similarity Metric: 1 - cosine_distance (higher = more similar)
  - Lexical Filter: JSONB metadata filtering on ['file_type', 'layer']
======================================================================

✅ Found 1 results
✅ Database connection closed

======================================================================
📊 RESULTS DETAILS
======================================================================

--- Result #1 ---
  📏 Similarity Score: 0.4228
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/controller/SampleController.java
  🏷️  Type: class
  🎯 Layer: controller
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: 01_dini_java17-quickstart-helloworld_2
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.09724753350019455, 0.009402425028383732, 0.025289280340075493, -0.05042288079857826, 0.03419797495007515]
  📝 Content preview: Type: class
Layer: controller
Class: SampleController
Package: com.example.hello.world.controller
An...

======================================================================
Based on the search results, here's an example of how REST controllers are structured in this codebase:

## REST Controller Structure

The codebase shows a clean and well-structured approach to REST controllers:

### **SampleController Example**

```java
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/hello")
public class SampleController {

    private final SampleService sampleService;

    @GetMapping
    public SampleResponse getHelloWorld() {
        log.info("Received request for hello world");
        return sampleService.getHelloWorld();
    }
}
```

### **Key Structure Elements:**

1. **Class-level Annotations:**
   - `@RestController` - Marks this as a REST controller
   - `@RequestMapping("/api/hello")` - Base path for all endpoints in this controller
   - `@RequiredArgsConstructor` - Lombok annotation for dependency injection
   - `@Slf4j` - Lombok annotation for logging

2. **Dependency Injection:**
   - Uses constructor injection with `private final` fields
   - Service layer dependency (`SampleService`) injected via constructor

3. **Method Structure:**
   - `@GetMapping` - HTTP GET mapping (inherits base path)
   - Logging for request tracking
   - Delegates business logic to service layer
   - Returns structured response objects (`SampleResponse`)

4. **Clean Architecture:**
   - Controller focuses only on HTTP concerns
   - Business logic delegated to service layer
   - Clear separation of concerns

This structure follows Spring Boot best practices with clean dependency injection, proper logging, and separation between web layer and business logic.Based on the search results, here's an example of how REST controllers are structured in this codebase:

## REST Controller Structure

The codebase shows a clean and well-structured approach to REST controllers:

### **SampleController Example**

```java
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/hello")
public class SampleController {

    private final SampleService sampleService;

    @GetMapping
    public SampleResponse getHelloWorld() {
        log.info("Received request for hello world");
        return sampleService.getHelloWorld();
    }
}
```

### **Key Structure Elements:**

1. **Class-level Annotations:**
   - `@RestController` - Marks this as a REST controller
   - `@RequestMapping("/api/hello")` - Base path for all endpoints in this controller
   - `@RequiredArgsConstructor` - Lombok annotation for dependency injection
   - `@Slf4j` - Lombok annotation for logging

2. **Dependency Injection:**
   - Uses constructor injection with `private final` fields
   - Service layer dependency (`SampleService`) injected via constructor

3. **Method Structure:**
   - `@GetMapping` - HTTP GET mapping (inherits base path)
   - Logging for request tracking
   - Delegates business logic to service layer
   - Returns structured response objects (`SampleResponse`)

4. **Clean Architecture:**
   - Controller focuses only on HTTP concerns
   - Business logic delegated to service layer
   - Clear separation of concerns

This structure follows Spring Boot best practices with clean dependency injection, proper logging, and separation between web layer and business logic.
