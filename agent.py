import os
import json
from datetime import datetime
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands.models.bedrock import BedrockModel
from strands_tools import shell, file_read, file_write, editor
from tools.code_analyser import ai_agent_tools
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set environment variables to bypass tool approval prompts
os.environ["STRANDS_NON_INTERACTIVE"] = "false"
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Configuration for logging
INCLUDE_TRACES_CONTENT = os.getenv("INCLUDE_TRACES_CONTENT", "true").lower() == "true"

def save_metrics_log(user_prompt, metrics_summary, system_prompt_template=None, include_traces_content=True):
    """Save metrics summary to a JSON file in logs directory"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create timestamp in dd/mm/yy-hh:mm format
    timestamp = datetime.now().strftime("%d-%m-%y-%H-%M")

    # Sanitise user prompt for filename (remove special characters)
    sanitised_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
    sanitised_prompt = sanitised_prompt.replace(' ', '_')[:50]  # Limit length and replace spaces

    # Create filename
    filename = f"{timestamp}-{sanitised_prompt}.json"
    file_path = logs_dir / filename

    # Filter metrics_summary to exclude message content if needed
    filtered_metrics = metrics_summary.copy() if isinstance(metrics_summary, dict) else metrics_summary

    if not include_traces_content and isinstance(filtered_metrics, dict):
        # Remove message content from traces to reduce log size
        if 'traces' in filtered_metrics:
            for trace in filtered_metrics['traces']:
                if 'message' in trace:
                    trace['message'] = "[CONTENT_EXCLUDED]"
                if 'children' in trace:
                    for child in trace['children']:
                        if 'message' in child:
                            child['message'] = "[CONTENT_EXCLUDED]"

    # Prepare log data
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "user_prompt": user_prompt,
        "system_prompt_template": system_prompt_template,
        "metrics_summary": filtered_metrics,
        "formatted_timestamp": timestamp,
        "traces_content_included": include_traces_content
    }

    try:
        # Save to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        content_status = "with traces content" if include_traces_content else "without traces content"
        print(f"📊 Metrics logged to: {file_path} ({content_status})")
        return str(file_path)
    except Exception as e:
        print(f"⚠️  Failed to save metrics log: {e}")
        return None

def code_analysis_tools():
    """Create code analysis tools from ai_agent_tools module"""
    from strands.tools import tool

    tools = []

    # Get all available tools from the ai_agent_tools module
    available_tools = ai_agent_tools.AVAILABLE_TOOLS

    for tool_name, tool_info in available_tools.items():
        # Create a tool using the decorator approach
        decorated_func = tool(
            name=tool_name,
            description=tool_info["description"]
        )(tool_info["function"])
        tools.append(decorated_func)

    return tools

def load_system_prompt(prompt_name=None):
    """Load system prompt from prompts directory"""
    prompts_dir = Path("prompts")
    prompt_files = list(prompts_dir.glob("*.md"))

    if not prompt_files:
        return "You are a helpful AI assistant.", None

    # Show interactive menu if no name specified
    if prompt_name is None:
        print("📝 Available system prompts:")
        for i, file in enumerate(prompt_files, 1):
            print(f"  {i}. {file.stem}")

        try:
            choice = input("Select prompt (number or name): ").strip()

            # Try to parse as number
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(prompt_files):
                    selected_file = prompt_files[choice_num - 1]
                else:
                    print("Invalid choice, using first available prompt")
                    selected_file = prompt_files[0]
            else:
                # Try to find by name
                matching = [f for f in prompt_files if choice.lower() in f.stem.lower()]
                if matching:
                    selected_file = matching[0]
                else:
                    print("Prompt not found, using first available prompt")
                    selected_file = prompt_files[0]
        except (KeyboardInterrupt, EOFError):
            print("\nUsing first available prompt")
            selected_file = prompt_files[0]
    else:
        # Find matching file
        matching = [f for f in prompt_files if prompt_name.lower() in f.stem.lower()]
        selected_file = matching[0] if matching else prompt_files[0]

    try:
        content = selected_file.read_text(encoding='utf-8').strip()
        # Remove markdown header
        if content.startswith('#'):
            content = '\n'.join(content.split('\n')[1:]).strip()
        print(f"✅ Loaded: {selected_file.stem}")
        return content, selected_file.stem
    except Exception:
        return "You are a helpful AI assistant.", None

def select_model_provider():
    """Interactive model provider selection"""
    print("🤖 Select Model Provider:")
    print("  1. LiteLLM (Mantel AI Gateway)")
    print("  2. AWS Bedrock")

    choice = input("Select model provider: ").strip()

    if choice == "1":
        print("✅ Using LiteLLM model")
        return LiteLLMModel(
            client_args={
                "base_url": os.getenv("API_BASE"),
                "api_key": os.getenv("API_KEY"),
            },
            model_id="openai/au-claude-4.5-sonnet",
            params={
                "max_tokens": 8000,
                "temperature": 0.1,
            }
        )
    elif choice == "2":
        print("✅ Using Bedrock model")
        return BedrockModel(
            model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0",
        )
    else:
        choice = input("Invalid choice, Select model provider: ").strip()

# Select model provider first
model = select_model_provider()

code_index_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="/usr/local/bin/uv",
        args=["run", "--directory", "/workspaces/code-index-mcp", "python", "run.py"]
    )
))


# Load system prompt (check for command line argument)
prompt_name = None
if len(sys.argv) > 1:
    prompt_name = sys.argv[1]
    print(f"🎯 Using specified prompt: {prompt_name}")

system_prompt, selected_prompt_name = load_system_prompt(prompt_name)

# Check prompt type and load appropriate tools
effective_prompt_name = prompt_name or selected_prompt_name
using_code_analysis = effective_prompt_name and "code_analyser" in effective_prompt_name.lower()
using_code_index_mcp = effective_prompt_name and "code_index_mcp" in effective_prompt_name.lower()

if using_code_analysis:
    print("🔧 Code analysis prompt detected - loading custom code analysis tools")
    try:
        code_index_tools = code_analysis_tools()
        print(f"✅ Loaded {len(code_index_tools)} code analysis tools")
    except Exception as e:
        print(f"⚠️  Failed to load code analysis tools: {e}")
        code_index_tools = []
elif using_code_index_mcp:
    print("🔗 Code index MCP prompt detected - starting MCP client")
    # Start MCP client and keep it running
    try:
        code_index_mcp_client.start()
        code_index_tools = code_index_mcp_client.list_tools_sync()
        print("✅ code-index-mcp client initialised successfully")
    except Exception as e:
        print(f"⚠️  code-index-mcp client initialisation failed: {e}")
        print("🔄 Continuing without code index tools...")
        code_index_tools = []
else:
    print("📝 Standard prompt detected - no additional tools loaded")
    code_index_tools = []

app = FastAPI()

agent = Agent(
    system_prompt=system_prompt,
    model=model,
    tools=[shell, file_read, file_write, editor] + code_index_tools
)

class InvokeRequest(BaseModel):
    prompt: str
    use_structured_output: bool = True


class AnalysisResponse(BaseModel):
    """Structured response for text analysis"""
    sentiment: str  # positive, negative, neutral
    tone: str  # formal, casual, technical, etc.
    summary: str
    key_points: list[str]


@app.post("/invoke")
async def invoke_agent(request: InvokeRequest):
    """Invoke the agent with a prompt"""
    try:
        # Check if context management is enabled
        use_context_management = effective_prompt_name and "context_aware" in effective_prompt_name.lower()

        if use_context_management:
            # Use context-aware agent
            from context_manager.context_aware_agent import create_context_aware_agent

            if not hasattr(invoke_agent, '_context_agent'):
                print("🧠 Initialising context-aware agent")
                invoke_agent._context_agent = create_context_aware_agent(
                    agent,
                    {"max_working_memory": 12, "max_context_tokens": 6000}
                )

            context_agent = invoke_agent._context_agent
            result = context_agent(request.prompt)

            # Get context statistics
            context_stats = context_agent.get_context_stats()
            message_text = result.message.get('content', [{}])[0].get('text', str(result.message))
            metrics_summary = result.metrics.get_summary()
            metrics_summary.update({
                "context_managed": True,
                "context_stats": context_stats
            })

        else:
            # Check if structured output is requested
            if request.use_structured_output:
                # Use structured output - this returns the structured object directly
                structured_data = agent.structured_output(AnalysisResponse, request.prompt)
                message_text = json.dumps(structured_data.model_dump(), indent=2)
                # Structured output doesn't return metrics, so create empty metrics
                metrics_summary = {}
            else:
                # Standard agent invocation
                result = agent(request.prompt)
                message_text = result.message.get('content', [{}])[0].get('text', str(result.message))
                metrics_summary = result.metrics.get_summary()

        # Save metrics to log file
        log_file_path = save_metrics_log(request.prompt, metrics_summary, effective_prompt_name, INCLUDE_TRACES_CONTENT)

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
