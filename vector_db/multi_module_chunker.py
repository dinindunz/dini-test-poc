# multi_module_chunker.py
import os
import json
import yaml
import re
from pathlib import Path
from typing import List, Dict
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

class MultiModuleChunker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.chunks = []
        self.java_parser = self._init_java_parser()
        
    def _init_java_parser(self):
        JAVA_LANGUAGE = get_language('java')
        parser = Parser()
        parser.set_language(JAVA_LANGUAGE)
        return parser
    
    def process_all_modules(self):
        """Process all dini modules"""
        # Find all module directories
        modules = [d for d in self.root_dir.glob("*_dini_*") if d.is_dir()]

        print(f"Found {len(modules)} modules to process:")
        for module in modules:
            print(f"  - {module.name}")
        
        for module_path in modules:
            print(f"\n{'='*60}")
            print(f"Processing module: {module_path.name}")
            print(f"{'='*60}")
            self.process_module(module_path)
        
        return self.chunks
    
    def process_module(self, module_path: Path):
        """Process a single module"""
        module_name = module_path.name
        
        # 1. Process Java files
        java_files = list(module_path.rglob("*.java"))
        print(f"\nFound {len(java_files)} Java files")
        for java_file in java_files:
            self.chunk_java_file(java_file, module_name)
        
        # 2. Process Swagger/YAML files
        yaml_files = list(module_path.rglob("*.yaml")) + list(module_path.rglob("*.yml"))
        swagger_files = [f for f in yaml_files if 'swagger' in f.name.lower() or 'api' in str(f.parent).lower()]
        print(f"Found {len(swagger_files)} Swagger/API files")
        for swagger_file in swagger_files:
            self.chunk_swagger_file(swagger_file, module_name)
        
        # 3. Process Markdown files
        md_files = list(module_path.rglob("*.md"))
        print(f"Found {len(md_files)} Markdown files")
        for md_file in md_files:
            self.chunk_markdown_file(md_file, module_name)
        
        # 4. Process build.gradle
        gradle_files = list(module_path.rglob("build.gradle"))
        print(f"Found {len(gradle_files)} Gradle files")
        for gradle_file in gradle_files:
            self.chunk_gradle_file(gradle_file, module_name)
    
    # ==================== JAVA FILE CHUNKING ====================
    
    def chunk_java_file(self, file_path: Path, module_name: str):
        """Chunk Java file using AST"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = self.java_parser.parse(bytes(content, "utf8"))
            
            # Extract package and imports
            package_name = self._extract_package(content)
            imports = self._extract_imports(content)
            
            # Find all classes
            class_nodes = self._find_nodes_by_type(tree.root_node, 'class_declaration')
            
            for class_node in class_nodes:
                class_name = self._get_identifier(class_node, 'identifier')
                
                # Check class size - if small, chunk as whole class
                class_content = content[class_node.start_byte:class_node.end_byte]
                
                if len(class_content) < 10000:  # ~300 lines
                    # Chunk entire class
                    self._add_chunk({
                        'content': class_content,
                        'full_content_with_imports': self._build_complete_content(imports, class_content),
                        'type': 'class',
                        'file_type': 'java',
                        'module': module_name,
                        'file_path': str(file_path.relative_to(self.root_dir)),
                        'package': package_name,
                        'class_name': class_name,
                        'layer': self._determine_layer(file_path),
                        'imports': imports,
                        'annotations': self._extract_annotations(class_node, content),
                        'line_start': class_node.start_point[0] + 1,
                        'line_end': class_node.end_point[0] + 1,
                    })
                else:
                    # Large class - chunk by methods
                    self._chunk_methods(class_node, content, file_path, module_name, 
                                       package_name, class_name, imports)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    def _chunk_methods(self, class_node, content, file_path, module_name, 
                       package_name, class_name, imports):
        """Chunk individual methods in a class"""
        method_nodes = self._find_nodes_by_type(class_node, 'method_declaration')
        
        for method_node in method_nodes:
            method_name = self._get_identifier(method_node, 'identifier')
            method_content = content[method_node.start_byte:method_node.end_byte]
            
            self._add_chunk({
                'content': method_content,
                'full_content_with_imports': self._build_complete_content(imports, method_content),
                'type': 'method',
                'file_type': 'java',
                'module': module_name,
                'file_path': str(file_path.relative_to(self.root_dir)),
                'package': package_name,
                'class_name': class_name,
                'method_name': method_name,
                'layer': self._determine_layer(file_path),
                'imports': imports,
                'annotations': self._extract_annotations(method_node, content),
                'is_api_endpoint': self._is_rest_endpoint(method_node, content),
                'http_method': self._extract_http_method(method_node, content),
                'api_path': self._extract_api_path(method_node, content),
                'line_start': method_node.start_point[0] + 1,
                'line_end': method_node.end_point[0] + 1,
            })
    
    # ==================== SWAGGER FILE CHUNKING ====================
    
    def chunk_swagger_file(self, file_path: Path, module_name: str):
        """Chunk Swagger/OpenAPI file by endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                swagger_doc = yaml.safe_load(f)
            
            # Add info section as a chunk
            if 'info' in swagger_doc:
                self._add_chunk({
                    'content': yaml.dump({'info': swagger_doc['info']}, default_flow_style=False),
                    'type': 'api_info',
                    'file_type': 'swagger',
                    'module': module_name,
                    'file_path': str(file_path.relative_to(self.root_dir)),
                    'api_title': swagger_doc['info'].get('title', ''),
                    'api_version': swagger_doc['info'].get('version', ''),
                    'description': swagger_doc['info'].get('description', ''),
                })
            
            # Chunk by paths (endpoints)
            if 'paths' in swagger_doc:
                for path, path_item in swagger_doc['paths'].items():
                    for method, operation in path_item.items():
                        if method in ['get', 'post', 'put', 'delete', 'patch']:
                            
                            # Build complete endpoint definition
                            endpoint_def = {
                                'path': path,
                                'method': method,
                                'operation': operation
                            }
                            
                            # Include related schemas if referenced
                            schemas = self._extract_referenced_schemas(operation, swagger_doc)
                            if schemas:
                                endpoint_def['schemas'] = schemas
                            
                            self._add_chunk({
                                'content': yaml.dump(endpoint_def, default_flow_style=False),
                                'type': 'api_endpoint',
                                'file_type': 'swagger',
                                'module': module_name,
                                'file_path': str(file_path.relative_to(self.root_dir)),
                                'http_method': method.upper(),
                                'api_path': path,
                                'operation_id': operation.get('operationId', ''),
                                'summary': operation.get('summary', ''),
                                'description': operation.get('description', ''),
                                'tags': operation.get('tags', []),
                                'parameters': [p.get('name') for p in operation.get('parameters', [])],
                                'request_body': operation.get('requestBody', {}).get('required', False),
                                'responses': list(operation.get('responses', {}).keys()),
                            })
            
            # Chunk schemas/definitions separately
            schema_section = swagger_doc.get('components', {}).get('schemas', {}) or swagger_doc.get('definitions', {})
            if schema_section:
                for schema_name, schema_def in schema_section.items():
                    self._add_chunk({
                        'content': yaml.dump({schema_name: schema_def}, default_flow_style=False),
                        'type': 'api_schema',
                        'file_type': 'swagger',
                        'module': module_name,
                        'file_path': str(file_path.relative_to(self.root_dir)),
                        'schema_name': schema_name,
                        'properties': list(schema_def.get('properties', {}).keys()) if isinstance(schema_def, dict) else [],
                        'required_fields': schema_def.get('required', []) if isinstance(schema_def, dict) else [],
                    })
        
        except Exception as e:
            print(f"Error processing Swagger file {file_path}: {e}")
    
    # ==================== MARKDOWN FILE CHUNKING ====================
    
    def chunk_markdown_file(self, file_path: Path, module_name: str):
        """Chunk Markdown by heading sections"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Split by headers (# ## ### etc)
            sections = self._split_markdown_by_headers(content)
            
            for idx, section in enumerate(sections):
                heading = section.get('heading', '')
                heading_level = section.get('level', 0)
                section_content = section.get('content', '')
                
                if not section_content.strip():
                    continue
                
                self._add_chunk({
                    'content': section_content,
                    'type': 'documentation',
                    'file_type': 'markdown',
                    'module': module_name,
                    'file_path': str(file_path.relative_to(self.root_dir)),
                    'document_name': file_path.stem,
                    'heading': heading,
                    'heading_level': heading_level,
                    'section_index': idx,
                    'contains_code': '```' in section_content,
                    'word_count': len(section_content.split()),
                })
        
        except Exception as e:
            print(f"Error processing Markdown file {file_path}: {e}")
    
    # ==================== GRADLE FILE CHUNKING ====================
    
    def chunk_gradle_file(self, file_path: Path, module_name: str):
        """Chunk Gradle file by major blocks"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse Gradle blocks
            blocks = self._parse_gradle_blocks(content)
            
            # Add full gradle file as one chunk for context
            self._add_chunk({
                'content': content,
                'type': 'build_config_full',
                'file_type': 'gradle',
                'module': module_name,
                'file_path': str(file_path.relative_to(self.root_dir)),
                'java_version': self._extract_java_version(content),
                'spring_boot_version': self._extract_spring_boot_version(content),
                'dependencies_count': content.count('implementation') + content.count('compile'),
            })
            
            # Chunk dependencies separately
            dependencies = self._extract_dependencies(content)
            if dependencies:
                self._add_chunk({
                    'content': dependencies,
                    'type': 'dependencies',
                    'file_type': 'gradle',
                    'module': module_name,
                    'file_path': str(file_path.relative_to(self.root_dir)),
                    'dependency_list': self._parse_dependency_list(dependencies),
                })
            
            # Chunk plugins
            plugins = self._extract_plugins(content)
            if plugins:
                self._add_chunk({
                    'content': plugins,
                    'type': 'plugins',
                    'file_type': 'gradle',
                    'module': module_name,
                    'file_path': str(file_path.relative_to(self.root_dir)),
                    'plugin_list': self._parse_plugin_list(plugins),
                })
        
        except Exception as e:
            print(f"Error processing Gradle file {file_path}: {e}")
    
    # ==================== HELPER METHODS ====================
    
    def _add_chunk(self, chunk_data: Dict):
        """Add chunk with auto-generated ID"""
        chunk_data['chunk_id'] = f"{chunk_data['module']}_{len(self.chunks)}"
        chunk_data['char_count'] = len(chunk_data['content'])
        self.chunks.append(chunk_data)
    
    def _determine_layer(self, file_path: Path) -> str:
        """Determine architectural layer from path"""
        path_str = str(file_path).lower()
        if '/controller/' in path_str:
            return 'controller'
        elif '/service/' in path_str:
            return 'service'
        elif '/config/' in path_str:
            return 'config'
        elif '/exception/' in path_str:
            return 'exception'
        elif '/model/' in path_str or '/entity/' in path_str:
            return 'model'
        elif '/repository/' in path_str:
            return 'repository'
        elif '/dto/' in path_str:
            return 'dto'
        return 'other'
    
    def _extract_package(self, content: str) -> str:
        """Extract package declaration"""
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else ''
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        return re.findall(r'import\s+([\w.*]+);', content)
    
    def _build_complete_content(self, imports: List[str], content: str) -> str:
        """Build complete code with imports for better context"""
        import_section = '\n'.join([f'import {imp};' for imp in imports[:10]])  # Top 10 imports
        return f"{import_section}\n\n{content}"
    
    def _find_nodes_by_type(self, node, node_type: str) -> List:
        """Recursively find all nodes of a specific type"""
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(self._find_nodes_by_type(child, node_type))
        return results
    
    def _get_identifier(self, node, identifier_type: str = 'identifier') -> str:
        """Extract identifier name from node"""
        for child in node.children:
            if child.type == identifier_type:
                return child.text.decode('utf8')
        return 'unknown'
    
    def _extract_annotations(self, node, content: str) -> List[str]:
        """Extract annotations from a node"""
        annotations = []
        # Look backwards from node for annotations
        lines_before = content[:node.start_byte].split('\n')
        for line in reversed(lines_before[-10:]):  # Check last 10 lines
            line = line.strip()
            if line.startswith('@'):
                annotations.append(line)
            elif line and not line.startswith('//'):
                break
        return list(reversed(annotations))
    
    def _is_rest_endpoint(self, node, content: str) -> bool:
        """Check if method is a REST endpoint"""
        annotations = self._extract_annotations(node, content)
        rest_annotations = ['@GetMapping', '@PostMapping', '@PutMapping', '@DeleteMapping', '@RequestMapping']
        return any(any(ra in ann for ra in rest_annotations) for ann in annotations)
    
    def _extract_http_method(self, node, content: str) -> str:
        """Extract HTTP method from annotations"""
        annotations = self._extract_annotations(node, content)
        for ann in annotations:
            if '@GetMapping' in ann:
                return 'GET'
            elif '@PostMapping' in ann:
                return 'POST'
            elif '@PutMapping' in ann:
                return 'PUT'
            elif '@DeleteMapping' in ann:
                return 'DELETE'
        return ''
    
    def _extract_api_path(self, node, content: str) -> str:
        """Extract API path from annotations"""
        annotations = self._extract_annotations(node, content)
        for ann in annotations:
            # Match patterns like @GetMapping("/path") or @GetMapping(value = "/path")
            match = re.search(r'["\']([/\w\-{}]+)["\']', ann)
            if match:
                return match.group(1)
        return ''
    
    def _split_markdown_by_headers(self, content: str) -> List[Dict]:
        """Split markdown content by headers"""
        lines = content.split('\n')
        sections = []
        current_section = {'heading': '', 'level': 0, 'content': ''}
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(line) - len(line.lstrip('#'))
                heading = line.lstrip('#').strip()
                current_section = {
                    'heading': heading,
                    'level': level,
                    'content': line + '\n'
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add last section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _parse_gradle_blocks(self, content: str) -> Dict:
        """Parse major blocks in Gradle file"""
        blocks = {}
        # This is simplified - you might want more sophisticated parsing
        return blocks
    
    def _extract_dependencies(self, content: str) -> str:
        """Extract dependencies block"""
        match = re.search(r'dependencies\s*\{([^}]+)\}', content, re.DOTALL)
        return match.group(0) if match else ''
    
    def _extract_plugins(self, content: str) -> str:
        """Extract plugins block"""
        match = re.search(r'plugins\s*\{([^}]+)\}', content, re.DOTALL)
        return match.group(0) if match else ''
    
    def _extract_java_version(self, content: str) -> str:
        """Extract Java version from Gradle"""
        match = re.search(r'sourceCompatibility\s*=\s*["\']?(\d+)', content)
        if not match:
            match = re.search(r'JavaVersion\.VERSION_(\d+)', content)
        return match.group(1) if match else ''
    
    def _extract_spring_boot_version(self, content: str) -> str:
        """Extract Spring Boot version"""
        match = re.search(r'org\.springframework\.boot["\'].*?version\s+["\']([^"\']+)', content)
        return match.group(1) if match else ''
    
    def _parse_dependency_list(self, deps: str) -> List[str]:
        """Parse individual dependencies"""
        return re.findall(r'["\']([^"\']+:[^"\']+:[^"\']+)["\']', deps)
    
    def _parse_plugin_list(self, plugins: str) -> List[str]:
        """Parse individual plugins"""
        return re.findall(r'id\s+["\']([^"\']+)["\']', plugins)
    
    def _extract_referenced_schemas(self, operation: Dict, swagger_doc: Dict) -> Dict:
        """Extract schemas referenced in an operation"""
        schemas = {}
        # Look for $ref in operation
        def find_refs(obj, found_schemas):
            if isinstance(obj, dict):
                if '$ref' in obj:
                    ref = obj['$ref']
                    schema_name = ref.split('/')[-1]
                    schema_path = swagger_doc.get('components', {}).get('schemas', {}) or swagger_doc.get('definitions', {})
                    if schema_name in schema_path:
                        found_schemas[schema_name] = schema_path[schema_name]
                for value in obj.values():
                    find_refs(value, found_schemas)
            elif isinstance(obj, list):
                for item in obj:
                    find_refs(item, found_schemas)
        
        find_refs(operation, schemas)
        return schemas
    
    def save_chunks(self, output_file: str):
        """Save all chunks to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(self.chunks)} chunks to {output_file}")
    
    def print_statistics(self):
        """Print chunking statistics"""
        print(f"\n{'='*60}")
        print("CHUNKING STATISTICS")
        print(f"{'='*60}")
        
        # By module
        modules = {}
        for chunk in self.chunks:
            module = chunk['module']
            modules[module] = modules.get(module, 0) + 1
        
        print("\n📦 Chunks per module:")
        for module, count in sorted(modules.items()):
            print(f"  {module}: {count}")
        
        # By file type
        file_types = {}
        for chunk in self.chunks:
            ftype = chunk['file_type']
            file_types[ftype] = file_types.get(ftype, 0) + 1
        
        print("\n📄 Chunks per file type:")
        for ftype, count in sorted(file_types.items()):
            print(f"  {ftype}: {count}")
        
        # By type
        types = {}
        for chunk in self.chunks:
            ctype = chunk['type']
            types[ctype] = types.get(ctype, 0) + 1
        
        print("\n🏷️  Chunks per type:")
        for ctype, count in sorted(types.items()):
            print(f"  {ctype}: {count}")
        
        print(f"\n📊 Total chunks: {len(self.chunks)}")


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    import sys
    
    # Usage: python multi_module_chunker.py /path/to/java17
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "../container/java17"
    
    print(f"🚀 Starting multi-module chunking for: {root_directory}")
    
    chunker = MultiModuleChunker(root_directory)
    chunks = chunker.process_all_modules()
    
    # Print statistics
    chunker.print_statistics()
    
    # Save to file
    chunker.save_chunks("chunks_output.json")
    
    # Save a sample for review
    sample_chunks = chunks[:10]
    with open("chunks_sample.json", 'w', encoding='utf-8') as f:
        json.dump(sample_chunks, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved 10 sample chunks to chunks_sample.json")
