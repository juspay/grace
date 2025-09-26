/**
 * TypeScript equivalent of Python workflow state management
 */

export interface CrawlResult {
  success: boolean;
  filepath?: string;
  content_length: number;
  error?: string;
  url: string;
}

export interface WorkflowMetadata {
  start_time?: number;
  end_time?: number;
  duration?: number;
  total_urls?: number;
  successful_crawls?: number;
  failed_crawls?: number;
  spec_generated?: boolean;
  estimated_tokens?: Record<string, number>;
  mock_server_generated?: boolean;
}

export interface NodeConfig {
  enabled: boolean;
  retry_count?: number;
  timeout?: number;
  parallel?: boolean;
  custom_params?: Record<string, any>;
}

export interface WorkflowConfig {
  url_collection?: NodeConfig;
  crawling?: NodeConfig;
  llm_processing?: NodeConfig;
  mock_server_generation?: NodeConfig;
  output_management?: NodeConfig;
}

export interface Config {
  firecrawl: {
    api_key: string;
  };
  litellm: {
    model: string;
    api_key: string;
    max_tokens: number;
    base_url?: string;
    custom_headers?: Record<string, string>;
  };
  workflow: WorkflowConfig;
}

export interface MockServerData {
  server_js: string;
  package_json: string;
  info: string;
}

export interface WorkflowState {
  // Configuration
  config: Config;
  output_dir: string;
  
  // Input data
  urls: string[];
  
  // Processing results
  crawl_results: Record<string, CrawlResult>;
  markdown_files: string[];
  tech_spec?: string;
  spec_filepath?: string;
  
  // Mock server results
  mock_server_dir?: string;
  mock_server_process?: any;
  mock_server_data?: MockServerData;
  
  // Error tracking
  errors: string[];
  warnings: string[];
  
  // Workflow metadata
  metadata: WorkflowMetadata;
  
  // Node control flags
  node_config?: Record<string, Record<string, any>>;
}

export type NodeFunction = (state: WorkflowState) => Promise<WorkflowState>;
export type ConditionalFunction = (state: WorkflowState) => string;