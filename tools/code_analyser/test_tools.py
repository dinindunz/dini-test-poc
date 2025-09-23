#!/usr/bin/env python3
"""
Test script for the Code Analysis Tools

This script tests all the functionality with the sample Java and TypeScript files.
"""

from ai_agent_tools import *
import os

def test_tools():
    print("Testing Code Analysis Tools")
    print("===========================\n")

    # Test 1: Initialise analyser
    print("1. Testing analyser initialisation...")
    result = initialise_code_analyser()
    assert result.get("success", False), f"Initialisation failed: {result}"
    print(f"✓ Initialised successfully: {result['message']}")
    print(f"  Cache directory: {result['cache_dir']}\n")

    # Test 2: Set project path
    test_project_path = os.path.join(os.getcwd(), "test_project")
    print(f"2. Testing project setup with: {test_project_path}")
    result = set_project_path(test_project_path)
    assert result.get("success", False), f"Project setup failed: {result}"
    print(f"✓ Project setup successful: {result['message']}")
    print(f"  Files indexed: {result['file_count']}")
    print(f"  Build time: {result['build_time']} seconds\n")

    # Test 3: Find files
    print("3. Testing file discovery...")
    java_files = find_files("*.java")
    ts_files = find_files("*.ts")
    print(f"✓ Found {len(java_files)} Java files: {java_files}")
    print(f"✓ Found {len(ts_files)} TypeScript files: {ts_files}\n")

    # Test 4: Project structure
    print("4. Testing project structure...")
    structure = get_project_structure()
    assert structure.get("success", False), f"Structure failed: {structure}"
    print(f"✓ Project structure retrieved (total files: {structure['total_files']})")
    print(f"  Structure: {structure['structure']}\n")

    # Test 5: Project statistics
    print("5. Testing project statistics...")
    stats = get_project_statistics()
    assert stats.get("success", False), f"Statistics failed: {stats}"
    print(f"✓ Project statistics:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total lines: {stats['total_lines']}")
    print(f"  Languages: {stats['languages']}")
    print(f"  Symbols: {stats['symbols']}")
    print(f"  Search tools: {stats['search_tools']}")
    print(f"  Preferred search tool: {stats['preferred_search_tool']}\n")

    # Test 6: Code search
    print("6. Testing code search...")
    search_result = search_code("class", case_sensitive=False, context_lines=1)
    assert search_result.get("success", False), f"Search failed: {search_result}"
    print(f"✓ Search successful: {search_result['total_matches']} matches found")
    if search_result['results']:
        first_match = search_result['results'][0]
        print(f"  First match: {first_match['file']}:{first_match['line_number']}")
        print(f"  Content: {first_match['line_content']}")
    print()

    # Test 7: File analysis
    if java_files:
        print("7. Testing file analysis (Java)...")
        analysis = analyse_file(java_files[0])
        assert analysis.get("success", False), f"Analysis failed: {analysis}"
        file_info = analysis['file_info']
        print(f"✓ Analysis of {java_files[0]}:")
        print(f"  Language: {file_info['language']}")
        print(f"  Lines: {file_info['line_count']}")
        print(f"  Functions: {len(file_info['symbols'].get('functions', []))}")
        print(f"  Classes: {len(file_info['symbols'].get('classes', []))}")
        print(f"  Imports: {len(file_info['imports'])}")
        print(f"  Total symbols: {len(analysis['symbols'])}")
        if file_info['symbols']['functions']:
            print(f"  Example functions: {file_info['symbols']['functions'][:3]}")
        print()

    if ts_files:
        print("8. Testing file analysis (TypeScript)...")
        analysis = analyse_file(ts_files[0])
        assert analysis.get("success", False), f"Analysis failed: {analysis}"
        file_info = analysis['file_info']
        print(f"✓ Analysis of {ts_files[0]}:")
        print(f"  Language: {file_info['language']}")
        print(f"  Lines: {file_info['line_count']}")
        print(f"  Functions: {len(file_info['symbols'].get('functions', []))}")
        print(f"  Classes: {len(file_info['symbols'].get('classes', []))}")
        print(f"  Imports: {len(file_info['imports'])}")
        print(f"  Exports: {len(file_info.get('exports', []))}")
        print(f"  Total symbols: {len(analysis['symbols'])}")
        if file_info['symbols']['functions']:
            print(f"  Example functions: {file_info['symbols']['functions'][:3]}")
        print()

    # Test 8: Symbol usage
    print("9. Testing symbol usage...")
    symbol_result = find_symbol_usage("User")
    assert symbol_result.get("success", False), f"Symbol search failed: {symbol_result}"
    print(f"✓ Found {symbol_result['total_matches']} symbols matching 'User'")
    if symbol_result['matches']:
        for match in symbol_result['matches'][:2]:
            print(f"  {match['symbol_name']} ({match['type']}) in {match['file']}:{match['line']}")
    print()

    # Test 9: Function calls
    print("10. Testing function call analysis...")
    call_result = find_functions_calling("save")
    assert call_result.get("success", False), f"Function call analysis failed: {call_result}"
    print(f"✓ Found {call_result['total_callers']} functions calling 'save'")
    if call_result['callers']:
        for caller in call_result['callers'][:2]:
            print(f"  Called by: {caller['symbol_id']}")
    print()

    # Test 10: File imports
    if java_files:
        print("11. Testing file imports (Java)...")
        imports = get_file_imports(java_files[0])
        assert imports.get("success", False), f"Import analysis failed: {imports}"
        print(f"✓ Imports for {java_files[0]}:")
        print(f"  Total imports: {imports['total_imports']}")
        if imports['imports']:
            for imp in imports['imports'][:3]:
                print(f"  Import: {imp}")
        if imports.get('package'):
            print(f"  Package: {imports['package']}")
        print()

    # Test 11: Search in file
    if java_files:
        print("12. Testing search in file...")
        file_search = search_in_file(java_files[0], "public", regex=False)
        assert file_search.get("success", False), f"File search failed: {file_search}"
        print(f"✓ Found {file_search['total_matches']} matches for 'public' in {java_files[0]}")
        if file_search['matches']:
            for match in file_search['matches'][:2]:
                print(f"  Line {match['line_number']}: {match['line_content'].strip()}")
        print()

    # Test 12: Refresh index
    print("13. Testing index refresh...")
    refresh_result = refresh_index()
    assert refresh_result.get("success", False), f"Index refresh failed: {refresh_result}"
    print(f"✓ Index refresh successful: {refresh_result['message']}")
    print(f"  File count: {refresh_result['file_count']}")
    print(f"  Build time: {refresh_result['build_time']} seconds\n")

    # Test 13: Shutdown
    print("14. Testing analyser shutdown...")
    shutdown_analyser()
    print("✓ Analyser shut down successfully\n")

    print("All tests passed! ✨")
    print("\nCode Analysis Tools are working correctly and ready for AI agents.")

if __name__ == "__main__":
    test_tools()