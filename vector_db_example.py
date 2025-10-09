"""
Example usage of PostgreSQL pgvector solution
"""
from rag import DatabaseConfig, PgVectorStore, EmbeddingGenerator


def main():
    # Initialise database configuration
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="vectordb",
        user="postgres",
        password="postgres"
    )

    # Initialise embedding generator
    embedder = EmbeddingGenerator(model="text-embedding-3-small")

    # Use context manager for automatic connection handling
    with PgVectorStore(config, table_name="documents") as vector_store:
        # Initialise schema with appropriate dimension
        dimension = embedder.get_dimension()
        vector_store.initialise_schema(dimension=dimension)

        # Example 1: Insert single document
        print("\n📝 Inserting single document...")
        text = "PostgreSQL is a powerful, open source object-relational database system."
        embedding = embedder.generate(text)
        doc_id = vector_store.insert_embedding(
            content=text,
            embedding=embedding,
            metadata={"source": "example", "type": "definition"}
        )
        print(f"✅ Inserted document with ID: {doc_id}")

        # Example 2: Insert multiple documents in batch
        print("\n📚 Inserting batch of documents...")
        documents = [
            "Vector databases enable semantic search using embeddings.",
            "pgvector is a PostgreSQL extension for vector similarity search.",
            "OpenAI provides embedding models for text vectorisation."
        ]

        # Generate embeddings for all documents
        embeddings = embedder.generate_batch(documents)

        # Prepare batch records
        records = [
            (doc, emb, {"source": "example", "batch": "1"})
            for doc, emb in zip(documents, embeddings)
        ]

        batch_ids = vector_store.insert_embeddings_batch(records)
        print(f"✅ Inserted {len(batch_ids)} documents: {batch_ids}")

        # Example 3: Perform similarity search
        print("\n🔍 Performing similarity search...")
        query = "How does vector search work in databases?"
        query_embedding = embedder.generate(query)

        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=3
        )

        print(f"\nQuery: {query}")
        print(f"\nTop {len(results)} similar documents:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity']:.4f}")
            print(f"   Content: {result['content']}")
            print(f"   Metadata: {result['metadata']}")

        # Example 4: Similarity search with metadata filter
        print("\n🔍 Similarity search with metadata filter...")
        filtered_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=2,
            metadata_filter={"source": "example"}
        )

        print(f"\nFiltered results (source='example'): {len(filtered_results)} matches")

        # Example 5: Get statistics
        print("\n📊 Database statistics:")
        total_count = vector_store.get_count()
        print(f"Total documents: {total_count}")


if __name__ == "__main__":
    main()
