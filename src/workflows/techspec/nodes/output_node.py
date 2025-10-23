from ..states.techspec_state import TechspecWorkflowState as WorkflowState
import click


def output_node(state: WorkflowState) -> WorkflowState:
    click.echo(f"\nProcessing Complete!")
    
    # Display tech spec preview if available
    if "tech_spec" in state and state["tech_spec"]:
        tech_spec = state["tech_spec"]
        click.echo(f"\nPreview of generated specification:")
        preview = tech_spec[:500] + "..." if len(tech_spec) > 500 else tech_spec
        click.echo("============== Tech Spec Preview ==============")
        click.echo(preview)
        click.echo("===============================================")
    
    # Display summary
    click.echo(f"\nSummary:")
    
    metadata = state["metadata"]
    successful_crawls = metadata.get("successful_crawls", 0)
    failed_crawls = metadata.get("failed_crawls", 0)
    
    click.echo(f"• Processed {successful_crawls} documentation source(s)")
    
    if failed_crawls > 0:
        click.echo(f"• Failed to process {failed_crawls} source(s)")
    
    if "tech_spec" in state:
        click.echo(f"• Generated {len(state['tech_spec'])} character specification")
    
    if state["metadata"].get("mock_server_generated", False):
        click.echo(f"• Mock server generated successfully")
        if "mock_server_dir" in state:
            click.echo(f"• Mock server directory: {state['mock_server_dir']}")
        if "mock_server_process" in state and state["mock_server_process"]:
            click.echo(f"• Mock server running (PID: {state['mock_server_process'].pid})")
    
    click.echo(f"• Results saved to: {state['output_dir']}")
    
    # Display any warnings
    if state["warnings"]:
        click.echo(f"\nWarnings ({len(state['warnings'])}):")
        for warning in state["warnings"]:
            click.echo(f"    {warning}")
    
    # Display any errors
    if state["errors"]:
        click.echo(f"\nErrors ({len(state['errors'])}):")
        for error in state["errors"]:
            click.echo(f"   {error}")
    
    # Add performance metrics if available
    if "duration" in metadata:
        click.echo(f"\nProcessing time: {metadata['duration']:.2f} seconds")
    
    if "estimated_tokens" in metadata:
        tokens = metadata["estimated_tokens"]
        click.echo(f"Token usage: ~{tokens.get('estimated_input_tokens', 0)} input + {tokens.get('max_output_tokens', 0)} output")
    
    return state