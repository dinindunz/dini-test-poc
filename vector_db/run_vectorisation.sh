#!/bin/bash

# Vectorise and Store Script
# This script runs the complete pipeline:
# 1. Ensures dependencies are installed
# 2. Runs vectorisation and storage using Bedrock Titan

set -e

echo "🚀 Starting vectorisation pipeline"
echo ""

# Ensure required packages are installed
echo "📦 Checking dependencies..."
pip install -q boto3 tqdm psycopg2-binary pgvector dotenv

echo ""
echo "⚙️  Running vectorisation and storage..."
echo ""

# Run vectorisation with default settings
# You can customise these arguments:
# --chunks-file: Path to chunks JSON file (default: chunks_output.json)
# --model-id: Bedrock model ID (default: amazon.titan-embed-text-v2:0)
# --table-name: Database table name (default: code_embeddings)
# --batch-size: Batch size for processing (default: 25)
# --clear: Clear existing data before inserting

python vectorise_and_store.py \
    --chunks-file chunks_output.json \
    --model-id amazon.titan-embed-text-v2:0 \
    --table-name code_embeddings \
    --batch-size 25

echo ""
echo "✅ Vectorisation pipeline complete!"
