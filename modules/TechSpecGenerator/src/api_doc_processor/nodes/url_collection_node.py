"""URL collection node for the workflow."""

import json
import re
import time
from typing import List

import click
from rich.console import Console

from ..workflow_state import WorkflowState
from ..utils import validate_url, deduplicate_urls, validate_urls_batch

console = Console()


def parse_urls_from_input(input_text: str) -> List[str]:
    """
    Super parser to extract URLs from various input formats.

    Supports:
    - Array format: ["url1", "url2"]
    - JSON array: ["url1", "url2"]
    - Comma-separated: url1, url2, url3
    - Space-separated: url1 url2 url3
    - Newline-separated: url1\\nurl2\\nurl3
    - Mixed formats

    Args:
        input_text: Raw input string

    Returns:
        List of extracted URLs
    """
    urls = []
    input_text = input_text.strip()

    if not input_text:
        return urls

    # Try parsing as JSON array
    try:
        parsed = json.loads(input_text)
        if isinstance(parsed, list):
            urls.extend([str(item).strip() for item in parsed if item])
            return urls
    except (json.JSONDecodeError, ValueError):
        pass

    # Try parsing Python-style array
    try:
        # Remove brackets and split
        if input_text.startswith('[') and input_text.endswith(']'):
            content = input_text[1:-1]
            # Split by comma and clean up quotes
            items = re.split(r',\s*', content)
            for item in items:
                item = item.strip().strip('"').strip("'").strip()
                if item:
                    urls.append(item)
            if urls:
                return urls
    except Exception:
        pass

    # Extract all URLs using regex pattern
    url_pattern = r'https?://[^\s,\'""\[\]]+|www\.[^\s,\'""\[\]]+'
    found_urls = re.findall(url_pattern, input_text)

    if found_urls:
        urls.extend([url.strip() for url in found_urls if url.strip()])
        return urls

    # Fallback: split by common delimiters
    delimiters = [',', '\n', ';', '\t', ' ']
    for delimiter in delimiters:
        if delimiter in input_text:
            parts = input_text.split(delimiter)
            urls.extend([part.strip().strip('"').strip("'").strip() for part in parts if part.strip()])
            break

    # If no delimiter found, treat as single URL
    if not urls:
        urls.append(input_text)

    return [url for url in urls if url]


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
    console.print("[dim]Supports: single URLs, JSON arrays, comma/space/newline separated lists[/dim]")
    console.print()

    urls = []
    while True:
        user_input = click.prompt("URL(s)", default="", show_default=False).strip()

        if not user_input:
            break

        # Parse URLs from input using super parser
        parsed_urls = parse_urls_from_input(user_input)

        if not parsed_urls:
            console.print("[yellow]No URLs found in input[/yellow]")
            continue

        # Validate and add each parsed URL
        for url in parsed_urls:
            is_valid, error = validate_url(url)
            if not is_valid:
                console.print(f"[red]Invalid URL:[/red] {url} - {error}")
                state["errors"].append(f"Invalid URL: {url} - {error}")
                continue

            urls.append(url)
            console.print(f"[green]✓[/green] Added: {url}")

        # Show current list of added URLs
        if urls:
            console.print(f"\n[dim]Total URLs added so far: {len(urls)}[/dim]\n")
    
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