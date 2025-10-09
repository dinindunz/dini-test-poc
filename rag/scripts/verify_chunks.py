#!/usr/bin/env python3
"""
Verification script to ensure all Java files have been chunked.
Compares Java files in the source directory with chunks in chunks_output.json
"""

import json
import sys
from pathlib import Path
from typing import Set, List, Dict

def get_all_java_files(root_dir: Path) -> Set[str]:
    """Get all Java files from the source directory."""
    java_files = set()

    # Find all modules
    modules = [d for d in root_dir.glob("*_dini_*") if d.is_dir()]

    for module_path in modules:
        for java_file in module_path.rglob("*.java"):
            # Store relative path from root
            rel_path = str(java_file.relative_to(root_dir))
            java_files.add(rel_path)

    return java_files

def get_chunked_java_files(chunks_file: Path) -> Dict[str, List[Dict]]:
    """Get all Java files that have been chunked."""
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Group chunks by file path
    chunked_files = {}
    for chunk in chunks:
        if chunk['file_type'] == 'java':
            file_path = chunk['file_path']
            if file_path not in chunked_files:
                chunked_files[file_path] = []
            chunked_files[file_path].append(chunk)

    return chunked_files

def main():
    # Paths
    # Get the rag directory (parent of scripts directory)
    rag_dir = Path(__file__).resolve().parent.parent

    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1]).resolve()
    else:
        root_dir = rag_dir / "java17"

    chunks_file = rag_dir / "chunks" / "chunks_output.json"

    print("=" * 70)
    print("JAVA FILE CHUNK VERIFICATION")
    print("=" * 70)
    print(f"\n📂 Source directory: {root_dir}")
    print(f"📄 Chunks file: {chunks_file}")
    print()

    # Get all Java files
    all_java_files = get_all_java_files(root_dir)
    print(f"✅ Found {len(all_java_files)} Java files in source directory")

    # Get chunked files
    chunked_files = get_chunked_java_files(chunks_file)
    print(f"✅ Found {len(chunked_files)} Java files in chunks")
    print()

    # Find missing files
    chunked_paths = set(chunked_files.keys())
    missing_files = all_java_files - chunked_paths

    # Find extra files (chunked but no longer in source)
    extra_files = chunked_paths - all_java_files

    # Display results
    print("=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    print()

    if not missing_files and not extra_files:
        print("✅ SUCCESS: All Java files have been chunked!")
        print(f"   Total files: {len(all_java_files)}")
    else:
        if missing_files:
            print(f"❌ MISSING: {len(missing_files)} Java file(s) not chunked:")
            for file_path in sorted(missing_files):
                print(f"   - {file_path}")
            print()

        if extra_files:
            print(f"⚠️  EXTRA: {len(extra_files)} chunked file(s) no longer in source:")
            for file_path in sorted(extra_files):
                print(f"   - {file_path}")
            print()

    # Display chunk statistics per file
    print("=" * 70)
    print("CHUNKS PER JAVA FILE")
    print("=" * 70)
    print()

    for file_path in sorted(chunked_files.keys()):
        chunks = chunked_files[file_path]
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk['type']
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        # Display file name and chunk breakdown
        file_name = Path(file_path).name
        print(f"📄 {file_name} ({len(chunks)} chunk{'s' if len(chunks) > 1 else ''})")
        print(f"   Path: {file_path}")
        print(f"   Types: {dict(chunk_types)}")

        # Show class/record names
        class_names = [c.get('class_name') for c in chunks if 'class_name' in c]
        if class_names:
            print(f"   Classes/Records: {', '.join(set(class_names))}")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Java files in source: {len(all_java_files)}")
    print(f"Total Java files chunked: {len(chunked_files)}")
    print(f"Missing from chunks: {len(missing_files)}")
    print(f"Extra in chunks: {len(extra_files)}")
    print(f"Total chunks for Java files: {sum(len(chunks) for chunks in chunked_files.values())}")
    print()

    # Exit with error code if there are missing files
    if missing_files:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
