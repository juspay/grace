"""Techspec workflow using LangGraph for technical specification generation."""

import asyncio
import click
from typing import Dict, Any, List, Literal, Optional
from pathlib import Path
from src.config import Config, TechSpecConfig, get_config
from langgraph.graph import StateGraph, START, END
from .states.techspec_state import TechspecWorkflowState
from datetime import datetime
from .nodes import collect_urls, scrap_urls, llm_analysis, output_node
class TechspecWorkflow:
    """LangGraph-based techspec workflow orchestrator."""

    def __init__(self):
        """Initialize the techspec workflow."""
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self):
        """Build the LangGraph workflow graph."""

        # Create state graph
        workflow = StateGraph(TechspecWorkflowState)

        # Add nodes for each step
        workflow.add_node("collect_urls", collect_urls)
        workflow.add_node("crawling", scrap_urls)
        workflow.add_node("llm_analysis", llm_analysis)
        # workflow.add_node("mock_server", lambda state: asyncio.run(mock_server_node(state)))
        workflow.add_node("output", output_node)
        workflow.add_node("end", lambda state: state)  # Terminal node

        # Add edges to define workflow flow



        workflow.add_edge(START, "collect_urls")

        workflow.add_conditional_edges(
            "collect_urls",
            self._should_continue_after_url_collection,
            {
                "crawling": "crawling",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "crawling", 
            self._should_continue_after_crawling,
            {
                "llm_analysis": "llm_analysis",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "llm_analysis",
            self._should_continue_after_llm,
            {
                # "mock_server": "mock_server",
                "output": "output",
                "end": "end"
            }
        )
                
        # workflow.add_conditional_edges(
        #     "mock_server",
        #     self._should_continue_after_mock_server,
        #     {
        #         "output": "output",
        #         "end": "end"
        #     }
        # )
        
        workflow.add_edge("output", "end")
        workflow.add_edge("end", END)

        # Compile the graph
        return workflow.compile()
    
    def _should_continue_after_url_collection(self, state: TechspecWorkflowState) -> Literal["crawling", "end"]:
        if not state["urls"]:
            click.echo("No URLs collected. Ending workflow.")
            return "end"
        return "crawling"

    def _should_continue_after_crawling(self, state: TechspecWorkflowState) -> Literal["llm_analysis", "end"]:
        if not state["markdown_files"]:
            click.echo("No files successfully crawled. Ending workflow.")
            return "end"
        return "llm_analysis"

    def _should_continue_after_llm(self, state: TechspecWorkflowState) -> Literal["mock_server", "output", "end"]:
        # Check if mock server generation is enabled and we have a spec
        if (state.get("mock_server") and state.get("tech_spec")):
            return "mock_server"
        return "output"


    def _should_continue_after_mock_server(self, state: TechspecWorkflowState) -> str:
        if state.get("errors"):
            return "end"
        return "output"
    

     
    async def execute(self,
                     connector_name: str,
                     output_dir: Optional[str] = None,
                     mock_server: bool = False,
                     test_only: bool = False,
                     verbose: bool = False) -> Dict[str, Any]:
        """Execute the techspec workflow."""
        config = get_config().getTechSpecConfig()

        # Convert output_dir to Path object
        output_path = Path(output_dir) if output_dir else Path(config.output_dir)

        # Initialize state
        initial_state: TechspecWorkflowState = {
            "connector_name": connector_name,
            "urls": [],
            "visited_urls": [],
            "output_dir": output_path,
            "mock_server" : mock_server,
            "config": config,
            "test_only": test_only,
            "verbose": verbose,
            "final_output": {},
            "error": None,
            "metadata": {"workflow_started": True, "timestamp": datetime.now().isoformat()},
        }

        try:
            # Execute the workflow graph
            result = await self.graph.ainvoke(initial_state)

            return {
                "success": result["error"] is None,
                "connector_name": result["connector_name"],
                "output": result["final_output"],
                "metadata": result["metadata"],
                "error": result["error"],
                "validation_status": result["validation_results"]["overall_status"] if result["validation_results"] else "unknown",
                "files_generated": result["final_output"].get("summary", {}).get("total_files", 0) if result["final_output"] else 0
            }

        except Exception as e:
            return {
                "success": False,
                "connector_name": connector_name,
                "output": {},
                "metadata": {"error": str(e), "workflow_failed": True},
                "error": str(e),
                "validation_status": "failed",
                "files_generated": 0
            }
        



# Factory function for easy workflow creation
def create_techspec_workflow() -> TechspecWorkflow:
    """Create and return a new techspec workflow instance."""
    return TechspecWorkflow()


# CLI integration function
async def run_techspec_workflow(connector_name: str,
                               output_dir: Optional[str] = None,
                               mock_server: bool = False,
                               test_only: bool = False,
                               verbose: bool = False) -> Dict[str, Any]:
    """Run techspec workflow from CLI."""
    workflow = create_techspec_workflow()
    return await workflow.execute(
        connector_name=connector_name,
        output_dir=output_dir,
        mock_server=mock_server,
        test_only=test_only,
        verbose=verbose
    )