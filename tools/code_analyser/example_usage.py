"""
Example usage of the Code Analysis Tools for AI Agents

This script demonstrates how to use all the available tools
to analyse Java and TypeScript codebases.
"""

from ai_agent_tools import *
import os
import json


def main():
    print("Code Analysis Tools - Example Usage")
    print("==================================\n")

    # Step 1: Initialise the analyser
    print("1. Initialsing code analyser...")
    result = initialise_code_analyser()
    if result.get("error"):
        print(f"Error: {result['error']}")
        return
    print(f"✓ {result['message']}")
    print(f"  Cache directory: {result['cache_dir']}\n")

    # Step 2: Set project path (you'll need to update this path)
    project_path = input("Enter the path to your Java/TypeScript project: ").strip()
    if not project_path:
        # Use the current directory's test samples as an example
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_path = os.path.join(os.path.dirname(current_dir), "test", "sample-projects", "python")
        print(f"Using sample project: {project_path}")

    if not os.path.exists(project_path):
        print(f"Error: Project path does not exist: {project_path}")
        return

    print(f"\n2. Setting project path: {project_path}")
    result = set_project_path(project_path)
    if result.get("error"):
        print(f"Error: {result['error']}")
        return
    print(f"✓ {result['message']}")
    print(f"  Files indexed: {result['file_count']}")
    print(f"  Build time: {result['build_time']} seconds\n")

    # Step 3: Get project structure
    print("3. Getting project structure...")
    structure = get_project_structure()
    if structure.get("error"):
        print(f"Error: {structure['error']}")
    else:
        print(f"✓ Project structure (total files: {structure['total_files']})")
        print(json.dumps(structure['structure'], indent=2)[:500] + "...\n")

    # Step 4: Get project statistics
    print("4. Getting project statistics...")
    stats = get_project_statistics()
    if stats.get("error"):
        print(f"Error: {stats['error']}")
    else:
        print("✓ Project Statistics:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total lines: {stats['total_lines']}")
        print(f"  Languages: {stats['languages']}")
        print(f"  Symbols: {stats['symbols']}")
        print(f"  Search tools: {stats['search_tools']}")
        print(f"  Preferred search tool: {stats['preferred_search_tool']}\n")

    # Step 5: Find files
    print("5. Finding files...")
    java_files = find_files("*.java")
    ts_files = find_files("*.ts")
    print(f"✓ Found {len(java_files)} Java files")
    print(f"✓ Found {len(ts_files)} TypeScript files")
    if java_files:
        print(f"  Example Java files: {java_files[:3]}")
    if ts_files:
        print(f"  Example TypeScript files: {ts_files[:3]}")
    print()

    # Step 6: Search for code patterns
    print("6. Searching code...")
    search_terms = ["class", "function", "import"]
    for term in search_terms:
        result = search_code(term, context_lines=1)
        if result.get("error"):
            print(f"Error searching for '{term}': {result['error']}")
        else:
            print(f"✓ Found {result['total_matches']} matches for '{term}' using {result['search_tool']}")
            if result['results']:
                first_match = result['results'][0]
                print(f"  First match in: {first_match['file']}:{first_match['line_number']}")
    print()

    # Step 7: Analyse specific files
    all_files = java_files + ts_files
    if all_files:
        print("7. Analysing specific files...")
        for file_path in all_files[:2]:  # Analyse first 2 files
            analysis = analyse_file(file_path)
            if analysis.get("error"):
                print(f"Error analysing {file_path}: {analysis['error']}")
            else:
                file_info = analysis['file_info']
                symbols = analysis['symbols']
                print(f"✓ Analysis of {file_path}:")
                print(f"  Language: {file_info['language']}")
                print(f"  Lines: {file_info['line_count']}")
                print(f"  Functions: {len(file_info['symbols'].get('functions', []))}")
                print(f"  Classes: {len(file_info['symbols'].get('classes', []))}")
                print(f"  Imports: {len(file_info['imports'])}")
                print(f"  Total symbols: {len(symbols)}")
        print()

    # Step 8: Find symbol usage
    print("8. Finding symbol usage...")
    # Try to find some common symbols
    common_symbols = ["main", "toString", "User", "Service"]
    for symbol in common_symbols:
        result = find_symbol_usage(symbol)
        if result.get("error"):
            print(f"Error finding symbol '{symbol}': {result['error']}")
        elif result['total_matches'] > 0:
            print(f"✓ Found {result['total_matches']} symbols matching '{symbol}'")
            if result['matches']:
                first_match = result['matches'][0]
                print(f"  First match: {first_match['symbol_name']} ({first_match['type']}) in {first_match['file']}")
            break
    print()

    # Step 9: Find function call relationships
    print("9. Finding function call relationships...")
    if all_files:
        # Analyse the first file to find functions
        analysis = analyse_file(all_files[0])
        if not analysis.get("error"):
            file_info = analysis['file_info']
            functions = file_info['symbols'].get('functions', [])
            if functions:
                func_name = functions[0].split('.')[-1]  # Get just the method name
                result = find_functions_calling(func_name)
                if result.get("error"):
                    print(f"Error finding callers of '{func_name}': {result['error']}")
                else:
                    print(f"✓ Function '{func_name}' is called by {result['total_callers']} other functions")
                    if result['callers']:
                        for caller in result['callers'][:2]:  # Show first 2 callers
                            print(f"  Called by: {caller['symbol_id']}")
    print()

    # Step 10: Get file imports
    if all_files:
        print("10. Getting file imports...")
        file_path = all_files[0]
        imports = get_file_imports(file_path)
        if imports.get("error"):
            print(f"Error getting imports for {file_path}: {imports['error']}")
        else:
            print(f"✓ Imports for {file_path}:")
            print(f"  Total imports: {imports['total_imports']}")
            if imports['imports']:
                for imp in imports['imports'][:3]:  # Show first 3 imports
                    print(f"  Import: {imp}")
            if imports.get('package'):
                print(f"  Package: {imports['package']}")
        print()

    # Step 11: Search within a specific file
    if all_files:
        print("11. Searching within a specific file...")
        file_path = all_files[0]
        result = search_in_file(file_path, "class", regex=False)
        if result.get("error"):
            print(f"Error searching in {file_path}: {result['error']}")
        else:
            print(f"✓ Found {result['total_matches']} matches for 'class' in {file_path}")
            if result['matches']:
                for match in result['matches'][:2]:  # Show first 2 matches
                    print(f"  Line {match['line_number']}: {match['line_content'].strip()}")
        print()

    # Step 12: Clean shutdown
    print("12. Shutting down analyser...")
    shutdown_analyser()
    print("✓ Analyser shut down successfully")

    print("\nExample usage completed!")


if __name__ == "__main__":
    main()