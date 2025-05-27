"""URL collection node for the workflow."""

import time
from typing import List

import click
from rich.console import Console

from ..workflow_state import WorkflowState
from ..utils import validate_url, deduplicate_urls, validate_urls_batch

console = Console()


def url_collection_node(state: WorkflowState) -> WorkflowState:
    """
    Collect and validate URLs from user input.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with collected URLs
    """
    console.print("[bold]Enter API documentation URLs[/bold]")
    console.print("(Press Enter without typing a URL to finish)")
    console.print()
    
    urls = []
    while True:
        url = click.prompt("URL", default="", show_default=False).strip()
        
        if not url:
            break
        
        is_valid, error = validate_url(url)
        if not is_valid:
            console.print(f"[red]Invalid URL:[/red] {error}")
            state["errors"].append(f"Invalid URL: {url} - {error}")
            continue
            
        urls.append(url)
        console.print(f"[green]✓[/green] Added: {url}")
    
    # Remove duplicates while preserving order
    urls = deduplicate_urls(urls)
    
    # Final validation
    valid_urls, invalid_urls = validate_urls_batch(urls)
    
    if invalid_urls:
        console.print("\n[yellow]Warning: Some URLs failed validation:[/yellow]")
        for url, error in invalid_urls:
            console.print(f"  [red]✗[/red] {url}: {error}")
            state["warnings"].append(f"URL validation warning: {url} - {error}")
    
    # Update state
    state["urls"] = valid_urls
    state["metadata"]["total_urls"] = len(valid_urls)
    
    if valid_urls:
        console.print(f"\n[bold]Processing {len(valid_urls)} URL(s):[/bold]")
        for i, url in enumerate(valid_urls, 1):
            console.print(f"  {i}. {url}")
    else:
        console.print("[yellow]No valid URLs provided.[/yellow]")
        state["errors"].append("No valid URLs collected")
    
    return state