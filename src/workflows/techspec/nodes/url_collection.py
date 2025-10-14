
from typing import List


from src.utils.validations import  validate_url
from src.utils.transformations import deduplicate_urls

from ..states.techspec_state import TechspecWorkflowState
import click
import json
import re


def _parse_urls_from_input(input_text: str) -> List[str]:
    urls: List[str] = []
    input_text = input_text.strip()

    if not input_text:
        return urls

    try:
        parsed = json.loads(input_text)
        if isinstance(parsed, list):
            urls.extend([str(item).strip() for item in parsed if item])
            return urls
    except (json.JSONDecodeError, ValueError):
        pass

    try:
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

    url_pattern = r'https?://[^\s,\'""\[\]]+|www\.[^\s,\'""\[\]]+'
    found_urls = re.findall(url_pattern, input_text)

    if found_urls:
        urls.extend([url.strip() for url in found_urls if url.strip()])
        return urls

    delimiters = [',', '\n', ';', '\t', ' ']
    for delimiter in delimiters:
        if delimiter in input_text:
            parts = input_text.split(delimiter)
            urls.extend([part.strip().strip('"').strip("'").strip() for part in parts if part.strip()])
            break

    if not urls:
        urls.append(input_text)

    return [url for url in urls if url]


def collect_urls(state: TechspecWorkflowState) -> TechspecWorkflowState:

    # Placeholder implementation for URL collection
    urls = []
    click.echo("Supports: single URLs, JSON arrays, comma/space/newline separated lists")

    while True:
        user_input = input("Enter a URL (or click Enter to finish): ")
        if not user_input.strip() or user_input.strip().lower() == '':
            break


        parsed_urls = _parse_urls_from_input(user_input)
        if not parsed_urls:
            click.echo("No URLs found in input")
            continue
        
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