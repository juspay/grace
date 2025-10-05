import { EventEmitter } from 'events';
import { DeepResearchOrchestrator, DeepResearchOptions } from '../services/DeepResearchOrchestrator';
import { ConfigService } from '../services/ConfigService';
import { StorageService } from '../services/StorageService';
import { ResultOutputService } from '../services/ResultOutputService';
import { DebugLogger } from '../utils/DebugLogger';
import { ResearchSession, LogEntry, ResearchConfig, AIConfig } from '../types';
import { GraceConfig } from './GraceConfig';

/**
 * Options for configuring a research session
 */
export interface ResearchOptions {
  /** Custom instructions to append to AI prompts */
  customInstructions?: string;
  /** Override default research configuration */
  researchConfig?: Partial<ResearchConfig>;
  /** Progress callback function */
  onProgress?: (progress: { percentage: number; stage: string; message: string }) => void;
  /** Log entry callback function */
  onLogEntry?: (entry: LogEntry) => void;
  /** Whether to save results to storage */
  saveResults?: boolean;
  /** Output format for results */
  outputFormat?: 'json' | 'html' | 'markdown';
}

/**
 * Result of a research session
 */
export interface ResearchResult {
  /** The final synthesized answer */
  finalAnswer: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** Complete research session data */
  session: ResearchSession;
  /** All log entries from the research process */
  logs: LogEntry[];
  /** Metadata about the research process */
  metadata: {
    totalPages: number;
    maxDepthReached: number;
    totalLinksFound: number;
    errorCount: number;
    aiTokensUsed: number;
    processingTimeMs: number;
  };
}

/**
 * Main class for programmatic access to Grace research capabilities
 *
 * @example
 * ```typescript
 * const researcher = new GraceResearcher(config);
 * const result = await researcher.research('What are the latest AI trends?');
 * console.log(result.finalAnswer);
 * ```
 */
export class GraceResearcher extends EventEmitter {
  private orchestrator: DeepResearchOrchestrator;
  private configService: ConfigService;
  private storageService: StorageService;
  private resultOutputService: ResultOutputService;
  private debugLogger: DebugLogger;
  private currentSession: ResearchSession | null = null;

  /**
   * Create a new GraceResearcher instance
   * @param config Configuration for the researcher
   */
  constructor(config: GraceConfig) {
    super();

    // Initialize services
    this.configService = new ConfigService();

    // Update configuration with provided values
    if (config.ai) {
      this.configService.updateAIConfig(config.ai);
    }
    if (config.research) {
      this.configService.updateResearchConfig(config.research);
    }

    this.orchestrator = new DeepResearchOrchestrator();
    this.debugLogger = DebugLogger.getInstance();
    this.resultOutputService = new ResultOutputService();

    const researchConfig = this.configService.getResearchConfig();
    this.storageService = new StorageService(
      researchConfig.dataDirectory,
      researchConfig.historyFile
    );

    this.setupEventListeners();
  }

  /**
   * Perform a research session
   * @param query The research question
   * @param options Optional configuration for the research
   * @returns Promise resolving to research results
   */
  async research(query: string, options: ResearchOptions = {}): Promise<ResearchResult> {
    const startTime = Date.now();

    try {
      // Validate configuration
      const configErrors = this.configService.validate();
      if (configErrors.length > 0) {
        throw new Error(`Configuration errors: ${configErrors.join(', ')}`);
      }

      // Apply research config overrides
      if (options.researchConfig) {
        this.configService.updateResearchConfig(options.researchConfig);
      }

      // Apply custom instructions if provided
      if (options.customInstructions) {
        const aiConfig = this.configService.getAIConfig();
        this.configService.updateAIConfig({
          ...aiConfig,
          customInstructions: options.customInstructions
        });
      }

      // Create research session
      this.currentSession = {
        id: `research_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        query,
        startTime,
        status: 'running',
        totalPages: 0,
        maxDepthReached: 0,
        metadata: {
          totalLinksFound: 0,
          errorCount: 0,
          aiTokensUsed: 0
        }
      };

      const logs: LogEntry[] = [];

      // Set up progress and log tracking
      const onProgress = options.onProgress || (() => {});
      const onLogEntry = (entry: LogEntry) => {
        logs.push(entry);
        if (options.onLogEntry) {
          options.onLogEntry(entry);
        }
        this.emit('logEntry', entry);
      };

      // Configure orchestrator callbacks
      this.orchestrator.removeAllListeners();
      this.orchestrator.on('logEntry', onLogEntry);
      this.orchestrator.on('progress', (progress) => {
        onProgress(progress);
        this.emit('progress', progress);
      });

      // Start research
      const researchOptions = {
        query,
        customInstructions: options.customInstructions,
        maxDepth: options.researchConfig?.maxDepth,
        maxPagesPerDepth: options.researchConfig?.maxPagesPerDepth,
        onProgress: (progress: number, status: string) => {
          const progressData = { percentage: progress, stage: 'research', message: status };
          onProgress(progressData);
          this.emit('progress', progressData);
        },
        onLogEntry: onLogEntry
      };

      const result = await this.orchestrator.startResearch(researchOptions);

      // Update session with results
      this.currentSession.endTime = Date.now();
      this.currentSession.status = 'completed';
      this.currentSession.finalAnswer = result.finalAnswer || '';
      this.currentSession.confidence = result.confidence || 0;
      this.currentSession.totalPages = result.totalPages || 0;
      this.currentSession.maxDepthReached = result.maxDepthReached || 0;
      this.currentSession.metadata = {
        totalLinksFound: result.metadata?.totalLinksFound || 0,
        errorCount: result.metadata?.errorCount || 0,
        aiTokensUsed: result.metadata?.aiTokensUsed || 0
      };

      // Save results if requested
      if (options.saveResults !== false) {
        try {
          await this.storageService.saveSession(this.currentSession);

          if (options.outputFormat) {
            // Get all page data from the orchestrator if available
            const allPages: any[] = []; // This would need to be populated from orchestrator
            const name = await this.orchestrator.generateNameForSession(query);
            const outputPaths = await this.resultOutputService.saveResults(
              this.currentSession,
              name,
              allPages
            );
            this.emit('resultsSaved', { paths: outputPaths, format: options.outputFormat });
          }
        } catch (error) {
          this.emit('error', new Error(`Failed to save results: ${error}`));
        }
      }

      const researchResult: ResearchResult = {
        finalAnswer: result.finalAnswer || '',
        confidence: result.confidence || 0,
        session: this.currentSession,
        logs,
        metadata: {
          totalPages: result.totalPages || 0,
          maxDepthReached: result.maxDepthReached || 0,
          totalLinksFound: result.metadata?.totalLinksFound || 0,
          errorCount: result.metadata?.errorCount || 0,
          aiTokensUsed: result.metadata?.aiTokensUsed || 0,
          processingTimeMs: Date.now() - startTime
        }
      };

      this.emit('researchComplete', researchResult);
      return researchResult;

    } catch (error) {
      if (this.currentSession) {
        this.currentSession.endTime = Date.now();
        this.currentSession.status = 'failed';
      }

      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Get the current research session
   */
  getCurrentSession(): ResearchSession | null {
    return this.currentSession;
  }

  /**
   * Cancel the current research session
   */
  async cancel(): Promise<void> {
    if (this.currentSession && this.currentSession.status === 'running') {
      this.currentSession.status = 'cancelled';
      this.currentSession.endTime = Date.now();

      // Cancel orchestrator
      this.orchestrator.removeAllListeners();
      this.emit('researchCancelled', this.currentSession);
    }
  }

  /**
   * Get research history
   * @param limit Maximum number of sessions to return
   */
  async getHistory(limit = 10): Promise<ResearchSession[]> {
    return this.storageService.getHistory(limit);
  }

  /**
   * Get statistics about past research sessions
   */
  async getStatistics(): Promise<{
    totalSessions: number;
    successfulSessions: number;
    averageConfidence: number;
    totalPagesProcessed: number;
    averageProcessingTime: number;
  }> {
    const history = await this.storageService.getHistory(100);

    const successful = history.filter(s => s.status === 'completed');
    const totalPages = history.reduce((sum, s) => sum + s.totalPages, 0);
    const avgConfidence = successful.length > 0
      ? successful.reduce((sum, s) => sum + (s.confidence || 0), 0) / successful.length
      : 0;

    const avgProcessingTime = history.length > 0
      ? history
          .filter(s => s.endTime)
          .reduce((sum, s) => sum + (s.endTime! - s.startTime), 0) / history.length
      : 0;

    return {
      totalSessions: history.length,
      successfulSessions: successful.length,
      averageConfidence: avgConfidence,
      totalPagesProcessed: totalPages,
      averageProcessingTime: avgProcessingTime
    };
  }

  /**
   * Test AI service connection
   */
  async testConnection(): Promise<{ success: boolean; error?: string }> {
    const aiConfig = this.configService.getAIConfig();
    const { AIService } = await import('../services/AIService');
    const aiService = new AIService(aiConfig);

    try {
      const result = await aiService.testConnection();
      return result;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get current configuration
   */
  getConfiguration(): { research: ResearchConfig; ai: AIConfig } {
    return {
      research: this.configService.getResearchConfig(),
      ai: this.configService.getAIConfig()
    };
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.orchestrator.removeAllListeners();
    this.removeAllListeners();
    this.debugLogger.close();
  }

  private setupEventListeners(): void {
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      this.destroy();
    });

    process.on('SIGTERM', () => {
      this.destroy();
    });
  }
}