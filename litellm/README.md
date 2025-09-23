# LiteLLM Server for Databricks Model Serving

A simple LiteLLM proxy server for Databricks model serving endpoints that provides OpenAI-compatible API access.

## 🚀 Quick Start

The simplest way to start the server:

```bash
# Install LiteLLM if not already installed
pip install litellm

# Start the server with the config file
litellm --config litellm_config.yaml --port 4000 --host 0.0.0.0
```

Or use the startup script:

```bash
# Make the startup script executable (if needed)
chmod +x start_litellm_server.sh

# Start the server
./start_litellm_server.sh
```

## 📁 Configuration

The server uses `litellm_config.yaml` for configuration. The current setup includes:

- **Model Name**: `databricks-model` (use this in your API calls)
- **Master Key**: `sk-1234` (for authentication)
- **Port**: `4000`
- **Host**: `0.0.0.0` (accessible from all interfaces)

### Environment Variables

You can customize the server using environment variables:

- `LITELLM_HOST`: Server host (default: `0.0.0.0`)
- `LITELLM_PORT`: Server port (default: `4000`)
- `LITELLM_CONFIG`: Config file path (default: `litellm_config.yaml`)

## 🌐 API Usage

Once the server is running, you can use it like any OpenAI API:

### List Available Models
```bash
curl -X GET "http://localhost:4000/v1/models" \
  -H "Authorization: Bearer sk-1234"
```

### Chat Completions
```bash
curl -X POST "http://localhost:4000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "databricks-model",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 🌐 Available Endpoints

- **OpenAI API**: `http://localhost:4000/v1`
- **Health Check**: `http://localhost:4000/health`
- **Model List**: `http://localhost:4000/v1/models`
- **Swagger UI**: `http://localhost:4000/docs`

## 🔑 Authentication

The server uses a master key for authentication. Include it in your requests:

```bash
curl -H "Authorization: Bearer sk-1234" ...
```

## 📝 Usage Examples

### Python Client

```python
import openai

# Configure the client to use your local LiteLLM server
client = openai.OpenAI(
    api_key="sk-1234",  # Your LITELLM_MASTER_KEY
    base_url="http://localhost:4000/v1"
)

# Use it like any OpenAI client
response = client.chat.completions.create(
    model="databricks-model",
    messages=[{"role": "user", "content": "Hello from Databricks!"}]
)

print(response.choices[0].message.content)
```

### cURL Examples

```bash
# Simple chat completion
curl -X POST "http://localhost:4000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "databricks-model",
    "messages": [
      {"role": "user", "content": "What is machine learning?"}
    ],
    "max_tokens": 100
  }'
```

## 🔧 Advanced Configuration

### Custom Model Names

Edit the `litellm_config.yaml` to add multiple models:

```yaml
model_list:
  - model_name: "databricks-llama"
    litellm_params:
      model: "databricks/llama-endpoint"
      api_base: "https://your-workspace.cloud.databricks.com/serving-endpoints"
      api_key: "your-token"
      custom_llm_provider: "databricks"
  - model_name: "databricks-claude"
    litellm_params:
      model: "databricks/claude-endpoint"
      api_base: "https://your-workspace.cloud.databricks.com/serving-endpoints"
      api_key: "your-token"
      custom_llm_provider: "databricks"
```

### Load Balancing

Add multiple endpoints for the same model:

```yaml
model_list:
  - model_name: "databricks-model"
    litellm_params:
      model: "databricks/endpoint-1"
      api_base: "https://your-workspace.cloud.databricks.com/serving-endpoints"
      api_key: "your-token"
      custom_llm_provider: "databricks"
  - model_name: "databricks-model"
    litellm_params:
      model: "databricks/endpoint-2"
      api_base: "https://your-workspace.cloud.databricks.com/serving-endpoints"
      api_key: "your-token"
      custom_llm_provider: "databricks"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Server won't start**
   - Check that port 4000 is available
   - Verify the config file exists and is valid YAML
   - Ensure LiteLLM is installed: `pip install litellm`

2. **Model not found error**
   - Verify the model name in your request matches the `model_name` in the config
   - Check that the Databricks endpoint exists and is accessible
   - Confirm the API key has proper permissions

3. **Authentication errors**
   - Verify your Databricks token has proper permissions
   - Check the workspace URL format in the config
   - Ensure the endpoint is in "Ready" state

### Logs

The server provides detailed logging. Check the console output for:
- Configuration validation
- Request/response details
- Error messages

## 📁 Files Overview

- **`litellm_config.yaml`** - LiteLLM configuration file
- **`start_litellm_server.sh`** - Simplified startup script
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## 💡 Notes

- The server configuration is stored in `litellm_config.yaml`
- Authentication uses the master key `sk-1234`
- The Databricks model is accessible via the name `databricks-model`
- No complex setup required - just run the standard LiteLLM command!
- The previous custom Python server (`litellm_server.py`) has been replaced with the standard LiteLLM approach for simplicity

## 📚 Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Databricks Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## 🤝 Support

For issues specific to this implementation, check:
1. Configuration file syntax and content
2. Databricks endpoint status and accessibility
3. Network connectivity to localhost:4000
4. Server logs for detailed error messages
