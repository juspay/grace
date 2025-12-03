"""
Pydantic models for the tool inputs of the code-generation agent.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

class AgentInput(BaseModel):
    """A short (3-5 word) description of the task"""
    description: str = Field(..., description="A short (3-5 word) description of the task")
    prompt: str = Field(..., description="The task for the agent to perform")
    subagent_type: str = Field(..., description="The type of specialized agent to use for this task")
    model: Optional[str] = Field(None, description="Optional model to use for this agent. If not specified, inherits from parent. Prefer haiku for quick, straightforward tasks to minimize cost and latency.")
    resume: Optional[str] = Field(None, description="Optional agent ID to resume from. If provided, the agent will continue from the previous execution transcript.")

class BashInput(BaseModel):
    """Input for the bash tool"""
    command: str = Field(..., description="The command to execute")
    timeout: Optional[int] = Field(None, description="Optional timeout in milliseconds (max 600000)")
    description: Optional[str] = Field(None, description="Clear, concise description of what this command does in 5-10 words, in active voice.")
    run_in_background: Optional[bool] = Field(False, description="Set to true to run this command in the background. Use BashOutput to read the output later.")
    dangerouslyDisableSandbox: Optional[bool] = Field(False, description="Set this to true to dangerously override sandbox mode and run commands without sandboxing.")

class BashOutputInput(BaseModel):
    """Input for the bash output tool"""
    bash_id: str = Field(..., description="The ID of the background shell to retrieve output from")
    filter: Optional[str] = Field(None, description="Optional regular expression to filter the output lines.")

class ExitPlanModeInput(BaseModel):
    """Input for exiting plan mode"""
    plan: str = Field(..., description="The plan you came up with, that you want to run by the user for approval. Supports markdown. The plan should be pretty concise.")

class FileEditInput(BaseModel):
    """Input for editing a file"""
    file_path: str = Field(..., description="The absolute path to the file to modify")
    old_string: str = Field(..., description="The text to replace")
    new_string: str = Field(..., description="The text to replace it with")
    replace_all: Optional[bool] = Field(False, description="Replace all occurences of old_string")

class FileReadInput(BaseModel):
    """Input for reading a file"""
    file_path: str = Field(..., description="The absolute path to the file to read")
    offset: Optional[int] = Field(None, description="The line number to start reading from")
    limit: Optional[int] = Field(None, description="The number of lines to read")

class FileWriteInput(BaseModel):
    """Input for writing a file"""
    file_path: str = Field(..., description="The absolute path to the file to write (must be absolute, not relative)")
    content: str = Field(..., description="The content to write to the file")

class GlobInput(BaseModel):
    """Input for glob"""
    pattern: str = Field(..., description="The glob pattern to match files against")
    path: Optional[str] = Field(None, description="The directory to search in. If not specified, the current working directory will be used.")

class GrepInput(BaseModel):
    """Input for grep"""
    pattern: str = Field(..., description="The regular expression pattern to search for in file contents")
    path: Optional[str] = Field(None, description="File or directory to search in. Defaults to current working directory.")
    glob: Optional[str] = Field(None, description='Glob pattern to filter files (e.g. "*.js", "*.{ts,tsx}")')
    output_mode: Optional[Literal["content", "files_with_matches", "count"]] = Field("files_with_matches", description='Output mode')
    B: Optional[int] = Field(None, alias="-B", description='Number of lines to show before each match')
    A: Optional[int] = Field(None, alias="-A", description='Number of lines to show after each match')
    C: Optional[int] = Field(None, alias="-C", description='Number of lines to show before and after each match')
    n: Optional[bool] = Field(True, alias="-n", description='Show line numbers in output')
    i: Optional[bool] = Field(False, alias="-i", description='Case insensitive search')
    type: Optional[str] = Field(None, description='File type to search')
    head_limit: Optional[int] = Field(None, description='Limit output to first N lines/entries')
    offset: Optional[int] = Field(0, description='Skip first N lines/entries before applying head_limit')
    multiline: Optional[bool] = Field(False, description='Enable multiline mode')

class KillShellInput(BaseModel):
    """Input for killing a shell"""
    shell_id: str = Field(..., description="The ID of the background shell to kill")

class ListMcpResourcesInput(BaseModel):
    """Input for listing MCP resources"""
    server: Optional[str] = Field(None, description="Optional server name to filter resources by")

class McpInput(BaseModel):
    """Input for MCP"""
    pass

class NotebookEditInput(BaseModel):
    """Input for editing a notebook"""
    notebook_path: str = Field(..., description="The absolute path to the Jupyter notebook file to edit")
    cell_id: Optional[str] = Field(None, description="The ID of the cell to edit")
    new_source: str = Field(..., description="The new source for the cell")
    cell_type: Optional[Literal["code", "markdown"]] = Field(None, description="The type of the cell")
    edit_mode: Optional[Literal["replace", "insert", "delete"]] = Field("replace", description="The type of edit to make")

class ReadMcpResourceInput(BaseModel):
    """Input for reading an MCP resource"""
    server: str = Field(..., description="The MCP server name")
    uri: str = Field(..., description="The resource URI to read")

class TodoWriteInput(BaseModel):
    """Input for writing a todo list"""
    class TodoItem(BaseModel):
        content: str
        status: Literal["pending", "in_progress", "completed"]
        activeForm: str
    todos: List[TodoItem]

class WebFetchInput(BaseModel):
    """Input for fetching web content"""
    url: str = Field(..., description="The URL to fetch content from")
    prompt: str = Field(..., description="The prompt to run on the fetched content")

class WebSearchInput(BaseModel):
    """Input for web search"""
    query: str = Field(..., description="The search query to use")
    allowed_domains: Optional[List[str]] = Field(None, description="Only include search results from these domains")
    blocked_domains: Optional[List[str]] = Field(None, description="Never include search results from these domains")

class QuestionOption(BaseModel):
    """Option for a user question"""
    label: str = Field(..., description="The display text for this option")
    description: str = Field(..., description="Explanation of what this option means")

class Question(BaseModel):
    """A question to ask the user"""
    question: str = Field(..., description="The complete question to ask the user")
    header: str = Field(..., description="Very short label displayed as a chip/tag (max 12 chars)")
    options: List[QuestionOption]
    multiSelect: bool = Field(..., description="Set to true to allow the user to select multiple options")

class AskUserQuestionInput(BaseModel):
    """Input for asking the user a question"""
    questions: List[Question]
    answers: Optional[dict] = Field(None, description="User answers collected by the permission component")
