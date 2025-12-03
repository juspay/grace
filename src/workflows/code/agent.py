from langchain.agents.factory import create_agent 
from langchain.tools import tool
import litellm
import requests
from src.config import get_config
from src.ai.system.prompt_config import PromptConfig
from . import tool_functions

DEBUG = get_config().getLogConfig().debug

# Define the tools with detailed descriptions
@tool
def agent(input: tool_functions.AgentInput):
    """Delegate complex tasks to specialized agents"""
    return tool_functions.agent(input)

@tool
def bash(input: tool_functions.BashInput):
    """Execute shell commands for build, test, or system operations"""
    return tool_functions.bash(input)

@tool
def bash_output(input: tool_functions.BashOutputInput):
    """Get output from previously executed background shell commands"""
    return tool_functions.bash_output(input)

@tool
def exit_plan_mode(input: tool_functions.ExitPlanModeInput):
    """Exit planning mode and switch to execution mode"""
    return tool_functions.exit_plan_mode(input)

@tool
def file_edit(input: tool_functions.FileEditInput):
    """Make targeted edits to existing files for updates or fixes"""
    return tool_functions.file_edit(input)

@tool
def file_read(input: tool_functions.FileReadInput):
    """Read file contents for analysis, understanding code structure"""
    return tool_functions.file_read(input)

@tool
def file_write(input: tool_functions.FileWriteInput):
    """Create new files or completely overwrite existing file contents"""
    return tool_functions.file_write(input)

@tool
def glob(input: tool_functions.GlobInput):
    """Find files using glob patterns (*.py, *.js, etc.)"""
    return tool_functions.glob(input)

@tool
def grep(input: tool_functions.GrepInput):
    """Search for text patterns within files for code analysis"""
    return tool_functions.grep(input)

@tool
def kill_shell(input: tool_functions.KillShellInput):
    """Terminate running shell processes to clean up or stop commands"""
    return tool_functions.kill_shell(input)

@tool
def list_mcp_resources(input: tool_functions.ListMcpResourcesInput):
    """List available MCP resources for discovering external tools"""
    return tool_functions.list_mcp_resources(input)

@tool
def mcp(input: tool_functions.McpInput):
    """Interact with Model Context Protocol resources for external integrations"""
    return tool_functions.mcp(input)

@tool
def notebook_edit(input: tool_functions.NotebookEditInput):
    """Edit Jupyter notebooks for data analysis and ML workflows"""
    return tool_functions.notebook_edit(input)

@tool
def read_mcp_resource(input: tool_functions.ReadMcpResourceInput):
    """Read data from MCP resources for accessing external information"""
    return tool_functions.read_mcp_resource(input)

@tool
def todo_write(input: tool_functions.TodoWriteInput):
    """Create or update task lists for planning and tracking progress"""
    return tool_functions.todo_write(input)

@tool
def web_fetch(input: tool_functions.WebFetchInput):
    """Retrieve web content from URLs for documentation or API access"""
    return tool_functions.web_fetch(input)

@tool
def web_search(input: tool_functions.WebSearchInput):
    """Search the web for documentation, solutions, or latest information"""
    return tool_functions.web_search(input)

@tool
def ask_user_question(input: tool_functions.AskUserQuestionInput):
    """Ask users for clarification, preferences, or additional requirements"""
    return tool_functions.ask_user_question(input)


tools = [
    agent,
    bash,
    bash_output,
    exit_plan_mode,
    file_edit,
    file_read,
    file_write,
    glob,
    grep,
    kill_shell,
    list_mcp_resources,
    mcp,
    notebook_edit,
    read_mcp_resource,
    todo_write,
    web_fetch,
    web_search,
    ask_user_question
]

def fetch_available_models(base_url: str, api_key: str) -> list:
    """Fetch available models from the API endpoint"""
    try:
        url = f"{base_url}/models?return_wildcard_routes=false&include_model_access_groups=false&only_model_access_groups=false&include_metadata=false"
        headers = {
            'accept': 'application/json',
            'x-litellm-api-key': api_key
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and 'data' in data:
            models = [model['id'] for model in data['data']]
            return models
        
        return []
    except Exception as e:
        print(f"Warning: Could not fetch available models: {e}")
        return []

def create_langchain_agent_with_model_validation():
    """Create agent with model validation and user-friendly error handling"""
    # Get configuration
    config = get_config()
    ai_config = config.getAiConfig()
    
    # Configure litellm with API settings (same pattern as AIService)
    litellm.api_key = ai_config.api_key
    if ai_config.base_url:
        litellm.api_base = ai_config.base_url
    
    # Get available models from API
    available_models = []
    if ai_config.base_url and ai_config.api_key:
        available_models = fetch_available_models(ai_config.base_url, ai_config.api_key)
    
    # Fallback hardcoded models if API call fails
    if not available_models:
        available_models = [
            "gemini-2.5-pro", "claude-sonnet-4-20250514", "claude-sonnet-4", 
            "gemini-2.5-flash", "claude-sonnet-4-5", "glm-46-fp8", "glm-latest"
        ]
    
    # Get the detailed system prompt from configuration
    system_prompt = PromptConfig(promptfile = "code-prompts.yaml").get("graceSystemPrompt")
    # Validate configured model
    configured_model = ai_config.model_id
    model_to_use = None
    model_invalid = False
    
    if configured_model and configured_model in available_models:
        model_to_use = configured_model
    else:
        model_invalid = True
        # Use first available model as fallback
        model_to_use = available_models[0] if available_models else "gemini-2.5-pro"
    
    # Display model information if invalid
    if model_invalid:
        print(f"\n⚠️  Model Configuration Warning:")
        print(f"   Configured model '{configured_model}' is not available.")
        print(f"   Using fallback model: '{model_to_use}'")
        print(f"\n📋 Available models:")
        for i, model in enumerate(available_models, 1):
            marker = "✓" if model == model_to_use else " "
            print(f"   {marker} {i:2d}. {model}")
        print()
    
    # Create the chat model using ChatOpenAI
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(
        model=model_to_use,
        api_key=ai_config.api_key,
        base_url=ai_config.base_url,
        temperature=ai_config.temperature,
        max_tokens=ai_config.max_tokens
    )
    
    # Create agent with the configured model
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=DEBUG
    )

    return agent_graph
