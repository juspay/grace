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
from .workflows.techspec.workflow import run_techspec_workflow
from .config import get_config


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Grace CLI - Intelligent research and technical specification generator."""
    pass


# @cli.command()
# @click.argument('query', required=False)
# @click.option('--output', '-o', help='Output file path')
# @click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']),
#                help='Output format')
# @click.option('--depth', '-d', type=int,
#                help='Research depth (1-10)')
# @click.option('--sources', '-s', type=int,
#              help='Number of sources to analyze')
# @click.option('--verbose', '-v', is_flag=True,
#               help='Enable verbose output')
# def research(query, output, format, depth, sources, verbose):
#     """Perform deep research on a given topic using LangGraph workflow."""
#     # config = get_config()
#     # if not query:
#     #     query = input("Enter your research query: ").strip()
#     #     if not query:
#     #         click.echo("Error: Research query is required", err=True)
#     #         sys.exit(1)


@cli.command()
@click.argument('connector', required=False)
@click.option('--api-doc', '-a', help='Path to API documentation')
@click.option('--output', '-o', help='Output directory for generated specs')
@click.option('--template', '-t', help='Template to use for spec generation')
@click.option('--create-config', is_flag=True, help='Create a sample configuration file')
@click.option('--test-only', is_flag=True, help='Run in test mode without generating files')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--mock-server', '-m', is_flag=True, help='Enable mock server for API interactions (for testing)')
def techspec(connector, api_doc, output, template, create_config, test_only, verbose, mock_server):
    """Generate technical specifications for a connector using LangGraph workflow."""
    # we will use the other flags in future for more customization don't remove them
    if create_config:
        env_content = """# Grace CLI Configuration
# Copy this to .env and update values as needed

# AI Configuration
AI_PROVIDER=litellm
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://grid.juspay.net
AI_MODEL_ID=qwen3-coder-480b
AI_PROJECT_ID=your_project_id
AI_LOCATION=us-east5

# TechSpec Configuration
TECHSPEC_OUTPUT_DIR=./output
TECHSPEC_TEMPLATE_DIR=./templates
TECHSPEC_TEMPERATURE=0.7
TECHSPEC_MAX_TOKENS=50000
FIRECRACKER_API_KEY=your_firecracker_key
USE_PLAYWRIGHT=false

# Research Configuration
SEARCH_TOOL=searxng
SEARCH_BASE_URL=https://localhost:32678
SEARCH_FORMAT_TYPE=markdown
SEARCH_DEPTH=5

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=grace.log
DEBUG=false
"""
        config_path = ".env"
        with open(config_path, 'w') as f:
            f.write(env_content)
        click.echo(f"Configuration template created: {config_path}")
        click.echo("Edit .env file to customize your settings")
        return

    async def run_techspec():
        """Async wrapper for techspec workflow."""
        try:
            if verbose:
                click.echo(f"Starting techspec workflow...")
                click.echo(f"Connector: {connector}")
                if api_doc:
                    click.echo(f"API doc: {api_doc}")
                if output:
                    click.echo(f"Output dir: {output}")
                if template:
                    click.echo(f"Template: {template}")
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
                output_dir=output_dir,
                test_only=test_only,
                verbose=verbose,
                mock_server=mock_server
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
