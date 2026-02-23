"""Claude Agent SDK enhancement node — reviews scraped MDs against generated tech spec."""

import asyncio
from pathlib import Path
from typing import List

import click
from rich.console import Console

from ..states.techspec_state import TechspecWorkflowState
from src.config import get_config
from src.tools.filemanager.filemanager import FileManager
from ._claude_display import display_tool_use, display_text, display_thinking, display_result

console = Console()

# Grace project root (where enhancer.md and analysis.md live)
GRACE_ROOT = Path(__file__).parent.parent.parent.parent.parent


def _read_enhancer_prompt() -> str:
    """Read the enhancer.md prompt from grace root."""
    enhancer_path = GRACE_ROOT / "enhacer.md "
    if not enhancer_path.exists():
        # Try without trailing space
        enhancer_path = GRACE_ROOT / "enhacer.md"
    if not enhancer_path.exists():
        enhancer_path = GRACE_ROOT / "enhancer.md"
    if not enhancer_path.exists():
        raise FileNotFoundError(
            f"enhancer.md not found in {GRACE_ROOT}. "
            "Looked for: enhacer.md, enhancer.md"
        )
    return enhancer_path.read_text(encoding="utf-8")


def _build_enhancement_prompt(
    enhancer_instructions: str,
    connector_name: str,
    tech_spec_content: str,
    markdown_files_content: List[str],
) -> str:
    """Build the full prompt for the enhancement step.
    
    Dynamically replaces hardcoded connector references in the enhancer
    prompt with the actual connector name.
    """
    # Replace hardcoded references with dynamic connector name
    prompt = enhancer_instructions
    prompt = prompt.replace("Airwallex", connector_name)
    prompt = prompt.replace("airwallex", connector_name.lower())
    prompt = prompt.replace("output/airwallex", f"output/{connector_name.lower()}")

    # Build the combined content for Claude to review
    md_sections = []
    for i, content in enumerate(markdown_files_content):
        md_sections.append(f"--- Source Document {i + 1} ---\n{content}")
    combined_md = "\n\n".join(md_sections)

    full_prompt = f"""{prompt}

--- CONNECTOR NAME ---
{connector_name}

--- CURRENT TECHNICAL SPECIFICATION ---
{tech_spec_content}

--- SOURCE MARKDOWN DOCUMENTATION ---
{combined_md}

IMPORTANT: All the content you need is provided above in this prompt. Do NOT attempt to read files from disk or explore the filesystem.
Review the technical specification against the source documentation provided above.
Enrich and complete the specification following the instructions provided.
Output ONLY the complete updated technical specification as markdown — no preamble, no explanation, just the full enriched spec."""

    return full_prompt


def enhance_spec(state: TechspecWorkflowState) -> TechspecWorkflowState:
    """Enhance the tech spec using Claude Agent SDK with enhancer.md prompt."""

    tech_spec = state.get("tech_spec")
    if not tech_spec:
        console.print("[yellow]Skipping enhancement: No tech spec to enhance[/yellow]")
        return state

    click.echo(f"\nStep 3: Enhancing technical specification with Claude Agent SDK...")

    try:
        # Load the enhancer prompt
        enhancer_instructions = _read_enhancer_prompt()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        state.setdefault("errors", []).append(str(e))
        return state

    # Read all scraped markdown files content
    output_dir = state.get("output_dir")
    markdown_files = state.get("markdown_files", [])
    connector_name = state.get("connector_name") or state.get("file_name", "unknown")

    markdown_contents = []
    filemanager = FileManager(base_path=str(output_dir))

    if state.get("folder"):
        filemanager.update_base_path("")

    for md_file in markdown_files:
        try:
            content = filemanager.read_file(md_file)
            if content:
                markdown_contents.append(content)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read {md_file}: {e}[/yellow]")

    if not markdown_contents:
        console.print("[yellow]No markdown source docs found, skipping enhancement[/yellow]")
        return state

    # Build the prompt
    full_prompt = _build_enhancement_prompt(
        enhancer_instructions, connector_name, tech_spec, markdown_contents
    )

    # Get Claude Agent SDK config
    claude_config = get_config().getClaudeAgentConfig()

    if not claude_config.enabled:
        console.print("[yellow]Claude Agent SDK is disabled, skipping enhancement[/yellow]")
        return state

    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ResultMessage, AssistantMessage

        # Build environment variables for LiteLLM proxy
        env_vars = {}
        if claude_config.api_key:
            env_vars["ANTHROPIC_API_KEY"] = claude_config.api_key
        if claude_config.base_url:
            env_vars["ANTHROPIC_BASE_URL"] = claude_config.base_url

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

        # Run the Claude Agent SDK with a dedicated session for enhancement
        enhanced_result_parts = []
        turn_count = 0

        async def run_enhancement():
            nonlocal turn_count
            # Create a new ClaudeSDKClient session
            client = ClaudeSDKClient(options)
            
            try:
                await client.connect()
                
                # Send the prompt and receive responses
                await client.query(full_prompt)
                async for message in client.receive_response():
                    console.print(message)  # Add spacing between turns
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
                                    enhanced_result_parts.append(block.text)
                                    display_text(turn_count, text)
                            elif hasattr(block, "thinking"):
                                # ThinkingBlock — Claude's internal reasoning
                                display_thinking(turn_count, block.thinking)
                    elif isinstance(message, ResultMessage):
                        if message.result:
                            enhanced_result_parts.append(message.result)
                        display_result(message)
            finally:
                await client.disconnect()

        console.print()
        console.rule("[bold cyan]Claude Agent: Enhancing Specification[/bold cyan]")
        console.print()
        asyncio.run(run_enhancement())
        console.rule("[bold cyan]Enhancement Complete[/bold cyan]")
        console.print()

        if enhanced_result_parts:
            enhanced_spec = "\n".join(enhanced_result_parts)

            # Save enhanced spec
            filemanager_out = FileManager(base_path=str(output_dir))
            enhanced_filename = f"{connector_name.lower()}_enhanced_spec.md"
            enhanced_filepath = Path("specs") / enhanced_filename
            filemanager_out.write_file(enhanced_filepath, enhanced_spec)

            state["enhanced_spec"] = enhanced_spec
            state["enhanced_spec_filepath"] = output_dir / enhanced_filepath

            console.print(f"[green]✓[/green] Enhanced specification saved to: {output_dir / enhanced_filepath}")
            click.echo(f"Enhanced specification generated!")
        else:
            console.print("[yellow]Warning: Claude Agent SDK returned no enhancement content[/yellow]")
            state.setdefault("warnings", []).append("Enhancement returned no content")

    except ImportError:
        error_msg = "claude-agent-sdk not installed. Install with: pip install claude-agent-sdk"
        console.print(f"[red]Error: {error_msg}[/red]")
        state.setdefault("errors", []).append(error_msg)
    except Exception as e:
        error_msg = f"Error during spec enhancement: {str(e)}"
        console.print(f"[red]Error: {error_msg}[/red]")
        state.setdefault("errors", []).append(error_msg)

    return state
