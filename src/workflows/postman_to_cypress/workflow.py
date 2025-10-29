"""
PostmanToCypress Workflow
Main LangGraph workflow for converting Postman collections to test structures
"""

import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from .states.postman_state import PostmanWorkflowState
from .nodes import (
    parse_collection,
    categorize_apis,
    generate_tests,
    collect_credentials, 
    execute_tests
)
from src.config import get_config
from src.utils.progress import create_workflow_progress


class PostmanToCypressWorkflow:
    """LangGraph workflow for Postman to Cypress conversion"""
    
    def __init__(self):
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self):
        """Build the workflow graph with nodes and edges"""
        workflow = StateGraph(PostmanWorkflowState)
        
        # Add nodes
        workflow.add_node("parse_collection", parse_collection)
        workflow.add_node("categorize_apis", categorize_apis)
        workflow.add_node("generate_tests", generate_tests)
        workflow.add_node("collect_credentials", collect_credentials)
        workflow.add_node("execute_tests", execute_tests)
        workflow.add_node("end", lambda state: state)
        
        # Define workflow edges
        workflow.add_edge(START, "parse_collection")
        
        workflow.add_conditional_edges(
            "parse_collection",
            self._should_continue_after_parsing,
            {
                "categorize": "categorize_apis",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "categorize_apis", 
            self._should_continue_after_categorization,
            {
                "generate": "generate_tests",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_tests",
            self._should_continue_after_generation,
            {
                "collect_creds": "collect_credentials",
                "end": "end"
            }
        )
        
        workflow.add_conditional_edges(
            "collect_credentials",
            self._should_continue_after_credentials,
            {
                "execute": "execute_tests",
                "end": "end"
            }
        )
        
        workflow.add_edge("execute_tests", "end")
        
        return workflow.compile()
    
    def _should_continue_after_parsing(self, state: PostmanWorkflowState) -> str:
        """Decide whether to continue after parsing collection"""
        if state.get("error"):
            return "end"
        
        api_endpoints = state.get("api_endpoints", [])
        if not api_endpoints:
            return "end"
        
        return "categorize"
    
    def _should_continue_after_categorization(self, state: PostmanWorkflowState) -> str:
        """Decide whether to continue after API categorization"""
        if state.get("error"):
            return "end"
        
        execution_sequence = state.get("execution_sequence", [])
        if not execution_sequence:
            return "end"
        
        return "generate"
    
    def _should_continue_after_generation(self, state: PostmanWorkflowState) -> str:
        """Decide whether to continue after test generation"""
        if state.get("error"):
            return "end"
        
        test_structures = state.get("test_structures", [])
        if not test_structures:
            return "end"
        
        return "collect_creds"
    
    def _should_continue_after_credentials(self, state: PostmanWorkflowState) -> str:
        """Decide whether to continue after credential collection"""
        if state.get("error"):
            return "end"
        
        # Check if user wants to execute tests
        # If in headless mode, always execute
        if state.get("headless", False):
            return "execute"
        
        # In interactive mode, ask user
        execute = input("\\nDo you want to execute the generated tests? (y/n): ").strip().lower()
        if execute in ['y', 'yes']:
            return "execute"
        else:
            if state.get("verbose", False):
                print("⏭️  Test execution skipped by user choice")
            return "end"
    
    async def run(self, initial_state: PostmanWorkflowState) -> PostmanWorkflowState:
        """Run the workflow asynchronously"""
        try:
            # Initialize workflow progress tracker
            progress = create_workflow_progress(
                total_steps=5,  # parse, categorize, generate, collect_creds, execute
                verbose=initial_state.get("verbose", False)
            )
            
            if initial_state.get("verbose", False):
                print(f"\n🚀 Starting PostmanToCypress Workflow")
                print(f"📄 Collection: {initial_state.get('collection_file', Path('unknown')).name}")
                print(f"🎯 Mode: {'Headless' if initial_state.get('headless') else 'Interactive'}")
                print(f"💡 Tip: Press Ctrl+C to toggle detailed progress view")
            
            # Add workflow metadata
            initial_state["metadata"] = {
                "start_time": time.time(),
                "workflow_started": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Store progress tracker in state for nodes to use
            initial_state["_progress_tracker"] = progress
            
            # Execute the workflow
            result = await self.graph.ainvoke(initial_state)
            
            # Update final metadata
            end_time = time.time()
            result["metadata"]["end_time"] = end_time
            result["metadata"]["duration"] = end_time - result["metadata"]["start_time"]
            
            # Show final summary
            if result.get("verbose", False):
                progress.show_summary()
            
            return result
            
        except Exception as e:
            # Handle workflow-level errors
            error_msg = f"Workflow execution failed: {str(e)}"
            initial_state["errors"] = initial_state.get("errors", []) + [error_msg]
            initial_state["error"] = error_msg
            initial_state["success"] = False
            
            if initial_state.get("verbose", False):
                print(f"❌ {error_msg}")
            
            return initial_state


def create_postman_to_cypress_workflow() -> PostmanToCypressWorkflow:
    """Create a new PostmanToCypress workflow instance"""
    return PostmanToCypressWorkflow()


async def run_postman_to_cypress_workflow(
    collection_file: str,
    output_dir: Optional[str] = None,
    headless: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run the complete Postman to Cypress workflow.
    
    Args:
        collection_file: Path to Postman collection JSON file
        output_dir: Output directory for generated tests
        headless: Run in headless mode (no user interaction)
        verbose: Enable verbose output
        
    Returns:
        Workflow execution results
    """
    try:
        # Validate inputs
        collection_path = Path(collection_file)
        if not collection_path.exists():
            return {
                "success": False,
                "error": f"Collection file not found: {collection_file}",
                "output": None
            }
        
        if not collection_path.suffix.lower() == '.json':
            return {
                "success": False,
                "error": f"Collection file must be a JSON file: {collection_file}",
                "output": None
            }
        
        # Setup output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            config = get_config()
            output_path = Path(config.getTechSpecConfig().output_dir) / "postman_tests"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Extract connector name from collection file
        connector_name = collection_path.stem
        
        # Initialize workflow state
        initial_state: PostmanWorkflowState = {
            "config": get_config().getTechSpecConfig(),
            "output_dir": output_path,
            "collection_file": collection_path,
            "connector_name": connector_name,
            "headless": headless,
            "verbose": verbose,
            "errors": [],
            "warnings": [],
            "node_config": {}
        }
        
        if verbose:
            print("🚀 Starting Postman to Cypress workflow...")
            print(f"📄 Collection: {collection_path.name}")
            print(f"📁 Output: {output_path}")
            print(f"🤖 Mode: {'Headless' if headless else 'Interactive'}")
            print()
        
        # Create and run workflow
        workflow = create_postman_to_cypress_workflow()
        result = await workflow.run(initial_state)
        
        # Prepare return value
        success = result.get("success", True) and not result.get("error")
        
        output = {
            "collection_name": result.get("collection_info", {}).get("name", connector_name),
            "total_endpoints": len(result.get("api_endpoints", [])),
            "categorized_endpoints": len(result.get("execution_sequence", [])),
            "generated_tests": len(result.get("test_structures", [])),
            "output_directory": str(output_path),
            "execution_results": result.get("final_output"),
            "metadata": result.get("metadata", {})
        }
        
        if verbose:
            print()
            print("=" * 60)
            print("📊 Workflow Summary")
            print("=" * 60)
            print(f"Collection: {output['collection_name']}")
            print(f"Endpoints Parsed: {output['total_endpoints']}")
            print(f"Tests Generated: {output['generated_tests']}")
            print(f"Output Directory: {output['output_directory']}")
            
            if success:
                print("✅ Workflow completed successfully!")
            else:
                print("❌ Workflow completed with errors")
                if result.get("errors"):
                    print("Errors:")
                    for error in result["errors"]:
                        print(f"  - {error}")
            print()
        
        return {
            "success": success,
            "error": result.get("error"),
            "output": output,
            "metadata": result.get("metadata", {}),
            "validation_status": "completed" if success else "failed",
            "files_generated": len(result.get("test_files", {}))
        }
        
    except Exception as e:
        error_msg = f"Workflow setup failed: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "output": None,
            "metadata": {"error": True}
        }