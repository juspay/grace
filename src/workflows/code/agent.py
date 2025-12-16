from langchain.agents.factory import create_agent 
from langchain.tools import tool
import litellm
import requests
from src.config import get_config
from src.ai.system.prompt_config import PromptConfig
from . import tool_functions
from .tool_wrapper import wrap_tool_functions

DEBUG = get_config().getLogConfig().debug

# Get wrapped tool functions for visualization
wrapped_tool_functions = wrap_tool_functions(tool_functions)

# Define the tools with detailed descriptions using wrapped functions for visualization
@tool
def agent(input: tool_functions.AgentInput):
    """Delegate complex tasks to specialized agents"""
    return wrapped_tool_functions['agent'](input)

@tool
def bash(input: tool_functions.BashInput):
    """Execute shell commands for build, test, or system operations"""
    return wrapped_tool_functions['bash'](input)

@tool
def bash_output(input: tool_functions.BashOutputInput):
    """Get output from previously executed background shell commands"""
    return wrapped_tool_functions['bash_output'](input)

@tool
def exit_plan_mode(input: tool_functions.ExitPlanModeInput):
    """Exit planning mode and switch to execution mode"""
    return wrapped_tool_functions['exit_plan_mode'](input)

@tool
def file_edit(input: tool_functions.FileEditInput):
    """Make targeted edits to existing files for updates or fixes"""
    return wrapped_tool_functions['file_edit'](input)

@tool
def file_read(input: tool_functions.FileReadInput):
    """Read file contents for analysis, understanding code structure"""
    return wrapped_tool_functions['file_read'](input)

@tool
def file_write(input: tool_functions.FileWriteInput):
    """Create new files or completely overwrite existing file contents"""
    return wrapped_tool_functions['file_write'](input)

@tool
def glob(input: tool_functions.GlobInput):
    """Find files using glob patterns (*.py, *.js, etc.)"""
    return wrapped_tool_functions['glob'](input)

@tool
def grep(input: tool_functions.GrepInput):
    """Search for text patterns within files for code analysis"""
    return wrapped_tool_functions['grep'](input)

@tool
def kill_shell(input: tool_functions.KillShellInput):
    """Terminate running shell processes to clean up or stop commands"""
    return wrapped_tool_functions['kill_shell'](input)

@tool
def list_mcp_resources(input: tool_functions.ListMcpResourcesInput):
    """List available MCP resources for discovering external tools"""
    return wrapped_tool_functions['list_mcp_resources'](input)

@tool
def mcp(input: tool_functions.McpInput):
    """Interact with Model Context Protocol resources for external integrations"""
    return wrapped_tool_functions['mcp'](input)

@tool
def notebook_edit(input: tool_functions.NotebookEditInput):
    """Edit Jupyter notebooks for data analysis and ML workflows"""
    return wrapped_tool_functions['notebook_edit'](input)

@tool
def read_mcp_resource(input: tool_functions.ReadMcpResourceInput):
    """Read data from MCP resources for accessing external information"""
    return wrapped_tool_functions['read_mcp_resource'](input)

@tool
def todo_write(input: tool_functions.TodoWriteInput):
    """Create or update task lists for planning and tracking progress"""
    return wrapped_tool_functions['todo_write'](input)

@tool
def web_fetch(input: tool_functions.WebFetchInput):
    """Retrieve web content from URLs for documentation or API access"""
    return wrapped_tool_functions['web_fetch'](input)

@tool
def web_search(input: tool_functions.WebSearchInput):
    """Search the web for documentation, solutions, or latest information"""
    return wrapped_tool_functions['web_search'](input)

@tool
def ask_user_question(input: tool_functions.AskUserQuestionInput):
    """Ask users for clarification, preferences, or additional requirements"""
    return wrapped_tool_functions['ask_user_question'](input)


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
    
    # Get the enhanced system prompt from configuration
    prompt_config = PromptConfig(promptfile="code-prompts.yaml", use_enhanced=True)
    
    # Try to get enhanced system prompt first, fallback to standard
    try:
        system_prompt = prompt_config.get_enhanced(
            "graceSystemPrompt", 
            fallback_prompt=prompt_config.get("graceSystemPrompt")
        )
        if DEBUG:
            print("DEBUG: Using enhanced system prompt from Promcode")
    except Exception as e:
        system_prompt = prompt_config.get("graceSystemPrompt")
        if DEBUG:
            print(f"DEBUG: Using standard system prompt: {e}")
    # Validate configured model
    configured_model = ai_config.model_id
    model_to_use = None
    
    if DEBUG:
        print(f"DEBUG: Configured model: '{configured_model}'")
        print(f"DEBUG: Available models: {available_models[:5]}...")  # Show first 5
        print(f"DEBUG: Model in available: {configured_model in available_models}")
    
    if configured_model and configured_model in available_models:
        model_to_use = configured_model
        if DEBUG:
            print(f"DEBUG: Using configured model: {model_to_use}")
    else:
        if DEBUG:
            print(f"DEBUG: Model invalid, prompting user selection")
        # Ask user to select a model
        model_to_use = _prompt_user_model_selection(configured_model, available_models)
        if model_to_use is None:
            # User cancelled, use default fallback
            model_to_use = "gemini-2.5-pro"
            print(f"Using default model: '{model_to_use}'")
        else:
            if DEBUG:
                print(f"DEBUG: User selected model: {model_to_use}")
    
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

def _prompt_user_model_selection(configured_model: str, available_models: list) -> str:
    """Prompt user to select a model from available options"""
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        from rich.prompt import IntPrompt
        
        console = Console()
        
        console.print(f"\n⚠️  Model Configuration Issue:")
        console.print(f"[dim]Configured model '{configured_model}' is not available.[/dim]")
        console.print(f"\n[cyan]Please select a model from the available options:[/cyan]")
        
        # Display available models with numbers
        for i, model in enumerate(available_models, 1):
            console.print(f"  [yellow]{i:2d}.[/yellow] [bold]{model}[/bold]")
        
        console.print(f"\n[dim]Enter the number of your choice (1-{len(available_models)}), or press Enter to use default.[/dim]")
        
        # Simple input validation loop
        while True:
            choice = console.input("Select model > ").strip()
            
            if not choice or choice == "":  # User pressed Enter for default
                console.print("Using default model: gemini-2.5-pro")
                return None
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_models):
                    selected_model = available_models[choice_num - 1]
                    console.print(f"Selected: {selected_model}")
                    return selected_model
                else:
                    console.print(f"[red]Invalid choice. Please enter a number between 1 and {len(available_models)}[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[red]")
            
    except Exception as e:
        print(f"Error prompting for model selection: {e}")
        return None
