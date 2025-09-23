import os
import uvicorn
from strands import Agent
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from cached_openai import CachedOpenAIModel
from save_metrics import save_metrics_log

# Load environment variables from .env file
load_dotenv()

# Set environment variables to bypass tool approval prompts
os.environ["STRANDS_NON_INTERACTIVE"] = "false"
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Configuration for logging
INCLUDE_TRACES_CONTENT = os.getenv("INCLUDE_TRACES_CONTENT", "true").lower() == "true"

model = CachedOpenAIModel(
    client_args={
        "api_base": "http://localhost:4000/v1",
        "api_key": "sk-1234",
    },
    model_id="openai/databricks-model",
    params={
        "max_tokens": 1000,
        "temperature": 0.1,
    },
    cache_config={
        "enable": True,
        "ttl_seconds": 1800,  # 30 minutes
        "key_fields": ["model_id", "messages", "temperature", "max_tokens"]
    }
)

base_model = model = LiteLLMModel(
    client_args={
        "api_base": "http://localhost:4000/v1",
        "api_key": "sk-1234",
    },
    model_id="openai/databricks-model",
    params={
        "max_tokens": 1000,
        "temperature": 0.1,
    }
)

agent = Agent(model=base_model)

app = FastAPI()

class InvokeRequest(BaseModel):
    prompt: str

@app.post("/invoke")
async def invoke_agent(request: InvokeRequest):
    """Invoke the agent with a prompt"""
    try:
        result = agent(request.prompt)
        message_text = result.message.get('content', [{}])[0].get('text', str(result.message))
        metrics_summary = result.metrics.get_summary()
        
        # Save metrics to log file
        log_file_path = save_metrics_log(request.prompt, metrics_summary, "simple_prompt", INCLUDE_TRACES_CONTENT)

        response_data = {
            "result": message_text + "\n",
            "log_file": log_file_path
        }

        return response_data
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting a FastAPI agent server on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)