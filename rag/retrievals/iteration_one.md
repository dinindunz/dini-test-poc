# Iteration One - Before Metadata Enhancement

**Context:** Basic vectorisation with minimal chunk content
**Commit:** Before a74674b309ad062d00b976dc1a8a03a551e0d55c
**Vectorised Content:**
```
Type: class
[code only]
```

**Metadata Stored:**
- Basic fields only: `module`, `file_path`, `file_type`, `type`, `name`
- **Missing:** `layer`, `class_name`, `annotations`, `chunk_id`, API fields

**Key Issue:**
- Metadata filter `layer=controller` returned **0 results** because `layer` field wasn't stored in database
- Content preview shows "Layer: N/A" and "Chunk ID: N/A"

---

➜ python examples/strands_example.py 

============================================================
Example 3: Using filters
============================================================
I'll search for Java controller classes to show you how REST controllers are structured in this codebase.
Tool #1: retrieve_code_examples

======================================================================
🔍 RETRIEVAL TOOL EXECUTION
======================================================================
📝 Query: REST controller classes
🔢 Top K: 7
🔧 Filters: file_type=java, module=None, layer=controller

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

✅ Found 0 results
✅ Database connection closed

⚠️  No results found
Let me try a broader search for Java controller examples without the layer filter:
Tool #2: retrieve_code_examples

======================================================================
🔍 RETRIEVAL TOOL EXECUTION
======================================================================
📝 Query: controller REST API endpoint
🔢 Top K: 7
🔧 Filters: file_type=java, module=None, layer=None

⚙️  Initialising components...
✅ Connected to PostgreSQL database: postgres
✅ Connected to vector database

🧮 Generating query embedding...
✅ Query vector dimension: 1024
📊 Query vector sample (first 5 values): [-0.11126164346933365, 0.042763981968164444, 0.037408001720905304, 0.010500555858016014, 0.014582687988877296]

🔍 Applying metadata filters: {'file_type': 'java'}

🔎 Searching vector database...

======================================================================
🔎 SQL QUERY
======================================================================

                SELECT id, content, metadata, embedding,
                       1 - (embedding <=> %s) as similarity
                FROM code_embeddings
             WHERE metadata->>'file_type' = %s ORDER BY embedding <=> %s LIMIT %s

📋 Query Parameters:
  - Vector dimension: 1024
  - Top K: 7
  - Metadata filters: {'file_type': 'java'}

💡 Search Strategy:
  - Semantic Search: Using cosine similarity (embedding <=> vector)
  - Distance Operator: '<=' (cosine distance)
  - Similarity Metric: 1 - cosine_distance (higher = more similar)
  - Lexical Filter: JSONB metadata filtering on ['file_type']
======================================================================

✅ Found 4 results
✅ Database connection closed

======================================================================
📊 RESULTS DETAILS
======================================================================

--- Result #1 ---
  📏 Similarity Score: 0.3887
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/controller/SampleController.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.1276344507932663, -0.02483461983501911, 0.028925001621246338, -0.05216953530907631, 0.028776273131370544]
  📝 Content preview: Type: class
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/hello")
public cla...

--- Result #2 ---
  📏 Similarity Score: 0.1928
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/application/SampleService.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.09281858801841736, -0.012408968061208725, 0.02057531289756298, -0.057035136967897415, 0.028261510655283928]
  📝 Content preview: Type: class
@Slf4j
@Service
@RequiredArgsConstructor
public class SampleService {

    private final...

--- Result #3 ---
  📏 Similarity Score: 0.1850
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/repository/sample/SampleRepository.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.07974057644605637, -0.008566603995859623, 0.049071550369262695, -0.03496905788779259, 0.001632504747249186]
  📝 Content preview: Type: class
@Slf4j
@Repository
public class SampleRepository {

    public SampleResponse getHelloWo...

--- Result #4 ---
  📏 Similarity Score: 0.1250
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/Application.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.019258864223957062, 0.026809528470039368, 0.010068308562040329, -0.054655592888593674, 0.012715090066194534]
  📝 Content preview: Type: class
@SpringBootApplication
public class Application {

    public static void main(String[] ...

======================================================================
Perfect! I found a Java controller class example. Let me search for more controller examples to give you a better understanding of different REST controller patterns:
Tool #3: retrieve_code_examples

======================================================================
🔍 RETRIEVAL TOOL EXECUTION
======================================================================
📝 Query: @RestController @RequestMapping
🔢 Top K: 5
🔧 Filters: file_type=java, module=None, layer=None

⚙️  Initialising components...
✅ Connected to PostgreSQL database: postgres
✅ Connected to vector database

🧮 Generating query embedding...
✅ Query vector dimension: 1024
📊 Query vector sample (first 5 values): [-0.1278943121433258, 0.032282304018735886, 0.014438249170780182, 0.028364455327391624, 0.006049408111721277]

🔍 Applying metadata filters: {'file_type': 'java'}

🔎 Searching vector database...

======================================================================
🔎 SQL QUERY
======================================================================

                SELECT id, content, metadata, embedding,
                       1 - (embedding <=> %s) as similarity
                FROM code_embeddings
             WHERE metadata->>'file_type' = %s ORDER BY embedding <=> %s LIMIT %s

📋 Query Parameters:
  - Vector dimension: 1024
  - Top K: 5
  - Metadata filters: {'file_type': 'java'}

💡 Search Strategy:
  - Semantic Search: Using cosine similarity (embedding <=> vector)
  - Distance Operator: '<=' (cosine distance)
  - Similarity Metric: 1 - cosine_distance (higher = more similar)
  - Lexical Filter: JSONB metadata filtering on ['file_type']
======================================================================

✅ Found 4 results
✅ Database connection closed

======================================================================
📊 RESULTS DETAILS
======================================================================

--- Result #1 ---
  📏 Similarity Score: 0.3456
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/controller/SampleController.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.1276344507932663, -0.02483461983501911, 0.028925001621246338, -0.05216953530907631, 0.028776273131370544]
  📝 Content preview: Type: class
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/hello")
public cla...

--- Result #2 ---
  📏 Similarity Score: 0.2244
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/repository/sample/SampleRepository.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.07974057644605637, -0.008566603995859623, 0.049071550369262695, -0.03496905788779259, 0.001632504747249186]
  📝 Content preview: Type: class
@Slf4j
@Repository
public class SampleRepository {

    public SampleResponse getHelloWo...

--- Result #3 ---
  📏 Similarity Score: 0.2218
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/application/SampleService.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.09281858801841736, -0.012408968061208725, 0.02057531289756298, -0.057035136967897415, 0.028261510655283928]
  📝 Content preview: Type: class
@Slf4j
@Service
@RequiredArgsConstructor
public class SampleService {

    private final...

--- Result #4 ---
  📏 Similarity Score: 0.1916
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/com/example/hello/world/Application.java
  🏷️  Type: class
  🎯 Layer: N/A
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: N/A
  📊 Stored vector dimension: 1024
  📊 Stored vector sample (first 5): [-0.019258864223957062, 0.026809528470039368, 0.010068308562040329, -0.054655592888593674, 0.012715090066194534]
  📝 Content preview: Type: class
@SpringBootApplication
public class Application {

    public static void main(String[] ...

======================================================================
Based on the codebase, I found one main REST controller example. Here's how REST controllers are structured in this Spring Boot project:

## Java REST Controller Structure

### **SampleController.java**
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

## Key Structural Elements:

### **Annotations Used:**
- `@Slf4j` - Lombok annotation for logging
- `@RestController` - Combines `@Controller` and `@ResponseBody`, automatically serializes return values to JSON
- `@RequiredArgsConstructor` - Lombok annotation that generates constructor for final fields
- `@RequestMapping("/api/hello")` - Maps all endpoints in this controller to the `/api/hello` base path

### **Dependency Injection:**
- Uses constructor injection with `private final SampleService sampleService`
- The `@RequiredArgsConstructor` annotation generates the constructor automatically

### **HTTP Endpoints:**
- `@GetMapping` - Maps HTTP GET requests to the method
- Since it's at the class level with `@RequestMapping("/api/hello")`, this endpoint responds to `GET /api/hello`

### **Best Practices Demonstrated:**
1. **Clean separation of concerns** - Controller only handles HTTP requests/responses
2. **Dependency injection** - Service layer injected via constructor
3. **Logging** - Uses SLF4J for request logging
4. **RESTful design** - Clear resource-based URL structure
5. **Response objects** - Returns structured `SampleResponse` objects

This is a simple but well-structured REST controller following Spring Boot best practices for a basic "Hello World" API endpoint.Based on the codebase, I found one main REST controller example. Here's how REST controllers are structured in this Spring Boot project:

## Java REST Controller Structure

### **SampleController.java**
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

## Key Structural Elements:

### **Annotations Used:**
- `@Slf4j` - Lombok annotation for logging
- `@RestController` - Combines `@Controller` and `@ResponseBody`, automatically serializes return values to JSON
- `@RequiredArgsConstructor` - Lombok annotation that generates constructor for final fields
- `@RequestMapping("/api/hello")` - Maps all endpoints in this controller to the `/api/hello` base path

### **Dependency Injection:**
- Uses constructor injection with `private final SampleService sampleService`
- The `@RequiredArgsConstructor` annotation generates the constructor automatically

### **HTTP Endpoints:**
- `@GetMapping` - Maps HTTP GET requests to the method
- Since it's at the class level with `@RequestMapping("/api/hello")`, this endpoint responds to `GET /api/hello`

### **Best Practices Demonstrated:**
1. **Clean separation of concerns** - Controller only handles HTTP requests/responses
2. **Dependency injection** - Service layer injected via constructor
3. **Logging** - Uses SLF4J for request logging
4. **RESTful design** - Clear resource-based URL structure
5. **Response objects** - Returns structured `SampleResponse` objects

This is a simple but well-structured REST controller following Spring Boot best practices for a basic "Hello World" API endpoint.