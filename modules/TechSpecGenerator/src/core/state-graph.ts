/**
 * Real LangGraph integration - TypeScript (flexible approach)
 */

import { StateGraph, END, Annotation } from '@langchain/langgraph';
import { WorkflowState, NodeFunction, ConditionalFunction } from '../types/workflow-state';

// Re-export LangGraph's StateGraph and END for use in workflow
export { StateGraph, END };

// Type for the compiled graph from LangGraph
export type CompiledGraph = any;

/**
 * Create a LangGraph StateGraph for our workflow
 * Using a more flexible approach that works with the current LangGraph API
 */
export function createStateGraph(): any {
  // Simple state schema that LangGraph can understand
  const graphState = Annotation.Root({
    config: Annotation<any>(),
    output_dir: Annotation<string>(),
    urls: Annotation<string[]>(),
    crawl_results: Annotation<Record<string, any>>(),
    markdown_files: Annotation<string[]>(),
    tech_spec: Annotation<string>(),
    spec_filepath: Annotation<string>(),
    mock_server_dir: Annotation<string>(),
    mock_server_process: Annotation<any>(),
    mock_server_data: Annotation<any>(),
    errors: Annotation<string[]>(),
    warnings: Annotation<string[]>(),
    metadata: Annotation<any>(),
    node_config: Annotation<Record<string, any>>()
  });

  return new StateGraph(graphState);
}