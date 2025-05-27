"""LLM processing node for the workflow."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..workflow_state import WorkflowState
from ..llm_client import LLMClient

console = Console()


def llm_processing_node(state: WorkflowState) -> WorkflowState:
    """
    Generate technical specification using LLM.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with generated tech spec
    """
    if not state["markdown_files"]:
        state["errors"].append("No markdown files to process")
        console.print("[red]Error:[/red] No markdown files to process")
        return state
    
    console.print(f"\n[bold]Step 2: Generating technical specification...[/bold]")
    
    # Initialize LLM client
    try:
        llm_client = LLMClient(state["config"].litellm)
    except Exception as e:
        error_msg = f"Failed to initialize LLM client: {str(e)}"
        state["errors"].append(error_msg)
        console.print(f"[red]Error:[/red] {error_msg}")
        return state
    
    # Show token estimation
    try:
        token_estimate = llm_client.estimate_token_usage(state["markdown_files"])
        if "error" not in token_estimate:
            state["metadata"]["estimated_tokens"] = token_estimate
            console.print(f"[dim]Estimated tokens: ~{token_estimate['estimated_input_tokens']} input + {token_estimate['max_output_tokens']} output[/dim]")
    except Exception as e:
        state["warnings"].append(f"Token estimation failed: {str(e)}")
    
    # Generate tech spec
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            llm_task = progress.add_task("Generating tech spec...", total=None)
            
            spec_success, tech_spec, spec_error = llm_client.generate_tech_spec(
                state["markdown_files"], state["config"].prompt
            )
            
            if spec_success:
                # Save the tech spec
                specs_dir = state["output_dir"] / "specs"
                specs_dir.mkdir(exist_ok=True)
                spec_filepath = llm_client.save_tech_spec(tech_spec, specs_dir)
                
                # Update state
                state["tech_spec"] = tech_spec
                state["spec_filepath"] = spec_filepath
                state["metadata"]["spec_generated"] = True
                
                progress.update(llm_task, description="Tech spec generated!")
                console.print(f"\n[green]✓[/green] Technical specification generated!")
                console.print(f"[dim]Saved to: {spec_filepath}[/dim]")
            else:
                state["errors"].append(f"Tech spec generation failed: {spec_error}")
                state["metadata"]["spec_generated"] = False
                progress.update(llm_task, description="Tech spec generation failed!")
                console.print(f"\n[red]Error generating tech spec:[/red] {spec_error}")
    
    except Exception as e:
        error_msg = f"Error during tech spec generation: {str(e)}"
        state["errors"].append(error_msg)
        state["metadata"]["spec_generated"] = False
        console.print(f"\n[red]Error:[/red] {error_msg}")
    
    return state