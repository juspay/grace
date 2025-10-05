import { config } from 'dotenv';
import { resolve } from 'path';
import { existsSync, readFileSync } from 'fs';
import { ResearchConfig, AIConfig } from '../types';

export class ConfigService {
  private static instance: ConfigService;
  private researchConfig: ResearchConfig;
  private aiConfig: AIConfig;
  private debugMode: boolean = false;

  constructor() {
    // Load environment variables
    config({ path: resolve(process.cwd(), '.env') });

    this.researchConfig = {
      maxDepth: parseInt(process.env.MAX_DEPTH || '10'),
      maxPagesPerDepth: parseInt(process.env.MAX_PAGES_PER_DEPTH || '10'),
      maxTotalPages: parseInt(process.env.MAX_TOTAL_PAGES || '100'),
      maxConcurrentPages: parseInt(process.env.CONCURRENT_PAGES || '3'),
      linkRelevanceThreshold: parseFloat(process.env.LINK_RELEVANCE_THRESHOLD || '0.2'),
      timeoutPerPage: parseInt(process.env.TIMEOUT_PER_PAGE_MS || '30000'),
      respectRobotsTxt: process.env.RESPECT_ROBOTS_TXT !== 'false',
      dataDirectory: process.env.RESEARCH_DATA_DIR || './research_data',
      historyFile: process.env.HISTORY_FILE || './research_history.json',
      interactiveMode: process.env.INTERACTIVE_MODE !== 'false',
      enableDeepLinkCrawling: process.env.ENABLE_DEEP_LINK_CRAWLING !== 'false',
      maxLinksPerPage: parseInt(process.env.MAX_LINKS_PER_PAGE || '10'),
      deepCrawlDepth: parseInt(process.env.DEEP_CRAWL_DEPTH || '10'),
      aiDrivenCrawling: process.env.AI_DRIVEN_CRAWLING === 'true',
      aiLinkRanking: process.env.AI_LINK_RANKING === 'true',
      aiCompletenessCheck: process.env.AI_COMPLETENESS_CHECK === 'true',
      searchResultsPerQuery: parseInt(process.env.SEARCH_RESULTS_PER_QUERY || '15')
    };
    const debugEnv = process.env.IS_DEBUG || 'false';
    this.debugMode = debugEnv.toLowerCase() === 'true' || debugEnv === '1';

    // Determine AI provider with intelligent fallback
    const determinedProvider = this.determineAIProvider();

    // Determine model ID based on provider
    let modelId: string;
    if (determinedProvider.provider === 'vertex') {
      modelId = process.env.VERTEX_AI_MODEL || process.env.LITELLM_MODEL_ID || 'claude-3-5-sonnet-v2@20241022';
    } else if (determinedProvider.provider === 'anthropic') {
      modelId = process.env.ANTHROPIC_MODEL_ID || process.env.LITELLM_MODEL_ID || 'claude-3-5-sonnet-20241022';
    } else {
      modelId = process.env.LITELLM_MODEL_ID || 'gpt-4';
    }

    // Determine API key based on provider
    let apiKey: string | undefined;
    if (determinedProvider.provider === 'anthropic') {
      apiKey = process.env.ANTHROPIC_API_KEY;
    } else {
      apiKey = process.env.LITELLM_API_KEY;
    }

    this.aiConfig = {
      provider: determinedProvider.provider,
      apiKey: apiKey,
      baseUrl: process.env.LITELLM_BASE_URL || 'http://localhost:4000/v1',
      modelId: modelId,
      projectId: determinedProvider.projectId || process.env.VERTEX_AI_PROJECT_ID,
      location: determinedProvider.location || process.env.VERTEX_AI_LOCATION || 'us-east5',
      customInstructionsFile: process.env.CUSTOM_INSTRUCTIONS_FILE,
      customInstructions: this.loadCustomInstructions(process.env.CUSTOM_INSTRUCTIONS_FILE)
    };

    // Log provider determination
    if (determinedProvider.message) {
      console.log(determinedProvider.message);
    }
  }

  static getInstance(): ConfigService {
    if (!ConfigService.instance) {
      ConfigService.instance = new ConfigService();
    }
    return ConfigService.instance;
  }

  isDebugMode(): boolean {
    return this.debugMode;
  }

  getResearchConfig(): ResearchConfig {
    return { ...this.researchConfig };
  }

  getAIConfig(): AIConfig {
    return { ...this.aiConfig };
  }

  updateResearchConfig(updates: Partial<ResearchConfig>): void {
    this.researchConfig = { ...this.researchConfig, ...updates };
  }

  updateAIConfig(updates: Partial<AIConfig>): void {
    this.aiConfig = { ...this.aiConfig, ...updates };
  }

  /**
   * Intelligently determine which AI provider to use based on configuration
   */
  private determineAIProvider(): {
    provider: 'litellm' | 'vertex' | 'anthropic';
    projectId?: string;
    location?: string;
    message?: string;
  } {
    // If user explicitly set AI_PROVIDER in .env, respect their choice
    const envProvider = process.env.AI_PROVIDER as 'litellm' | 'vertex' | 'anthropic' | undefined;

    if (envProvider === 'litellm') {
      if (process.env.LITELLM_API_KEY) {
        return { provider: 'litellm' };
      } else {
        // User wants LiteLLM but no API key, try Vertex AI fallback
        const vertexConfig = this.checkVertexAIAvailability();
        if (vertexConfig.available) {
          return {
            provider: 'vertex',
            projectId: vertexConfig.projectId,
            location: vertexConfig.location,
            message: '⚠️  LiteLLM API key not found, falling back to Vertex AI'
          };
        } else {
          // Keep litellm as provider, will error in validation
          return { provider: 'litellm' };
        }
      }
    }

    if (envProvider === 'vertex') {
      const vertexConfig = this.checkVertexAIAvailability();
      return {
        provider: 'vertex',
        projectId: vertexConfig.projectId,
        location: vertexConfig.location,
        message: vertexConfig.available ? undefined : '⚠️  Vertex AI configuration incomplete'
      };
    }

    // No explicit provider set, try intelligent detection
    // Priority: LiteLLM (if has key) -> Vertex AI (if configured) -> Default to LiteLLM
    if (process.env.LITELLM_API_KEY) {
      return { provider: 'litellm' };
    }

    const vertexConfig = this.checkVertexAIAvailability();
    if (vertexConfig.available) {
      return {
        provider: 'vertex',
        projectId: vertexConfig.projectId,
        location: vertexConfig.location,
        message: '🔍 No LiteLLM API key found, using Vertex AI'
      };
    }

    // Default to LiteLLM (will require user to add API key)
    return { provider: 'litellm' };
  }

  /**
   * Check Vertex AI availability with multiple fallback methods
   */
  private checkVertexAIAvailability(): {
    available: boolean;
    projectId?: string;
    location?: string;
  } {
    // Method 1: Check environment variables
    if (process.env.VERTEX_AI_PROJECT_ID) {
      return {
        available: true,
        projectId: process.env.VERTEX_AI_PROJECT_ID,
        location: process.env.VERTEX_AI_LOCATION || 'us-central1'
      };
    }

    // Method 2: Check Google Cloud SDK configuration
    try {
      const { execSync } = require('child_process');
      const projectId = execSync('gcloud config get-value project', {
        encoding: 'utf8',
        stdio: 'pipe'
      }).trim();

      if (projectId && projectId !== '(unset)' && projectId !== '') {
        return {
          available: true,
          projectId: projectId,
          location: 'us-central1'
        };
      }
    } catch (error) {
      // gcloud CLI not available or not configured
    }

    // Method 3: Check Application Default Credentials
    const adcPaths = [
      process.env.GOOGLE_APPLICATION_CREDENTIALS,
      `${process.env.HOME}/.config/gcloud/application_default_credentials.json`,
      `${process.env.USERPROFILE}\\AppData\\Roaming\\gcloud\\application_default_credentials.json`
    ].filter(Boolean);

    for (const path of adcPaths) {
      if (path && existsSync(path)) {
        try {
          const credentials = JSON.parse(readFileSync(path, 'utf8'));
          if (credentials.project_id || credentials.quota_project_id) {
            return {
              available: true,
              projectId: credentials.project_id || credentials.quota_project_id,
              location: 'us-central1'
            };
          }
        } catch (error) {
          // Invalid JSON or permissions issue
        }
      }
    }

    return { available: false };
  }

  private loadCustomInstructions(filePath?: string): string | undefined {
    if (!filePath) {
      return undefined;
    }

    try {
      const resolvedPath = resolve(filePath);
      if (!existsSync(resolvedPath)) {
        console.warn(`Custom instructions file not found: ${resolvedPath}`);
        return undefined;
      }

      const instructions = readFileSync(resolvedPath, 'utf-8').trim();
      if (instructions.length === 0) {
        console.warn(`Custom instructions file is empty: ${resolvedPath}`);
        return undefined;
      }

      console.log(`Loaded custom instructions from: ${resolvedPath} (${instructions.length} characters)`);
      return instructions;
    } catch (error) {
      console.error(`Error loading custom instructions from ${filePath}:`, error);
      return undefined;
    }
  }

  reloadCustomInstructions(): void {
    this.aiConfig.customInstructions = this.loadCustomInstructions(this.aiConfig.customInstructionsFile);
  }

  validate(): string[] {
    const errors: string[] = [];

    // Validate AI provider configuration
    if (this.aiConfig.provider === 'litellm') {
      if (!this.aiConfig.apiKey) {
        errors.push('LITELLM_API_KEY is required when using litellm provider');
        errors.push('To fix: Add LITELLM_API_KEY to your .env file');
        errors.push('Or set AI_PROVIDER=vertex in .env to use Vertex AI instead');
      }
    }

    if (this.aiConfig.provider === 'vertex') {
      if (!this.aiConfig.projectId) {
        errors.push('Vertex AI project ID is required when using vertex provider');
        errors.push('To fix: Set VERTEX_AI_PROJECT_ID in .env or configure gcloud CLI');
      }
    }

    // Validate research configuration
    if (this.researchConfig.maxDepth < 1 || this.researchConfig.maxDepth > 10) {
      errors.push('MAX_DEPTH must be between 1 and 10');
    }

    if (this.researchConfig.maxConcurrentPages < 1 || this.researchConfig.maxConcurrentPages > 10) {
      errors.push('CONCURRENT_PAGES must be between 1 and 10');
    }

    // Validate custom instructions file if specified
    if (this.aiConfig.customInstructionsFile) {
      const resolvedPath = resolve(this.aiConfig.customInstructionsFile);
      if (!existsSync(resolvedPath)) {
        errors.push(`Custom instructions file not found: ${resolvedPath}`);
      }
    }

    return errors;
  }
}