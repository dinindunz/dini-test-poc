# Strands Agent with Code Retrieval Tool

How to use the `@tool` decorator pattern for code generation with RAG.

---

## 🎯 Quick Start

### 1. Run the Interactive Agent

```bash
cd rag/examples
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

| File | Purpose |
|------|---------|
| `strands_retrieval_tool.py` | Tool using `@tool` decorator |
| `strands_code_agent.py` | Interactive agent with retrieval |
| `strands_example.py` | Simple usage examples |

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
- RAG (Retrieval Augmented Generation) concepts
- Vector similarity search

---

## 🚀 Next Steps

1. **Test the agent:**
   ```bash
   cd rag/examples
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

**Happy coding with Strands! 🎉**
