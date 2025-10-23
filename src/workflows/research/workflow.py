"""Techspec workflow using LangGraph for technical specification generation."""

import asyncio
import click
from typing import Dict, Any, List, Literal, Optional
from pathlib import Path
from src.config import get_config
from langgraph.graph import StateGraph, START, END
from .states.research_state import WorkflowState
from datetime import datetime
from .nodes import input_node, generate_queries, analyse_pages, scrap_links, search_queries, verify_content, verify_links, mock_server, markdown_generation,techspec_generation
class ResearchWorkflow:

    def __init__(self):
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self):

        # Create state graph
        workflow = StateGraph(WorkflowState)

        # Add nodes for each step
        workflow.add_node("input_node", input_node)
        workflow.add_node("generate_queries", generate_queries)
        workflow.add_node("search_queries", search_queries)
        workflow.add_node("verify_links", verify_links)
        workflow.add_node("scrap_links", scrap_links)
        workflow.add_node("analyse_pages", analyse_pages)
        workflow.add_node("verify_content", verify_content)
        workflow.add_node("markdown_generation", markdown_generation)
        workflow.add_node("techspec_generation", techspec_generation)
        workflow.add_node("mock_server", mock_server)
        workflow.add_node("end", lambda state: state)

        # Define conditions for branching
        workflow.add_conditional_edges(
            START,
            self._should_continue_after_input,
            {
                "input_node": "input_node",
                "generate_queries": "generate_queries"
            }
        )
        workflow.add_edge("generate_queries", "search_queries")
        workflow.add_edge("search_queries", "verify_links")

        workflow.add_conditional_edges(
            "verify_links",
            self._should_continue_after_verify_links,
            {
                "scrap_links": "scrap_links",
                "generate_queries": "generate_queries"
            }
        )
        workflow.add_edge("scrap_links", "analyse_pages")
        workflow.add_conditional_edges(
            "analyse_pages",
            self._should_continue_after_analyse_pages,
            {
                "verify_content": "verify_content",
                "verify_links": "verify_links"
            }
        )
        workflow.add_conditional_edges(
            "verify_content",
            self._should_continue_after_verify_content,
            {
                "markdown_generation": "markdown_generation",
                "generate_queries": "generate_queries",
                "end": "end"
            }
        )
        workflow.add_conditional_edges(
            "markdown_generation",
            self._should_continue_after_markdown_generation,
            {
                "techspec_generation": "techspec_generation",
                "end": "end"
            }
        )
        workflow.add_conditional_edges(
            "techspec_generation",
            self._should_continue_after_techspec_generation,
            {
                "mock_server": "mock_server",
                "end": "end"
            }
        )
        workflow.add_edge("mock_server", "end")
        workflow.add_edge("end", END)

        # Compile the graph
        return workflow.compile()
    def _should_continue_after_input(self, state: WorkflowState) -> Literal["input_node", "generate_queries"]:
        return "input_node"
    
    def _should_continue_after_verify_links(self, state: WorkflowState) -> Literal["scrap_links", "generate_queries"]:
        return "scrap_links"
    def _should_continue_after_analyse_pages(self, state: WorkflowState) -> Literal["verify_content", "verify_links"]:
        return "verify_content"
    def _should_continue_after_verify_content(self, state: WorkflowState) -> Literal["markdown_generation", "generate_queries", "end"]:
        return "markdown_generation"
    def _should_continue_after_markdown_generation(self, state: WorkflowState) -> Literal["techspec_generation", "end"]:
        return "techspec_generation"
    def _should_continue_after_techspec_generation(self, state: WorkflowState) -> Literal["mock_server", "end"]:
        return "mock_server"
    
    def execute(self,
                connector_name: str,
                output_dir: Optional[str] = None,
                mock_server: bool = False,
                test_only: bool = False,
    ):
        return self.graph.ainvoke(
            connector_name,
            output_dir,
            mock_server,
            test_only
        )

     
    async def execute(self,
                     connector_name: str,
                     output_dir: Optional[str] = None,
                     mock_server: bool = False,
                     test_only: bool = False,
                     verbose: bool = False) -> Dict[str, Any]:
        global_config = get_config()
        techspec_config = global_config.getTechSpecConfig()
        ai_config = global_config.getAiConfig()

        # Convert output_dir to Path object
        output_path = Path(output_dir) if output_dir else Path(techspec_config.output_dir)

        # Initialize state
        initial_state: WorkflowState = {
            "connector_name": connector_name,
            "urls": [],
            "visited_urls": [],
            "output_dir": output_path,
            "generate_mockserver" : mock_server,
            "config": ai_config,
            "techSpecConfig": techspec_config,
            "test_only": test_only,
            "verbose": verbose,
            "final_output": {},
            "error": None,
            "errors": [],
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
        
class SearchWorkflow:
    pass



# Factory function for easy workflow creation
def create_research_workflow() -> WorkflowState:
    """Create and return a new research workflow instance."""
    return ResearchWorkflow()


# CLI integration function
async def run_research_workflow(connector_name: str,
                               output_dir: Optional[str] = None,
                               mock_server: bool = False,
                               test_only: bool = False,
                               verbose: bool = False) -> Dict[str, Any]:
    """Run research workflow from CLI."""
    workflow = create_research_workflow()
    return await workflow.execute(
        connector_name=connector_name,
        output_dir=output_dir,
        mock_server=mock_server,
        test_only=test_only,
        verbose=verbose
    )