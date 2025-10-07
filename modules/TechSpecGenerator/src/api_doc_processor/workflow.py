"""LangGraph workflow for API Documentation Processor."""

import asyncio
import time
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END
from rich.console import Console

from .workflow_state import WorkflowState, WorkflowMetadata
from .config import Config
from .nodes import (
    url_collection_node,
    crawling_node,
    llm_processing_node,
    mock_server_node,
    output_node
)

console = Console()


def should_continue_after_url_collection(state: WorkflowState) -> Literal["crawling", "end"]:
    """Decide whether to continue after URL collection."""
    if not state["urls"]:
        console.print("[yellow]No URLs collected. Ending workflow.[/yellow]")
        return "end"
    return "crawling"


def should_continue_after_crawling(state: WorkflowState) -> Literal["llm_processing", "end"]:
    """Decide whether to continue after crawling."""
    if not state["markdown_files"]:
        console.print("[red]No files successfully crawled. Ending workflow.[/red]")
        return "end"
    return "llm_processing"


def should_continue_after_llm(state: WorkflowState) -> Literal["mock_server", "output", "end"]:
    """Decide whether to continue after LLM processing."""
    # Check if mock server generation is enabled and we have a spec
    if ("tech_spec" in state and state["tech_spec"] and 
        hasattr(state["config"], "workflow") and 
        hasattr(state["config"].workflow, "mock_server_generation") and
        state["config"].workflow.mock_server_generation.enabled):
        return "mock_server"
    return "output"


def should_continue_after_mock_server(state: WorkflowState) -> Literal["output", "end"]:
    """Decide whether to continue after mock server generation."""
    # Always continue to output to show results
    return "output"


class APIDocumentationWorkflow:
    """LangGraph-based workflow for API documentation processing."""
    
    def __init__(self, config: Config, output_dir: Path):
        """Initialize the workflow."""
        self.config = config
        self.output_dir = output_dir
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("url_collection", url_collection_node)
        workflow.add_node("crawling", crawling_node)
        workflow.add_node("llm_processing", llm_processing_node)
        workflow.add_node("mock_server", lambda state: asyncio.run(mock_server_node(state)))
        workflow.add_node("output", output_node)
        workflow.add_node("end", lambda state: state)  # Terminal node
        
        # Set entry point
        workflow.set_entry_point("url_collection")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "url_collection",
            should_continue_after_url_collection,
            {
                "crawling": "crawling",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "crawling", 
            should_continue_after_crawling,
            {
                "llm_processing": "llm_processing",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "llm_processing",
            should_continue_after_llm,
            {
                "mock_server": "mock_server",
                "output": "output",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "mock_server",
            should_continue_after_mock_server,
            {
                "output": "output",
                "end": "end"
            }
        )
        
        # Final edge to end
        workflow.add_edge("output", "end")
        workflow.add_edge("end", END)
        
        return workflow.compile()
    
    def create_initial_state(self) -> WorkflowState:
        """Create the initial workflow state."""
        start_time = time.time()
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "specs").mkdir(exist_ok=True)
        
        return WorkflowState(
            config=self.config,
            output_dir=self.output_dir,
            urls=[],
            crawl_results={},
            markdown_files=[],
            errors=[],
            warnings=[],
            metadata=WorkflowMetadata(
                start_time=start_time,
                total_urls=0,
                successful_crawls=0,
                failed_crawls=0,
                spec_generated=False,
                mock_server_generated=False
            )
        )
    
    def run(self) -> WorkflowState:
        """Execute the complete workflow."""
        console.print(f"[bold]Output directory:[/bold] {self.output_dir}")
        
        # Create initial state
        initial_state = self.create_initial_state()
        
        try:
            # Execute the workflow
            final_state = self.graph.invoke(initial_state)
            
            # Calculate duration
            if "start_time" in final_state["metadata"]:
                end_time = time.time()
                duration = end_time - final_state["metadata"]["start_time"]
                final_state["metadata"]["end_time"] = end_time
                final_state["metadata"]["duration"] = duration
            
            return final_state
            
        except Exception as e:
            console.print(f"[red]Workflow execution failed:[/red] {str(e)}")
            initial_state["errors"].append(f"Workflow execution failed: {str(e)}")
            return initial_state
    
    def run_node(self, node_name: str, state: WorkflowState) -> WorkflowState:
        """Run a single node for testing purposes."""
        node_functions = {
            "url_collection": url_collection_node,
            "crawling": crawling_node,
            "llm_processing": llm_processing_node,
            "mock_server": lambda state: asyncio.run(mock_server_node(state)),
            "output": output_node
        }
        
        if node_name not in node_functions:
            raise ValueError(f"Unknown node: {node_name}")
        
        return node_functions[node_name](state)


def create_workflow(config: Config, output_dir: Path) -> APIDocumentationWorkflow:
    """Factory function to create a workflow instance."""
    return APIDocumentationWorkflow(config, output_dir)