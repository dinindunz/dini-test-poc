"""
Strands tool for retrieving code examples using RAG
"""
from strands import tool
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bedrock_embeddings import BedrockEmbeddingGenerator
from core.pgvector_store import PgVectorStore
from core.config import DatabaseConfig


@tool
def retrieve_code_examples(
    query: str,
    top_k: int = 5,
    file_type: Optional[str] = None,
    module: Optional[str] = None,
    layer: Optional[str] = None
) -> str:
    """
    Search for relevant code examples from the vectorised codebase.

    Use this tool when you need to find examples of Spring Boot code, API definitions,
    build configurations, or project structure. The tool returns formatted code examples
    that match the semantic meaning of your query.

    Args:
        query (str): Search query describing what code examples you need (e.g., "REST controller", "service layer", "Gradle configuration")
        top_k (int): Number of examples to retrieve (default: 5, recommended range: 3-10)
        file_type (Optional[str]): Filter by file type - "java", "gradle", "swagger", or "markdown"
        module (Optional[str]): Filter by specific module name
        layer (Optional[str]): Filter by code layer - "controller", "service", "repository", or "api"

    Returns:
        str: Formatted code examples with file paths, metadata, and relevance scores
    """
    try:
        print(f"\n{'='*70}")
        print(f"🔍 RETRIEVAL TOOL EXECUTION")
        print(f"{'='*70}")
        print(f"📝 Query: {query}")
        print(f"🔢 Top K: {top_k}")
        if file_type or module or layer:
            print(f"🔧 Filters: file_type={file_type}, module={module}, layer={layer}")

        # Initialise retriever components
        print(f"\n⚙️  Initialising components...")
        embedder = BedrockEmbeddingGenerator(model_id="amazon.titan-embed-text-v2:0")
        db_config = DatabaseConfig()
        vector_store = PgVectorStore(config=db_config, table_name="code_embeddings")
        vector_store.connect()
        print(f"✅ Connected to vector database")

        # Generate query embedding
        print(f"\n🧮 Generating query embedding...")
        query_embedding = embedder.generate(query)
        print(f"✅ Query vector dimension: {len(query_embedding)}")
        print(f"📊 Query vector sample (first 5 values): {query_embedding[:5]}")

        # Build metadata filter
        metadata_filter = {}
        if file_type:
            metadata_filter['file_type'] = file_type
        if module:
            metadata_filter['module'] = module
        if layer:
            metadata_filter['layer'] = layer

        if metadata_filter:
            print(f"\n🔍 Applying metadata filters: {metadata_filter}")

        # Search vector database
        print(f"\n🔎 Searching vector database...")
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            metadata_filter=metadata_filter if metadata_filter else None,
            verbose=True
        )
        print(f"✅ Found {len(results)} results")

        # Close connection
        vector_store.close()

        # Format results for agent/LLM
        if not results:
            print(f"\n⚠️  No results found")
            return "No relevant code examples found in the vectorised codebase."

        print(f"\n{'='*70}")
        print(f"📊 RESULTS DETAILS")
        print(f"{'='*70}")

        formatted_output = "Here are relevant code examples from the codebase:\n\n"

        for idx, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            similarity = result.get('similarity', 0)
            stored_vector = result.get('embedding', [])

            print(f"\n--- Result #{idx} ---")
            print(f"  📏 Similarity Score: {similarity:.4f}")
            print(f"  📄 File: {metadata.get('file_path', 'N/A')}")
            print(f"  🏷️  Type: {metadata.get('type', 'N/A')}")
            print(f"  🎯 Layer: {metadata.get('layer', 'N/A')}")
            print(f"  📦 Module: {metadata.get('module', 'N/A')}")
            print(f"  🔢 Chunk ID: {metadata.get('chunk_id', 'N/A')}")
            if stored_vector:
                print(f"  📊 Stored vector dimension: {len(stored_vector)}")
                print(f"  📊 Stored vector sample (first 5): {stored_vector[:5]}")
            print(f"  📝 Content preview: {result['content'][:100]}...")

            formatted_output += f"--- Example {idx} (relevance: {similarity:.2f}) ---\n"

            # Add metadata context
            if 'file_path' in metadata:
                formatted_output += f"📄 File: {metadata['file_path']}\n"
            if 'module' in metadata:
                formatted_output += f"📦 Module: {metadata['module']}\n"
            if 'type' in metadata:
                formatted_output += f"🏷️  Type: {metadata['type']}\n"
            if 'layer' in metadata:
                formatted_output += f"🎯 Layer: {metadata['layer']}\n"

            formatted_output += f"\n💻 Code:\n{result['content']}\n\n"

        print(f"\n{'='*70}")
        formatted_output += "\n✨ Use these examples as reference when generating code."

        return formatted_output

    except Exception as e:
        return f"❌ Error retrieving code examples: {str(e)}\n\nPlease check that the vector database is running and contains vectorised code."
