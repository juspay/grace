import { GraceResearcher } from './GraceResearcher';
import { GraceConfig } from './GraceConfig';
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

/**
 * Create a default configuration for Grace researcher
 */
export function createDefaultConfig(): GraceConfig {
  return {
    ai: {
      provider: 'litellm',
      modelId: 'gpt-4',
      baseUrl: 'http://localhost:4000/v1'
    },
    research: {
      maxDepth: 5,
      maxPagesPerDepth: 10,
      maxTotalPages: 50,
      maxConcurrentPages: 3,
      linkRelevanceThreshold: 0.6,
      timeoutPerPage: 30000,
      respectRobotsTxt: true,
      dataDirectory: './research_data',
      historyFile: './research_history.json'
    }
  };
}

/**
 * Create a GraceResearcher instance with smart configuration detection
 *
 * This function will:
 * 1. Load configuration from environment variables if available
 * 2. Merge with provided configuration
 * 3. Apply intelligent defaults
 */
export function createGraceResearcher(config: Partial<GraceConfig> = {}): GraceResearcher {
  const defaultConfig = createDefaultConfig();
  const envConfig = loadConfigFromEnvironment();

  // Merge configurations: defaults <- env <- provided
  const finalConfig: GraceConfig = {
    ai: { ...defaultConfig.ai, ...envConfig.ai, ...config.ai },
    research: { ...defaultConfig.research, ...envConfig.research, ...config.research }
  };

  return new GraceResearcher(finalConfig);
}

/**
 * Create a GraceResearcher from environment variables and .env file
 */
export function createGraceResearcherFromEnv(envPath?: string): GraceResearcher {
  const envConfig = loadConfigFromEnvironment(envPath);
  const defaultConfig = createDefaultConfig();

  const finalConfig: GraceConfig = {
    ai: { ...defaultConfig.ai, ...envConfig.ai },
    research: { ...defaultConfig.research, ...envConfig.research }
  };

  return new GraceResearcher(finalConfig);
}

/**
 * Load configuration from environment variables and .env file
 */
function loadConfigFromEnvironment(envPath?: string): GraceConfig {
  // Load .env file if it exists
  if (envPath || existsSync('.env')) {
    try {
      const { config } = require('dotenv');
      config({ path: envPath || '.env' });
    } catch (error) {
      // .env loading is optional, continue silently
    }
  }

  // Load custom instructions if specified
  let customInstructions: string | undefined;
  if (process.env.CUSTOM_INSTRUCTIONS_FILE) {
    try {
      const filePath = resolve(process.env.CUSTOM_INSTRUCTIONS_FILE);
      if (existsSync(filePath)) {
        customInstructions = readFileSync(filePath, 'utf-8').trim();
      }
    } catch (error) {
      // Custom instructions loading is optional
    }
  }

  return {
    ai: {
      provider: (process.env.AI_PROVIDER as 'litellm' | 'vertex') || 'litellm',
      apiKey: process.env.LITELLM_API_KEY,
      baseUrl: process.env.LITELLM_BASE_URL,
      modelId: process.env.LITELLM_MODEL_ID,
      projectId: process.env.VERTEX_AI_PROJECT_ID,
      location: process.env.VERTEX_AI_LOCATION,
      customInstructions
    },
    research: {
      maxDepth: process.env.MAX_DEPTH ? parseInt(process.env.MAX_DEPTH) : undefined,
      maxPagesPerDepth: process.env.MAX_PAGES_PER_DEPTH ? parseInt(process.env.MAX_PAGES_PER_DEPTH) : undefined,
      maxTotalPages: process.env.MAX_TOTAL_PAGES ? parseInt(process.env.MAX_TOTAL_PAGES) : undefined,
      maxConcurrentPages: process.env.CONCURRENT_PAGES ? parseInt(process.env.CONCURRENT_PAGES) : undefined,
      linkRelevanceThreshold: process.env.LINK_RELEVANCE_THRESHOLD ? parseFloat(process.env.LINK_RELEVANCE_THRESHOLD) : undefined,
      timeoutPerPage: process.env.TIMEOUT_PER_PAGE_MS ? parseInt(process.env.TIMEOUT_PER_PAGE_MS) : undefined,
      respectRobotsTxt: process.env.RESPECT_ROBOTS_TXT !== 'false',
      dataDirectory: process.env.RESEARCH_DATA_DIR,
      historyFile: process.env.HISTORY_FILE
    }
  };
}

/**
 * Validate a configuration object
 */
export function validateConfig(config: GraceConfig): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Validate AI configuration
  if (config.ai) {
    if (config.ai.provider === 'litellm' && !config.ai.apiKey) {
      errors.push('AI API key is required for litellm provider');
    }
    if (config.ai.provider === 'vertex' && !config.ai.projectId) {
      errors.push('Project ID is required for vertex provider');
    }
  }

  // Validate research configuration
  if (config.research) {
    if (config.research.maxDepth && (config.research.maxDepth < 1 || config.research.maxDepth > 10)) {
      errors.push('Max depth must be between 1 and 10');
    }
    if (config.research.maxConcurrentPages && (config.research.maxConcurrentPages < 1 || config.research.maxConcurrentPages > 10)) {
      errors.push('Max concurrent pages must be between 1 and 10');
    }
    if (config.research.linkRelevanceThreshold && (config.research.linkRelevanceThreshold < 0 || config.research.linkRelevanceThreshold > 1)) {
      errors.push('Link relevance threshold must be between 0 and 1');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}