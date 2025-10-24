"""LLM processing node for the workflow."""
from typing import List
import click

from ..states.techspec_state import TechspecWorkflowState
from src.ai.ai_service import AIService
from src.utils.ai_utils import estimate_token_usage
from src.config import get_config

def llm_analysis(state: TechspecWorkflowState) -> TechspecWorkflowState:
    if not state.get("markdown_files"):
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("No markdown files to process")
        click.echo("Error: No markdown files to process")
        return state

    click.echo(f"\nStep 2: Generating technical specification...")

    # Initialize LLM client
    try:
        ai_config = get_config().getAiConfig()
        llm_client = AIService(ai_config)
    except Exception as e:
        error_msg = f"Failed to initialize LLM client: {str(e)}"
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(error_msg)
        click.echo(f"Error: {error_msg}")
        return state

    # Show token estimation
    try:
        token_estimate = estimate_token_usage(state["markdown_files"], ai_config)
        if "error" not in token_estimate:
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["estimated_tokens"] = token_estimate
            click.echo(f"Estimated tokens: ~{token_estimate['estimated_input_tokens']} input + {token_estimate['max_output_tokens']} output")
    except Exception as e:
        if "warnings" not in state:
            state["warnings"] = []
        state["warnings"].append(f"Token estimation failed: {str(e)}")

    # Generate tech spec
    try:
        spec_success, tech_spec, spec_error = llm_client.generate_tech_spec(
            state["markdown_files"], prompt=""
        )

        if spec_success and tech_spec:
            # Save the tech spec
            from pathlib import Path
            from src.tools.filemanager.filemanager import FileManager
            output_dir = state.get("output_dir")
            if not output_dir:
                raise ValueError("Output directory not configured")
            filemanager = FileManager(
                base_path=str(output_dir)
            )
            spec_filepath = filemanager.save_tech_spec(tech_spec, llm_client.get_file_name(state.get("urls"),))

            # Update state
            state["tech_spec"] = tech_spec
            state["spec_filepath"] = spec_filepath
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["spec_generated"] = True
            click.echo(f"\nTechnical specification generated!")
            click.echo(f"Saved to: {spec_filepath}")
        else:
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Tech spec generation failed: {spec_error}")
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["spec_generated"] = False
            click.echo(f"\nError generating tech spec: {spec_error}")

    except Exception as e:
        error_msg = f"Error during tech spec generation: {str(e)}"
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(error_msg)
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["spec_generated"] = False
        click.echo(f"\nError: {error_msg}")

    return state