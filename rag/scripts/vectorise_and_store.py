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
    from ..core.s3_vector_store import S3VectorStore
    from ..core.config import DatabaseConfig
except ImportError:
    # Fall back to direct imports (when run as script)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.bedrock_embeddings import BedrockEmbeddingGenerator
    from core.pgvector_store import PgVectorStore
    from core.s3_vector_store import S3VectorStore
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

    # Add layer information (important for Spring Boot architecture)
    if 'layer' in chunk:
        parts.append(f"Layer: {chunk['layer']}")

    # Add Java-specific context
    if 'class_name' in chunk:
        parts.append(f"Class: {chunk['class_name']}")
    if 'package' in chunk:
        parts.append(f"Package: {chunk['package']}")
    if 'annotations' in chunk and chunk['annotations']:
        parts.append(f"Annotations: {', '.join(chunk['annotations'])}")

    # Add API-specific context
    if 'http_method' in chunk:
        parts.append(f"HTTP Method: {chunk['http_method']}")
    if 'api_path' in chunk:
        parts.append(f"API Path: {chunk['api_path']}")
    if 'operation_id' in chunk:
        parts.append(f"Operation: {chunk['operation_id']}")

    # Add documentation context
    if 'heading' in chunk:
        parts.append(f"Heading: {chunk['heading']}")

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
    for field in ['module', 'file_path', 'file_type', 'type', 'name', 'language', 'layer', 'chunk_id']:
        if field in chunk:
            metadata[field] = chunk[field]

    # Location information
    if 'line_start' in chunk:
        metadata['line_start'] = chunk['line_start']
    if 'line_end' in chunk:
        metadata['line_end'] = chunk['line_end']

    # Java-specific fields
    if 'package' in chunk:
        metadata['package'] = chunk['package']
    if 'class_name' in chunk:
        metadata['class_name'] = chunk['class_name']
    if 'annotations' in chunk:
        metadata['annotations'] = chunk['annotations']  # Store as JSONB array

    # API/Swagger-specific fields
    if 'http_method' in chunk:
        metadata['http_method'] = chunk['http_method']
    if 'api_path' in chunk:
        metadata['api_path'] = chunk['api_path']
    if 'operation_id' in chunk:
        metadata['operation_id'] = chunk['operation_id']
    if 'schema_name' in chunk:
        metadata['schema_name'] = chunk['schema_name']
    if 'api_title' in chunk:
        metadata['api_title'] = chunk['api_title']
    if 'api_version' in chunk:
        metadata['api_version'] = chunk['api_version']
    if 'tags' in chunk:
        metadata['tags'] = chunk['tags']  # Store as JSONB array

    # Documentation-specific fields
    if 'document_name' in chunk:
        metadata['document_name'] = chunk['document_name']
    if 'heading' in chunk:
        metadata['heading'] = chunk['heading']
    if 'heading_level' in chunk:
        metadata['heading_level'] = chunk['heading_level']

    return metadata


def vectorise_and_store(
    chunks_file: Path,
    model_id: str = "amazon.titan-embed-text-v2:0",
    table_name: str = "code_embeddings",
    batch_size: int = 25,
    clear_existing: bool = False,
    vector_store_type: str = "pgvector",
    s3_bucket_name: str = None
):
    """
    Main function to vectorise chunks and store in vector database

    Args:
        chunks_file: Path to chunks JSON file
        model_id: Bedrock embedding model ID
        table_name: Database table name (for pgvector) or index name (for S3)
        batch_size: Number of chunks to process in each batch
        clear_existing: Whether to clear existing data before inserting
        vector_store_type: Type of vector store - "pgvector" or "s3" (default: "pgvector")
        s3_bucket_name: S3 bucket name (required if vector_store_type is "s3")
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

    # Initialise vector store based on type
    print(f"\n🗄️  Initialising {vector_store_type.upper()} vector store")

    if vector_store_type == "pgvector":
        # PostgreSQL with pgvector
        db_config = DatabaseConfig()
        vector_store = PgVectorStore(config=db_config, table_name=table_name)
        vector_store.connect()
        vector_store.initialise_schema(dimension=embedding_dimension)

    elif vector_store_type == "s3":
        # Amazon S3 Vectors
        if not s3_bucket_name:
            raise ValueError("s3_bucket_name is required when vector_store_type is 's3'")

        vector_store = S3VectorStore(
            bucket_name=s3_bucket_name,
            index_name=table_name  # Use table_name as index_name for consistency
        )
        vector_store.connect()
        vector_store.initialise_schema(dimension=embedding_dimension, distance_metric="cosine")

    else:
        raise ValueError(f"Unsupported vector_store_type: {vector_store_type}. Use 'pgvector' or 's3'")

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

    parser.add_argument(
        "--vector-store",
        type=str,
        choices=["pgvector", "s3"],
        default="pgvector",
        help="Vector store type: pgvector (PostgreSQL) or s3 (Amazon S3 Vectors) (default: pgvector)"
    )

    parser.add_argument(
        "--s3-bucket",
        type=str,
        help="S3 bucket name (required when --vector-store=s3)"
    )

    args = parser.parse_args()

    # Run vectorisation
    vectorise_and_store(
        chunks_file=args.chunks_file,
        model_id=args.model_id,
        table_name=args.table_name,
        batch_size=args.batch_size,
        clear_existing=args.clear,
        vector_store_type=args.vector_store,
        s3_bucket_name=args.s3_bucket
    )


if __name__ == "__main__":
    main()
