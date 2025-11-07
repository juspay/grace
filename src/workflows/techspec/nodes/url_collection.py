
from typing import List


from src.utils.validations import  validate_url
from src.utils.transformations import deduplicate_urls

from ..states.techspec_state import TechspecWorkflowState
import click
import json
import re


def _parse_urls_from_input(input_text: str) -> List[str]:
    """Parse URLs from input text, splitting by newlines only."""
    if not input_text.strip():
        return []
    
    # Split by newlines and return non-empty lines as URLs
    urls = [line.strip() for line in input_text.split('\n') if line.strip()]
    return urls


def collect_urls(state: TechspecWorkflowState) -> TechspecWorkflowState:

    # Placeholder implementation for URL collection
    urls = []
    click.echo("Enter URLs (one per line). Press Enter on an empty line to finish:")

    # Collect multi-line input until an empty line is entered (after content)
    lines = []
    
    while True:
        try:
            line = input()
            is_empty = not line.strip()
            
            if is_empty:
                # If we have content and get an empty line, finish
                # If no content yet, allow one empty line (for two consecutive newlines case)
                if lines:
                    break
            else:
                lines.append(line)
        except EOFError:
            break
    
    # Combine all lines into a single input string
    user_input = '\n'.join(lines)
    
    if user_input.strip():
        parsed_urls = _parse_urls_from_input(user_input)
        if not parsed_urls:
            click.echo("No URLs found in input")
        else:
            for url in parsed_urls:
                is_valid, error = validate_url(url)
                if not is_valid:
                    click.echo(f"Invalid URL: {url} - {error}")
                    # state["warning"].append(f"Invalid URL: {url} - {error}")
                    continue

                urls.append(url)
                click.echo(f"Added: {url}")

    urls = deduplicate_urls(urls)

    state["urls"] = urls
    if "metadata" not in state:
        state["metadata"] = {}
    state["metadata"]["total_urls"] = len(urls)
    if urls:
        click.echo(f"\nProcessing {len(urls)} URL(s):")
        for i, url in enumerate(urls, 1):
            click.echo(f"  {i}. {url}")
    else:
        click.echo("No valid URLs provided.")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("No valid URLs collected")
    return state