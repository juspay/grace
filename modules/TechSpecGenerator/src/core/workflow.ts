/**
 * Main Workflow class - TypeScript implementation of APIDocumentationWorkflow
 */

import * as path from 'path';
import * as fs from 'fs-extra';
import { StateGraph, CompiledGraph, END, createStateGraph } from './state-graph';
import { WorkflowState, Config, WorkflowMetadata } from '../types/workflow-state';
import { console } from '../utils/console';
import {
  urlCollectionNode,
  crawlingNode,
  llmProcessingNode,
  mockServerNode,
  outputNode
} from '../nodes';

export type ContinueDecision = 'crawling' | 'llm_processing' | 'mock_server' | 'output' | 'end';

export function shouldContinueAfterUrlCollection(state: WorkflowState): string {
  if (!state.urls || state.urls.length === 0) {
    console.print('[yellow]No URLs collected. Ending workflow.[/yellow]');
    return 'end';
  }
  return 'crawling';
}

export function shouldContinueAfterCrawling(state: WorkflowState): string {
  if (!state.markdown_files || state.markdown_files.length === 0) {
    console.print('[red]No files successfully crawled. Ending workflow.[/red]');
    return 'end';
  }
  return 'llm_processing';
}

export function shouldContinueAfterLlm(state: WorkflowState): string {
  // Check if mock server generation is enabled and we have a spec
  if (
    state.tech_spec &&
    state.config.workflow?.mock_server_generation?.enabled
  ) {
    return 'mock_server';
  }
  return 'output';
}

export function shouldContinueAfterMockServer(state: WorkflowState): string {
  // Always continue to output to show results
  return 'output';
}

export class APIDocumentationWorkflow {
  private config: Config;
  private outputDir: string;
  private graph: CompiledGraph;

  constructor(config: Config, outputDir: string) {
    this.config = config;
    this.outputDir = outputDir;
    this.graph = this.buildGraph();
  }

  private buildGraph(): CompiledGraph {
    // Create the LangGraph state graph
    const workflow = createStateGraph();

    // Add nodes
    workflow.addNode('url_collection', urlCollectionNode);
    workflow.addNode('crawling', crawlingNode);
    workflow.addNode('llm_processing', llmProcessingNode);
    workflow.addNode('mock_server', mockServerNode);
    workflow.addNode('output', outputNode);

    // Set entry point
    workflow.setEntryPoint('url_collection');

    // Add conditional edges
    workflow.addConditionalEdges(
      'url_collection',
      shouldContinueAfterUrlCollection,
      {
        'crawling': 'crawling',
        'end': END
      }
    );

    workflow.addConditionalEdges(
      'crawling',
      shouldContinueAfterCrawling,
      {
        'llm_processing': 'llm_processing',
        'end': END
      }
    );

    workflow.addConditionalEdges(
      'llm_processing',
      shouldContinueAfterLlm,
      {
        'mock_server': 'mock_server',
        'output': 'output',
        'end': END
      }
    );

    workflow.addConditionalEdges(
      'mock_server',
      shouldContinueAfterMockServer,
      {
        'output': 'output',
        'end': END
      }
    );

    // Final edge to end
    workflow.addEdge('output', END);

    return workflow.compile();
  }

  createInitialState(): WorkflowState {
    const startTime = Date.now();

    // Create output directories
    fs.ensureDirSync(this.outputDir);
    fs.ensureDirSync(path.join(this.outputDir, 'markdown'));
    fs.ensureDirSync(path.join(this.outputDir, 'specs'));

    const metadata: WorkflowMetadata = {
      start_time: startTime,
      total_urls: 0,
      successful_crawls: 0,
      failed_crawls: 0,
      spec_generated: false,
      mock_server_generated: false
    };

    return {
      config: this.config,
      output_dir: this.outputDir,
      urls: [],
      crawl_results: {},
      markdown_files: [],
      errors: [],
      warnings: [],
      metadata
    };
  }

  async run(): Promise<WorkflowState> {
    console.print(`[bold]Output directory:[/bold] ${this.outputDir}`);

    // Create initial state
    const initialState = this.createInitialState();

    try {
      // Execute the workflow using LangGraph
      const result = await this.graph.invoke(initialState);
      
      // LangGraph returns the full state, extract our WorkflowState
      const finalState = result as WorkflowState;

      // Calculate duration
      if (finalState.metadata.start_time) {
        const endTime = Date.now();
        const duration = endTime - finalState.metadata.start_time;
        finalState.metadata.end_time = endTime;
        finalState.metadata.duration = duration;
      }

      return finalState;

    } catch (error: any) {
      const errorMsg = `Workflow execution failed: ${error.message}`;
      console.error(errorMsg);
      initialState.errors.push(errorMsg);
      return initialState;
    }
  }

  async runNode(nodeName: string, state: WorkflowState): Promise<WorkflowState> {
    const nodeFunctions: Record<string, (state: WorkflowState) => Promise<WorkflowState>> = {
      'url_collection': urlCollectionNode,
      'crawling': crawlingNode,
      'llm_processing': llmProcessingNode,
      'mock_server': mockServerNode,
      'output': outputNode
    };

    const nodeFunction = nodeFunctions[nodeName];
    if (!nodeFunction) {
      throw new Error(`Unknown node: ${nodeName}`);
    }

    return nodeFunction(state);
  }
}

export function createWorkflow(config: Config, outputDir: string): APIDocumentationWorkflow {
  return new APIDocumentationWorkflow(config, outputDir);
}