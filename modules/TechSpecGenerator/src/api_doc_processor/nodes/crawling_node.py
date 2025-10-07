"""Crawling node for the workflow."""

import time
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..workflow_state import WorkflowState, CrawlResult
from ..firecrawl_client import FirecrawlClient

console = Console()


def crawling_node(state: WorkflowState) -> WorkflowState:
    """
    Crawl URLs and save markdown content.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with crawling results
    """
    if not state["urls"]:
        state["errors"].append("No URLs to crawl")
        return state
    
    console.print(f"\n[bold]Step 1: Crawling documentation...[/bold]")
    
    # Initialize Firecrawl client
    try:
        firecrawl_client = FirecrawlClient(state["config"].firecrawl)
    except Exception as e:
        error_msg = f"Failed to initialize Firecrawl client: {str(e)}"
        state["errors"].append(error_msg)
        console.print(f"[red]Error:[/red] {error_msg}")
        return state
    
    # Create markdown directory
    markdown_dir = state["output_dir"] / "markdown"
    markdown_dir.mkdir(exist_ok=True)
    
    # Process URLs with progress tracking
    urls = state["urls"]
    crawl_results: Dict[str, CrawlResult] = {}
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            crawl_task = progress.add_task("Crawling URLs...", total=len(urls))
            
            # Use the existing batch processing method
            raw_results = firecrawl_client.scrape_urls_batch(urls, markdown_dir)
            
            # Convert to our typed format
            for url, result in raw_results.items():
                crawl_results[url] = CrawlResult(
                    success=result["success"],
                    filepath=result["filepath"],
                    content_length=result["content_length"],
                    error=result["error"],
                    url=url
                )
            
            progress.update(crawl_task, advance=len(urls), description="Crawling complete!")
    
    except Exception as e:
        error_msg = f"Error during crawling: {str(e)}"
        state["errors"].append(error_msg)
        console.print(f"\n[red]Error:[/red] {error_msg}")
        return state
    
    # Process results
    successful_crawls = []
    failed_crawls = []
    markdown_files = []
    
    for url, result in crawl_results.items():
        if result["success"] and result["filepath"]:
            successful_crawls.append((url, result))
            markdown_files.append(Path(result["filepath"]))
            console.print(f"[green]✓[/green] {url} → {Path(result['filepath']).name}")
        else:
            failed_crawls.append((url, result))
            console.print(f"[red]✗[/red] {url}: {result['error']}")
            state["errors"].append(f"Crawling failed for {url}: {result['error']}")
    
    # Update state
    state["crawl_results"] = crawl_results
    state["markdown_files"] = markdown_files
    state["metadata"]["successful_crawls"] = len(successful_crawls)
    state["metadata"]["failed_crawls"] = len(failed_crawls)
    
    if not successful_crawls:
        state["errors"].append("No URLs were successfully crawled")
        console.print("\n[red]Error:[/red] No URLs were successfully crawled")
    
    if failed_crawls:
        state["warnings"].append(f"{len(failed_crawls)} URL(s) failed to crawl")
        console.print(f"\n[yellow]Warning:[/yellow] {len(failed_crawls)} URL(s) failed to crawl")
    
    return state