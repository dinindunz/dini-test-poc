"""
PostgreSQL pgvector vector store implementation
"""
import psycopg2
from psycopg2.extras import execute_values, Json
from typing import List, Dict, Optional, Tuple, Any
from pgvector.psycopg2 import register_vector
import numpy as np

try:
    from .config import DatabaseConfig
except ImportError:
    from config import DatabaseConfig


class PgVectorStore:
    """Vector store using PostgreSQL with pgvector extension"""

    def __init__(self, config: DatabaseConfig, table_name: str = "embeddings"):
        self.config = config
        self.table_name = table_name
        self.conn = None
        self.dimension = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.config.connection_params)
            register_vector(self.conn)
            print(f"✅ Connected to PostgreSQL database: {self.config.database}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def initialise_schema(self, dimension: int = 1536):
        """
        Initialise database schema with pgvector extension

        Args:
            dimension: Vector dimension (default 1536 for OpenAI embeddings)
        """
        self.dimension = dimension

        with self.conn.cursor() as cur:
            # Enable pgvector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create table with vector column
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector({dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster similarity search
            # HNSW with cosine distance - optimal for code search (semantic similarity)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name}
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)

            self.conn.commit()
            print(f"✅ Schema initialised for table: {self.table_name}")

    def insert_embedding(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Insert a single embedding

        Args:
            content: Text content
            embedding: Vector embedding
            metadata: Optional metadata dictionary

        Returns:
            Inserted record ID
        """
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self.table_name} (content, embedding, metadata)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (content, np.array(embedding), Json(metadata))
            )
            record_id = cur.fetchone()[0]
            self.conn.commit()
            return record_id

    def insert_embeddings_batch(
        self,
        records: List[Tuple[str, List[float], Optional[Dict]]]
    ) -> List[int]:
        """
        Insert multiple embeddings in batch

        Args:
            records: List of (content, embedding, metadata) tuples

        Returns:
            List of inserted record IDs
        """
        with self.conn.cursor() as cur:
            # Convert embeddings to numpy arrays and metadata to JSON
            formatted_records = [
                (content, np.array(embedding), Json(metadata))
                for content, embedding, metadata in records
            ]

            execute_values(
                cur,
                f"""
                INSERT INTO {self.table_name} (content, embedding, metadata)
                VALUES %s
                RETURNING id
                """,
                formatted_records,
                template="(%s, %s, %s)"
            )

            record_ids = [row[0] for row in cur.fetchall()]
            self.conn.commit()
            return record_ids

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using cosine distance

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filter (e.g., {"type": "document"})
            verbose: Print SQL query for debugging

        Returns:
            List of matching records with similarity scores
        """
        with self.conn.cursor() as cur:
            # Build query with optional metadata filter
            query = f"""
                SELECT id, content, metadata, embedding,
                       1 - (embedding <=> %s) as similarity
                FROM {self.table_name}
            """

            params = [np.array(query_embedding)]

            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(f"metadata->>'{key}' = %s")
                    params.append(str(value))
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY embedding <=> %s LIMIT %s"
            params.extend([np.array(query_embedding), top_k])

            if verbose:
                print(f"\n{'='*70}")
                print(f"🔎 SQL QUERY")
                print(f"{'='*70}")
                print(query)
                print(f"\n📋 Query Parameters:")
                print(f"  - Vector dimension: {len(query_embedding)}")
                print(f"  - Top K: {top_k}")
                if metadata_filter:
                    print(f"  - Metadata filters: {metadata_filter}")
                print(f"\n💡 Search Strategy:")
                print(f"  - Semantic Search: Using cosine similarity (embedding <=> vector)")
                print(f"  - Distance Operator: '<=' (cosine distance)")
                print(f"  - Similarity Metric: 1 - cosine_distance (higher = more similar)")
                if metadata_filter:
                    print(f"  - Lexical Filter: JSONB metadata filtering on {list(metadata_filter.keys())}")
                print(f"{'='*70}\n")

            cur.execute(query, params)

            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "embedding": row[3].tolist() if row[3] is not None else [],
                    "similarity": float(row[4])
                })

            return results

    def delete_by_id(self, record_id: int):
        """Delete a record by ID"""
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table_name} WHERE id = %s", (record_id,))
            self.conn.commit()

    def delete_all(self):
        """Delete all records from the table"""
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table_name}")
            self.conn.commit()

    def get_count(self) -> int:
        """Get total number of records"""
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cur.fetchone()[0]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
