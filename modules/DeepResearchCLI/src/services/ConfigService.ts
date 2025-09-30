import { config } from 'dotenv';
import { resolve } from 'path';
import { existsSync, readFileSync } from 'fs';
import { ResearchConfig, AIConfig } from '../types';

export class ConfigService {
  private static instance: ConfigService;
  private researchConfig: ResearchConfig;
  private aiConfig: AIConfig;

  constructor() {
    // Load environment variables
    config({ path: resolve(process.cwd(), '.env') });

    this.researchConfig = {
      maxDepth: parseInt(process.env.MAX_DEPTH || '5'),
      maxPagesPerDepth: parseInt(process.env.MAX_PAGES_PER_DEPTH || '10'),
      maxTotalPages: parseInt(process.env.MAX_TOTAL_PAGES || '50'),
      maxConcurrentPages: parseInt(process.env.CONCURRENT_PAGES || '3'),
      linkRelevanceThreshold: parseFloat(process.env.LINK_RELEVANCE_THRESHOLD || '0.6'),
      timeoutPerPage: parseInt(process.env.TIMEOUT_PER_PAGE_MS || '30000'),
      respectRobotsTxt: process.env.RESPECT_ROBOTS_TXT !== 'false',
      dataDirectory: process.env.RESEARCH_DATA_DIR || './research_data',
      historyFile: process.env.HISTORY_FILE || './research_history.json',
      interactiveMode: process.env.INTERACTIVE_MODE !== 'false',
      enableDeepLinkCrawling: process.env.ENABLE_DEEP_LINK_CRAWLING !== 'false',
      maxLinksPerPage: parseInt(process.env.MAX_LINKS_PER_PAGE || '10'),
      deepCrawlDepth: parseInt(process.env.DEEP_CRAWL_DEPTH || '2')
    };

    this.aiConfig = {
      provider: (process.env.AI_PROVIDER as 'litellm' | 'vertex') || 'litellm',
      apiKey: process.env.LITELLM_API_KEY,
      baseUrl: process.env.LITELLM_BASE_URL || 'http://localhost:4000/v1',
      modelId: process.env.LITELLM_MODEL_ID || 'gpt-4',
      projectId: process.env.VERTEX_AI_PROJECT_ID,
      location: process.env.VERTEX_AI_LOCATION || 'us-central1',
      customInstructionsFile: process.env.CUSTOM_INSTRUCTIONS_FILE,
      customInstructions: this.loadCustomInstructions(process.env.CUSTOM_INSTRUCTIONS_FILE)
    };
  }

  static getInstance(): ConfigService {
    if (!ConfigService.instance) {
      ConfigService.instance = new ConfigService();
    }
    return ConfigService.instance;
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

    if (this.aiConfig.provider === 'litellm' && !this.aiConfig.apiKey) {
      errors.push('LITELLM_API_KEY is required when using litellm provider');
    }

    if (this.aiConfig.provider === 'vertex' && !this.aiConfig.projectId) {
      errors.push('VERTEX_AI_PROJECT_ID is required when using vertex provider');
    }

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