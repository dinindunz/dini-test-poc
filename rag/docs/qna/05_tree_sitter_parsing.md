# Tree-sitter AST Parsing

[← Back to Documentation Index](../README.md)

**Navigation:** [← Previous: Metadata in Embeddings](./04_metadata_in_embeddings.md) | [Next: pgvector Indexing →](./06_pgvector_indexing.md)

---

Does tree-sitter work with source code text or compiled binaries? Explain the input format.

Tree-sitter works with **source code text**, not compiled binaries. Here's a detailed explanation of the input format and how it builds the AST.

### What AST Parsing Works With

AST parsing works with **source code text** (like your `.java` files), NOT machine code or binary. Here's the breakdown:

#### Your Java File (Source Code Text)

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

#### Step 1: Read as Plain Text

```python
# Line 74 in multi_module_chunker.py
content = file_path.read_text(encoding='utf-8')
# content = "@RestController\n@RequestMapping...\npublic class SampleController..."
```

This is just **plain text** - the same as opening the file in a text editor.

#### Step 2: Parse Text into AST (Tree Structure)

```python
# Line 75 in multi_module_chunker.py
tree = self.java_parser.parse(bytes(content, "utf8"))
```

Tree-sitter analyses the text and builds a **tree structure** representing the code's syntax:

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

#### Step 3: Navigate the Tree to Find Nodes

```python
# Line 82-84 in multi_module_chunker.py
class_nodes = self._find_nodes_by_type(tree.root_node, 'class_declaration')
record_nodes = self._find_nodes_by_type(tree.root_node, 'record_declaration')
```

We traverse the tree to find specific node types (like finding `<div>` tags in HTML DOM).

#### Step 4: Extract Code Using Byte Positions

```python
# Line 91 in multi_module_chunker.py
class_content = content[class_node.start_byte:class_node.end_byte]
```

Each node knows its **start and end position** in the original text. We use these positions to extract the exact code.

### Key Concept: Source Code, Not Binary

| **What It Is** | **What It's NOT** |
|----------------|-------------------|
| ✅ Source code text (`.java` files) | ❌ Compiled bytecode (`.class` files) |
| ✅ Plain text characters | ❌ Machine code (binary) |
| ✅ Abstract Syntax Tree (structured representation) | ❌ Execution instructions |
| ✅ Parsing (like HTML parser) | ❌ Compilation |

### Analogy: HTML Parser

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

### Why Use AST Instead of Regex?

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

### Real Example from Our Chunker

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

### What Tree-sitter Provides

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

### Summary

- **Input**: Plain text source code (`.java`, `.py`, `.ts` files)
- **Process**: Tree-sitter parses text into an Abstract Syntax Tree (AST)
- **Output**: Structured tree representing code syntax
- **NOT**: Binary code, machine code, or compiled bytecode

**Tree-sitter is like a "smart code parser"** that understands programming language grammar, similar to how an HTML parser understands HTML tags!

It works with **human-readable source code**, not compiled binaries. This is why we can extract exact code snippets and understand the structure - we're working with the original text file, just organised into a tree for easy navigation.


