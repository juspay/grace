import chalk from "chalk";
import { ConfigService } from "./ConfigService";
import { AIMessage, AIService } from "./AIService";
import { SearchService } from "./SearchService";
import { WebScrapingService } from "./WebScrapingService";
import { ResultOutputService } from "./ResultOutputService";
import { StorageService } from "./StorageService";
import { DebugLogger } from "../utils/DebugLogger";
import { ResearchSession, PageData, ExtractedLink } from "../types";
import { v4 as uuidv4 } from "uuid";
import * as fs from "fs";
import * as path from "path";

/**
 * Direct Research Service
 * Handles non-interactive research: query -> search -> crawl -> deep links -> output
 */
export class DirectResearchService {
  private config: ConfigService;
  private aiService: AIService;
  private searchService: SearchService;
  private webScrapingService: WebScrapingService;
  private resultOutputService: ResultOutputService;
  private storageService: StorageService;
  private debugLogger: DebugLogger;

  constructor() {
    this.config = ConfigService.getInstance();
    this.debugLogger = DebugLogger.getInstance();

    const aiConfig = this.config.getAIConfig();
    this.aiService = new AIService(aiConfig);

    this.searchService = new SearchService(process.env.SEARXNG_BASE_URL);

    const researchConfig = this.config.getResearchConfig();
    const proxies = process.env.PROXY_LIST
      ? process.env.PROXY_LIST.split(",")
      : [];
    this.webScrapingService = new WebScrapingService({
      maxConcurrentPages: researchConfig.maxConcurrentPages,
      timeout: researchConfig.timeoutPerPage,
      respectRobotsTxt: researchConfig.respectRobotsTxt,
      proxies,
    });

    this.resultOutputService = new ResultOutputService();
    this.storageService = new StorageService(
      researchConfig.dataDirectory,
      researchConfig.historyFile
    );
  }

  /**
   * Main direct research flow
   * query -> search -> crawl pages -> follow links -> deep analysis -> output
   */
  async research(query: string): Promise<void> {
    console.log(chalk.cyan.bold(`\nStarting Grace Deep Research: "${query}"`));
    console.log(chalk.gray("━".repeat(60)));

    const startTime = Date.now();
    const session: ResearchSession = {
      id: uuidv4(),
      query,
      startTime,
      status: "running",
      totalPages: 0,
      maxDepthReached: 0,
      metadata: {
        totalLinksFound: 0,
        errorCount: 0,
        aiTokensUsed: 0,
      },
    };

    // Global URL tracker to avoid duplicates across all steps
    const globalVisitedUrls = new Set<string>();

    // Load custom instructions and generate link quality prompt
    let linkQualityPrompt: string | null = null;
    try {
      const customInstructions = this.loadCustomInstructions();
      if (customInstructions) {
        linkQualityPrompt = await this.aiService.generateLinkQualityPrompt(
          customInstructions,
          query
        );
        if (this.config.isDebugMode()) {
          console.log(
            chalk.green(
              `   Loaded custom instructions and generated link quality prompt`
            )
          );
          console.log(chalk.gray(`   → ${linkQualityPrompt}`));
        }
      }
    } catch (error) {
      console.log(
        chalk.yellow(
          "Custom instructions not found, using default link evaluation"
        )
      );
    }

    try {
      // Step 1: Generate search queries
      console.log(chalk.yellow("Generating search queries..."));
      const searchQueries = await this.aiService.generateSearchQueries(
        query,
        0
      );
      if (this.config.isDebugMode()) {
        console.log(
          chalk.green(`  Generated ${searchQueries.length} search queries`)
        );

        searchQueries.forEach((q, idx) => {
          console.log(chalk.gray(`      ${idx + 1}. ${q}`));
        });
      }

      // Step 2: Perform searches
      console.log(chalk.yellow("Performing web searches..."));
      const allSearchResults = [];
      for (const searchQuery of searchQueries) {
        console.log(chalk.gray(`   Searching: "${searchQuery}"`));
        const results = await this.searchService.search(searchQuery, {
          limit: 10,
        });
        allSearchResults.push(...results);
      }
      console.log(
        chalk.green(`   Found ${allSearchResults.length} search results`)
      );

      // Step 3: Initial page crawling

      const researchConfig = this.config.getResearchConfig();
      const initialUrls = allSearchResults
        .slice(0, researchConfig.maxPagesPerDepth)
        .map((result) => result.url)
        .filter((url) => {
          if (globalVisitedUrls.has(url)) return false;
          globalVisitedUrls.add(url);
          return true;
        });

      // AI Analysis of search results to filter/rank
      let analysedResults = initialUrls;
      if (allSearchResults.length > 10) {
        console.log(chalk.yellow("Analyzing search results with AI..."));
        analysedResults = await this.aiService.analyzeSearchResults(
          query,
          allSearchResults
        );
        console.log(
          chalk.green(
            `   ✓ AI analysis complete, ${analysedResults.length} relevant results`
          )
        );
        if (this.config.isDebugMode()) {
          this.debugLogger.log(
            `Top analyzed search results:\n` +
              analysedResults
                .map((result, index) => `   ${index + 1}. ${result}`)
                .join("\n")
          );
        }
      }
      console.log(chalk.yellow("Crawling initial pages..."));
      const initialPages =
        await this.webScrapingService.scrapeMultiplePages(analysedResults);
      const validPages = initialPages.filter(
        (page: any) => page.content.length > 100
      );
      console.log(
        chalk.green(`   ✓ Successfully crawled ${validPages.length} pages`)
      );

      // Step 4: Deep link crawling (if enabled)
      let allPages = validPages;
      if (researchConfig.enableDeepLinkCrawling) {
        console.log(chalk.yellow("Crawling with links found in the pages."));

        const deepPages = await this.performDeepLinkCrawling(
          validPages,
          query,
          globalVisitedUrls,
          linkQualityPrompt
        );
        allPages = [...validPages, ...deepPages];
        console.log(
          chalk.green(
            `   ✓ Found ${deepPages.length} additional pages through deep crawling`
          )
        );

        if (this.debugLogger.isEnabled()) {
          this.debugLogger.log(
            `Deep crawling complete: ${deepPages.length} pages added`
          );
          this.debugLogger.log(
            `Total pages after deep crawl: ${allPages.length}`
          );
        }
      } else {
        console.log(chalk.gray("    •   Deep link crawling DISABLED"));
        if (this.debugLogger.isEnabled()) {
          this.debugLogger.log(
            "Deep link crawling skipped - disabled in config"
          );
        }
      }

      // Step 4.5: Iterative AI completeness check with additional searches
      if (researchConfig.aiCompletenessCheck) {
        const maxIterations = 3; // Maximum number of additional search iterations
        let iteration = 0;

        while (iteration < maxIterations) {
          iteration++;
          console.log(
            chalk.yellow(
              `\n${iteration}: AI completeness check (iteration ${iteration}/${maxIterations})...`
            )
          );

          const insights = allPages
            .map((p) => p.title + ": " + p.content)
            .filter(Boolean);
          const completenessCheck =
            await this.aiService.assessInformationCompleteness(
              query,
              allPages.length,
              insights
            );

          console.log(
            chalk.gray(
              `   • Information complete: ${completenessCheck.isComplete ? "YES" : "NO"}`
            )
          );
          console.log(
            chalk.gray(
              `   • Confidence: ${(completenessCheck.confidence * 100).toFixed(0)}%`
            )
          );

          if (completenessCheck.customInstructionsMet !== undefined) {
            console.log(
              chalk.gray(
                `   • Custom instructions met: ${completenessCheck.customInstructionsMet ? "YES" : "NO"}`
              )
            );
          }

          // Check if we should stop
          if (
            completenessCheck.isComplete &&
            completenessCheck.customInstructionsMet !== false
          ) {
            console.log(chalk.green(`     All required information gathered!`));
            break;
          }

          if (completenessCheck.missingAspects.length > 0) {
            console.log(chalk.yellow(`     Missing aspects detected:`));
            completenessCheck.missingAspects.forEach((aspect) => {
              console.log(chalk.gray(`      • ${aspect}`));
            });

            console.log(
              chalk.cyan(
                `\n    Performing additional targeted searches (iteration ${iteration})...`
              )
            );

            const additionalSearchQueries = completenessCheck.missingAspects
              .slice(0, 4) // Top 2 missing aspects per iteration
              .map((aspect) => `${query} ${aspect}`);

            let newPagesAdded = 0;

            for (const searchQuery of additionalSearchQueries) {
              console.log(chalk.gray(`      • Searching: "${searchQuery}"`));
              const results = await this.searchService.search(searchQuery, {
                limit: 5,
              });

              if (results.length > 0) {
                // Filter out already visited URLs
                const newUrls = results
                  .map((r) => r.url)
                  .filter((url) => !globalVisitedUrls.has(url))
                  .slice(0, 3);

                if (newUrls.length === 0) {
                  console.log(
                    chalk.gray(
                      `        All results already visited, skipping...`
                    )
                  );
                  continue;
                }

                console.log(
                  chalk.gray(
                    `        Found ${results.length} results, ${newUrls.length} new URLs to scrape...`
                  )
                );

                // Mark as visited
                newUrls.forEach((url) => globalVisitedUrls.add(url));

                const additionalPages =
                  await this.webScrapingService.scrapeMultiplePages(newUrls);
                const validAdditionalPages = additionalPages.filter(
                  (page: any) => page.content.length > 100
                );

                allPages.push(...validAdditionalPages);
                newPagesAdded += validAdditionalPages.length;
                console.log(
                  chalk.green(
                    `        ✓ Added ${validAdditionalPages.length} pages`
                  )
                );
              }
            }

            if (newPagesAdded === 0) {
              console.log(
                chalk.yellow(
                  `   ⚠️  No new pages found, stopping additional searches`
                )
              );
              break;
            }

            console.log(
              chalk.green(
                `   ✓ Iteration ${iteration} complete, total pages: ${allPages.length}, new: ${newPagesAdded}`
              )
            );
          } else {
            console.log(chalk.green(`   ✅ No missing aspects identified`));
            break;
          }
        }

        if (iteration >= maxIterations) {
          console.log(
            chalk.yellow(
              `   ⚠️  Reached maximum iterations (${maxIterations}), proceeding with analysis...`
            )
          );
        }
      }

      // Step 5: AI Analysis - Break into chunks to avoid timeout
      console.log(chalk.yellow("AI analysis and synthesis..."));
      const pageDataForAI = allPages.map((page: any) => ({
        url: page.url,
        title: page.title,
        content: page.content || "",
        relevanceScore: page.relevanceScore || 0.5,
        depth: page.depth || 0,
      }));

      // Break pages into chunks to avoid timeout
      const CHUNK_SIZE = 5; // Process 5 pages at a time
      const chunks: any[][] = [];
      for (let i = 0; i < pageDataForAI.length; i += CHUNK_SIZE) {
        chunks.push(pageDataForAI.slice(i, i + CHUNK_SIZE));
      }

      console.log(
        chalk.gray(
          `      Processing ${pageDataForAI.length} pages in ${chunks.length} chunks...`
        )
      );

      // Process each chunk and collect insights
      const chunkInsights: string[] = [];
      for (let i = 0; i < chunks.length; i++) {
        console.log(
          chalk.cyan(
            `    Analyzing chunk ${i + 1}/${chunks.length} (${chunks[i].length} pages)...`
          )
        );

        const chunkAnalysis = await this.aiService.synthesizeResults(
          query,
          chunks[i]
        );
        chunkInsights.push(chunkAnalysis.answer);

        console.log(
          chalk.green(`   ✓ Chunk ${i + 1}/${chunks.length} complete`)
        );
      }

      // Final synthesis: combine all chunk insights
      console.log(
        chalk.cyan(
          `     Performing final synthesis of ${chunks.length} chunk results...`
        )
      );

      let finalAnalysis;
      if (chunks.length > 1) {
        // Synthesize the chunk insights into a final answer
        const combinedPages = chunkInsights.map((insight, idx) => ({
          url: `chunk-${idx + 1}`,
          title: `Analysis Chunk ${idx + 1}`,
          content: insight,
          relevanceScore: 1.0,
          depth: 0,
        }));
        finalAnalysis = await this.aiService.synthesizeResults(
          query,
          combinedPages
        );
      } else {
        // Single chunk, use its result directly
        finalAnalysis = { answer: chunkInsights[0], confidence: 0.8 };
      }

      const analysis = finalAnalysis;
      console.log(
        chalk.green(
          `   ✓ Final analysis complete (confidence: ${Math.round(analysis.confidence * 100)}%)`
        )
      );

      // Step 6: Save results
      console.log(chalk.yellow("Saving results..."));
      session.endTime = Date.now();
      session.status = "completed";
      session.finalAnswer = analysis.answer;
      session.confidence = analysis.confidence;
      session.totalPages = allPages.length;
      session.metadata.totalLinksFound = allPages.reduce(
        (sum: any, page: any) => sum + (page.links?.length || 0),
        0
      );

      await this.storageService.saveSession(session);
      const name = await this.aiService.generateNamedDescription(query);
      const outputPaths = await this.resultOutputService.saveResults(
        session,
        name,
        allPages
      );

      // Step 7: Display results
      if (this.config.isDebugMode()) {
        console.log(chalk.cyan.bold("\n  Research Results:"));
        console.log(chalk.gray("━".repeat(60)));
        console.log(chalk.white("\n" + analysis.answer));
        console.log(chalk.gray("\n━".repeat(60)));
        console.log(chalk.cyan(` Pages analyzed: ${allPages.length}`));
        console.log(
          chalk.cyan(` Links found: ${session.metadata.totalLinksFound}`)
        );
        console.log(
          chalk.cyan(` Confidence: ${Math.round(analysis.confidence * 100)}%`)
        );
        console.log(
          chalk.cyan(
            `   Time taken: ${Math.round((Date.now() - startTime) / 1000)}s`
          )
        );
      }
      console.log(chalk.green(`\n  Results saved to:`));
      if (outputPaths.htmlPath)
        console.log(chalk.gray(`   • HTML: ${outputPaths.htmlPath}`));
      if (outputPaths.jsonPath)
        console.log(chalk.gray(`   • JSON: ${outputPaths.jsonPath}`));
      if (outputPaths.markdownPath)
        console.log(chalk.gray(`   • Markdown: ${outputPaths.markdownPath}`));
      process.exit(0);
    } catch (error) {
      session.endTime = Date.now();
      session.status = "failed";
      console.error(chalk.red("\n  Research failed:"), error);
      throw error;
    }
  }

  /**
   * Perform deep link crawling on pages with AI-driven decisions
   */
  private async performDeepLinkCrawling(
    initialPages: PageData[],
    query: string,
    globalVisitedUrls: Set<string>,
    linkQualityPrompt: string | null
  ): Promise<PageData[]> {
    const researchConfig = this.config.getResearchConfig();
    const deepPages: PageData[] = [];
    const visitedUrls = globalVisitedUrls; // Use global tracker instead of local
    if (this.debugLogger.isEnabled()) {
      this.debugLogger.log("=== DEEP LINK CRAWLING START ===");
      this.debugLogger.log(`Initial pages: ${initialPages.length}`);
      this.debugLogger.log(`Max depth: ${researchConfig.deepCrawlDepth}`);
      this.debugLogger.log(`AI-driven: ${researchConfig.aiDrivenCrawling}`);
    }

    for (let depth = 1; depth <= researchConfig.deepCrawlDepth; depth++) {
      const pagesToCrawl =
        depth === 1
          ? initialPages
          : deepPages.filter((p) => p.depth === depth - 1);
      console.log(
        chalk.gray(
          `      • Processing ${pagesToCrawl.length} pages from previous depth`
        )
      );

      // Check if AI wants to continue
      if (researchConfig.aiDrivenCrawling && depth > 1) {
        console.log(chalk.cyan(`       AI evaluating whether to continue...`));

        const currentInsights = [...initialPages, ...deepPages]
          .map((p) => p.title)
          .filter(Boolean);

        const aiDecision = await this.aiService.shouldContinueCrawling(
          query,
          depth - 1,
          researchConfig.deepCrawlDepth,
          initialPages.length + deepPages.length,
          currentInsights
        );

        console.log(
          aiDecision.shouldContinue
            ? chalk.green(
                `      ✓ AI decision: CONTINUE to depth ${depth} (${aiDecision.reason})`
              )
            : chalk.red(
                `      ✗ AI decision: STOP at depth ${depth - 1} (${aiDecision.reason})`
              )
        );

        console.log(chalk.gray(`      • Reason: ${aiDecision.reason}`));
        console.log(
          chalk.gray(
            `      • Confidence: ${(aiDecision.confidence * 100).toFixed(0)}%`
          )
        );

        if (!aiDecision.shouldContinue) {
          console.log(
            chalk.yellow(
              `      ⚠️  AI recommends stopping at depth ${depth - 1}`
            )
          );
          break;
        }
      }
      console.log(
        chalk.yellow(`\n    Depth ${depth}/${researchConfig.deepCrawlDepth}:`)
      );

      // Collect all links from current depth pages
      let allLinks: Array<{ url: string; text: string; context?: string }> = [];
      let totalLinksFound = 0;

      for (const page of pagesToCrawl) {
        if (page.links) {
          totalLinksFound += page.links.length;

          const pageLinks = page.links
            .filter((link) => !visitedUrls.has(link.url))
            .map((link) => ({
              url: link.url,
              text: link.text,
              context: link.context,
            }));

          allLinks.push(...pageLinks);
        }
      }

      console.log(chalk.gray(`      • Total links found: ${totalLinksFound}`));
      console.log(
        chalk.gray(`      • New unique URLs available: ${allLinks.length}`)
      );

      if (allLinks.length === 0) {
        console.log(
          chalk.yellow(
            `      • No more links found at depth ${depth}, stopping early`
          )
        );
        break;
      }

      // Step 1: Filter links by quality using AI if custom instructions are available
      if (linkQualityPrompt && allLinks.length > 0) {
        console.log(
          chalk.cyan(
            `      • AI filtering links by quality (${allLinks.length} links)...`
          )
        );

        const filteredLinks = await this.aiService.filterLinksByQuality(
          allLinks,
          linkQualityPrompt,
          query
        );

        console.log(
          chalk.gray(
            `      • Quality filtering: ${allLinks.length} → ${filteredLinks.length} links`
          )
        );
        console.log(
          chalk.gray(
            `      • Removed ${allLinks.length - filteredLinks.length} low-quality links`
          )
        );

        // Update allLinks with filtered results
        allLinks = filteredLinks.map((link) => ({
          url: link.url,
          text: link.text,
          context: link.context,
        }));

        if (allLinks.length === 0) {
          console.log(
            chalk.yellow(
              `      • No quality links remaining at depth ${depth}, stopping early`
            )
          );
          break;
        }
      }

      // Step 2: Use AI to rank links if enabled
      let urlsToCrawl: string[] = allLinks.map((link) => link.url);

      if (researchConfig.aiLinkRanking && allLinks.length > 0) {
        console.log(
          chalk.cyan(
            `      • AI ranking ${Math.min(allLinks.length, 20)} links...`
          )
        );

        // Use only pages from the previous depth for context to avoid recommending similar links
        const currentContext = pagesToCrawl
          .map((p) => p.title + ": " + p.content.substring(0, 200))
          .join(" ");

        const rankedLinks = await this.aiService.rankLinksForCrawling(
          query,
          allLinks,
          currentContext
        );

        console.log(
          chalk.gray(`      • AI ranked ${rankedLinks.length} links`)
        );

        // Take top-ranked links
        urlsToCrawl = rankedLinks
          .slice(0, researchConfig.maxPagesPerDepth)
          .map((l) => l.url);

        if (this.debugLogger.isEnabled() && rankedLinks.length > 0) {
          this.debugLogger.log(`Top AI-ranked links:`);
          rankedLinks.forEach((link, idx) => {
            this.debugLogger.log(
              `  ${idx + 1}. [${link.score.toFixed(2)}] ${link.url}`
            );
            this.debugLogger.log(`     Reason: ${link.reason}`);
          });
        }

        // Show top links in console
        if (rankedLinks.length > 0) {
          console.log(
            chalk.gray(
              `      • Top link score: ${(rankedLinks[0].score * 100).toFixed(0)}% - ${rankedLinks[0].reason}`
            )
          );
        }
      } else {
        // Fallback: use threshold-based filtering
        console.log(
          chalk.gray(
            `      • Using threshold-based filtering (${researchConfig.linkRelevanceThreshold})`
          )
        );

        urlsToCrawl = allLinks
          .slice(0, researchConfig.maxPagesPerDepth)
          .map((link) => link.url);
      }

      // Mark URLs as visited
      urlsToCrawl.forEach((url) => visitedUrls.add(url));

      if (urlsToCrawl.length === 0) {
        console.log(
          chalk.yellow(`      • No links to crawl at depth ${depth}`)
        );
        break;
      }

      console.log(
        chalk.cyan(
          `      • Scraping ${urlsToCrawl.length} pages at depth ${depth}...`
        )
      );

      try {
        const scrapeStartTime = Date.now();

        if (this.debugLogger.isEnabled()) {
          this.debugLogger.log(
            `Starting scrape of ${urlsToCrawl.length} URLs at depth ${depth}:`
          );
          urlsToCrawl.forEach((url, idx) => {
            this.debugLogger.log(`  ${idx + 1}. ${url}`);
          });
        }

        const newPages = await this.webScrapingService.scrapeMultiplePages(
          urlsToCrawl,
          depth
        );
        const scrapeDuration = ((Date.now() - scrapeStartTime) / 1000).toFixed(
          1
        );

        const validNewPages = newPages
          .filter((page: any) => page.content.length > 100)
          .map((page: any) => ({ ...page, depth }));

        const invalidPages = newPages.length - validNewPages.length;

        deepPages.push(...validNewPages);

        console.log(
          chalk.green(
            `      ✓ Depth ${depth} complete: ${validNewPages.length} valid pages in ${scrapeDuration}s`
          )
        );
        if (invalidPages > 0) {
          console.log(
            chalk.yellow(
              `      • Skipped ${invalidPages} pages (content too short)`
            )
          );
        }

        console.log(
          chalk.gray(
            `      • Total deep pages collected so far: ${deepPages.length}`
          )
        );

        if (this.debugLogger.isEnabled()) {
          this.debugLogger.log(
            `Depth ${depth} - Completed in ${scrapeDuration}s`
          );
          this.debugLogger.log(
            `  Scraped: ${validNewPages.length} valid, ${invalidPages} invalid`
          );
        }
      } catch (error) {
        console.warn(chalk.red(`      • Error at depth ${depth}:`), error);
        if (this.debugLogger.isEnabled()) {
          this.debugLogger.log(`Depth ${depth} - Error: ${error}`);
        }
      }
    }

    console.log(
      chalk.green(
        `\n   ✓ Deep crawling complete: ${deepPages.length} additional pages found`
      )
    );

    if (this.debugLogger.isEnabled()) {
      this.debugLogger.log("=== DEEP LINK CRAWLING COMPLETE ===");
      this.debugLogger.log(`Total deep pages: ${deepPages.length}`);
      const depthBreakdown = deepPages.reduce((acc: any, page: any) => {
        acc[page.depth] = (acc[page.depth] || 0) + 1;
        return acc;
      }, {});
      this.debugLogger.log(`Pages by depth: ${JSON.stringify(depthBreakdown)}`);
    }

    return deepPages;
  }

  /**
   * Load custom instructions from custom_instructions.txt
   */
  private loadCustomInstructions(): string | null {
    try {
      const instructionsPath = path.join(
        process.cwd(),
        "custom_instructions.txt"
      );
      if (fs.existsSync(instructionsPath)) {
        return fs.readFileSync(instructionsPath, "utf-8");
      }
      return null;
    } catch (error) {
      return null;
    }
  }
}
