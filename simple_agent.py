import os
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands_tools import shell, file_read, file_write, editor
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Set environment variables to bypass tool approval prompts
os.environ["STRANDS_NON_INTERACTIVE"] = "false"
os.environ["BYPASS_TOOL_CONSENT"] = "true"

model = LiteLLMModel(
    client_args={
        "api_base": "https://ai.mantelgroup.com.au/v1",
        "api_key": "sk-1234",
    },
    model_id="openai/global-claude-4.0-sonnet",
    params={
        "max_tokens": 1000,
        "temperature": 0.1,
    }
)

app = FastAPI()

agent = Agent(
    system_prompt="""You are an expert in software development and cloud computing with GitHub repository access.

When users request code changes or new features, follow this workflow:
1. **Repository Setup**:
   - If repository doesn't exist locally: Clone using 'git clone <repo-url>'
   - If repository already exists: Navigate to directory and run 'git pull'
2. **Branch Management**:
   - Always checkout main/master branch first: 'git checkout main' or 'git checkout master'
   - Pull latest changes: 'git pull origin main' (or master)
   - Create a new feature branch: 'git checkout -b feature/description-of-change'
   - EXCEPTION: Only work on existing non-main/non-master branches if user specifically requests it
3. **Analysis**: Analyze the user's requirements and explore the codebase structure
4. **Implementation**: Make the necessary code changes using file_read, file_write, and editor tools
5. **Testing**: Run any existing tests to ensure changes don't break functionality
6. **Commit**: Stage and commit changes with descriptive commit messages
7. **Push**: Push the feature branch to the remote repository
8. **PR Creation**: Use 'gh pr create --title "feat/fix: descriptive title" --body "Detailed description of changes"'

Use conventional commit prefixes (feat:, fix:, docs:) for meaningful titles and descriptions.

You have access to these tools:
- shell: Run git, gh, and other shell commands
- file_read: Read file contents to understand codebase
- file_write: Write new files or overwrite existing ones
- editor: Make precise edits to existing files""",
    model=model,
    tools=[shell, file_read, file_write, editor]
)

class InvokeRequest(BaseModel):
    prompt: str

@app.post("/invoke")
async def invoke_agent(request: InvokeRequest):
    """Invoke the agent with a prompt"""
    try:
        result = agent(request.prompt)
        return {"result": result.message}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting simple FastAPI agent server on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8081)
