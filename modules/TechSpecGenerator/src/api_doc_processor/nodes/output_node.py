"""Output management node for the workflow."""

from rich.console import Console
from rich.panel import Panel

from ..workflow_state import WorkflowState

console = Console()


def output_node(state: WorkflowState) -> WorkflowState:
    """
    Manage output display and final results.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with output management complete
    """
    console.print(f"\n[bold]Processing Complete![/bold]")
    
    # Display tech spec preview if available
    if "tech_spec" in state and state["tech_spec"]:
        tech_spec = state["tech_spec"]
        console.print(f"\n[bold]Preview of generated specification:[/bold]")
        preview = tech_spec[:500] + "..." if len(tech_spec) > 500 else tech_spec
        console.print(Panel(preview, border_style="green", title="Tech Spec Preview"))
    
    # Display summary
    console.print(f"\n[bold]Summary:[/bold]")
    
    metadata = state["metadata"]
    successful_crawls = metadata.get("successful_crawls", 0)
    failed_crawls = metadata.get("failed_crawls", 0)
    
    console.print(f"• Processed {successful_crawls} documentation source(s)")
    
    if failed_crawls > 0:
        console.print(f"• Failed to process {failed_crawls} source(s)")
    
    if "tech_spec" in state:
        console.print(f"• Generated {len(state['tech_spec'])} character specification")
    
    if state["metadata"].get("mock_server_generated", False):
        console.print(f"• Mock server generated successfully")
        if "mock_server_dir" in state:
            console.print(f"• Mock server directory: {state['mock_server_dir']}")
        if "mock_server_process" in state and state["mock_server_process"]:
            console.print(f"• Mock server running (PID: {state['mock_server_process'].pid})")
    
    console.print(f"• Results saved to: {state['output_dir']}")
    
    # Display any warnings
    if state["warnings"]:
        console.print(f"\n[yellow]Warnings ({len(state['warnings'])}):[/yellow]")
        for warning in state["warnings"]:
            console.print(f"  ⚠️  {warning}")
    
    # Display any errors
    if state["errors"]:
        console.print(f"\n[red]Errors ({len(state['errors'])}):[/red]")
        for error in state["errors"]:
            console.print(f"  ❌ {error}")
    
    # Add performance metrics if available
    if "duration" in metadata:
        console.print(f"\n[dim]Processing time: {metadata['duration']:.2f} seconds[/dim]")
    
    if "estimated_tokens" in metadata:
        tokens = metadata["estimated_tokens"]
        console.print(f"[dim]Token usage: ~{tokens.get('estimated_input_tokens', 0)} input + {tokens.get('max_output_tokens', 0)} output[/dim]")
    
    return state