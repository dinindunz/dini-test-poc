"""
Code Analysis Tools for AI Agents

A code analysis tool set that provides intelligent indexing, advanced search, and detailed code analysis for Java and TypeScript codebases.

This tool set extracts all functionality from the original MCP server and presents it as easy-to-use tools for AI agents.
"""

import os
import re
import json
import time
import logging
import subprocess
import hashlib
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Tree-sitter imports
import tree_sitter
try:
    from tree_sitter_java import language as java_language
except ImportError:
    java_language = None
try:
    from tree_sitter_typescript import language_typescript as typescript_language
except ImportError:
    typescript_language = None
try:
    from tree_sitter_javascript import language as javascript_language
except ImportError:
    javascript_language = None

# File watching
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Pattern matching
import pathspec
import msgpack

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class LanguageType(Enum):
    JAVA = "java"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, method, etc.)"""
    type: str  # "function", "class", "method", "interface"
    file: str
    line: int
    signature: Optional[str] = None
    called_by: List[str] = None

    def __post_init__(self):
        if self.called_by is None:
            self.called_by = []


@dataclass
class FileInfo:
    """Information about a source file"""
    language: str
    line_count: int
    symbols: Dict[str, List[str]]
    imports: List[str]
    exports: Optional[List[str]] = None
    package: Optional[str] = None


@dataclass
class SearchResult:
    """Search result from code search"""
    file: str
    line_number: int
    line_content: str
    context_before: List[str] = None
    context_after: List[str] = None

    def __post_init__(self):
        if self.context_before is None:
            self.context_before = []
        if self.context_after is None:
            self.context_after = []


class ParsingStrategy:
    """Base class for language-specific parsing strategies"""

    def __init__(self, language_type: LanguageType):
        self.language_type = language_type
        self._setup_parser()

    def _setup_parser(self):
        if self.language_type == LanguageType.JAVA:
            if java_language is None:
                raise ImportError("tree-sitter-java not available")
            self.language = tree_sitter.Language(java_language())
        elif self.language_type == LanguageType.TYPESCRIPT:
            if typescript_language is None:
                raise ImportError("tree-sitter-typescript not available")
            self.language = tree_sitter.Language(typescript_language())
        elif self.language_type == LanguageType.JAVASCRIPT:
            if javascript_language is None:
                raise ImportError("tree-sitter-javascript not available")
            self.language = tree_sitter.Language(javascript_language())
        else:
            raise ValueError(f"Unsupported language: {self.language_type}")

    def parse_file(self, file_path: str, content: str) -> Tuple[Dict[str, SymbolInfo], FileInfo]:
        """Parse file and extract symbols and file info"""
        raise NotImplementedError

    def _create_symbol_id(self, file_path: str, symbol_name: str) -> str:
        """Create unique symbol ID"""
        return f"{file_path}::{symbol_name}"


class JavaParsingStrategy(ParsingStrategy):
    """Java-specific parsing strategy using tree-sitter"""

    def __init__(self):
        super().__init__(LanguageType.JAVA)

    def parse_file(self, file_path: str, content: str) -> Tuple[Dict[str, SymbolInfo], FileInfo]:
        symbols = {}
        functions = []
        classes = []
        imports = []
        package = None
        symbol_lookup = {}

        parser = tree_sitter.Parser(self.language)

        try:
            tree = parser.parse(content.encode('utf8'))

            # Extract package info
            for node in tree.root_node.children:
                if node.type == 'package_declaration':
                    package = self._extract_package(node, content)
                    break

            # Single-pass traversal
            self._traverse_node(tree.root_node, content, file_path, symbols,
                              functions, classes, imports, symbol_lookup)

        except Exception as e:
            logger.warning(f"Error parsing Java file {file_path}: {e}")

        file_info = FileInfo(
            language="java",
            line_count=len(content.splitlines()),
            symbols={"functions": functions, "classes": classes},
            imports=imports,
            package=package
        )

        return symbols, file_info

    def _traverse_node(self, node, content: str, file_path: str, symbols: Dict,
                      functions: List, classes: List, imports: List, symbol_lookup: Dict,
                      current_class: Optional[str] = None, current_method: Optional[str] = None):

        # Handle class declarations
        if node.type == 'class_declaration':
            name = self._get_identifier(node, content)
            if name:
                symbol_id = self._create_symbol_id(file_path, name)
                symbols[symbol_id] = SymbolInfo(
                    type="class",
                    file=file_path,
                    line=node.start_point[0] + 1
                )
                symbol_lookup[name] = symbol_id
                classes.append(name)

                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols,
                                      functions, classes, imports, symbol_lookup,
                                      current_class=name, current_method=current_method)
                return

        # Handle method declarations
        elif node.type == 'method_declaration':
            name = self._get_identifier(node, content)
            if name:
                full_name = f"{current_class}.{name}" if current_class else name
                symbol_id = self._create_symbol_id(file_path, full_name)
                symbols[symbol_id] = SymbolInfo(
                    type="method",
                    file=file_path,
                    line=node.start_point[0] + 1,
                    signature=self._get_signature(node, content)
                )
                symbol_lookup[full_name] = symbol_id
                symbol_lookup[name] = symbol_id
                functions.append(full_name)

                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols,
                                      functions, classes, imports, symbol_lookup,
                                      current_class=current_class, current_method=symbol_id)
                return

        # Handle method invocations
        elif node.type == 'method_invocation' and current_method:
            called_method = self._get_called_method(node, content)
            if called_method and called_method in symbol_lookup:
                symbol_id = symbol_lookup[called_method]
                if current_method not in symbols[symbol_id].called_by:
                    symbols[symbol_id].called_by.append(current_method)

        # Handle imports
        elif node.type == 'import_declaration':
            import_text = content[node.start_byte:node.end_byte]
            import_path = import_text.replace('import', '').replace(';', '').strip()
            if import_path:
                imports.append(import_path)

        # Continue traversing children
        for child in node.children:
            self._traverse_node(child, content, file_path, symbols, functions,
                              classes, imports, symbol_lookup, current_class, current_method)

    def _get_identifier(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
        return None

    def _get_signature(self, node, content: str) -> str:
        return content[node.start_byte:node.end_byte].split('\n')[0].strip()

    def _extract_package(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'scoped_identifier':
                return content[child.start_byte:child.end_byte]
        return None

    def _get_called_method(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'field_access':
                for subchild in child.children:
                    if subchild.type == 'identifier' and subchild.start_byte > child.start_byte:
                        return content[subchild.start_byte:subchild.end_byte]
            elif child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
        return None


class TypeScriptParsingStrategy(ParsingStrategy):
    """TypeScript-specific parsing strategy using tree-sitter"""

    def __init__(self):
        super().__init__(LanguageType.TYPESCRIPT)

    def parse_file(self, file_path: str, content: str) -> Tuple[Dict[str, SymbolInfo], FileInfo]:
        symbols = {}
        functions = []
        classes = []
        imports = []
        exports = []
        symbol_lookup = {}

        parser = tree_sitter.Parser(self.language)
        tree = parser.parse(content.encode('utf8'))

        self._traverse_node(tree.root_node, content, file_path, symbols,
                          functions, classes, imports, exports, symbol_lookup)

        file_info = FileInfo(
            language="typescript",
            line_count=len(content.splitlines()),
            symbols={"functions": functions, "classes": classes},
            imports=imports,
            exports=exports
        )

        return symbols, file_info

    def _traverse_node(self, node, content: str, file_path: str, symbols: Dict,
                      functions: List, classes: List, imports: List, exports: List,
                      symbol_lookup: Dict, current_function: Optional[str] = None,
                      current_class: Optional[str] = None):

        # Handle function declarations
        if node.type == 'function_declaration':
            name = self._get_identifier(node, content)
            if name:
                symbol_id = self._create_symbol_id(file_path, name)
                symbols[symbol_id] = SymbolInfo(
                    type="function",
                    file=file_path,
                    line=node.start_point[0] + 1,
                    signature=self._get_signature(node, content)
                )
                symbol_lookup[name] = symbol_id
                functions.append(name)

                func_context = f"{file_path}::{name}"
                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols, functions,
                                      classes, imports, exports, symbol_lookup,
                                      current_function=func_context, current_class=current_class)
                return

        # Handle class declarations
        elif node.type == 'class_declaration':
            name = self._get_identifier(node, content)
            if name:
                symbol_id = self._create_symbol_id(file_path, name)
                symbols[symbol_id] = SymbolInfo(
                    type="class",
                    file=file_path,
                    line=node.start_point[0] + 1
                )
                symbol_lookup[name] = symbol_id
                classes.append(name)

                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols, functions,
                                      classes, imports, exports, symbol_lookup,
                                      current_function=current_function, current_class=name)
                return

        # Handle interface declarations
        elif node.type == 'interface_declaration':
            name = self._get_type_identifier(node, content)
            if name:
                symbol_id = self._create_symbol_id(file_path, name)
                symbols[symbol_id] = SymbolInfo(
                    type="interface",
                    file=file_path,
                    line=node.start_point[0] + 1
                )
                symbol_lookup[name] = symbol_id
                classes.append(name)

                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols, functions,
                                      classes, imports, exports, symbol_lookup,
                                      current_function=current_function, current_class=name)
                return

        # Handle method definitions
        elif node.type == 'method_definition':
            method_name = self._get_property_identifier(node, content)
            if method_name and current_class:
                full_name = f"{current_class}.{method_name}"
                symbol_id = self._create_symbol_id(file_path, full_name)
                symbols[symbol_id] = SymbolInfo(
                    type="method",
                    file=file_path,
                    line=node.start_point[0] + 1,
                    signature=self._get_signature(node, content)
                )
                symbol_lookup[full_name] = symbol_id
                symbol_lookup[method_name] = symbol_id
                functions.append(full_name)

                method_context = f"{file_path}::{full_name}"
                for child in node.children:
                    self._traverse_node(child, content, file_path, symbols, functions,
                                      classes, imports, exports, symbol_lookup,
                                      current_function=method_context, current_class=current_class)
                return

        # Handle function calls
        elif node.type == 'call_expression' and current_function:
            called_function = self._get_called_function(node, content)
            if called_function and called_function in symbol_lookup:
                symbol_id = symbol_lookup[called_function]
                if current_function not in symbols[symbol_id].called_by:
                    symbols[symbol_id].called_by.append(current_function)

        # Handle imports
        elif node.type == 'import_statement':
            import_text = content[node.start_byte:node.end_byte]
            imports.append(import_text)

        # Handle exports
        elif node.type in ['export_statement', 'export_default_declaration']:
            export_text = content[node.start_byte:node.end_byte]
            exports.append(export_text)

        # Continue traversing children
        for child in node.children:
            self._traverse_node(child, content, file_path, symbols, functions,
                              classes, imports, exports, symbol_lookup,
                              current_function, current_class)

    def _get_identifier(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'identifier':
                return content[child.start_byte:child.end_byte]
        return None

    def _get_type_identifier(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'type_identifier':
                return content[child.start_byte:child.end_byte]
        return None

    def _get_property_identifier(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type == 'property_identifier':
                return content[child.start_byte:child.end_byte]
        return None

    def _get_signature(self, node, content: str) -> str:
        return content[node.start_byte:node.end_byte].split('\n')[0].strip()

    def _get_called_function(self, node, content: str) -> Optional[str]:
        if node.children:
            func_node = node.children[0]
            if func_node.type == 'identifier':
                return content[func_node.start_byte:func_node.end_byte]
            elif func_node.type == 'member_expression':
                for child in func_node.children:
                    if child.type == 'property_identifier':
                        return content[child.start_byte:child.end_byte]
        return None


class SearchTool:
    """Advanced search tool that automatically selects the best available command-line search utility"""

    def __init__(self):
        self.available_tools = self._detect_tools()
        self.preferred_tool = self._get_preferred_tool()

    def _detect_tools(self) -> List[str]:
        tools = []
        for tool in ['ugrep', 'rg', 'ag', 'grep']:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
                tools.append(tool)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return tools

    def _get_preferred_tool(self) -> str:
        """Get the preferred search tool in order of performance"""
        preference_order = ['ugrep', 'rg', 'ag', 'grep']
        for tool in preference_order:
            if tool in self.available_tools:
                return tool
        return 'grep'  # Fallback to system grep

    def search(self, pattern: str, base_path: str, case_sensitive: bool = True,
               context_lines: int = 0, file_pattern: Optional[str] = None,
               fuzzy: bool = False, regex: bool = False,
               max_line_length: Optional[int] = None) -> List[SearchResult]:
        """
        Search for patterns in code using the best available tool

        Args:
            pattern: Search pattern
            base_path: Directory to search in
            case_sensitive: Whether search should be case-sensitive
            context_lines: Number of context lines to show
            file_pattern: Glob pattern to filter files
            fuzzy: Enable fuzzy matching (tool-dependent)
            regex: Whether pattern is a regex
            max_line_length: Maximum line length to display

        Returns:
            List of SearchResult objects
        """
        if self.preferred_tool == 'ugrep':
            return self._search_ugrep(pattern, base_path, case_sensitive, context_lines,
                                    file_pattern, fuzzy, regex, max_line_length)
        elif self.preferred_tool == 'rg':
            return self._search_ripgrep(pattern, base_path, case_sensitive, context_lines,
                                      file_pattern, fuzzy, regex, max_line_length)
        elif self.preferred_tool == 'ag':
            return self._search_ag(pattern, base_path, case_sensitive, context_lines,
                                 file_pattern, fuzzy, regex, max_line_length)
        else:
            return self._search_grep(pattern, base_path, case_sensitive, context_lines,
                                   file_pattern, fuzzy, regex, max_line_length)

    def _search_ugrep(self, pattern, base_path, case_sensitive, context_lines,
                     file_pattern, fuzzy, regex, max_line_length) -> List[SearchResult]:
        cmd = ['ugrep', '-n']

        if not case_sensitive:
            cmd.append('-i')
        if context_lines > 0:
            cmd.extend(['-A', str(context_lines), '-B', str(context_lines)])
        if file_pattern:
            cmd.extend(['--include', file_pattern])
        if fuzzy:
            cmd.append('--fuzzy')
        if regex:
            cmd.append('-E')
        if max_line_length:
            cmd.extend(['--max-line-length', str(max_line_length)])

        cmd.extend([pattern, base_path])
        return self._execute_search(cmd)

    def _search_ripgrep(self, pattern, base_path, case_sensitive, context_lines,
                       file_pattern, fuzzy, regex, max_line_length) -> List[SearchResult]:
        cmd = ['rg', '-n']

        if not case_sensitive:
            cmd.append('-i')
        if context_lines > 0:
            cmd.extend(['-A', str(context_lines), '-B', str(context_lines)])
        if file_pattern:
            cmd.extend(['-g', file_pattern])
        if regex:
            cmd.append('-e')
        if max_line_length:
            cmd.extend(['-M', str(max_line_length)])

        cmd.extend([pattern, base_path])
        return self._execute_search(cmd)

    def _search_ag(self, pattern, base_path, case_sensitive, context_lines,
                  file_pattern, fuzzy, regex, max_line_length) -> List[SearchResult]:
        cmd = ['ag', '--line-numbers']

        if not case_sensitive:
            cmd.append('-i')
        if context_lines > 0:
            cmd.extend(['-A', str(context_lines), '-B', str(context_lines)])
        if file_pattern:
            cmd.extend(['--file-search-regex', file_pattern])

        cmd.extend([pattern, base_path])
        return self._execute_search(cmd)

    def _search_grep(self, pattern, base_path, case_sensitive, context_lines,
                    file_pattern, fuzzy, regex, max_line_length) -> List[SearchResult]:
        cmd = ['grep', '-rn']

        if not case_sensitive:
            cmd.append('-i')
        if context_lines > 0:
            cmd.extend(['-A', str(context_lines), '-B', str(context_lines)])
        if regex:
            cmd.append('-E')
        if file_pattern:
            cmd.extend(['--include', file_pattern])

        cmd.extend([pattern, base_path])
        return self._execute_search(cmd)

    def _execute_search(self, cmd: List[str]) -> List[SearchResult]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return self._parse_search_output(result.stdout)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:  # No matches found
                return []
            raise RuntimeError(f"Search command failed: {e}")

    def _parse_search_output(self, output: str) -> List[SearchResult]:
        results = []
        lines = output.strip().split('\n')

        for line in lines:
            if ':' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    try:
                        line_number = int(parts[1])
                        content = parts[2]
                        results.append(SearchResult(
                            file=file_path,
                            line_number=line_number,
                            line_content=content
                        ))
                    except ValueError:
                        continue

        return results


class FileWatcher:
    """File system watcher for automatic index updates"""

    def __init__(self, base_path: str, callback):
        self.base_path = base_path
        self.callback = callback
        self.observer = Observer()
        self.is_watching = False

        # File patterns to watch
        self.watch_patterns = ['*.java', '*.ts', '*.tsx', '*.js', '*.jsx']
        self.ignore_patterns = [
            '**/node_modules/**',
            '**/target/**',
            '**/build/**',
            '**/dist/**',
            '**/.git/**',
            '**/.vscode/**',
            '**/.idea/**'
        ]

    def start(self):
        if not self.is_watching:
            event_handler = CodeFileHandler(self.callback, self.watch_patterns, self.ignore_patterns)
            self.observer.schedule(event_handler, self.base_path, recursive=True)
            self.observer.start()
            self.is_watching = True

    def stop(self):
        if self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False


class CodeFileHandler(FileSystemEventHandler):
    """Handle file system events for code files"""

    def __init__(self, callback, watch_patterns, ignore_patterns):
        self.callback = callback
        self.spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        self.watch_extensions = {'.java', '.ts', '.tsx', '.js', '.jsx'}

    def on_modified(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self.callback(event.src_path, 'modified')

    def on_created(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self.callback(event.src_path, 'created')

    def on_deleted(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self.callback(event.src_path, 'deleted')

    def _should_process(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.suffix not in self.watch_extensions:
            return False
        return not self.spec.match_file(str(path))


class CodeIndexer:
    """Main class that provides all code analysis functionality"""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix='code_analysis_')
        self.base_path: Optional[str] = None
        self.index_data: Dict[str, Any] = {}
        self.file_watcher: Optional[FileWatcher] = None
        self.search_tool = SearchTool()

        # Initialise parsing strategies
        self.java_parser = JavaParsingStrategy()
        self.typescript_parser = TypeScriptParsingStrategy()

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

    def set_project_path(self, path: str) -> Dict[str, Any]:
        """
        Set the base project path and initialise indexing

        Args:
            path: Path to the project directory

        Returns:
            Dictionary with initialisation results
        """
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}

        if not os.path.isdir(path):
            return {"error": f"Path is not a directory: {path}"}

        self.base_path = os.path.abspath(path)

        # Stop existing file watcher
        if self.file_watcher:
            self.file_watcher.stop()

        # Build initial index
        start_time = time.time()
        self._build_index()
        build_time = time.time() - start_time

        # Start file watcher
        self.file_watcher = FileWatcher(self.base_path, self._on_file_change)
        self.file_watcher.start()

        file_count = len(self.index_data.get('files', {}))

        return {
            "success": True,
            "message": f"Project initialised at {self.base_path}",
            "file_count": file_count,
            "build_time": round(build_time, 2),
            "cache_location": self.cache_dir
        }

    def _build_index(self):
        """Build the complete project index"""
        if not self.base_path:
            return

        self.index_data = {
            "files": {},
            "symbols": {},
            "file_list": []
        }

        # Find all relevant files
        for root, dirs, files in os.walk(self.base_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                      ['node_modules', 'target', 'build', 'dist']]

            for file in files:
                if self._is_code_file(file):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.base_path)
                    self._index_file(file_path, rel_path)

        # Save index to cache
        self._save_index()

    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a supported code file"""
        return any(filename.endswith(ext) for ext in ['.java', '.ts', '.tsx', '.js', '.jsx'])

    def _index_file(self, file_path: str, rel_path: str):
        """Index a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Determine parser based on file extension
            ext = Path(file_path).suffix.lower()
            if ext == '.java':
                symbols, file_info = self.java_parser.parse_file(file_path, content)
            elif ext in ['.ts', '.tsx']:
                symbols, file_info = self.typescript_parser.parse_file(file_path, content)
            else:
                # Use JavaScript parser for .js/.jsx files
                js_parser = TypeScriptParsingStrategy()  # Can handle JS too
                symbols, file_info = js_parser.parse_file(file_path, content)

            # Store in index
            self.index_data["files"][rel_path] = asdict(file_info)
            self.index_data["symbols"].update({k: asdict(v) for k, v in symbols.items()})
            self.index_data["file_list"].append(rel_path)

        except Exception as e:
            logger.warning(f"Failed to index {file_path}: {e}")

    def _save_index(self):
        """Save index to cache file"""
        cache_file = os.path.join(self.cache_dir, 'index.msgpack')
        with open(cache_file, 'wb') as f:
            msgpack.pack(self.index_data, f)

    def _load_index(self) -> bool:
        """Load index from cache file"""
        cache_file = os.path.join(self.cache_dir, 'index.msgpack')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    self.index_data = msgpack.unpack(f)
                return True
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return False

    def _on_file_change(self, file_path: str, event_type: str):
        """Handle file system events"""
        if not self.base_path:
            return

        rel_path = os.path.relpath(file_path, self.base_path)

        if event_type == 'deleted':
            # Remove from index
            if rel_path in self.index_data.get("files", {}):
                del self.index_data["files"][rel_path]
            if rel_path in self.index_data.get("file_list", []):
                self.index_data["file_list"].remove(rel_path)
        else:
            # Re-index file
            if os.path.exists(file_path):
                self._index_file(file_path, rel_path)

        self._save_index()

    def find_files(self, pattern: str) -> List[str]:
        """
        Find files matching a glob pattern

        Args:
            pattern: Glob pattern (e.g., "*.java", "**/*.ts")

        Returns:
            List of matching file paths
        """
        if not self.index_data:
            return []

        import fnmatch
        files = self.index_data.get("file_list", [])

        # Support both filename-only and full path matching
        matches = []
        for file_path in files:
            # Check full path match
            if fnmatch.fnmatch(file_path, pattern):
                matches.append(file_path)
            # Check filename-only match
            elif fnmatch.fnmatch(os.path.basename(file_path), pattern):
                matches.append(file_path)

        return sorted(matches)

    def search_code(self, pattern: str, case_sensitive: bool = True,
                   context_lines: int = 0, file_pattern: Optional[str] = None,
                   fuzzy: bool = False, regex: bool = False,
                   max_line_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for code patterns in the project

        Args:
            pattern: Search pattern
            case_sensitive: Whether search should be case-sensitive
            context_lines: Number of context lines to show
            file_pattern: Glob pattern to filter files
            fuzzy: Enable fuzzy matching
            regex: Whether pattern is a regex
            max_line_length: Maximum line length to display

        Returns:
            Dictionary with search results
        """
        if not self.base_path:
            return {"error": "No project path set"}

        try:
            results = self.search_tool.search(
                pattern=pattern,
                base_path=self.base_path,
                case_sensitive=case_sensitive,
                context_lines=context_lines,
                file_pattern=file_pattern,
                fuzzy=fuzzy,
                regex=regex,
                max_line_length=max_line_length
            )

            return {
                "success": True,
                "results": [asdict(r) for r in results],
                "total_matches": len(results),
                "search_tool": self.search_tool.preferred_tool
            }
        except Exception as e:
            return {"error": f"Search failed: {e}"}

    def analyse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed analysis of a specific file

        Args:
            file_path: Path to the file (relative to project root)

        Returns:
            Dictionary with file analysis
        """
        if not self.index_data:
            return {"error": "No project indexed"}

        # Normalise path
        if file_path.startswith(self.base_path or ''):
            rel_path = os.path.relpath(file_path, self.base_path)
        else:
            rel_path = file_path

        if rel_path in self.index_data.get("files", {}):
            file_info = self.index_data["files"][rel_path]

            # Find symbols in this file
            file_symbols = {}
            for symbol_id, symbol_info in self.index_data.get("symbols", {}).items():
                if symbol_info["file"] == os.path.join(self.base_path or '', rel_path):
                    file_symbols[symbol_id] = symbol_info

            return {
                "success": True,
                "file_path": rel_path,
                "file_info": file_info,
                "symbols": file_symbols
            }
        else:
            return {"error": f"File not found in index: {rel_path}"}

    def get_project_structure(self) -> Dict[str, Any]:
        """
        Get the project structure as a tree

        Returns:
            Dictionary representing the project structure
        """
        if not self.index_data:
            return {"error": "No project indexed"}

        files = self.index_data.get("file_list", [])
        structure = {}

        for file_path in files:
            parts = file_path.split(os.sep)
            current = structure

            for part in parts[:-1]:  # All except filename
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Add file
            filename = parts[-1]
            current[filename] = "file"

        return {
            "success": True,
            "structure": structure,
            "total_files": len(files)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get project statistics

        Returns:
            Dictionary with project statistics
        """
        if not self.index_data:
            return {"error": "No project indexed"}

        files = self.index_data.get("files", {})
        symbols = self.index_data.get("symbols", {})

        # Count by language
        lang_counts = {}
        total_lines = 0

        for file_info in files.values():
            lang = file_info.get("language", "unknown")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            total_lines += file_info.get("line_count", 0)

        # Count by symbol type
        symbol_counts = {}
        for symbol_info in symbols.values():
            symbol_type = symbol_info.get("type", "unknown")
            symbol_counts[symbol_type] = symbol_counts.get(symbol_type, 0) + 1

        return {
            "success": True,
            "total_files": len(files),
            "total_lines": total_lines,
            "languages": lang_counts,
            "symbols": symbol_counts,
            "search_tools": self.search_tool.available_tools,
            "preferred_search_tool": self.search_tool.preferred_tool
        }

    def refresh_index(self) -> Dict[str, Any]:
        """
        Manually refresh the entire project index

        Returns:
            Dictionary with refresh results
        """
        if not self.base_path:
            return {"error": "No project path set"}

        start_time = time.time()
        self._build_index()
        build_time = time.time() - start_time

        file_count = len(self.index_data.get("files", {}))

        return {
            "success": True,
            "message": "Index refreshed successfully",
            "file_count": file_count,
            "build_time": round(build_time, 2)
        }

    def shutdown(self):
        """Clean shutdown of the indexer"""
        if self.file_watcher:
            self.file_watcher.stop()