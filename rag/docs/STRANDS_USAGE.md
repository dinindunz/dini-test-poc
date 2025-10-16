# Strands Agent with Code Retrieval Tool

**[← Back to Main Documentation](./README.md)**

How to use the `@tool` decorator pattern for code generation with RAG.

---

## 📖 Table of Contents

- [Quick Start](#-quick-start)
- [Files](#-files)
- [Tools Overview](#️-tools-overview)
  - [Strands Retrieval Tool](#1-strands-retrieval-tool-primary)
  - [LangChain Retrieval Tool](#2-langchain-retrieval-tool-example)
- [Tool Definition](#-tool-definition)
- [Creating an Agent](#-creating-an-agent)
- [Usage Patterns](#-usage-patterns)
- [How the Agent Uses the Tool](#-how-the-agent-uses-the-tool)
- [Tool Parameters](#-tool-parameters)
- [Example Conversations](#-example-conversations)
- [Customising the Tool](#️-customising-the-tool)
- [Troubleshooting](#-troubleshooting)
- [Best Practices](#-best-practices)
- [Next Steps](#-next-steps)

---

## 🎯 Quick Start

### 1. Run the Interactive Agent

```bash
cd strands-agent
python strands_code_agent.py
```

Then ask questions like:
- "Generate a Spring Boot REST controller"
- "Show me the project structure"
- "Create a service layer class"

### 2. Run Examples

```bash
python strands_example.py
```

---

## 📁 Files

### Strands Agent Scripts

| File | Location | Purpose |
|------|----------|---------|
| `strands_code_agent.py` | `strands-agent/` | Interactive agent with retrieval |
| `strands_example.py` | `strands-agent/` | Simple usage examples |

### Tools

| File | Location | Purpose |
|------|----------|---------|
| `strands_retrieval_tool.py` | `tools/` | Primary retrieval tool using `@tool` decorator |
| `langchain_retrieval_tool.py` | `tools/` | LangChain example (reference only) |

---

## 🛠️ Tools Overview

### Available Tools

This project includes retrieval tools for RAG-based code generation:

| Tool | Location | Framework | Status |
|------|----------|-----------|--------|
| **retrieve_code_examples** | `tools/strands_retrieval_tool.py` | Strands | ✅ Active |
| **langchain_retrieval_tool** | `tools/langchain_retrieval_tool.py` | LangChain | 📝 Example only |

---

### 1. Strands Retrieval Tool (Primary)

**File:** `tools/strands_retrieval_tool.py`

The main retrieval tool built with Strands' `@tool` decorator pattern.

#### Features

- 🔍 **Semantic Search**: Vector similarity using Bedrock Titan embeddings
- 🎯 **Metadata Filtering**: Filter by file type, layer, module, class name, HTTP method
- 📊 **Verbose Output**: Detailed logging of query execution and results
- 🔢 **Configurable Results**: Adjust `top_k` to control number of examples returned
- ✅ **Production Ready**: Full error handling and connection management

#### Parameters

```python
def retrieve_code_examples(
    query: str,                      # Required: Search query
    top_k: int = 5,                  # Optional: Number of results (default: 5)
    file_type: Optional[str] = None, # Optional: "java", "gradle", "swagger", "markdown"
    module: Optional[str] = None,    # Optional: Module name filter
    layer: Optional[str] = None,     # Optional: "controller", "service", "repository", "dto"
    class_name: Optional[str] = None,# Optional: Specific class name
    http_method: Optional[str] = None# Optional: "GET", "POST", "PUT", "DELETE"
) -> str
```

#### How It Works

1. **Embedding Generation**: Converts query to 1024-dimensional vector using Bedrock Titan v2
2. **Vector Search**: Searches PostgreSQL pgvector for semantically similar code chunks
3. **Metadata Filtering**: Applies JSONB filters to narrow results
4. **Result Formatting**: Returns formatted examples with metadata and relevance scores
5. **Connection Management**: Automatically opens and closes database connections

#### Example Output

```
🔍 RETRIEVAL TOOL EXECUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Query: REST controller Spring Boot
🔢 Top K: 5
🔧 Filters: file_type=java, layer=controller

⚙️  Initialising components...
✅ Connected to vector database

🧮 Generating query embedding...
✅ Query vector dimension: 1024
📊 Query vector sample (first 5 values): [0.123, 0.456, ...]

🔎 Searching vector database...
✅ Found 1 results

📊 RESULTS DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- Result #1 ---
  📏 Similarity Score: 0.9234
  📄 File: 01_dini_java17-quickstart-helloworld/src/main/java/.../SampleController.java
  🏷️  Type: class
  🎯 Layer: controller
  📦 Module: 01_dini_java17-quickstart-helloworld
  🔢 Chunk ID: 01_dini_java17-quickstart-helloworld_0
```

#### Dependencies

```python
from strands import tool
from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig
```

#### Usage with Agent

```python
from strands import Agent
from tools.strands_retrieval_tool import retrieve_code_examples

# Agent automatically uses the tool when needed
agent = Agent(tools=[retrieve_code_examples])
response = agent("Generate a Spring Boot REST controller")
```

---

### 2. LangChain Retrieval Tool (Example)

**File:** `tools/langchain_retrieval_tool.py`

An example implementation showing how to use LangChain's pgvector integration.

#### Status

⚠️ **Example Only** - Not actively used in this project. Provided as reference for LangChain users.

#### Features

- Uses LangChain's `PGVector` wrapper
- Compatible with OpenAI embeddings
- Simpler API for basic use cases

#### Example Code

```python
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vector_store = PGVector(
    collection_name="code_embeddings",
    embedding_function=embeddings,
    connection_string=os.environ["PGVECTOR_URL"]
)

# Search for similar items
results = vector_store.similarity_search("REST controller examples")
```

#### Why We Use Strands Instead

| Aspect | Strands Tool | LangChain Tool |
|--------|--------------|----------------|
| **Integration** | Native `@tool` decorator | Requires wrapper |
| **Embeddings** | Bedrock Titan (AWS) | OpenAI (external API) |
| **Filtering** | Rich JSONB metadata filters | Basic filters |
| **Logging** | Verbose execution details | Minimal logging |
| **Control** | Full control over vector store | Abstracted interface |

---

## 🔧 Tool Definition

The retrieval tool is defined using the `@tool` decorator:

```python
from strands import tool

@tool
def retrieve_code_examples(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    module: Optional[str] = None,
    layer: Optional[str] = None
) -> str:
    """
    Search for relevant code examples from the vectorised codebase.

    Args:
        query: Search query for code examples
        top_k: Number of examples to retrieve (default: 5)
        file_type: Filter by "java", "gradle", "swagger", "markdown"
        module: Filter by module name
        layer: Filter by "controller", "service", "repository", "api"

    Returns:
        Formatted code examples with metadata
    """
    # Implementation here...
```

**Key features:**
- ✅ Uses `@tool` decorator (Strands pattern)
- ✅ Type hints for all parameters
- ✅ Clear docstring describing functionality
- ✅ Returns formatted string for LLM

---

## 🤖 Creating an Agent

### Basic Agent

```python
from strands import Agent
from strands_retrieval_tool import retrieve_code_examples

# Create agent with tool
agent = Agent(tools=[retrieve_code_examples])

# Ask a question
response = agent("Generate a Spring Boot REST controller")
```

### Agent with Instructions

```python
agent = Agent(
    name="CodeGeneratorAgent",
    description="Expert Spring Boot developer",
    instructions="""
You are an expert Spring Boot developer.
Use the retrieve_code_examples tool to find relevant examples.
Generate code following the same patterns.
Use Australian English spelling.
    """,
    tools=[retrieve_code_examples],
    model="anthropic/claude-3-5-sonnet-20241022"
)

response = agent("Create a user management controller")
```

---

## 💡 Usage Patterns

### Pattern 1: Simple Query

```python
from strands import Agent
from strands_retrieval_tool import retrieve_code_examples

agent = Agent(tools=[retrieve_code_examples])

# Agent automatically uses the tool when helpful
response = agent("Show me a Spring Boot controller example")
```

### Pattern 2: Multiple Questions

```python
message = """
I have 3 requests:
1. Show me the project structure
2. Generate a REST controller
3. Create a service class
"""

response = agent(message)
```

### Pattern 3: Combining with Other Tools

```python
from strands import Agent
from strands_tools import calculator
from strands_retrieval_tool import retrieve_code_examples

# Agent with multiple tools
agent = Agent(tools=[retrieve_code_examples, calculator])

message = """
1. Find me controller examples
2. If there are 5 controllers and I need 3 more, how many total?
"""

response = agent(message)
```

---

## 🎪 How the Agent Uses the Tool

### Step 1: User asks a question
```
User: "Generate a Spring Boot REST controller"
```

### Step 2: Agent decides to use tool
```
Agent thinks: "I should search for controller examples"
Agent calls: retrieve_code_examples(
    query="REST controller Spring Boot",
    file_type="java",
    layer="controller"
)
```

### Step 3: Tool returns examples
```
Tool returns:
--- Example 1 (relevance: 0.92) ---
📄 File: SampleController.java
💻 Code:
@RestController
public class SampleController {...}
```

### Step 4: Agent generates response
```
Agent: "Here's a REST controller based on the examples:

@RestController
@RequestMapping("/api/users")
public class UserController {
    ...
}

This follows the pattern from SampleController.java"
```

---

## 🔍 Tool Parameters

### query (required)
```python
# What to search for
agent("Find examples of service classes")
# Tool receives: query="service classes"
```

### top_k (optional, default=5)
```python
# How many examples to return
# Agent automatically adjusts based on context
# You can hint in your message:
agent("Show me 3 different controller examples")
```

### file_type (optional)
```python
# Filter by file type
agent("Show me Gradle configuration")
# Tool uses: file_type="gradle"

agent("Find Java service classes")
# Tool uses: file_type="java"
```

### module (optional)
```python
# Filter by module
agent("Show me code from the quickstart module")
# Tool uses: module="01_dini_java17-quickstart-helloworld"
```

### layer (optional)
```python
# Filter by architectural layer
agent("Find repository layer examples")
# Tool uses: layer="repository"

agent("Show me controller examples")
# Tool uses: layer="controller"
```

---

## 📊 Example Conversations

### Conversation 1: Code Generation

**User:** Generate a product management REST controller

**Agent:**
1. Calls `retrieve_code_examples("REST controller", file_type="java", layer="controller")`
2. Receives SampleController.java example
3. Generates ProductController.java following the pattern
4. Explains the structure

### Conversation 2: Understanding Structure

**User:** How is this Spring Boot application organised?

**Agent:**
1. Calls `retrieve_code_examples("application structure architecture", top_k=10)`
2. Receives examples from all layers
3. Explains the layered architecture pattern
4. Shows examples from each layer

### Conversation 3: Configuration Help

**User:** How do I add dependencies to Gradle?

**Agent:**
1. Calls `retrieve_code_examples("dependencies", file_type="gradle")`
2. Receives build.gradle chunks
3. Explains dependency management
4. Shows example from your build.gradle

---

## ⚙️ Customising the Tool

### Adjust Default top_k

```python
@tool
def retrieve_code_examples(
    query: str,
    top_k: int = 3,  # Changed from 5 to 3
    ...
):
```

### Add New Filters

```python
@tool
def retrieve_code_examples(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    language: Optional[str] = None,  # NEW filter
    ...
):
    # Add to metadata filter
    if language:
        metadata_filter['language'] = language
```

### Change Model

```python
# In strands_retrieval_tool.py
embedder = BedrockEmbeddingGenerator(
    model_id="amazon.titan-embed-text-v1"  # Use different model
)
```

---

## 🚨 Troubleshooting

### Agent doesn't use the tool

**Problem:** Agent responds without retrieving examples

**Solution:** Make instructions more explicit:
```python
instructions="""
ALWAYS use retrieve_code_examples tool before generating code.
Search for relevant examples first, then generate based on patterns.
"""
```

### Tool returns no results

**Problem:** "No relevant code examples found"

**Solutions:**
1. Check database has data: `vector_store.get_count()`
2. Broaden search: Remove filters, increase top_k
3. Check query relevance: Use more specific terms

### Connection errors

**Problem:** "Error retrieving code examples"

**Solutions:**
1. Check PostgreSQL is running: `docker ps`
2. Verify .env configuration
3. Test connection: `python -c "from config import DatabaseConfig; print(DatabaseConfig().connection_string)"`

---

## 🎯 Best Practices

### 1. Clear Instructions
```python
# ✅ Good
instructions="Use retrieve_code_examples to find patterns, then generate code"

# ❌ Bad
instructions="Help the user"
```

### 2. Specific Queries
```python
# ✅ Good - Agent will pass good query
"Generate a REST controller for users"

# ❌ Bad - Vague query
"Make some code"
```

### 3. Trust the Agent
```python
# ✅ Good - Let agent decide parameters
agent = Agent(tools=[retrieve_code_examples])

# ❌ Bad - Over-constraining
# Don't manually call the tool, let agent decide
```

---

## 📚 Further Reading

- [Strands Documentation](https://github.com/strands-ai/strands)
- [Tool Decorator Pattern](https://docs.strands.ai/tools)

---

## 🚀 Next Steps

1. **Test the agent:**
   ```bash
   cd strands-agent
   python strands_code_agent.py
   ```

2. **Try different queries:**
   - Code generation
   - Understanding structure
   - Finding configurations

3. **Customise instructions:**
   - Modify agent instructions in `strands_code_agent.py`
   - Adjust for your specific needs

4. **Add more code:**
   - Vectorise more modules
   - Larger knowledge base = better results

---

**Last Updated:** 2025-10-16
