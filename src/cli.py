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
from .workflows import run_techspec_workflow, run_research_workflow
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
@click.option('--output', '-o', help='Output directory for generated specs')
@click.option('--test-only', is_flag=True, help='Run in test mode without generating files')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--mock-server', '-m', is_flag=True, help='Enable mock server for API interactions (for testing)')
def techspec(connector, folder, output, test_only, verbose, mock_server):
    # we will use the other flags in future for more customization don't remove them
    """ -m flag to mock server and use --help for more details
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

            # Use config for output directory if not specified
            config_instance = get_config()
            output_dir = output or config_instance.getTechSpecConfig().output_dir
            # Execute the techspec workflow
            result = await run_techspec_workflow(
                connector_name=connector,
                folder=folder,
                output_dir=output_dir,
                test_only=test_only,
                verbose=verbose,
                mock_server=mock_server,

            )

            if result["success"]:
                click.echo("Techspec generation completed successfully!")

                if verbose:
                    click.echo(f"Validation status: {result.get('validation_status', 'unknown')}")
                    click.echo(f"Files generated: {result.get('files_generated', 0)}")
                    click.echo()

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
                click.echo(f"Techspec generation failed: {result['error']}", err=True)
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




def main():
    """Main entry point for Grace CLI."""
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
