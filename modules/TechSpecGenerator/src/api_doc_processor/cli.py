"""Command-line interface for API Documentation Processor."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from .config import Config, create_sample_config, load_config
from .workflow import create_workflow
from .firecrawl_client import FirecrawlClient
from .llm_client import LLMClient


console = Console()


def print_header():
    """Print the application header."""
    header = Text("API Documentation Processor", style="bold blue")
    subheader = Text("Automate API integration research and planning", style="dim")
    
    console.print()
    console.print(Panel.fit(f"{header}\n{subheader}", border_style="blue"))
    console.print()




@click.command()
@click.option(
    "--config", 
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.json)"
)
@click.option(
    "--create-config",
    is_flag=True,
    help="Create a sample configuration file and exit"
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="api-doc-processor-data",
    help="Output directory for generated files"
)
@click.option(
    "--test-only",
    is_flag=True,
    help="Test API connections and exit"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--generate-mock-server",
    is_flag=True,
    help="Generate a mock server after creating the tech spec"
)
def main(config_path: Path, create_config: bool, output_dir: Path, test_only: bool, verbose: bool, generate_mock_server: bool):
    """API Documentation Processor - Automate API integration research."""
    
    if create_config:
        config_file = config_path or Path("config.json")
        create_sample_config(config_file)
        return
    
    print_header()
    
    # Load configuration
    try:
        config = load_config(config_path)
        console.print("[green]✓[/green] Configuration loaded successfully")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Run with --create-config to generate a sample configuration")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)
    
    # Test connections if requested
    if test_only:
        console.print("\n[bold]Testing API connections...[/bold]")
        
        try:
            firecrawl_client = FirecrawlClient(config.firecrawl)
            firecrawl_ok, firecrawl_msg = firecrawl_client.test_connection()
            if firecrawl_ok:
                console.print(f"[green]✓[/green] {firecrawl_msg}")
            else:
                console.print(f"[red]✗[/red] {firecrawl_msg}")
                if verbose:
                    console.print(f"[dim]Debug info: Check your Firecrawl API key in config.json[/dim]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗[/red] Firecrawl connection failed: {str(e)}")
            sys.exit(1)
        
        try:
            llm_client = LLMClient(config.litellm)
            llm_ok, llm_msg = llm_client.test_connection()
            if llm_ok:
                console.print(f"[green]✓[/green] {llm_msg}")
            else:
                console.print(f"[red]✗[/red] {llm_msg}")
                if verbose:
                    console.print(f"[dim]Debug info: Check your LLM API key and model settings in config.json[/dim]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗[/red] LLM connection failed: {str(e)}")
            sys.exit(1)
        
        console.print("\n[green]✓[/green] All API connections successful!")
        return
    
    # Enable mock server generation if requested
    if generate_mock_server:
        config.workflow.mock_server_generation.enabled = True
        console.print(f"[green]✓[/green] Mock server generation enabled")
    
    # Create and run the workflow
    try:
        workflow = create_workflow(config, output_dir)
        final_state = workflow.run()
        
        # Check for critical errors
        if final_state["errors"]:
            critical_errors = [e for e in final_state["errors"] if "No URLs" in e or "No files" in e or "failed to initialize" in e.lower()]
            if critical_errors:
                console.print(f"\n[red]Critical errors encountered:[/red]")
                for error in critical_errors:
                    console.print(f"  ❌ {error}")
                sys.exit(1)
        
        # Display verbose error information if requested
        if verbose and final_state["errors"]:
            console.print(f"\n[yellow]Verbose error details:[/yellow]")
            for error in final_state["errors"]:
                console.print(f"  🔍 {error}")
    
    except Exception as e:
        console.print(f"\n[red]Workflow execution failed:[/red] {str(e)}")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()