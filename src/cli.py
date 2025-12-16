#!/usr/bin/env python3
"""Grace CLI - Command line interface with research and techspec commands."""

import sys
import asyncio
import click
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import workflow modules
from .workflows import run_techspec_workflow, run_research_workflow, run_pr_workflow
from .workflows.code.main import chat_loop
from .config import get_config
from .scripts.searxng_setup import setup_docker, setup_local, check_docker

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """ Grace CLI - Intelligent research and technical specification generator.\n
        usage:\n
        grace techspec [OPTIONS] [CONNECTOR]\n
        options:\n
            --output TEXT            Output directory for generated specs\n
            --verbose                Enable verbose output\n
            --mock-server or -m      Enable mock server\n
        grace research [OPTIONS] [QUERY]\n
        options:\n
            --output TEXT            Output file path\n
            --tech-spec              Generate technical specification\n
            --format [markdown|json|text]  Output format\n
            --depth INTEGER          Research depth (1-10)\n
            --sources INTEGER        Number of sources to analyze\n
            --verbose                Enable verbose output\n
        grace pr [OPTIONS] [PR_URL]\n
        options:\n
            --output TEXT            Output directory for PR data\n
            --verbose                Enable verbose output\n
        grace code
    """
    pass


@cli.command()
@click.option('--local', '-l', is_flag=True, help='Use local installation instead of Docker')
def setupsearch(local):
    """Setup SearXNG search engine for Grace Research."""
    if local:
        setup_local()
    elif check_docker():
        setup_docker()
    else:
        setup_local()

@cli.command()
@click.argument('connector', required=False)
@click.option('folder', '-f', help="the docs folder")
@click.option('urls', '-u', help="the docs urls file")
@click.option('--output', '-o', help='Output directory for generated specs')
@click.option('--test-only', is_flag=True, help='Run in test mode without generating files')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--mock-server', '-m', is_flag=True, help='Enable mock server for API interactions (for testing)')
def techspec(connector, folder, urls, output, test_only, verbose, mock_server):
    # we will use the other flags in future for more customization don't remove them
    """ -m flag to mock server and use --help for more details
    -u pass the urls file for docs
    -f pass the docs folder
    """
    async def run_techspec():
        """Async wrapper for techspec workflow."""
        try:
            if verbose:
                click.echo(f"Starting techspec workflow...")
                click.echo(f"Connector: {connector}")
                if output:
                    click.echo(f"Output dir: {output}")
                if mock_server:
                    click.echo("Mock server: ENABLED")
                if test_only:
                    click.echo("Mode: TEST ONLY")
                click.echo()

            if urls:
                click.echo(f"Docs URLs file: {urls}")
            # Use config for output directory if not specified
            output_dir = output or None
            # Execute the techspec workflow
            result = await run_techspec_workflow(
                connector_name=connector,
                folder=folder,
                urls_file=urls,
                output_dir=output_dir,
                test_only=test_only,
                verbose=verbose,
                mock_server=mock_server,
            )

            if result["success"]:
                click.echo("Techspec generation completed successfully!")

                # Display output summary
                output_data = result.get("output", {})
                if output_data:
                    click.echo("\nGeneration Summary:")
                    click.echo(f"  • Connector: {output_data.get('connector_name', connector)}")

                    summary = output_data.get("summary", {})
                    if summary:
                        click.echo(f"  • Total files: {summary.get('total_files', 0)}")
                        click.echo(f"  • Code files: {summary.get('code_files', 0)}")
                        click.echo(f"  • Test files: {summary.get('test_files', 0)}")
                        click.echo(f"  • Documentation: {summary.get('documentation_files', 0)}")

                    output_dir_path = output_data.get("output_directory", f"./generated/{connector}")
                    if not test_only:
                        click.echo(f"  • Output directory: {output_dir_path}")

                        # Create output directory and files (in real implementation)
                        output_path = Path(output_dir_path)
                        output_path.mkdir(parents=True, exist_ok=True)

                        # Save a summary file
                        summary_file = output_path / "generation_summary.json"
                        import json
                        with open(summary_file, 'w') as f:
                            json.dump(result, f, indent=2, default=str)

                        click.echo(f"  • Summary saved: {summary_file}")

                    instructions = output_data.get("instructions", {})
                    if instructions:
                        click.echo("\nNext Steps:")
                        for step in instructions.get("next_steps", []):
                            click.echo(f"  • {step}")

                        if not test_only:
                            test_cmd = instructions.get("test_command")
                            build_cmd = instructions.get("build_command")
                            if test_cmd:
                                click.echo(f"\nTest command: {test_cmd}")
                            if build_cmd:
                                click.echo(f"Build command: {build_cmd}")

            else:
                # click.echo(f"result: {result}")
                if verbose and result.get("metadata"):
                    click.echo(f"Debug info: {result['metadata']}", err=True)
                sys.exit(1)

        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}", err=True)
            if verbose:
                import traceback
                click.echo(f"Traceback: {traceback.format_exc()}", err=True)
            sys.exit(1)

    # Run the async workflow
    asyncio.run(run_techspec())

@cli.command()
@click.argument('query', required=False)
@click.option('--output', '-o', help='Output file path')
@click.option('--tech-spec', '-ts', is_flag=True, help='Generate technical specification')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']),
              help='Output format')
@click.option('--depth', '-d', type=int, help='Research depth (1-10)')
@click.option('--ai-browser', '-ai', is_flag=True, help='Enable AI assistance')
@click.option('--sources', '-s', type=int, help='Number of sources to analyze')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def research(query, output, tech_spec, format, depth, ai_browser, sources, verbose):
    """Perform research on a given connector."""
    while not query or query.strip() == "":
        query = click.prompt("Enter your research query: ", type=str, default="", show_default=False)
        if not query:
            click.echo("Error: Research query is required", err=True)
            continue

    async def run_research():
        """Async wrapper for research workflow."""
        try:
            if verbose:
                click.echo(f"Starting research workflow...")
                click.echo(f"Query: {query}")
                if output:
                    click.echo(f"Output file: {output}")
                if tech_spec:
                    click.echo("Technical specification generation: ENABLED")
                if format:
                    click.echo(f"Output format: {format}")
                if depth:
                    click.echo(f"Research depth: {depth}")
                if sources:
                    click.echo(f"Number of sources: {sources}")
                if ai_browser:
                    click.echo("AI assistance: ENABLED")
                click.echo()

            # Use config for output file if not specified
            config_instance = get_config()
            output_file = output or config_instance.getTechSpecConfig().output_dir

            # Execute the research workflow 
            result = await run_research_workflow(
                connector_name=query,
                output_dir=output_file,
                tech_spec=tech_spec,
                format=format,
                depth=depth,
                ai_browser=ai_browser,
                sources=sources,
                verbose=verbose
            )
            click.echo(f"Research result: {result}")
        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}", err=True)
            if verbose:
                import traceback
                click.echo(f"Traceback: {traceback.format_exc()}", err=True)
            sys.exit(1)
        

    asyncio.run(run_research())


@cli.command()
@click.argument('pr_url', required=False)
@click.option('--output', '-o', help='Output directory for PR data')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def pr(pr_url, output, verbose):
    """Fetches PR and summarizes changes using AI."""
    while not pr_url or pr_url.strip() == "":
        pr_url = click.prompt(
            "Enter GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
            type=str,
            default="",
            show_default=False
        )
        if not pr_url:
            click.echo("Error: PR URL is required", err=True)
            continue

    async def run_pr():
        try:
            if verbose:
                click.echo(f"Starting PR workflow...")
                click.echo(f"PR URL: {pr_url}")
                if output:
                    click.echo(f"Output directory: {output}")
                click.echo()

            config_instance = get_config()
            output_dir = output or config_instance.getTechSpecConfig().output_dir

            result = await run_pr_workflow(
                pr_url=pr_url,
                output_dir=output_dir,
                verbose=verbose
            )

            if result["success"]:
                output_data = result.get("output", {})
                if output_data:
                    connector_name = output_data.get('connector_name')
                    if connector_name and connector_name != 'unknown':
                        click.echo(f"  • Connector: {connector_name}")

                    stats = output_data.get("statistics", {})
                    if stats:
                        click.echo(f"\n  Statistics:")
                        click.echo(f"    - Files changed: {stats.get('files_changed', 0)}")
                        click.echo(f"    - Total comments: {stats.get('total_comments', 0)}")
                        click.echo(f"      • Review comments (inline): {stats.get('review_comments', 0)}")
                        click.echo(f"      • Issue comments (general): {stats.get('issue_comments', 0)}")

                    # Show AI summary status
                    if output_data.get('has_ai_summary'):
                        click.echo(f"\n  ✓ AI analysis completed")

                    # Show storage locations
                    grace_dir = output_data.get("grace_storage_directory")
                    summary_file = output_data.get("summary_file")

                    click.echo(f"\n  Storage Locations:")
                    if grace_dir:
                        click.echo(f"    - Raw data: {grace_dir}")
                    if summary_file:
                        click.echo(f"    - AI summary: {summary_file}")

            else:
                click.echo(f"PR workflow failed: {result['error']}", err=True)
                if verbose and result.get("metadata"):
                    click.echo(f"Debug info: {result['metadata']}", err=True)
                sys.exit(1)

        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}", err=True)
            if verbose:
                import traceback
                click.echo(f"Traceback: {traceback.format_exc()}", err=True)
            sys.exit(1)

    asyncio.run(run_pr())


@cli.command()
def code():
    """Starts an interactive chat session with the AI agent."""
    asyncio.run(chat_loop())

@cli.command()
@click.option('--list', '-l', 'list_prompts', is_flag=True, help='List all available prompts')
@click.option('--validate', '-v', is_flag=True, help='Validate all loaded prompts')
@click.option('--stats', '-s', is_flag=True, help='Show prompt statistics')
@click.option('--reload', '-r', is_flag=True, help='Reload all prompt sources')
@click.option('--source', type=click.Choice(['default', 'promcode', 'system', 'user']), 
              help='Filter by prompt source')
@click.option('--info', help='Get detailed information about a specific prompt')
def prompts(list_prompts, validate, stats, reload, source, info):
    """Manage and inspect Grace Code prompts including Promcode integration."""
    from src.ai.system.prompt_manager import get_prompt_manager, PromptSource
    from src.ai.system.prompt_config import PromptConfig
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    import json
    
    console = Console()
    
    try:
        # Initialize prompt manager
        prompt_manager = get_prompt_manager()
        
        # Handle reload first if requested
        if reload:
            console.print("[yellow]Reloading all prompt sources...[/yellow]")
            success = prompt_manager.reload_all()
            if success:
                console.print("[green]✓ Successfully reloaded all prompt sources[/green]")
            else:
                console.print("[red]✗ Failed to reload some prompt sources[/red]")
                return
        
        # Handle specific prompt info
        if info:
            prompt_entry = prompt_manager.get_prompt_info(info)
            if prompt_entry:
                console.print(f"\n[bold cyan]Prompt Information: {info}[/bold cyan]")
                
                # Create info table
                info_table = Table(show_header=False, box=None)
                info_table.add_column("Property", style="bold yellow")
                info_table.add_column("Value")
                
                info_table.add_row("Name", prompt_entry.name)
                info_table.add_row("Source", prompt_entry.source.value)
                info_table.add_row("Priority", str(prompt_entry.priority))
                info_table.add_row("Length", f"{len(prompt_entry.content)} characters")
                info_table.add_row("Created", prompt_entry.metadata.created or "Unknown")
                info_table.add_row("Version", prompt_entry.metadata.version)
                
                console.print(info_table)
                
                # Show content preview
                content_preview = prompt_entry.content[:500]
                if len(prompt_entry.content) > 500:
                    content_preview += "\n... (truncated)"
                
                console.print(f"\n[bold]Content Preview:[/bold]")
                console.print(Panel(content_preview, title="Prompt Content"))
            else:
                console.print(f"[red]Prompt '{info}' not found[/red]")
            return
        
        # Handle list prompts
        if list_prompts:
            source_filter = None
            if source:
                source_filter = PromptSource(source)
            
            prompts_list = prompt_manager.list_prompts(source_filter)
            
            console.print(f"\n[bold cyan]Available Prompts[/bold cyan]")
            if source:
                console.print(f"[dim]Filtered by source: {source}[/dim]")
            
            # Create prompts table
            prompts_table = Table(show_header=True)
            prompts_table.add_column("Prompt Name", style="bold green")
            prompts_table.add_column("Source", style="yellow")
            prompts_table.add_column("Length", justify="right")
            prompts_table.add_column("Enhanced", justify="center")
            
            for prompt_name in sorted(prompts_list):
                entry = prompt_manager.get_prompt_info(prompt_name)
                if entry:
                    is_enhanced = prompt_name.startswith('enhanced')
                    enhanced_marker = "✓" if is_enhanced else "-"
                    
                    prompts_table.add_row(
                        prompt_name,
                        entry.source.value,
                        str(len(entry.content)),
                        enhanced_marker
                    )
            
            console.print(prompts_table)
            console.print(f"\n[dim]Total prompts: {len(prompts_list)}[/dim]")
        
        # Handle validation
        if validate:
            console.print("\n[yellow]Validating prompts...[/yellow]")
            issues = prompt_manager.validate_prompts()
            
            if not issues:
                console.print("[green]✓ All prompts are valid[/green]")
            else:
                console.print(f"[red]Found issues in {len(issues)} prompts:[/red]")
                
                for prompt_name, prompt_issues in issues.items():
                    console.print(f"\n[bold red]• {prompt_name}:[/bold red]")
                    for issue in prompt_issues:
                        console.print(f"  - {issue}")
        
        # Handle statistics
        if stats:
            stats_data = prompt_manager.get_statistics()
            
            console.print(f"\n[bold cyan]Prompt Statistics[/bold cyan]")
            
            # Create stats table
            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Metric", style="bold yellow")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Total Prompts", str(stats_data['total_prompts']))
            stats_table.add_row("Sources Loaded", str(stats_data['sources_loaded']))
            stats_table.add_row("Total Content Length", f"{stats_data['total_content_length']:,} chars")
            stats_table.add_row("Average Prompt Length", f"{stats_data['average_prompt_length']:,} chars")
            
            if stats_data.get('last_reload'):
                stats_table.add_row("Last Reload", str(stats_data['last_reload']))
            
            console.print(stats_table)
            
            # Show prompts by source
            console.print(f"\n[bold]Prompts by Source:[/bold]")
            source_table = Table(show_header=True)
            source_table.add_column("Source", style="yellow")
            source_table.add_column("Count", justify="right", style="green")
            
            for source_name, count in stats_data['prompts_by_source'].items():
                source_table.add_row(source_name, str(count))
            
            console.print(source_table)
            
            # Show loaded files
            if stats_data.get('loaded_files'):
                console.print(f"\n[bold]Loaded Files:[/bold]")
                for file_path in stats_data['loaded_files']:
                    console.print(f"  • {file_path}")
        
        # Default behavior - show basic info
        if not any([list_prompts, validate, stats, reload, info]):
            console.print("[bold cyan]Grace Code Prompt Management[/bold cyan]")
            console.print("\nUse --help to see available options:")
            console.print("  --list     List all prompts")
            console.print("  --validate Validate prompts")
            console.print("  --stats    Show statistics")
            console.print("  --reload   Reload all sources")
            console.print("  --info     Get prompt details")
            
            # Show quick stats
            stats_data = prompt_manager.get_statistics()
            console.print(f"\n[dim]Quick stats: {stats_data['total_prompts']} prompts from {stats_data['sources_loaded']} sources[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error managing prompts: {str(e)}[/red]")
        if click.get_current_context().params.get('verbose'):
            import traceback
            console.print(f"[dim red]Traceback: {traceback.format_exc()}[/dim red]")


def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
