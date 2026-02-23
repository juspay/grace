"""Claude Agent SDK field dependency analysis node — performs API sequence analysis using analysis.md."""

import asyncio
from pathlib import Path

import click
from rich.console import Console

from ..states.techspec_state import TechspecWorkflowState
from src.config import get_config
from src.tools.filemanager.filemanager import FileManager
from ._claude_display import display_tool_use, display_text, display_thinking, display_result

console = Console()

# Grace project root (where analysis.md lives)
GRACE_ROOT = Path(__file__).parent.parent.parent.parent.parent


def _read_analysis_prompt() -> str:
    """Read the analysis.md prompt from grace root."""
    analysis_path = GRACE_ROOT / "analysis.md"
    if not analysis_path.exists():
        raise FileNotFoundError(
            f"analysis.md not found at {analysis_path}."
        )
    return analysis_path.read_text(encoding="utf-8")


def _build_analysis_prompt(
    analysis_instructions: str,
    connector_name: str,
    tech_spec_content: str,
) -> str:
    """Build the full prompt for the field dependency analysis step."""
    full_prompt = f"""{analysis_instructions}

--- CONNECTOR NAME ---
{connector_name}

--- TECHNICAL SPECIFICATION ---
{tech_spec_content}

IMPORTANT: The complete technical specification is provided above in this prompt. Do NOT search the filesystem for it.
Use ONLY the specification content above to perform the field dependency analysis.
If you need to use tools, the working directory is the connector's output folder.

Perform a complete field dependency analysis for this connector following the step-by-step process defined above.
Generate the full analysis including:
1. All API flows identified
2. Field source categorization for each flow
3. Prerequisite API call chains
4. Complete field dependency map
5. All UNDECIDED fields with specific questions
6. Summary document

Output the complete analysis as a markdown document — no preamble, just the full analysis."""

    return full_prompt


def field_analysis(state: TechspecWorkflowState) -> TechspecWorkflowState:
    """Perform API field dependency analysis using Claude Agent SDK with analysis.md prompt."""

    # Use enhanced spec if available, otherwise fall back to original tech spec
    tech_spec = state.get("enhanced_spec") or state.get("tech_spec")
    if not tech_spec:
        console.print("[yellow]Skipping field analysis: No tech spec available[/yellow]")
        return state

    connector_name = state.get("connector_name") or state.get("file_name", "unknown")
    click.echo(f"\nStep 4: Running API field dependency analysis for {connector_name}...")

    try:
        analysis_instructions = _read_analysis_prompt()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        state.setdefault("errors", []).append(str(e))
        return state

    # Build prompt
    full_prompt = _build_analysis_prompt(analysis_instructions, connector_name, tech_spec)

    # Get Claude Agent SDK config
    claude_config = get_config().getClaudeAgentConfig()

    if not claude_config.enabled:
        console.print("[yellow]Claude Agent SDK is disabled, skipping field analysis[/yellow]")
        return state

    output_dir = state.get("output_dir")

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ResultMessage, AssistantMessage

        # Build environment variables for LiteLLM proxy
        env_vars = {}
        if claude_config.api_key:
            env_vars["ANTHROPIC_API_KEY"] = claude_config.api_key
        if claude_config.base_url:
            env_vars["ANTHROPIC_BASE_URL"] = claude_config.base_url

        # Create analysis output directory
        analysis_dir = Path(output_dir).resolve() / "field-analysis" if output_dir else Path.cwd() / "field-analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # Resolve output_dir to absolute path for Claude Agent SDK
        abs_output_dir = Path(output_dir).resolve() if output_dir else Path.cwd()

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            cwd=str(abs_output_dir),
            env=env_vars,
            max_turns=claude_config.max_turns,
        )
        if claude_config.model:
            options.model = claude_config.model

        # Run the Claude Agent SDK with a dedicated session for field analysis
        analysis_result_parts = []
        turn_count = 0

        async def run_analysis():
            nonlocal turn_count
            # Create a new ClaudeSDKClient session
            client = ClaudeSDKClient(options)
            
            try:
                await client.connect()
                
                # Send the prompt and receive responses
                await client.query(full_prompt)
                async for message in client.receive_response():
                    console.print(message) 
                    if isinstance(message, AssistantMessage):
                        turn_count += 1
                        for block in message.content:
                            if hasattr(block, "name") and hasattr(block, "input"):
                                # ToolUseBlock — show which tool Claude is calling
                                tool_name = block.name
                                tool_input = block.input or {}
                                display_tool_use(turn_count, tool_name, tool_input)
                            elif hasattr(block, "text"):
                                # TextBlock — Claude's reasoning / output text
                                text = block.text.strip()
                                if text:
                                    analysis_result_parts.append(block.text)
                                    display_text(turn_count, text)
                            elif hasattr(block, "thinking"):
                                # ThinkingBlock — Claude's internal reasoning
                                display_thinking(turn_count, block.thinking)
                    elif isinstance(message, ResultMessage):
                        if message.result:
                            analysis_result_parts.append(message.result)
                        display_result(message)
            finally:
                await client.disconnect()

        console.print()
        console.rule("[bold cyan]Claude Agent: Field Dependency Analysis[/bold cyan]")
        console.print()
        asyncio.run(run_analysis())
        console.rule("[bold cyan]Field Analysis Complete[/bold cyan]")
        console.print()

        if analysis_result_parts:
            analysis_content = "\n".join(analysis_result_parts)

            # Save analysis to the field-analysis subdirectory
            analysis_filename = f"{connector_name.lower()}_field_dependency_analysis.md"
            analysis_filepath = analysis_dir / analysis_filename
            analysis_filepath.write_text(analysis_content, encoding="utf-8")

            state["field_dependency_analysis"] = analysis_content
            state["field_dependency_filepath"] = analysis_filepath

            console.print(f"[green]✓[/green] Field dependency analysis saved to: {analysis_filepath}")
            click.echo(f"Field dependency analysis completed!")
        else:
            console.print("[yellow]Warning: Claude Agent SDK returned no analysis content[/yellow]")
            state.setdefault("warnings", []).append("Field analysis returned no content")

    except ImportError:
        error_msg = "claude-agent-sdk not installed. Install with: pip install claude-agent-sdk"
        console.print(f"[red]Error: {error_msg}[/red]")
        state.setdefault("errors", []).append(error_msg)
    except Exception as e:
        error_msg = f"Error during field analysis: {str(e)}"
        console.print(f"[red]Error: {error_msg}[/red]")
        state.setdefault("errors", []).append(error_msg)

    return state
