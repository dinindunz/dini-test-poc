"""
AI Agent Tools Interface

This module provides a clean, simple interface for AI agents to use
all the code analysis capabilities. Each function represents a tool
that can be called by an AI agent.
"""

import os
from typing import Dict, List, Any, Optional
from .code_analysis_tools import CodeIndexer


# Global indexer instance
_indexer: Optional[CodeIndexer] = None


def initialise_code_analyser(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialise the code analyser (call this first)

    Args:
        cache_dir: Optional directory for caching index data

    Returns:
        Dictionary with initialisation status
    """
    global _indexer
    try:
        _indexer = CodeIndexer(cache_dir)
        return {
            "success": True,
            "message": "Code analyser initialised successfully",
            "cache_dir": _indexer.cache_dir
        }
    except Exception as e:
        return {"error": f"Failed to initialise: {e}"}


def set_project_path(path: str) -> Dict[str, Any]:
    """
    Set the project path and build initial index

    Tool for AI agents to specify which codebase to analyse.
    This must be called before using other analysis tools.

    Args:
        path: Absolute path to the project directory

    Returns:
        Dictionary with setup results including file count and build time
    """
    if not _indexer:
        return {"error": "Code analyser not initialised. Call initialise_code_analyser() first."}

    return _indexer.set_project_path(path)


def find_files(pattern: str) -> List[str]:
    """
    Find files matching a glob pattern

    Tool for AI agents to discover files in the codebase.
    Supports patterns like "*.java", "**/*.ts", "UserService.java"

    Args:
        pattern: Glob pattern to match files

    Returns:
        List of file paths matching the pattern
    """
    if not _indexer:
        return []

    return _indexer.find_files(pattern)


def search_code(pattern: str,
                case_sensitive: bool = True,
                context_lines: int = 0,
                file_pattern: Optional[str] = None,
                fuzzy: bool = False,
                regex: bool = False,
                max_line_length: Optional[int] = None) -> Dict[str, Any]:
    """
    Search for code patterns in the project

    Tool for AI agents to search through code content.
    Uses the best available search tool (ugrep, ripgrep, ag, or grep).

    Args:
        pattern: Text or regex pattern to search for
        case_sensitive: Whether search should be case-sensitive
        context_lines: Number of lines to show before/after matches
        file_pattern: Glob pattern to limit search to specific files
        fuzzy: Enable fuzzy matching (best with ugrep)
        regex: Treat pattern as regular expression
        max_line_length: Maximum line length to display

    Returns:
        Dictionary with search results, match count, and tool used
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    return _indexer.search_code(
        pattern=pattern,
        case_sensitive=case_sensitive,
        context_lines=context_lines,
        file_pattern=file_pattern,
        fuzzy=fuzzy,
        regex=regex,
        max_line_length=max_line_length
    )


def analyse_file(file_path: str) -> Dict[str, Any]:
    """
    Get detailed analysis of a specific file

    Tool for AI agents to understand file structure, symbols, and metadata.
    Provides functions, classes, imports, line count, and complexity info.

    Args:
        file_path: Path to file (relative to project root)

    Returns:
        Dictionary with file analysis including symbols and metadata
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    return _indexer.analyse_file(file_path)


def get_project_structure() -> Dict[str, Any]:
    """
    Get the project directory structure as a tree

    Tool for AI agents to understand the overall project layout.
    Shows directories and files in a hierarchical structure.

    Returns:
        Dictionary representing the project structure
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    return _indexer.get_project_structure()


def get_project_statistics() -> Dict[str, Any]:
    """
    Get comprehensive project statistics

    Tool for AI agents to understand project metrics.
    Includes file counts, language breakdown, symbol counts, etc.

    Returns:
        Dictionary with project statistics and tool information
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    return _indexer.get_statistics()


def refresh_index() -> Dict[str, Any]:
    """
    Manually refresh the project index

    Tool for AI agents to rebuild the index after file changes.
    Use when automatic file watching isn't sufficient.

    Returns:
        Dictionary with refresh results
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    return _indexer.refresh_index()


def find_symbol_usage(symbol_name: str, symbol_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Find where a symbol (function, class, method) is used

    Tool for AI agents to analyse symbol relationships and dependencies.

    Args:
        symbol_name: Name of the symbol to find
        symbol_type: Optional filter by symbol type ("function", "class", "method")

    Returns:
        Dictionary with symbol locations and usage information
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    if not _indexer.index_data:
        return {"error": "No project indexed"}

    symbols = _indexer.index_data.get("symbols", {})
    matches = []

    for symbol_id, symbol_info in symbols.items():
        # Extract symbol name from ID (format: file_path::symbol_name)
        if "::" in symbol_id:
            name = symbol_id.split("::")[-1]
        else:
            name = symbol_id

        # Check if name matches (support both exact and partial matches)
        if (symbol_name.lower() in name.lower() or
            name.endswith(f".{symbol_name}") or
            name == symbol_name):

            if symbol_type is None or symbol_info.get("type") == symbol_type:
                match_info = dict(symbol_info)
                match_info["symbol_id"] = symbol_id
                match_info["symbol_name"] = name
                matches.append(match_info)

    return {
        "success": True,
        "symbol_name": symbol_name,
        "matches": matches,
        "total_matches": len(matches)
    }


def find_functions_calling(function_name: str) -> Dict[str, Any]:
    """
    Find all functions that call a specific function

    Tool for AI agents to understand function dependencies and call graphs.

    Args:
        function_name: Name of the function to analyse

    Returns:
        Dictionary with calling functions and call relationships
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    if not _indexer.index_data:
        return {"error": "No project indexed"}

    symbols = _indexer.index_data.get("symbols", {})
    callers = []

    # Find the target function
    target_symbol_id = None
    for symbol_id, symbol_info in symbols.items():
        if "::" in symbol_id:
            name = symbol_id.split("::")[-1]
        else:
            name = symbol_id

        if (name == function_name or
            name.endswith(f".{function_name}") or
            function_name in name):
            target_symbol_id = symbol_id
            break

    if not target_symbol_id:
        return {
            "success": True,
            "function_name": function_name,
            "callers": [],
            "message": "Function not found in index"
        }

    # Find all functions that call this function
    target_symbol = symbols[target_symbol_id]
    for caller_id in target_symbol.get("called_by", []):
        if caller_id in symbols:
            caller_info = dict(symbols[caller_id])
            caller_info["symbol_id"] = caller_id
            callers.append(caller_info)

    return {
        "success": True,
        "function_name": function_name,
        "target_symbol_id": target_symbol_id,
        "callers": callers,
        "total_callers": len(callers)
    }


def get_file_imports(file_path: str) -> Dict[str, Any]:
    """
    Get all imports for a specific file

    Tool for AI agents to understand file dependencies.

    Args:
        file_path: Path to file (relative to project root)

    Returns:
        Dictionary with import statements and dependencies
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    if not _indexer.index_data:
        return {"error": "No project indexed"}

    # Normalize path
    if file_path.startswith(_indexer.base_path or ''):
        rel_path = os.path.relpath(file_path, _indexer.base_path)
    else:
        rel_path = file_path

    files = _indexer.index_data.get("files", {})
    if rel_path in files:
        file_info = files[rel_path]
        imports = file_info.get("imports", [])
        exports = file_info.get("exports", [])
        package = file_info.get("package")

        return {
            "success": True,
            "file_path": rel_path,
            "imports": imports,
            "exports": exports,
            "package": package,
            "total_imports": len(imports)
        }
    else:
        return {"error": f"File not found in index: {rel_path}"}


def search_in_file(file_path: str, pattern: str, regex: bool = False) -> Dict[str, Any]:
    """
    Search for patterns within a specific file

    Tool for AI agents to examine specific files in detail.

    Args:
        file_path: Path to file (relative to project root)
        pattern: Pattern to search for
        regex: Whether pattern is a regular expression

    Returns:
        Dictionary with search results within the file
    """
    if not _indexer:
        return {"error": "Code analyser not initialised"}

    if not _indexer.base_path:
        return {"error": "No project path set"}

    import os

    # Construct full path
    if file_path.startswith(_indexer.base_path):
        full_path = file_path
    else:
        full_path = os.path.join(_indexer.base_path, file_path)

    if not os.path.exists(full_path):
        return {"error": f"File not found: {file_path}"}

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        matches = []
        import re as regex_module

        for i, line in enumerate(lines, 1):
            if regex:
                if regex_module.search(pattern, line):
                    matches.append({
                        "line_number": i,
                        "line_content": line.rstrip(),
                        "match_start": regex_module.search(pattern, line).start() if regex_module.search(pattern, line) else 0
                    })
            else:
                if pattern.lower() in line.lower():
                    matches.append({
                        "line_number": i,
                        "line_content": line.rstrip(),
                        "match_start": line.lower().find(pattern.lower())
                    })

        return {
            "success": True,
            "file_path": file_path,
            "pattern": pattern,
            "matches": matches,
            "total_matches": len(matches)
        }

    except Exception as e:
        return {"error": f"Failed to search file: {e}"}


def shutdown_analyser():
    """
    Clean shutdown of the code analyser

    Tool for AI agents to properly clean up resources.
    """
    global _indexer
    if _indexer:
        _indexer.shutdown()
        _indexer = None


# Tool registry for AI agents
AVAILABLE_TOOLS = {
    "initialise_code_analyser": {
        "function": initialise_code_analyser,
        "description": "Initialise the code analyser (call this first)",
        "parameters": {
            "cache_dir": "Optional directory for caching index data"
        }
    },
    "set_project_path": {
        "function": set_project_path,
        "description": "Set the project path and build initial index",
        "parameters": {
            "path": "Absolute path to the project directory"
        }
    },
    "find_files": {
        "function": find_files,
        "description": "Find files matching a glob pattern",
        "parameters": {
            "pattern": "Glob pattern to match files (e.g., '*.java', '**/*.ts')"
        }
    },
    "search_code": {
        "function": search_code,
        "description": "Search for code patterns in the project",
        "parameters": {
            "pattern": "Text or regex pattern to search for",
            "case_sensitive": "Whether search should be case-sensitive (default: True)",
            "context_lines": "Number of lines to show before/after matches (default: 0)",
            "file_pattern": "Glob pattern to limit search to specific files",
            "fuzzy": "Enable fuzzy matching (default: False)",
            "regex": "Treat pattern as regular expression (default: False)",
            "max_line_length": "Maximum line length to display"
        }
    },
    "analyse_file": {
        "function": analyse_file,
        "description": "Get detailed analysis of a specific file",
        "parameters": {
            "file_path": "Path to file (relative to project root)"
        }
    },
    "get_project_structure": {
        "function": get_project_structure,
        "description": "Get the project directory structure as a tree",
        "parameters": {}
    },
    "get_project_statistics": {
        "function": get_project_statistics,
        "description": "Get comprehensive project statistics",
        "parameters": {}
    },
    "refresh_index": {
        "function": refresh_index,
        "description": "Manually refresh the project index",
        "parameters": {}
    },
    "find_symbol_usage": {
        "function": find_symbol_usage,
        "description": "Find where a symbol (function, class, method) is used",
        "parameters": {
            "symbol_name": "Name of the symbol to find",
            "symbol_type": "Optional filter by symbol type ('function', 'class', 'method')"
        }
    },
    "find_functions_calling": {
        "function": find_functions_calling,
        "description": "Find all functions that call a specific function",
        "parameters": {
            "function_name": "Name of the function to analyse"
        }
    },
    "get_file_imports": {
        "function": get_file_imports,
        "description": "Get all imports for a specific file",
        "parameters": {
            "file_path": "Path to file (relative to project root)"
        }
    },
    "search_in_file": {
        "function": search_in_file,
        "description": "Search for patterns within a specific file",
        "parameters": {
            "file_path": "Path to file (relative to project root)",
            "pattern": "Pattern to search for",
            "regex": "Whether pattern is a regular expression (default: False)"
        }
    },
    "shutdown_analyser": {
        "function": shutdown_analyser,
        "description": "Clean shutdown of the code analyser",
        "parameters": {}
    }
}


def get_tool_descriptions() -> Dict[str, Any]:
    """
    Get descriptions of all available tools for AI agents

    Returns:
        Dictionary with tool names, descriptions, and parameters
    """
    return AVAILABLE_TOOLS


if __name__ == "__main__":
    # Example usage
    print("Code Analysis Tools for AI Agents")
    print("=================================")

    tools = get_tool_descriptions()
    for tool_name, tool_info in tools.items():
        print(f"\n{tool_name}:")
        print(f"  Description: {tool_info['description']}")
        if tool_info['parameters']:
            print("  Parameters:")
            for param, desc in tool_info['parameters'].items():
                print(f"    - {param}: {desc}")
        else:
            print("  Parameters: None")