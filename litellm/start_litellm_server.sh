#!/bin/bash

# LiteLLM Databricks Server Startup Script

set -e

echo "🚀 Starting LiteLLM Server for Databricks Model Serving"
echo "=================================================="

# Check if virtual environment exists
# if [ ! -d "venv" ]; then
#     echo "📦 Creating virtual environment..."
#     python3 -m venv venv
# fi

# Activate conda environment
# echo "🔧 Activating virtual environment..."
# source venv/bin/activate

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Set default values
HOST=${LITELLM_HOST:-"0.0.0.0"}
PORT=${LITELLM_PORT:-4000}
CONFIG_FILE=${LITELLM_CONFIG:-"litellm_config.yaml"}

echo "🌐 Server will start on: http://$HOST:$PORT"
echo "📋 Available endpoints:"
echo "   - OpenAI API: http://$HOST:$PORT/v1"
echo "   - Health check: http://$HOST:$PORT/health"
echo "   - Model list: http://$HOST:$PORT/v1/models"
echo ""
echo "🔑 Use master key: sk-1234"
echo "📄 Using config file: $CONFIG_FILE"
echo ""
echo "Starting server..."

# Start the LiteLLM server using the standard command
litellm --config "$CONFIG_FILE" --port "$PORT" --host "$HOST"
