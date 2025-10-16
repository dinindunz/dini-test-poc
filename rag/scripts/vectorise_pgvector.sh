#!/bin/bash
#
# Vectorise code chunks and store in PostgreSQL with pgvector
#
# Usage:
#   ./vectorise_pgvector.sh [chunks_file] [table_name] [batch_size] [--clear]
#
# Examples:
#   ./vectorise_pgvector.sh
#   ./vectorise_pgvector.sh chunks_output.json
#   ./vectorise_pgvector.sh chunks_output.json code_embeddings 25 --clear
#

# Default values
CHUNKS_FILE="${1:-chunks/chunks_output.json}"
TABLE_NAME="${2:-code_embeddings}"
BATCH_SIZE="${3:-25}"
CLEAR_FLAG="${4:-}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make chunks file path relative to script directory's parent (rag/)
if [[ ! "$CHUNKS_FILE" = /* ]]; then
    CHUNKS_FILE="$SCRIPT_DIR/../$CHUNKS_FILE"
fi

echo "=================================="
echo "Vectorise & Store (PostgreSQL)"
echo "=================================="
echo "Chunks file: $CHUNKS_FILE"
echo "Table name: $TABLE_NAME"
echo "Batch size: $BATCH_SIZE"
echo "Clear existing: ${CLEAR_FLAG:-no}"
echo "=================================="
echo ""

# Run vectorisation with pgvector
python "$SCRIPT_DIR/vectorise_and_store.py" \
    --chunks-file "$CHUNKS_FILE" \
    --vector-store pgvector \
    --table-name "$TABLE_NAME" \
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
