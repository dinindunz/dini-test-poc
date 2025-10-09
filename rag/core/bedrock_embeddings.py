"""
Embedding generation utilities using Amazon Bedrock Titan
"""
import os
import json
import boto3
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class BedrockEmbeddingGenerator:
    """Generate embeddings using Amazon Bedrock Titan embedding models"""

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2:0",
        region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None
    ):
        """
        Initialise Bedrock embedding generator

        Args:
            model_id: Bedrock embedding model ID (default: amazon.titan-embed-text-v2:0)
            region: AWS region (defaults to AWS_REGION env var or ap-southeast-2)
            aws_access_key_id: AWS access key (defaults to AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token (defaults to AWS_SESSION_TOKEN env var)
        """
        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", "ap-southeast-2")

        # Create boto3 session with credentials
        session_params = {
            "region_name": self.region
        }

        if aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"):
            session_params["aws_access_key_id"] = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")

        if aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"):
            session_params["aws_secret_access_key"] = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        if aws_session_token or os.getenv("AWS_SESSION_TOKEN"):
            session_params["aws_session_token"] = aws_session_token or os.getenv("AWS_SESSION_TOKEN")

        # Create Bedrock runtime client
        session = boto3.Session(**session_params)
        self.client = session.client("bedrock-runtime")

    def generate(self, text: str, normalize: bool = True) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text
            normalize: Whether to normalise the embedding (default: True)

        Returns:
            Embedding vector
        """
        # Prepare request body
        request_body = {
            "inputText": text
        }

        # Add normalisation parameter if supported
        if normalize:
            request_body["normalize"] = True

        try:
            # Invoke Bedrock model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract embedding based on model response format
            if "embedding" in response_body:
                return response_body["embedding"]
            elif "embeddings" in response_body:
                return response_body["embeddings"][0]
            else:
                raise ValueError(f"Unexpected response format: {response_body}")

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise

    def generate_batch(self, texts: List[str], normalize: bool = True, batch_size: int = 25) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            normalize: Whether to normalise the embeddings (default: True)
            batch_size: Number of texts to process at once (default: 25)

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                try:
                    embedding = self.generate(text, normalize=normalize)
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"❌ Failed to generate embedding for text (index {i}): {e}")
                    # Use zero vector as fallback
                    embeddings.append([0.0] * self.get_dimension())

        return embeddings

    def get_dimension(self) -> int:
        """
        Get embedding dimension for the current model

        Returns:
            Embedding dimension
        """
        # Embedding dimensions for Bedrock Titan models
        dimensions = {
            "amazon.titan-embed-text-v1": 1536,
            "amazon.titan-embed-text-v2:0": 1024,
            "amazon.titan-embed-image-v1": 1024,
        }
        return dimensions.get(self.model_id, 1024)
