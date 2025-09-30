#!/usr/bin/env node

import { Command } from 'commander';
import inquirer from 'inquirer';
import chalk from 'chalk';
import { TerminalUI } from './ui/TerminalUI';
import { DeepResearchOrchestrator } from './services/DeepResearchOrchestrator';
import { ConfigService } from './services/ConfigService';
import { StorageService } from './services/StorageService';
import { ResultOutputService } from './services/ResultOutputService';
import { DebugLogger } from './utils/DebugLogger';
import { UserAction, ResearchSession } from './types';
import * as path from 'path';

class MassResearchCLI {
  private ui: TerminalUI | null = null;
  private orchestrator: DeepResearchOrchestrator;
  private config: ConfigService;
  private storageService: StorageService;
  private resultOutputService: ResultOutputService;
  private debugLogger: DebugLogger;
  private currentSession: ResearchSession | null = null;

  constructor() {
    this.config = ConfigService.getInstance();
    this.orchestrator = new DeepResearchOrchestrator();
    this.debugLogger = DebugLogger.getInstance();
    this.resultOutputService = new ResultOutputService();

    const researchConfig = this.config.getResearchConfig();
    this.storageService = new StorageService(
      researchConfig.dataDirectory,
      researchConfig.historyFile
    );

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Handle graceful shutdown
    process.on('SIGINT', () => {
      this.cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      this.cleanup();
      process.exit(0);
    });

    // Research orchestrator events
    this.orchestrator.on('logEntry', (entry) => {
      if (this.ui) {
        this.ui.addLogEntry(entry);
      }
    });
  }

  private cleanup(): void {
    if (this.ui) {
      this.ui.destroy();
    }
    this.debugLogger.close();
  }

  async startInteractiveResearch(): Promise<void> {
    try {
      // Validate configuration
      const configErrors = this.config.validate();
      if (configErrors.length > 0) {
        console.error(chalk.red('❌ Configuration errors:'));
        configErrors.forEach(error => console.error(chalk.red(`  • ${error}`)));
        console.log(chalk.yellow('\n💡 Please check your .env file and fix the configuration.'));
        return;
      }

      // Test AI connection
      console.log(chalk.cyan('🤖 Testing AI service connection...'));
      const aiConfig = this.config.getAIConfig();
      const { AIService, AIConfigurationError } = await import('./services/AIService');
      const aiService = new AIService(aiConfig);

      const aiTest = await aiService.testConnection();
      if (!aiTest.success) {
        console.error(chalk.red(`❌ AI service test failed: ${aiTest.error}`));
        console.log(chalk.yellow('\n💡 AI Configuration Help:'));
        console.log(aiTest.configHelp);

        const { continueAnyway } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'continueAnyway',
            message: 'Would you like to continue anyway? (Research will fail without AI)',
            default: false
          }
        ]);

        if (!continueAnyway) {
          return;
        }
      } else {
        console.log(chalk.green('✅ AI service connection successful'));
      }

      // Get research query
      const { query } = await inquirer.prompt([
        {
          type: 'input',
          name: 'query',
          message: 'What would you like to research?',
          validate: (input: string) => input.trim().length > 0 || 'Please enter a research query'
        }
      ]);

      // Get optional custom instructions
      const { customInstructions } = await inquirer.prompt([
        {
          type: 'input',
          name: 'customInstructions',
          message: 'Any specific instructions for the research? (optional)',
          default: ''
        }
      ]);

      // Get research parameters
      const researchConfig = this.config.getResearchConfig();
      const { maxDepth, maxPagesPerDepth } = await inquirer.prompt([
        {
          type: 'number',
          name: 'maxDepth',
          message: 'Maximum research depth:',
          default: researchConfig.maxDepth,
          validate: (input: number) => input >= 1 && input <= 10 || 'Depth must be between 1 and 10'
        },
        {
          type: 'number',
          name: 'maxPagesPerDepth',
          message: 'Maximum pages per depth level:',
          default: researchConfig.maxPagesPerDepth,
          validate: (input: number) => input >= 1 && input <= 50 || 'Pages must be between 1 and 50'
        }
      ]);

      // Initialize UI
      this.ui = new TerminalUI({
        title: 'MASS Deep Research CLI',
        onUserAction: this.handleUserAction.bind(this)
      });

      this.ui.updateStatus('Starting deep research...', 'info');

      // Start research
      this.currentSession = await this.orchestrator.startResearch({
        query: query.trim(),
        customInstructions: customInstructions.trim() || undefined,
        maxDepth,
        maxPagesPerDepth,
        onProgress: (progress, status) => {
          if (this.ui) {
            this.ui.updateProgress(progress, status);
            this.ui.updateStatus(status, 'info');
          }
        },
        onUserActionNeeded: async (question) => {
          if (this.ui) {
            return await this.ui.prompt(question);
          }
          return '';
        }
      });

      // Save and display results
      await this.handleResearchComplete();

    } catch (error) {
      // Import AIConfigurationError for type checking
      const { AIConfigurationError } = await import('./services/AIService');

      if (error instanceof AIConfigurationError) {
        if (this.ui) {
          this.ui.showAIError(error.message, error.configHelp);
        } else {
          console.error(chalk.red('❌ AI Configuration Error:'), error.message);
          console.log(chalk.yellow('\n💡 Configuration Help:'));
          console.log(error.configHelp);
        }
      } else {
        if (this.ui) {
          this.ui.updateStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        } else {
          console.error(chalk.red('❌ Error:'), error instanceof Error ? error.message : 'Unknown error');
        }
      }
    }
  }

  private async handleUserAction(action: UserAction): Promise<void> {
    this.debugLogger.logUserAction(action.type, action.data);

    switch (action.type) {
      case 'skip':
        if (action.data?.showHistory) {
          await this.showHistory();
        } else {
          this.orchestrator.skip();
          this.ui?.updateStatus('Skipping current operation...', 'warning');
        }
        break;

      case 'cancel':
        this.orchestrator.stop();
        this.ui?.updateStatus('Cancelling research...', 'warning');
        break;

      case 'input':
        if (action.data?.message) {
          this.orchestrator.provideGuidance(action.data.message);
          this.ui?.updateStatus(`Guidance provided: "${action.data.message}"`, 'info');
        }
        break;
    }
  }

  private async showHistory(): Promise<void> {
    try {
      const history = await this.storageService.getHistory(20);
      if (this.ui) {
        this.ui.showHistory(history);
      }
    } catch (error) {
      if (this.ui) {
        this.ui.updateStatus('Failed to load history', 'error');
      }
    }
  }

  private async handleResearchComplete(): Promise<void> {
    if (!this.currentSession) return;

    this.ui?.updateStatus('Research completed! Generating reports...', 'success');

    try {
      // Get all page data
      const allPages = this.orchestrator.getAllPageData();

      // Save results
      const { htmlPath, jsonPath, markdownPath } = await this.resultOutputService.saveResults(
        this.currentSession,
        allPages
      );

      // Log completion
      if (this.debugLogger.isEnabled()) {
        const duration = this.currentSession.endTime! - this.currentSession.startTime;
        this.debugLogger.logSessionSummary(
          this.currentSession.id,
          this.currentSession.totalPages,
          this.currentSession.maxDepthReached,
          duration,
          this.currentSession.status
        );
      }

      // Show results to user
      if (this.ui) {
        this.ui.updateStatus('Results saved successfully!', 'success');
        this.ui.updateProgress(100, 'Complete');

        // Wait a moment before showing results
        setTimeout(async () => {
          this.cleanup();
          await this.resultOutputService.openResult(htmlPath);

          // Show summary
          console.log('\n' + chalk.green.bold('🎉 Research Complete!'));
          console.log(chalk.white(`Query: "${this.currentSession!.query}"`));
          console.log(chalk.white(`Status: ${this.currentSession!.status}`));
          console.log(chalk.white(`Pages Processed: ${this.currentSession!.totalPages}`));
          console.log(chalk.white(`Max Depth: ${this.currentSession!.maxDepthReached}`));

          if (this.currentSession!.confidence !== undefined) {
            console.log(chalk.white(`Confidence: ${(this.currentSession!.confidence * 100).toFixed(1)}%`));
          }

          if (this.debugLogger.isEnabled()) {
            console.log(chalk.yellow(`\n📝 Debug log: ${this.debugLogger.getLogFilePath()}`));
          }

          process.exit(0);
        }, 2000);
      }

    } catch (error) {
      this.ui?.updateStatus(`Failed to save results: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  }

  async showConfig(): Promise<void> {
    const config = this.config.getResearchConfig();
    const aiConfig = this.config.getAIConfig();

    console.log(chalk.cyan.bold('\n🔧 Current Configuration'));
    console.log(chalk.white('================================'));

    console.log(chalk.yellow('\nAI Configuration:'));
    console.log(`  Provider: ${aiConfig.provider}`);
    console.log(`  Model: ${aiConfig.modelId}`);
    console.log(`  Base URL: ${aiConfig.baseUrl}`);
    console.log(`  API Key: ${aiConfig.apiKey ? '***configured***' : 'NOT SET'}`);
    console.log(`  Custom Instructions File: ${aiConfig.customInstructionsFile || 'NOT SET'}`);
    if (aiConfig.customInstructions) {
      console.log(`  Custom Instructions: ${chalk.green('LOADED')} (${aiConfig.customInstructions.length} characters)`);
    } else {
      console.log(`  Custom Instructions: ${chalk.gray('NOT LOADED')}`);
    }

    console.log(chalk.yellow('\nResearch Configuration:'));
    console.log(`  Max Depth: ${config.maxDepth}`);
    console.log(`  Max Pages per Depth: ${config.maxPagesPerDepth}`);
    console.log(`  Max Total Pages: ${config.maxTotalPages}`);
    console.log(`  Concurrent Pages: ${config.maxConcurrentPages}`);
    console.log(`  Link Relevance Threshold: ${config.linkRelevanceThreshold}`);
    console.log(`  Timeout per Page: ${config.timeoutPerPage}ms`);
    console.log(`  Respect Robots.txt: ${config.respectRobotsTxt}`);

    console.log(chalk.yellow('\nStorage Configuration:'));
    console.log(`  Data Directory: ${config.dataDirectory}`);
    console.log(`  History File: ${config.historyFile}`);

    console.log(chalk.yellow('\nDebug Configuration:'));
    console.log(`  Debug Enabled: ${this.debugLogger.isEnabled()}`);
    if (this.debugLogger.isEnabled()) {
      console.log(`  Debug Log File: ${this.debugLogger.getLogFilePath()}`);
    }
  }

  async showHistoryCommand(): Promise<void> {
    try {
      const history = await this.storageService.getHistory(20);

      if (history.length === 0) {
        console.log(chalk.yellow('📝 No research history found.'));
        return;
      }

      console.log(chalk.cyan.bold('\n📚 Research History'));
      console.log(chalk.white('================================'));

      history.forEach((session, index) => {
        const duration = session.endTime ? (session.endTime - session.startTime) / 1000 : 0;
        const statusIcon = session.status === 'completed' ? '✅' :
                          session.status === 'failed' ? '❌' :
                          session.status === 'cancelled' ? '⚠️ ' : '🔄';

        console.log(`\n${index + 1}. ${statusIcon} ${chalk.white(session.query)}`);
        console.log(`   ${chalk.gray('Session ID:')} ${session.id}`);
        console.log(`   ${chalk.gray('Status:')} ${session.status} ${chalk.gray('|')} ${chalk.gray('Duration:')} ${duration.toFixed(1)}s`);
        console.log(`   ${chalk.gray('Pages:')} ${session.totalPages} ${chalk.gray('|')} ${chalk.gray('Depth:')} ${session.maxDepthReached}`);
        console.log(`   ${chalk.gray('Started:')} ${new Date(session.startTime).toLocaleString()}`);
      });

    } catch (error) {
      console.error(chalk.red('❌ Failed to load history:'), error instanceof Error ? error.message : 'Unknown error');
    }
  }

  async showStats(): Promise<void> {
    try {
      const stats = await this.storageService.getSessionStatistics();

      console.log(chalk.cyan.bold('\n📊 Research Statistics'));
      console.log(chalk.white('================================'));

      console.log(`${chalk.yellow('Total Sessions:')} ${stats.totalSessions}`);
      console.log(`${chalk.yellow('Completed Sessions:')} ${stats.completedSessions}`);
      console.log(`${chalk.yellow('Success Rate:')} ${stats.totalSessions > 0 ? ((stats.completedSessions / stats.totalSessions) * 100).toFixed(1) : 0}%`);
      console.log(`${chalk.yellow('Average Pages:')} ${stats.averagePages}`);
      console.log(`${chalk.yellow('Average Depth:')} ${stats.averageDepth}`);
      console.log(`${chalk.yellow('Storage Used:')} ${(stats.totalStorageSize / 1024 / 1024).toFixed(2)} MB`);

    } catch (error) {
      console.error(chalk.red('❌ Failed to load statistics:'), error instanceof Error ? error.message : 'Unknown error');
    }
  }
}

// CLI Program
const program = new Command();
const cli = new MassResearchCLI();

program
  .name('mass-research')
  .description('MASS Deep Research CLI - Intelligent web research with AI analysis')
  .version('1.0.0');

program
  .command('research')
  .description('Start an interactive deep research session')
  .action(async () => {
    await cli.startInteractiveResearch();
  });

program
  .command('config')
  .description('Show current configuration')
  .action(async () => {
    await cli.showConfig();
  });

program
  .command('history')
  .description('Show research history')
  .action(async () => {
    await cli.showHistoryCommand();
  });

program
  .command('stats')
  .description('Show research statistics')
  .action(async () => {
    await cli.showStats();
  });

program
  .command('clean')
  .description('Clean up old research data')
  .option('-d, --days <days>', 'Clean data older than specified days', '30')
  .action(async (options) => {
    try {
      const config = ConfigService.getInstance().getResearchConfig();
      const storageService = new StorageService(config.dataDirectory, config.historyFile);

      const maxAge = parseInt(options.days) * 24 * 60 * 60 * 1000;
      const deletedCount = await storageService.cleanupOldSessions(maxAge);

      console.log(chalk.green(`🧹 Cleanup complete! Removed ${deletedCount} old sessions.`));
    } catch (error) {
      console.error(chalk.red('❌ Cleanup failed:'), error instanceof Error ? error.message : 'Unknown error');
    }
  });

// Default action
if (process.argv.length === 2) {
  // No command provided, start interactive research
  cli.startInteractiveResearch();
} else {
  program.parse(process.argv);
}