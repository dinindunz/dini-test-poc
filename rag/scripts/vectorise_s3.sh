#!/bin/bash
#
# Vectorise code chunks and store in Amazon S3 Vectors
#
# Usage:
#   ./vectorise_s3.sh <s3_bucket> [chunks_file] [index_name] [batch_size] [--clear]
#
# Examples:
#   ./vectorise_s3.sh my-code-vectors
#   ./vectorise_s3.sh my-code-vectors chunks_output.json
#   ./vectorise_s3.sh my-code-vectors chunks_output.json code-embeddings 25 --clear
#

# Check if S3 bucket is provided
if [ -z "$1" ]; then
    echo "❌ Error: S3 bucket name is required"
    echo ""
    echo "Usage: ./vectorise_s3.sh <s3_bucket> [chunks_file] [index_name] [batch_size] [--clear]"
    echo ""
    echo "Examples:"
    echo "  ./vectorise_s3.sh my-code-vectors"
    echo "  ./vectorise_s3.sh my-code-vectors chunks_output.json"
    echo "  ./vectorise_s3.sh my-code-vectors chunks_output.json code-embeddings 25 --clear"
    exit 1
fi

# Parameters
S3_BUCKET="$1"
CHUNKS_FILE="${2:-chunks/chunks_output.json}"
INDEX_NAME="${3:-code-embeddings}"
BATCH_SIZE="${4:-25}"
CLEAR_FLAG="${5:-}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make chunks file path relative to script directory's parent (rag/)
if [[ ! "$CHUNKS_FILE" = /* ]]; then
    CHUNKS_FILE="$SCRIPT_DIR/../$CHUNKS_FILE"
fi

echo "=================================="
echo "Vectorise & Store (S3 Vectors)"
echo "=================================="
echo "S3 bucket: $S3_BUCKET"
echo "Chunks file: $CHUNKS_FILE"
echo "Index name: $INDEX_NAME"
echo "Batch size: $BATCH_SIZE"
echo "Clear existing: ${CLEAR_FLAG:-no}"
echo "=================================="
echo ""

# Run vectorisation with S3 Vectors
python "$SCRIPT_DIR/vectorise_and_store.py" \
    --chunks-file "$CHUNKS_FILE" \
    --vector-store s3 \
    --s3-bucket "$S3_BUCKET" \
    --table-name "$INDEX_NAME" \
    --batch-size "$BATCH_SIZE" \
    $CLEAR_FLAG

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Script completed"
else
    echo ""
    echo "❌ Script failed with errors"
    exit 1
fi
