#!/usr/bin/env python3
"""
Vectorise code chunks and store in pgvector database

This script:
1. Reads chunks from chunks_output.json
2. Generates embeddings using Amazon Bedrock Titan
3. Stores embeddings in PostgreSQL with pgvector extension
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm

try:
    # Try relative imports (when run as module)
    from ..core.bedrock_embeddings import BedrockEmbeddingGenerator
    from ..core.pgvector_store import PgVectorStore
    from ..core.config import DatabaseConfig
except ImportError:
    # Fall back to direct imports (when run as script)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.bedrock_embeddings import BedrockEmbeddingGenerator
    from core.pgvector_store import PgVectorStore
    from core.config import DatabaseConfig


def load_chunks(chunks_file: Path) -> List[Dict]:
    """
    Load chunks from JSON file

    Args:
        chunks_file: Path to chunks JSON file

    Returns:
        List of chunk dictionaries
    """
    print(f"📂 Loading chunks from: {chunks_file}")

    with open(chunks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both direct array and wrapped object formats
    if isinstance(data, list):
        chunks = data
    elif isinstance(data, dict):
        chunks = data.get('chunks', [])
    else:
        chunks = []

    print(f"✅ Loaded {len(chunks)} chunks")

    return chunks


def prepare_chunk_content(chunk: Dict) -> str:
    """
    Prepare chunk content for embedding

    Args:
        chunk: Chunk dictionary

    Returns:
        Text content to embed
    """
    # Combine relevant fields for embedding
    parts = []

    # Add type information
    if 'type' in chunk:
        parts.append(f"Type: {chunk['type']}")

    # Add main content
    if 'content' in chunk:
        parts.append(chunk['content'])

    # Add name/identifier if available
    if 'name' in chunk:
        parts.append(f"Name: {chunk['name']}")

    return "\n".join(parts)


def prepare_chunk_metadata(chunk: Dict) -> Dict:
    """
    Extract metadata from chunk for storage

    Args:
        chunk: Chunk dictionary

    Returns:
        Metadata dictionary
    """
    metadata = {}

    # Core fields
    for field in ['module', 'file_path', 'file_type', 'type', 'name', 'language']:
        if field in chunk:
            metadata[field] = chunk[field]

    # Location information
    if 'start_line' in chunk:
        metadata['start_line'] = chunk['start_line']
    if 'end_line' in chunk:
        metadata['end_line'] = chunk['end_line']

    # Additional context
    if 'package' in chunk:
        metadata['package'] = chunk['package']

    return metadata


def vectorise_and_store(
    chunks_file: Path,
    model_id: str = "amazon.titan-embed-text-v2:0",
    table_name: str = "code_embeddings",
    batch_size: int = 25,
    clear_existing: bool = False
):
    """
    Main function to vectorise chunks and store in database

    Args:
        chunks_file: Path to chunks JSON file
        model_id: Bedrock embedding model ID
        table_name: Database table name
        batch_size: Number of chunks to process in each batch
        clear_existing: Whether to clear existing data before inserting
    """
    print("\n🚀 Starting vectorisation and storage process\n")

    # Load chunks
    chunks = load_chunks(chunks_file)

    if not chunks:
        print("⚠️  No chunks to process")
        return

    # Initialise embedding generator
    print(f"🤖 Initialising Bedrock Titan embedding generator: {model_id}")
    embedder = BedrockEmbeddingGenerator(model_id=model_id)
    embedding_dimension = embedder.get_dimension()
    print(f"📊 Embedding dimension: {embedding_dimension}")

    # Initialise database connection
    print("\n🗄️  Connecting to PostgreSQL database")
    db_config = DatabaseConfig()
    vector_store = PgVectorStore(config=db_config, table_name=table_name)
    vector_store.connect()

    # Initialise schema
    vector_store.initialise_schema(dimension=embedding_dimension)

    # Clear existing data if requested
    if clear_existing:
        print("\n🗑️  Clearing existing data")
        vector_store.delete_all()

    # Process chunks in batches
    print(f"\n⚙️  Processing {len(chunks)} chunks in batches of {batch_size}")
    total_inserted = 0
    failed_chunks = []
    skipped_chunks = []

    for i in tqdm(range(0, len(chunks), batch_size), desc="Processing batches"):
        batch = chunks[i:i + batch_size]

        # Prepare batch content and metadata
        batch_contents = []
        batch_metadata = []
        valid_chunks = []

        for chunk in batch:
            metadata = prepare_chunk_metadata(chunk)

            # Skip chunks without metadata
            if not metadata:
                print(f"\n⚠️  Skipping chunk without metadata: {chunk.get('file_path', 'unknown')}")
                skipped_chunks.append(chunk)
                continue

            content = prepare_chunk_content(chunk)

            batch_contents.append(content)
            batch_metadata.append(metadata)
            valid_chunks.append(chunk)

        # Skip batch if no valid chunks
        if not batch_contents:
            continue

        try:
            # Generate embeddings
            embeddings = embedder.generate_batch(batch_contents, batch_size=batch_size)

            # Prepare records for insertion
            records: List[Tuple[str, List[float], Dict]] = []
            for content, embedding, metadata in zip(batch_contents, embeddings, batch_metadata):
                records.append((content, embedding, metadata))

            # Insert batch
            record_ids = vector_store.insert_embeddings_batch(records)
            total_inserted += len(record_ids)

        except Exception as e:
            print(f"\n❌ Error processing batch {i // batch_size + 1}: {e}")
            failed_chunks.extend(valid_chunks)

    # Summary
    print("\n" + "=" * 60)
    print("📊 VECTORISATION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully processed: {total_inserted} chunks")
    print(f"⏭️  Skipped (no metadata): {len(skipped_chunks)} chunks")
    print(f"❌ Failed: {len(failed_chunks)} chunks")
    print(f"📦 Total in database: {vector_store.get_count()} records")
    print("=" * 60)

    # Show skipped chunks if any
    if skipped_chunks:
        print("\n⚠️  Skipped chunks (no metadata):")
        for chunk in skipped_chunks[:5]:  # Show first 5
            print(f"  - {chunk.get('file_path', 'unknown')} ({chunk.get('type', 'unknown')})")
        if len(skipped_chunks) > 5:
            print(f"  ... and {len(skipped_chunks) - 5} more")

    # Show failed chunks if any
    if failed_chunks:
        print("\n❌ Failed chunks:")
        for chunk in failed_chunks[:5]:  # Show first 5
            print(f"  - {chunk.get('file_path', 'unknown')} ({chunk.get('type', 'unknown')})")
        if len(failed_chunks) > 5:
            print(f"  ... and {len(failed_chunks) - 5} more")

    # Close connection
    vector_store.close()
    print("\n✅ Vectorisation complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vectorise code chunks and store in pgvector database"
    )

    parser.add_argument(
        "--chunks-file",
        type=Path,
        default=Path("chunks_output.json"),
        help="Path to chunks JSON file (default: chunks_output.json)"
    )

    parser.add_argument(
        "--model-id",
        type=str,
        default="amazon.titan-embed-text-v2:0",
        help="Bedrock embedding model ID (default: amazon.titan-embed-text-v2:0)"
    )

    parser.add_argument(
        "--table-name",
        type=str,
        default="code_embeddings",
        help="Database table name (default: code_embeddings)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Batch size for processing (default: 25)"
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before inserting"
    )

    args = parser.parse_args()

    # Run vectorisation
    vectorise_and_store(
        chunks_file=args.chunks_file,
        model_id=args.model_id,
        table_name=args.table_name,
        batch_size=args.batch_size,
        clear_existing=args.clear
    )


if __name__ == "__main__":
    main()
