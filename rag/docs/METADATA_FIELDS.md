# Metadata Fields Reference

**[← Back to Main Documentation](./README.md)**

This document describes all metadata fields stored in the vector database for code chunks.

## Core Fields (All Chunk Types)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `chunk_id` | string | Unique identifier for the chunk | `01_dini_java17-quickstart-helloworld_0` |
| `module` | string | Module/project name | `01_dini_java17-quickstart-helloworld` |
| `file_path` | string | Relative path to source file | `01_dini_java17-quickstart-helloworld/src/main/java/...` |
| `file_type` | string | Type of source file | `java`, `swagger`, `markdown`, `gradle` |
| `type` | string | Chunk content type | `class`, `record`, `api_endpoint`, `api_schema`, `documentation` |
| `layer` | string | Architectural layer | `controller`, `service`, `repository`, `dto`, `other` |

## Location Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `line_start` | integer | Starting line number in source file | `7` |
| `line_end` | integer | Ending line number in source file | `15` |

## Java-Specific Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `package` | string | Java package name | `com.example.hello.world.controller` |
| `class_name` | string | Class or record name | `SampleController` |
| `annotations` | array | List of annotations on the class | `["@RestController", "@Slf4j"]` |

## API/Swagger-Specific Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `http_method` | string | HTTP method for API endpoint | `GET`, `POST`, `PUT`, `DELETE` |
| `api_path` | string | API endpoint path | `/hello`, `/api/users/{id}` |
| `operation_id` | string | OpenAPI operation ID | `getHelloWorld` |
| `schema_name` | string | OpenAPI schema name | `SampleResponse`, `ErrorResponse` |
| `api_title` | string | API title from OpenAPI spec | `Hello World API` |
| `api_version` | string | API version | `1.0.0` |
| `tags` | array | API endpoint tags | `["Hello", "User Management"]` |

## Documentation-Specific Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `document_name` | string | Document name | `README` |
| `heading` | string | Section heading | `Hello World Quickstart` |
| `heading_level` | integer | Heading level (1-6) | `1`, `2`, `3` |

## Embedding Content Structure

The text content that gets embedded includes structured metadata prefixes to improve semantic search:

```
Type: class
Layer: controller
Class: SampleController
Package: com.example.hello.world.controller
Annotations: @Slf4j, @RestController, @RequiredArgsConstructor

[actual code content here]
```

For API endpoints:
```
Type: api_endpoint
HTTP Method: GET
API Path: /hello
Operation: getHelloWorld

[API specification content here]
```

## Filtering Examples

### Filter by Layer
```python
retrieve_code_examples(
    query="REST API handling",
    layer="controller"
)
```

### Filter by Class Name
```python
retrieve_code_examples(
    query="sample implementation",
    class_name="SampleController"
)
```

### Filter by HTTP Method
```python
retrieve_code_examples(
    query="API endpoints",
    http_method="GET"
)
```

### Combined Filters
```python
retrieve_code_examples(
    query="repository pattern",
    file_type="java",
    layer="repository",
    module="01_dini_java17-quickstart-helloworld"
)
```

## Search Strategy

The system uses **hybrid search** combining:

1. **Semantic Search**: Vector similarity using cosine distance on embeddings
2. **Lexical Filtering**: JSONB metadata filtering for precise field matching

Example SQL query:
```sql
SELECT id, content, metadata, embedding,
       1 - (embedding <=> $query_vector) as similarity
FROM code_embeddings
WHERE metadata->>'file_type' = 'java'
  AND metadata->>'layer' = 'controller'
ORDER BY embedding <=> $query_vector
LIMIT 5
```

This provides both semantic understanding ("find code similar to REST controllers") and precise filtering ("only Java controller layer classes").

---

**Last Updated**: 2025-10-16