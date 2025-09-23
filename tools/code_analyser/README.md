# Code Analysis Tools for AI Agents

A code analysis tool set that provides intelligent indexing, advanced search, and detailed code analysis for Java and TypeScript codebases. This tool set extracts all functionality from the original MCP server and presents it as easy-to-use tools for AI agents.

## Features

### 🔍 **Intelligent Analysis**
- **Tree-sitter AST Parsing**: Native syntax parsing for Java and TypeScript
- **Symbol Extraction**: Functions, classes, methods, interfaces with line numbers
- **Call Graph Analysis**: Track function calls and dependencies
- **Import/Export Analysis**: Understand module relationships

### 🚀 **Advanced Search**
- **Multi-Tool Support**: Automatically uses the best available search tool (ugrep, ripgrep, ag, or grep)
- **Pattern Matching**: Literal text, regex, and fuzzy search capabilities
- **Context Lines**: Show surrounding code for better understanding
- **File Filtering**: Limit searches to specific file patterns

### ⚡ **Performance & Efficiency**
- **Persistent Caching**: Fast index loading with msgpack serialisation
- **File Watching**: Automatic index updates when files change
- **Smart Filtering**: Ignores build directories and temporary files
- **Memory Efficient**: Optimised for large codebases

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from ai_agent_tools import *

# 1. Initialise the analyser
initialise_code_analyser()

# 2. Set your project path
set_project_path("/path/to/your/java-or-typescript-project")

# 3. Start using the tools
files = find_files("*.java")
results = search_code("public class")
analysis = analyse_file("src/main/java/Main.java")
```

## Available Tools

### 🏗️ **Project Management**
| Tool | Description |
|------|-------------|
| `initialise_code_analyser()` | Initialise the code analyser (call this first) |
| `set_project_path(path)` | Set project path and build initial index |
| `refresh_index()` | Manually refresh the project index |
| `get_project_structure()` | Get project directory structure as a tree |
| `get_project_statistics()` | Get comprehensive project statistics |

### 🔍 **Search & Discovery**
| Tool | Description |
|------|-------------|
| `find_files(pattern)` | Find files using glob patterns (e.g., `*.java`) |
| `search_code(pattern, ...)` | Advanced code search with multiple options |
| `search_in_file(file_path, pattern)` | Search within a specific file |

### 🔬 **Code Analysis**
| Tool | Description |
|------|-------------|
| `analyse_file(file_path)` | Get detailed file analysis (symbols, imports, etc.) |
| `find_symbol_usage(symbol_name)` | Find where symbols are defined |
| `find_functions_calling(function_name)` | Find all callers of a function |
| `get_file_imports(file_path)` | Get all imports for a specific file |

### 🛠️ **System Management**
| Tool | Description |
|------|-------------|
| `shutdown_analyser()` | Clean shutdown of the code analyser |

## Detailed Tool Documentation

### Project Management Tools

#### `initialise_code_analyser(cache_dir=None)`
Initialise the code analyser system.

**Parameters:**
- `cache_dir` (optional): Directory for caching index data

**Returns:**
```python
{
    "success": True,
    "message": "Code analyser initialised successfully",
    "cache_dir": "/tmp/code_analysis_xxx"
}
```

#### `set_project_path(path)`
Set the project path and build the initial index.

**Parameters:**
- `path`: Absolute path to the project directory

**Returns:**
```python
{
    "success": True,
    "message": "Project initialised at /path/to/project",
    "file_count": 150,
    "build_time": 2.5,
    "cache_location": "/tmp/code_analysis_xxx"
}
```

### Search Tools

#### `search_code(pattern, case_sensitive=True, context_lines=0, file_pattern=None, fuzzy=False, regex=False, max_line_length=None)`
Search for code patterns using the best available search tool.

**Parameters:**
- `pattern`: Text or regex pattern to search for
- `case_sensitive`: Whether search should be case-sensitive (default: True)
- `context_lines`: Number of lines to show before/after matches (default: 0)
- `file_pattern`: Glob pattern to limit search to specific files
- `fuzzy`: Enable fuzzy matching (default: False)
- `regex`: Treat pattern as regular expression (default: False)
- `max_line_length`: Maximum line length to display

**Returns:**
```python
{
    "success": True,
    "results": [
        {
            "file": "src/Main.java",
            "line_number": 15,
            "line_content": "public class Main {",
            "context_before": ["package com.example;", ""],
            "context_after": ["    public static void main(String[] args) {"]
        }
    ],
    "total_matches": 1,
    "search_tool": "ugrep"
}
```

#### `find_files(pattern)`
Find files matching a glob pattern.

**Parameters:**
- `pattern`: Glob pattern (e.g., "*.java", "**/*.ts", "UserService.java")

**Returns:**
```python
[
    "src/main/java/Main.java",
    "src/main/java/service/UserService.java",
    "src/test/java/MainTest.java"
]
```

### Analysis Tools

#### `analyse_file(file_path)`
Get detailed analysis of a specific file.

**Parameters:**
- `file_path`: Path to file (relative to project root)

**Returns:**
```python
{
    "success": True,
    "file_path": "src/main/java/Main.java",
    "file_info": {
        "language": "java",
        "line_count": 45,
        "symbols": {
            "functions": ["Main.main", "Main.initialise"],
            "classes": ["Main"]
        },
        "imports": ["java.util.List", "java.io.IOException"],
        "package": "com.example"
    },
    "symbols": {
        "src/main/java/Main.java::Main": {
            "type": "class",
            "file": "src/main/java/Main.java",
            "line": 5
        }
    }
}
```

#### `find_symbol_usage(symbol_name, symbol_type=None)`
Find where a symbol is defined and used.

**Parameters:**
- `symbol_name`: Name of the symbol to find
- `symbol_type`: Optional filter by type ("function", "class", "method")

**Returns:**
```python
{
    "success": True,
    "symbol_name": "UserService",
    "matches": [
        {
            "symbol_id": "src/service/UserService.java::UserService",
            "type": "class",
            "file": "src/service/UserService.java",
            "line": 8,
            "called_by": ["src/Main.java::Main.main"]
        }
    ],
    "total_matches": 1
}
```

## Language Support

### Java (.java)
- **Classes**: Full class hierarchy extraction
- **Methods**: Method signatures with parameter types
- **Imports**: Package and class imports
- **Packages**: Package declarations
- **Call Analysis**: Method invocation tracking

### TypeScript (.ts, .tsx)
- **Functions**: Function declarations and expressions
- **Classes**: Class definitions with methods
- **Interfaces**: Interface declarations
- **Imports/Exports**: ES6 module analysis
- **Types**: Type annotations and generics

### JavaScript (.js, .jsx)
- **Functions**: Function declarations and expressions
- **Classes**: ES6 class definitions
- **Modules**: CommonJS and ES6 imports/exports

## Search Tool Integration

The system automatically detects and uses the best available command-line search tool:

1. **ugrep** (fastest, best features)
   - True fuzzy search
   - Advanced regex support
   - Best performance

2. **ripgrep** (fast, good features)
   - Excellent performance
   - Good regex support

3. **ag (Silver Searcher)** (good performance)
   - Fast searching
   - Basic features

4. **grep** (fallback, always available)
   - System default
   - Basic functionality

## File Watching

The system includes automatic file watching that:
- Monitors changes to Java and TypeScript files
- Automatically updates the index when files are modified
- Ignores build directories and temporary files
- Provides real-time index synchronisation

## Performance Optimisation

- **Tree-sitter Parsing**: Native AST parsing for accurate symbol extraction
- **Msgpack Caching**: Fast binary serialisation for index persistence
- **Smart Exclusions**: Automatically ignores irrelevant files and directories
- **Incremental Updates**: Only re-processes changed files
- **Memory Efficient**: Optimised data structures for large codebases

## Example Workflows

### Code Review Assistant
```python
# Initialise for a pull request review
initialise_code_analyser()
set_project_path("/path/to/repo")

# Find all modified files
modified_files = find_files("src/**/*.java")

# Analyse each file for complexity
for file_path in modified_files:
    analysis = analyse_file(file_path)
    functions = analysis['file_info']['symbols']['functions']
    print(f"{file_path}: {len(functions)} functions")

# Search for potential issues
security_results = search_code("password|secret|key", regex=True)
```

### Refactoring Assistant
```python
# Find all usages of a function to be refactored
old_function = "getUserById"
callers = find_functions_calling(old_function)

# Find all files that import the module
import_results = search_code(f"import.*{old_function}", regex=True)

# Analyse impact
for caller in callers['callers']:
    print(f"Update needed in: {caller['file']}:{caller['line']}")
```

### Architecture Analysis
```python
# Get project overview
stats = get_project_statistics()
structure = get_project_structure()

# Find all service classes
services = find_files("*Service.java")

# Analyse dependencies
for service in services:
    imports = get_file_imports(service)
    print(f"{service} depends on: {len(imports['imports'])} modules")
```

## Error Handling

All tools return consistent error formats:

```python
{
    "error": "Description of what went wrong",
    "success": False  # Only present on errors
}
```

Common error scenarios:
- Project not initialised
- File not found
- Invalid patterns
- Search tool failures
- Permission issues

## Best Practices

1. **Always initialise first**: Call `initialise_code_analyser()` before other tools
2. **Set project path early**: Call `set_project_path()` as the second step
3. **Use appropriate patterns**: Leverage glob patterns for file discovery
4. **Handle errors gracefully**: Check for error keys in responses
5. **Clean shutdown**: Call `shutdown_analyser()` when done
6. **Cache benefits**: Let the file watcher handle updates automatically

## Troubleshooting

### No search results
- Verify project path is correct
- Check file patterns are valid
- Ensure files exist and are readable

### Slow performance
- Ensure search tools (ugrep, ripgrep) are installed
- Check if cache directory has proper permissions
- Verify project doesn't include massive binary files

### Missing symbols
- Check if files are properly indexed
- Call `refresh_index()` to rebuild
- Verify file extensions are supported

## Requirements

- Python 3.7+
- tree-sitter libraries for Java and TypeScript
- watchdog for file monitoring
- pathspec for pattern matching
- msgpack for fast serialisation

Optional but recommended:
- ugrep (fastest search)
- ripgrep (fast search)
- ag (Silver Searcher)

## License

MIT License - see LICENSE file for details.