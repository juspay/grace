/**
 * @mass-research/cli - Professional AI-powered deep web research library
 *
 * This library provides both programmatic access to MASS research capabilities
 * and a beautiful CLI interface for interactive research sessions.
 *
 * @example
 * ```typescript
 * import { MassResearcher, MassConfig } from '@mass-research/cli';
 *
 * const config: MassConfig = {
 *   ai: {
 *     provider: 'litellm',
 *     apiKey: 'your-api-key',
 *     baseUrl: 'http://localhost:4000/v1',
 *     modelId: 'gpt-4'
 *   },
 *   research: {
 *     maxDepth: 5,
 *     maxPagesPerDepth: 10,
 *     maxTotalPages: 50
 *   }
 * };
 *
 * const researcher = new MassResearcher(config);
 * const result = await researcher.research('What are the latest trends in AI research?');
 * console.log(result.finalAnswer);
 * ```
 */

// Export core types
export * from '../types';

// Export services for programmatic use
export { AIService, AIConfigurationError } from '../services/AIService';
export { ConfigService } from '../services/ConfigService';
export { DeepResearchOrchestrator } from '../services/DeepResearchOrchestrator';
export { SearchService } from '../services/SearchService';
export { WebScrapingService } from '../services/WebScrapingService';
export { StorageService } from '../services/StorageService';
export { ResultOutputService } from '../services/ResultOutputService';
export { DebugLogger } from '../utils/DebugLogger';

// Main library classes
export { MassResearcher } from './MassResearcher';
export { MassConfig } from './MassConfig';

// Utility functions
export { createMassResearcher, createDefaultConfig } from './factory';

// Version info
export const VERSION = '1.0.0';