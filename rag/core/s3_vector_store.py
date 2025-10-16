"""
Amazon S3 Vector Store implementation
"""
import boto3
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class S3VectorStore:
    """Vector store using Amazon S3 Vectors"""

    def __init__(
        self,
        bucket_name: str,
        index_name: str = "code-embeddings",
        region: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        aws_session_token: str = None
    ):
        """
        Initialise S3 Vector Store

        Args:
            bucket_name: S3 bucket name for vector storage
            index_name: Name of the vector index (default: "code-embeddings")
                       Must be 3-63 chars, lowercase letters, numbers, hyphens, dots only
            region: AWS region (defaults to AWS_REGION env var or "ap-southeast-2")
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token (optional, from AWS_SESSION_TOKEN env var)
        """
        self.bucket_name = bucket_name
        self.index_name = index_name
        self.region = region or os.getenv("AWS_REGION", "ap-southeast-2")

        # Initialise boto3 session
        # If no credentials provided, boto3 will use default credential chain (AWS profile, IAM role, etc.)
        session_params = {}

        if self.region:
            session_params["region_name"] = self.region

        # Add credentials if explicitly provided
        if aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"):
            session_params["aws_access_key_id"] = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        if aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"):
            session_params["aws_secret_access_key"] = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        if aws_session_token or os.getenv("AWS_SESSION_TOKEN"):
            session_params["aws_session_token"] = aws_session_token or os.getenv("AWS_SESSION_TOKEN")

        session = boto3.Session(**session_params)

        # Create S3 client for bucket operations
        self.s3_client = session.client("s3")

        # Create S3 Vectors client for vector operations
        self.vectors_client = session.client("s3vectors")

        self.dimension = None
        self.distance_metric = None

    def connect(self):
        """
        Verify vector bucket access and create if it doesn't exist
        """
        try:
            # Try to check if vector bucket exists by attempting to list indexes
            self.vectors_client.list_indexes(vectorBucketName=self.bucket_name, maxResults=1)
            print(f"✅ Connected to S3 vector bucket: {self.bucket_name}")
        except Exception as e:
            error_code = e.response.get('Error', {}).get('Code') if hasattr(e, 'response') else None

            if error_code == 'NotFoundException' or 'not found' in str(e).lower():
                # Vector bucket doesn't exist, create it
                print(f"⚠️  Vector bucket {self.bucket_name} doesn't exist. Creating...")
                try:
                    self.vectors_client.create_vector_bucket(
                        vectorBucketName=self.bucket_name
                    )
                    print(f"✅ Created S3 vector bucket: {self.bucket_name} in region {self.region}")
                except Exception as create_error:
                    print(f"❌ Failed to create S3 vector bucket: {create_error}")
                    raise
            elif error_code == '403' or error_code == 'Forbidden' or error_code == 'AccessDeniedException':
                # Access denied
                print(f"❌ Access denied to vector bucket {self.bucket_name}. Check IAM permissions.")
                raise
            else:
                # Other error
                print(f"❌ Vector bucket access failed: {e}")
                raise

    def initialise_schema(self, dimension: int = 1536, distance_metric: str = "cosine"):
        """
        Initialise vector index - creates index if it doesn't exist

        Args:
            dimension: Vector dimension (default: 1536, use 1024 for Titan v2)
            distance_metric: Distance metric - "cosine" or "euclidean" (default: "cosine")
        """
        self.dimension = dimension
        self.distance_metric = distance_metric

        # Check if index exists, create if not
        try:
            # Try to describe the index to see if it exists
            response = self.vectors_client.list_indexes(
                vectorBucketName=self.bucket_name,
                maxResults=100
            )

            existing_indexes = [idx.get('indexName') for idx in response.get('indexes', [])]

            if self.index_name in existing_indexes:
                print(f"✅ Vector index exists: {self.index_name}")
            else:
                # Create the index
                print(f"⚠️  Vector index {self.index_name} doesn't exist. Creating...")
                self.vectors_client.create_index(
                    vectorBucketName=self.bucket_name,
                    indexName=self.index_name,
                    dataType='float32',
                    dimension=dimension,
                    distanceMetric=distance_metric,
                    metadataConfiguration={
                        'nonFilterableMetadataKeys': ['content']  # Content is not filterable, won't count toward 2048 byte limit
                    }
                )
                print(f"✅ Created vector index: {self.index_name}")

            print(f"   Dimension: {dimension}")
            print(f"   Distance metric: {distance_metric}")

        except Exception as e:
            print(f"❌ Failed to initialise vector index: {e}")
            raise

    def insert_embedding(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Insert a single embedding into S3 Vectors

        Args:
            content: Text content (stored in metadata)
            embedding: Vector embedding
            metadata: Optional metadata dictionary

        Returns:
            Vector key (unique identifier)
        """
        # Generate unique key (use chunk_id from metadata or generate UUID)
        if metadata and "chunk_id" in metadata:
            vector_key = metadata["chunk_id"]
        else:
            import uuid
            vector_key = str(uuid.uuid4())

        # Prepare metadata - S3 Vectors has a 10-key limit
        # Keep only essential filterable fields
        vector_metadata = {
            "content": content,
            "chunk_id": vector_key
        }

        # Add essential filterable fields (max 10 total keys)
        if metadata:
            # Priority fields for filtering
            essential_fields = ["file_path", "layer", "type", "class_name", "module", "package", "file_type", "line_start"]
            for field in essential_fields:
                if field in metadata and len(vector_metadata) < 10:
                    vector_metadata[field] = metadata[field]

        # Validate dimension
        if self.dimension and len(embedding) != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")

        # Insert using S3 Vectors API
        try:
            self.vectors_client.put_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                vectors=[
                    {
                        "key": vector_key,
                        "data": {"float32": embedding},
                        "metadata": vector_metadata
                    }
                ]
            )

            return vector_key

        except Exception as e:
            print(f"❌ Failed to insert vector: {e}")
            raise

    def insert_embeddings_batch(
        self,
        records: List[tuple]
    ) -> List[str]:
        """
        Insert multiple embeddings using S3 Vectors API

        Note: Batches up to 500 vectors per API call (S3 Vectors limit)

        Args:
            records: List of (content, embedding, metadata) tuples

        Returns:
            List of vector keys
        """
        import uuid

        vector_keys = []
        batch_size = 500  # S3 Vectors API limit

        # Process in batches of 500
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            vectors = []

            for content, embedding, metadata in batch:
                # Generate unique key
                if metadata and "chunk_id" in metadata:
                    vector_key = metadata["chunk_id"]
                else:
                    vector_key = str(uuid.uuid4())

                # Prepare metadata - S3 Vectors has a 10-key limit
                # Keep only essential filterable fields
                vector_metadata = {
                    "content": content,
                    "chunk_id": vector_key
                }

                # Add essential filterable fields (max 10 total keys)
                if metadata:
                    # Priority fields for filtering
                    essential_fields = ["file_path", "layer", "type", "class_name", "module", "package", "file_type", "line_start"]
                    for field in essential_fields:
                        if field in metadata and len(vector_metadata) < 10:
                            vector_metadata[field] = metadata[field]

                # Validate dimension
                if self.dimension and len(embedding) != self.dimension:
                    raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")

                vectors.append({
                    "key": vector_key,
                    "data": {"float32": embedding},
                    "metadata": vector_metadata
                })

                vector_keys.append(vector_key)

            # Insert batch using S3 Vectors API
            try:
                self.vectors_client.put_vectors(
                    vectorBucketName=self.bucket_name,
                    indexName=self.index_name,
                    vectors=vectors
                )
            except Exception as e:
                print(f"❌ Failed to insert batch: {e}")
                # Mark failed batch keys as None
                for j in range(len(vectors)):
                    vector_keys[i + j] = None

        return vector_keys

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        metadata_filter: Optional[Dict] = None,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using S3 Vectors query_vectors API

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            metadata_filter: Optional metadata filter (e.g., {"layer": "controller"})
            verbose: Print query details

        Returns:
            List of matching records with similarity scores
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"🔎 S3 VECTOR SEARCH")
            print(f"{'='*70}")
            print(f"  - Index: {self.index_name}")
            print(f"  - Top K: {top_k}")
            print(f"  - Distance metric: {self.distance_metric}")
            if metadata_filter:
                print(f"  - Metadata filters: {metadata_filter}")
            print(f"{'='*70}\n")

        try:
            # Build query parameters
            query_params = {
                "vectorBucketName": self.bucket_name,
                "indexName": self.index_name,
                "queryVector": {"float32": query_embedding},
                "topK": top_k,
                "returnMetadata": True,
                "returnDistance": True
            }

            # Add metadata filter if provided
            if metadata_filter:
                query_params["filter"] = metadata_filter

            # Execute query
            response = self.vectors_client.query_vectors(**query_params)

            # Format results
            results = []
            for vector_match in response.get("vectors", []):
                # Extract metadata
                metadata = vector_match.get("metadata", {})
                content = metadata.get("content", "")

                # Calculate similarity from distance
                # S3 Vectors returns distance, convert to similarity
                distance = vector_match.get("distance", 0.0)
                if self.distance_metric == "cosine":
                    # Cosine distance is (1 - cosine_similarity)
                    similarity = 1.0 - distance
                else:  # euclidean
                    # Convert euclidean distance to similarity score
                    similarity = 1.0 / (1.0 + distance)

                results.append({
                    "id": vector_match.get("key"),
                    "content": content,
                    "metadata": metadata,
                    "embedding": vector_match.get("data", {}).get("float32", []),
                    "similarity": similarity,
                    "distance": distance
                })

            return results

        except Exception as e:
            print(f"❌ Failed to query vectors: {e}")
            raise

    def delete_by_key(self, vector_key: str):
        """
        Delete a vector by its key

        Args:
            vector_key: Vector key to delete
        """
        try:
            self.vectors_client.delete_vectors(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name,
                keys=[vector_key]
            )

            print(f"✅ Deleted vector: {vector_key}")

        except Exception as e:
            print(f"❌ Failed to delete vector: {e}")
            raise

    def delete_index(self):
        """
        Delete the vector index entirely (including all vectors)

        Warning: This completely removes the index and all its data
        """
        try:
            print(f"⚠️  Deleting vector index: {self.index_name}")
            self.vectors_client.delete_index(
                vectorBucketName=self.bucket_name,
                indexName=self.index_name
            )
            print(f"✅ Deleted vector index: {self.index_name}")
        except Exception as e:
            # Index might not exist, that's okay
            if 'NotFoundException' in str(e) or 'not found' in str(e).lower():
                print(f"⚠️  Index {self.index_name} doesn't exist (already deleted)")
            else:
                print(f"❌ Failed to delete index: {e}")
                raise

    def delete_all(self):
        """
        Delete all vectors from the index

        Warning: This deletes all vectors from the vector index
        """
        try:
            # List all vector keys using S3 Vectors API
            vector_keys = []
            next_token = None

            while True:
                # Build list parameters
                list_params = {
                    "vectorBucketName": self.bucket_name,
                    "indexName": self.index_name,
                    "maxResults": 500,
                    "returnData": False,
                    "returnMetadata": False
                }

                if next_token:
                    list_params["nextToken"] = next_token

                # List vectors
                response = self.vectors_client.list_vectors(**list_params)

                # Collect keys
                for vector in response.get("vectors", []):
                    vector_keys.append(vector.get("key"))

                # Check for more pages
                next_token = response.get("nextToken")
                if not next_token:
                    break

            # Delete vectors in batches (delete_vectors supports multiple keys)
            if vector_keys:
                # Delete in batches of 1000 (reasonable batch size)
                for i in range(0, len(vector_keys), 1000):
                    batch = vector_keys[i:i+1000]
                    self.vectors_client.delete_vectors(
                        vectorBucketName=self.bucket_name,
                        indexName=self.index_name,
                        keys=batch
                    )
                print(f"✅ Deleted {len(vector_keys)} vectors from index: {self.index_name}")
            else:
                print(f"⚠️  No vectors found in index: {self.index_name}")

        except Exception as e:
            print(f"❌ Failed to delete vectors: {e}")
            raise

    def get_count(self) -> int:
        """
        Get total number of vectors in the index

        Returns:
            Number of vectors
        """
        try:
            count = 0
            next_token = None

            while True:
                # Build list parameters
                list_params = {
                    "vectorBucketName": self.bucket_name,
                    "indexName": self.index_name,
                    "maxResults": 500,
                    "returnData": False,
                    "returnMetadata": False
                }

                if next_token:
                    list_params["nextToken"] = next_token

                # List vectors
                response = self.vectors_client.list_vectors(**list_params)

                # Count vectors in this page
                count += len(response.get("vectors", []))

                # Check for more pages
                next_token = response.get("nextToken")
                if not next_token:
                    break

            return count
        except Exception as e:
            print(f"❌ Failed to count vectors: {e}")
            return 0

    def close(self):
        """
        Close connection

        Note: S3 client doesn't require explicit closing
        """
        print("✅ S3 Vector Store closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
        """Context manager exit"""
        self.close()
