#!/usr/bin/env node

import { Command } from "commander";
import chalk from "chalk";
import { DirectResearchService } from "../services/DirectResearchService";
import { ConfigService } from "../services/ConfigService";
import { StorageService } from "../services/StorageService";
import { DebugLogger } from "../utils/DebugLogger";
import inquirer from "inquirer";

class GraceResearchCLI {
  private directResearch: DirectResearchService;
  private config: ConfigService;
  private storageService: StorageService;
  private debugLogger: DebugLogger;

  constructor() {
    this.config = ConfigService.getInstance();
    this.directResearch = new DirectResearchService();
    this.debugLogger = DebugLogger.getInstance();

    const researchConfig = this.config.getResearchConfig();
    this.storageService = new StorageService(
      researchConfig.dataDirectory,
      researchConfig.historyFile
    );

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Handle graceful shutdown
    process.on("SIGINT", () => {
      this.cleanup();
      process.exit(0);
    });

    process.on("SIGTERM", () => {
      this.cleanup();
      
      process.exit(0);
    });
  }

  private cleanup(): void {
    this.debugLogger.close();
  }

  async showConfig(): Promise<void> {
    const config = this.config.getResearchConfig();
    const aiConfig = this.config.getAIConfig();

    console.log(chalk.cyan.bold("\n🔧 Current Configuration"));
    console.log(chalk.white("================================"));

    console.log(chalk.yellow("\nAI Configuration:"));
    console.log(`  Provider: ${aiConfig.provider}`);
    console.log(`  Model: ${aiConfig.modelId}`);
    console.log(`  Base URL: ${aiConfig.baseUrl}`);
    console.log(
      `  API Key: ${aiConfig.apiKey ? "***configured***" : "NOT SET"}`
    );
    console.log(
      `  Custom Instructions File: ${aiConfig.customInstructionsFile || "NOT SET"}`
    );
    if (aiConfig.customInstructions) {
      console.log(
        `  Custom Instructions: ${chalk.green("LOADED")} (${aiConfig.customInstructions.length} characters)`
      );
    } else {
      console.log(`  Custom Instructions: ${chalk.gray("NOT LOADED")}`);
    }

    console.log(chalk.yellow("\nResearch Configuration:"));
    console.log(`  Max Depth: ${config.maxDepth}`);
    console.log(`  Max Pages per Depth: ${config.maxPagesPerDepth}`);
    console.log(`  Max Total Pages: ${config.maxTotalPages}`);
    console.log(`  Concurrent Pages: ${config.maxConcurrentPages}`);
    console.log(`  Link Relevance Threshold: ${config.linkRelevanceThreshold}`);
    console.log(`  Timeout per Page: ${config.timeoutPerPage}ms`);
    console.log(`  Respect Robots.txt: ${config.respectRobotsTxt}`);

    console.log(chalk.yellow("\nStorage Configuration:"));
    console.log(`  Data Directory: ${config.dataDirectory}`);
    console.log(`  History File: ${config.historyFile}`);

    console.log(chalk.yellow("\nDebug Configuration:"));
    console.log(`  Debug Enabled: ${this.debugLogger.isEnabled()}`);
    if (this.debugLogger.isEnabled()) {
      console.log(`  Debug Log File: ${this.debugLogger.getLogFilePath()}`);
    }
  }

  async showHistoryCommand(): Promise<void> {
    try {
      const history = await this.storageService.getHistory(20);

      if (history.length === 0) {
        console.log(chalk.yellow("📝 No research history found."));
        return;
      }

      console.log(chalk.cyan.bold("\n📚 Research History"));
      console.log(chalk.white("================================"));

      history.forEach((session, index) => {
        const duration = session.endTime
          ? (session.endTime - session.startTime) / 1000
          : 0;
        const statusIcon =
          session.status === "completed"
            ? "✅"
            : session.status === "failed"
              ? "❌"
              : session.status === "cancelled"
                ? "⚠️ "
                : "🔄";

        console.log(
          `\n${index + 1}. ${statusIcon} ${chalk.white(session.query)}`
        );
        console.log(`   ${chalk.gray("Session ID:")} ${session.id}`);
        console.log(
          `   ${chalk.gray("Status:")} ${session.status} ${chalk.gray("|")} ${chalk.gray("Duration:")} ${duration.toFixed(1)}s`
        );
        console.log(
          `   ${chalk.gray("Pages:")} ${session.totalPages} ${chalk.gray("|")} ${chalk.gray("Depth:")} ${session.maxDepthReached}`
        );
        console.log(
          `   ${chalk.gray("Started:")} ${new Date(session.startTime).toLocaleString()}`
        );
      });
    } catch (error) {
      console.error(
        chalk.red("❌ Failed to load history:"),
        error instanceof Error ? error.message : "Unknown error"
      );
    }
  }

  async showStats(): Promise<void> {
    try {
      const stats = await this.storageService.getSessionStatistics();

      console.log(chalk.cyan.bold("\n📊 Research Statistics"));
      console.log(chalk.white("================================"));

      console.log(`${chalk.yellow("Total Sessions:")} ${stats.totalSessions}`);
      console.log(
        `${chalk.yellow("Completed Sessions:")} ${stats.completedSessions}`
      );
      console.log(
        `${chalk.yellow("Success Rate:")} ${stats.totalSessions > 0 ? ((stats.completedSessions / stats.totalSessions) * 100).toFixed(1) : 0}%`
      );
      console.log(`${chalk.yellow("Average Pages:")} ${stats.averagePages}`);
      console.log(`${chalk.yellow("Average Depth:")} ${stats.averageDepth}`);
      console.log(
        `${chalk.yellow("Storage Used:")} ${(stats.totalStorageSize / 1024 / 1024).toFixed(2)} MB`
      );
    } catch (error) {
      console.error(
        chalk.red("❌ Failed to load statistics:"),
        error instanceof Error ? error.message : "Unknown error"
      );
    }
  }

  async startDeepResearch(query: string): Promise<void> {
    try {
      console.log(chalk.cyan.bold("Grace Deep Research Mode"));
      console.log(chalk.gray(`Query: "${query}"`));

      // Validate configuration
      const configErrors = this.config.validate();
      if (configErrors.length > 0) {
        console.error(chalk.red("Configuration errors:"));
        configErrors.forEach((error) =>
          console.error(chalk.red(`  • ${error}`))
        );
        console.log(
          chalk.yellow(
            "\n💡 Please check your .env file and fix the configuration."
          )
        );
        return;
      }
      // Test AI connection
      console.log(chalk.cyan("Testing AI service connection..."));
      const aiConfig = this.config.getAIConfig();
      const { AIService } = await import("../services/AIService");
      const aiService = new AIService(aiConfig);

      const aiTest = await aiService.testConnection();
      if (!aiTest.success) {
        console.error(chalk.red(`AI service test failed: ${aiTest.error}`));
        console.log(
          chalk.yellow("\nPlease check your AI configuration in .env file.")
        );
        return;
      }
      console.log(chalk.green("AI service connected"));

      // Start direct research
      await this.directResearch.research(query);
    } catch (error) {
      console.error(
        chalk.red("\nDeep research failed:"),
        error instanceof Error ? error.message : "Unknown error"
      );
      process.exit(1);
    }
  }
}

// CLI Program
const program = new Command();
const cli = new GraceResearchCLI();

program
  .name("GRACE-deep-research")
  .description(
    "GRACE Deep Research CLI - Intelligent web research with AI analysis"
  )
  .version("1.1.0");

program
  .command("research [query]")
  .description("Start a direct research session")
  .action(async (query?: string) => {
    let finalQuery = query || "";
    if (!query || !query.trim()) {
      // Prompt for query if not provided
      const answers = await inquirer.prompt([
        {
          type: "input",
          name: "query",
          message: "Enter your research query:",
          validate: (input) => input.trim() !== "" || "Query cannot be empty",
        },
      ]);
      finalQuery = answers.query;
    }
    await cli.startDeepResearch(finalQuery);
  });

program
  .command("config")
  .description("Show current configuration")
  .action(async () => {
    await cli.showConfig();
  });

program
  .command("history")
  .description("Show research history")
  .action(async () => {
    await cli.showHistoryCommand();
  });

program
  .command("stats")
  .description("Show research statistics")
  .action(async () => {
    await cli.showStats();
  });

program
  .command("clean")
  .description("Clean up old research data")
  .option("-d, --days <days>", "Clean data older than specified days", "30")
  .action(async (options) => {
    try {
      const config = ConfigService.getInstance().getResearchConfig();
      const storageService = new StorageService(
        config.dataDirectory,
        config.historyFile
      );

      const maxAge = parseInt(options.days) * 24 * 60 * 60 * 1000;
      const deletedCount = await storageService.cleanupOldSessions(maxAge);

      console.log(
        chalk.green(
          `🧹 Cleanup complete! Removed ${deletedCount} old sessions.`
        )
      );
    } catch (error) {
      console.error(
        chalk.red("❌ Cleanup failed:"),
        error instanceof Error ? error.message : "Unknown error"
      );
    }
  });

program
  .command("test-search")
  .description("Test SearxNG connectivity and JSON API")
  .option("-q, --query <query>", "Test query to search for", "test search")
  .action(async (options) => {
    try {
      console.log(chalk.cyan.bold("🔍 Testing SearxNG Connectivity"));
      console.log(chalk.gray("================================"));

      const config = ConfigService.getInstance();
      const { SearchService } = await import("../services/SearchService");

      // Get SearxNG URL from env or use default
      const searxngUrl =
        process.env.SEARXNG_BASE_URL || "http://localhost:32768";
      console.log(chalk.yellow(`SearxNG URL: ${searxngUrl}`));

      const searchService = new SearchService(searxngUrl);

      // Test basic connectivity
      console.log(chalk.cyan("\n🌐 Testing basic connectivity..."));
      try {
        const axios = (await import("axios")).default;
        const response = await axios.get(searxngUrl, { timeout: 5000 });
        console.log(
          chalk.green(`✅ SearxNG responding (HTTP ${response.status})`)
        );
      } catch (error: any) {
        console.log(
          chalk.red(
            `❌ SearxNG not accessible: ${error?.message || "Unknown error"}`
          )
        );
        return;
      }

      // Test available engines
      console.log(chalk.cyan("\n🔧 Testing available engines..."));
      try {
        const engines = await searchService.getAvailableEngines();
        console.log(
          chalk.green(`✅ Found ${engines.length} available engines:`)
        );
        console.log(
          chalk.gray(
            `   ${engines.slice(0, 10).join(", ")}${engines.length > 10 ? "..." : ""}`
          )
        );
      } catch (error: any) {
        console.log(
          chalk.yellow(
            `⚠️  Could not get engines: ${error?.message || "Unknown error"}`
          )
        );
      }

      // Test JSON search API
      console.log(
        chalk.cyan(
          `\n🔍 Testing JSON search API with query: "${options.query}"`
        )
      );
      try {
        const results = await searchService.search(options.query, { limit: 5 });

        if (results.length > 0) {
          console.log(
            chalk.green(
              `✅ Search successful! Found ${results.length} results:`
            )
          );
          results.forEach((result, index) => {
            console.log(chalk.gray(`   ${index + 1}. ${result.title}`));
            console.log(chalk.gray(`      ${result.url}`));
            console.log(
              chalk.gray(
                `      Engine: ${result.engine}, Score: ${result.score.toFixed(2)}`
              )
            );
          });
        } else {
          console.log(chalk.yellow("⚠️  Search returned no results"));
        }
      } catch (error: any) {
        console.log(
          chalk.red(`❌ Search failed: ${error?.message || "Unknown error"}`)
        );
      }

      console.log(chalk.green("\n✅ SearxNG test completed!"));
    } catch (error) {
      console.error(
        chalk.red("❌ Test failed:"),
        error instanceof Error ? error.message : "Unknown error"
      );
    }
  });

// Default action
if (process.argv.length === 2) {
  // No command provided, show help
  program.help();
} else {
  program.parse(process.argv);
}
