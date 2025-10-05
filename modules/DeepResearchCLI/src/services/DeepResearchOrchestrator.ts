import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";
import { ConfigService } from "./ConfigService";
import { AIMessage, AIService } from "./AIService";
import { SearchService } from "./SearchService";
import { WebScrapingService } from "./WebScrapingService";
import { StorageService } from "./StorageService";
import {
  ResearchSession,
  PageData,
  ExtractedLink,
  UserAction,
  LogEntry,
} from "../types";
import * as fs from "fs";
import * as path from "path";

export interface DeepResearchOptions {
  query: string;
  customInstructions?: string;
  maxDepth?: number;
  maxPagesPerDepth?: number;
  onProgress?: (progress: number, status: string) => void;
  onLogEntry?: (entry: LogEntry) => void;
  onUserActionNeeded?: (question: string) => Promise<string>;
}

export class DeepResearchOrchestrator extends EventEmitter {
  private config: ConfigService;
  private aiService: AIService;
  private searchService: SearchService;
  private webScrapingService: WebScrapingService;
  private storageService: StorageService;
  private currentSession: ResearchSession | null = null;
  private visitedUrls: Set<string> = new Set();
  private allPageData: PageData[] = [];
  private linkQueue: Array<{
    url: string;
    relevance: number;
    depth: number;
    source: string;
  }> = [];
  private isRunning: boolean = false;
  private shouldStop: boolean = false;
  private shouldSkip: boolean = false;
  private userInstructions: string = "";
  private customInstructions: string = "";

  constructor() {
    super();
    this.config = ConfigService.getInstance();

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

    this.storageService = new StorageService(
      researchConfig.dataDirectory,
      researchConfig.historyFile
    );
  }
  async generateNameForSession(query: string): Promise<string> {
    return this.aiService.generateNamedDescription(query)
  }

  async startResearch(options: DeepResearchOptions): Promise<ResearchSession> {
    if (this.isRunning) {
      throw new Error("Research already in progress");
    }

    this.isRunning = true;
    this.shouldStop = false;
    this.shouldSkip = false;
    this.visitedUrls.clear();
    this.allPageData = [];
    this.linkQueue = [];

    const sessionId = uuidv4();
    const config = this.config.getResearchConfig();

    // Get custom instructions from config (already loaded)
    const aiConfig = this.config.getAIConfig();
    this.customInstructions = aiConfig.customInstructions || "";
    if (this.customInstructions) {
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "info",
        message: "Custom research instructions loaded from configuration",
        expandable: false,
      });
    }

    this.currentSession = {
      id: sessionId,
      query: options.query,
      startTime: Date.now(),
      status: "running",
      totalPages: 0,
      maxDepthReached: 0,
      metadata: {
        totalLinksFound: 0,
        errorCount: 0,
        aiTokensUsed: 0,
      },
    };

    await this.storageService.saveSession(this.currentSession);

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `Starting deep research for: "${options.query}"`,
      expandable: false,
    });

    try {
      await this.webScrapingService.initialize();

      // Phase 1: Initial Search
      await this.performInitialSearch(options);

      if (this.shouldStop) {
        return this.finalizeSession("cancelled");
      }

      // Phase 2: Intelligent Deep Research (AI-driven depth control)
      const maxDepth = options.maxDepth || config.maxDepth;
      let currentDepth = 1;

      while (
        currentDepth <= maxDepth &&
        !this.shouldStop &&
        this.linkQueue.length > 0
      ) {
        await this.processDepthLevel(currentDepth, options);

        if (this.shouldStop) break;

        // AI-driven decision: Should we continue deeper?
        const shouldContinue = await this.aiDecideContinueResearch(
          currentDepth,
          options
        );

        if (!shouldContinue.continue) {
          this.emitLogEntry({
            timestamp: Date.now(),
            type: "info",
            message: `AI Decision: Stopping research at depth ${currentDepth}`,
            expandable: true,
            expanded: false,
            children: [
              {
                timestamp: Date.now(),
                type: "info",
                message: `Reason: ${shouldContinue.reason}`,
              },
              {
                timestamp: Date.now(),
                type: "info",
                message: `Confidence: ${(shouldContinue.confidence * 100).toFixed(1)}%`,
              },
              {
                timestamp: Date.now(),
                type: "info",
                message: `Information Quality: ${shouldContinue.informationQuality}`,
              },
            ],
          });
          break;
        }

        this.emitLogEntry({
          timestamp: Date.now(),
          type: "info",
          message: `🤖 AI Decision: Continue to depth ${currentDepth + 1} (${shouldContinue.reason})`,
        });

        currentDepth++;

        // Optional user guidance
        // if (options.onUserActionNeeded && Math.random() < 0.2) { // 20% chance to ask for guidance
        //   const question = `Research has reached depth ${currentDepth - 1}. Found ${this.linkQueue.length} potential links. Any specific direction you'd like me to focus on?`;
        //   this.userInstructions = await options.onUserActionNeeded(question);

        //   if (this.userInstructions.toLowerCase().includes('stop') || this.userInstructions.toLowerCase().includes('cancel')) {
        //     this.shouldStop = true;
        //     break;
        //   }
        // }
      }

      if (this.shouldStop) {
        return this.finalizeSession("cancelled");
      }

      // Phase 3: Final Analysis and Synthesis
      await this.performFinalAnalysis(options);

      return this.finalizeSession("completed");
    } catch (error) {
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "error",
        message: `Research failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      });

      this.currentSession!.metadata.errorCount++;
      return this.finalizeSession("failed");
    } finally {
      await this.webScrapingService.dispose();
      this.isRunning = false;
    }
  }

  private async performInitialSearch(
    options: DeepResearchOptions
  ): Promise<void> {
    this.emitLogEntry({
      timestamp: Date.now(),
      type: "search",
      message: `Search → "${options.query}"`,
      expandable: true,
      expanded: false,
      children: [],
    });

    options.onProgress?.(10, "Generating search strategies...");

    // Generate multiple search queries using AI
    const searchQueries = await this.aiService.generateSearchQueries(
      options.query,
      0
    );

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `├── Generated ${searchQueries.length} search strategies`,
      children: searchQueries.map((query) => ({
        timestamp: Date.now(),
        type: "info",
        message: `    └── "${query}"`,
      })),
    });

    options.onProgress?.(20, "Performing web searches...");

    // Perform searches
    const searchResults = await this.searchService.searchMultipleQueries(
      searchQueries,
      {
        maxResultsPerQuery:
          this.config.getResearchConfig().searchResultsPerQuery || 15,
      }
    );

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `├── Found ${searchResults.length} initial search results`,
      expandable: true,
      expanded: false,
      children: searchResults.slice(0, 5).map((result) => ({
        timestamp: Date.now(),
        type: "info",
        message: `    └── ${result.title} (${result.engine})`,
      })),
    });

    options.onProgress?.(30, "Processing search result pages...");

    // Process search result pages to extract additional links
    const extractedLinks = await this.extractLinksFromSearchResults(
      searchResults,
      options.query
    );

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `├── Extracted ${extractedLinks.length} links from search result pages`,
      expandable: true,
      expanded: false,
      children: extractedLinks.slice(0, 5).map((link) => ({
        timestamp: Date.now(),
        type: "info",
        message: `    └── ${link.url} (relevance: ${(link.relevance * 100).toFixed(1)}%)`,
      })),
    });

    // Add search results and extracted links to queue
    for (const result of searchResults) {
      this.linkQueue.push({
        url: result.url,
        relevance: result.score,
        depth: 1,
        source: "search_result",
      });
    }

    for (const link of extractedLinks) {
      this.linkQueue.push({
        url: link.url,
        relevance: link.relevance,
        depth: 1,
        source: "extracted_link",
      });
    }

    this.currentSession!.metadata.totalLinksFound +=
      searchResults.length + extractedLinks.length;

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `└── Total ${this.linkQueue.length} links queued for processing`,
    });
  }

  private async processDepthLevel(
    depth: number,
    options: DeepResearchOptions
  ): Promise<void> {
    const config = this.config.getResearchConfig();
    const linksForThisDepth = this.linkQueue
      .filter((link) => link.depth === depth)
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, options.maxPagesPerDepth || config.maxPagesPerDepth);

    if (linksForThisDepth.length === 0) {
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "info",
        message: `No links available for depth ${depth}`,
      });
      return;
    }

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "info",
      message: `Processing depth level ${depth} (${linksForThisDepth.length} pages)`,
      expandable: true,
      expanded: true,
      children: [],
    });

    this.currentSession!.maxDepthReached = depth;

    const totalPages = linksForThisDepth.length;
    let processedPages = 0;

    // Process pages in batches
    const batchSize = config.maxConcurrentPages;
    for (let i = 0; i < linksForThisDepth.length; i += batchSize) {
      if (this.shouldStop) break;

      const batch = linksForThisDepth.slice(i, i + batchSize);
      const batchPromises = batch.map((link) =>
        this.processPage(link, depth, options)
      );

      const results = await Promise.allSettled(batchPromises);

      for (let j = 0; j < results.length; j++) {
        processedPages++;
        const progress =
          30 + (depth / 5) * 40 + (processedPages / totalPages) * 20;
        options.onProgress?.(
          progress,
          `Processing page ${processedPages}/${totalPages} at depth ${depth}`
        );

        if (this.shouldSkip) {
          this.shouldSkip = false;
          this.emitLogEntry({
            timestamp: Date.now(),
            type: "info",
            message: `├── Skipping remaining pages at depth ${depth} (user requested)`,
          });
          return;
        }
      }

      // Small delay between batches to avoid overwhelming servers
      await new Promise((resolve) =>
        setTimeout(resolve, 1000 + Math.random() * 2000)
      );
    }

    await this.storageService.saveSession(this.currentSession!);
  }

  private async processPage(
    link: { url: string; relevance: number; depth: number; source: string },
    depth: number,
    options: DeepResearchOptions
  ): Promise<void> {
    if (this.visitedUrls.has(link.url)) {
      return;
    }

    this.visitedUrls.add(link.url);

    this.emitLogEntry({
      timestamp: Date.now(),
      type: "fetch",
      message: `├── Fetching: ${this.truncateUrl(link.url)}`,
      url: link.url,
    });

    try {
      // Scrape the page
      const pageData = await this.webScrapingService.scrapePage(
        link.url,
        depth
      );

      if (pageData.error) {
        throw new Error(pageData.error);
      }

      this.emitLogEntry({
        timestamp: Date.now(),
        type: "process",
        message: `    ├── Processing content (${pageData.content.length} chars)`,
        url: link.url,
      });

      // Score relevance using AI
      const relevanceScore = await this.aiService.scoreRelevance(
        options.query,
        pageData.content
      );
      pageData.relevanceScore = relevanceScore;

      // Process and summarize content following custom instructions
      const processedPageData = await this.processPageContent(
        pageData,
        options.query
      );

      // Extract key insights from processed content
      const insights = await this.aiService.extractKeyInsights(
        processedPageData.content,
        options.query
      );

      this.emitLogEntry({
        timestamp: Date.now(),
        type: "analysis",
        message: `    ├── Relevance: ${(relevanceScore * 100).toFixed(1)}% | Insights: ${insights.length} | Processed: ✓`,
        url: link.url,
      });

      // Only proceed with high-relevance content
      const config = this.config.getResearchConfig();
      if (relevanceScore >= config.linkRelevanceThreshold) {
        this.allPageData.push(processedPageData);
        this.currentSession!.totalPages++;

        // Add new links for next depth level with enhanced strategy
        if (depth < 7) {
          // Increased max depth for deeper research
          const scoredLinks = await this.scoreLinksForRelevance(
            pageData.links,
            options.query
          );

          // Adaptive link selection based on depth and content quality
          let linkLimit = this.calculateLinkLimitForDepth(
            depth,
            processedPageData.relevanceScore
          );
          let relevanceThreshold =
            this.calculateRelevanceThresholdForDepth(depth);

          const nextDepthLinks = scoredLinks
            .filter((link) => link.relevanceScore >= relevanceThreshold)
            .slice(0, linkLimit);

          // Priority links get added immediately, others get queued with lower priority
          const priorityLinks = nextDepthLinks.filter(
            (link) => link.relevanceScore >= 0.8
          );
          const standardLinks = nextDepthLinks.filter(
            (link) => link.relevanceScore < 0.8
          );

          // Add priority links first
          for (const newLink of priorityLinks) {
            if (!this.visitedUrls.has(newLink.url)) {
              this.linkQueue.unshift({
                // Add to front of queue
                url: newLink.url,
                relevance: newLink.relevanceScore,
                depth: depth + 1,
                source: `${link.url} (priority)`,
              });
            }
          }

          // Add standard links
          for (const newLink of standardLinks) {
            if (!this.visitedUrls.has(newLink.url)) {
              this.linkQueue.push({
                url: newLink.url,
                relevance: newLink.relevanceScore,
                depth: depth + 1,
                source: link.url,
              });
            }
          }

          this.emitLogEntry({
            timestamp: Date.now(),
            type: "info",
            message: `    └── Found ${nextDepthLinks.length} links for depth ${depth + 1} (${priorityLinks.length} priority, ${standardLinks.length} standard)`,
            url: link.url,
          });

          this.currentSession!.metadata.totalLinksFound +=
            nextDepthLinks.length;
        }

        // Save page data
        await this.storageService.savePageData(
          this.currentSession!.id,
          pageData
        );
      } else {
        this.emitLogEntry({
          timestamp: Date.now(),
          type: "info",
          message: `    └── Skipped (low relevance: ${(relevanceScore * 100).toFixed(1)}%)`,
          url: link.url,
        });
      }
    } catch (error) {
      this.currentSession!.metadata.errorCount++;
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "error",
        message: `    └── Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        url: link.url,
      });
    }
  }

  private async scoreLinksForRelevance(
    links: ExtractedLink[],
    query: string
  ): Promise<ExtractedLink[]> {
    // Use AI to score link relevance in batches
    const batchSize = 10;
    const scoredLinks: ExtractedLink[] = [];

    for (let i = 0; i < links.length; i += batchSize) {
      const batch = links.slice(i, i + batchSize);
      const promises = batch.map(async (link) => {
        try {
          const score = await this.aiService.scoreRelevance(
            query,
            `${link.text} ${link.context || ""}`
          );
          return { ...link, relevanceScore: score };
        } catch (error) {
          return { ...link, relevanceScore: 0.5 };
        }
      });

      const results = await Promise.allSettled(promises);
      for (const result of results) {
        if (result.status === "fulfilled") {
          scoredLinks.push(result.value);
        }
      }
    }

    return scoredLinks.sort((a, b) => b.relevanceScore - a.relevanceScore);
  }

  private async performFinalAnalysis(
    options: DeepResearchOptions
  ): Promise<void> {
    this.emitLogEntry({
      timestamp: Date.now(),
      type: "analysis",
      message: "Synthesizing research findings...",
      expandable: false,
    });

    options.onProgress?.(90, "Generating comprehensive analysis...");

    try {
      // Create a comprehensive analysis prompt that incorporates custom instructions
      const finalAnalysisPrompt = this.createFinalAnalysisPrompt(options.query);

      // Get high-quality filtered content
      const highQualityContent = this.allPageData.filter(
        (page) => page.relevanceScore >= 0.6
      );

      this.emitLogEntry({
        timestamp: Date.now(),
        type: "info",
        message: `Processing ${highQualityContent.length} high-quality sources for final analysis`,
      });

      // let synthesis = {
      //   answer: '',
      //   summary: '',
      //   confidence: 0
      // };
      // If we have custom instructions, also generate a specialized response
      // if (this.customInstructions) {
      //   const specializedResponse = await this.aiService.generateResponse(
      //     `${finalAnalysisPrompt}\n\nBased on the research data, provide a response that follows these instructions:\n${this.customInstructions}`,
      //     { temperature: 0.3, maxTokens: 4096 }
      //   );

      //   synthesis.answer = specializedResponse || synthesis.answer;

      // }else{
      const synthesis = await this.aiService.synthesizeResults(
        options.query,
        highQualityContent
      );
      // }

      this.currentSession!.finalAnswer = synthesis.answer;
      this.currentSession!.confidence = synthesis.confidence;

      // Save final analysis
      await this.storageService.saveFinalAnswer(
        this.currentSession!.id,
        synthesis.answer,
        synthesis.summary,
        synthesis.confidence
      );

      this.emitLogEntry({
        timestamp: Date.now(),
        type: "info",
        message: `Analysis complete (confidence: ${(synthesis.confidence * 100).toFixed(1)}%) | Custom instructions: ${this.customInstructions ? "✓" : "✗"}`,
      });

      options.onProgress?.(100, "Research completed successfully");
    } catch (error) {
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "error",
        message: `Failed to generate final analysis: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
      throw error;
    }
  }

  private async extractLinksFromSearchResults(
    searchResults: any[],
    query: string
  ): Promise<Array<{ url: string; relevance: number }>> {
    const extractedLinks: Array<{ url: string; relevance: number }> = [];
    const seenUrls = new Set<string>();

    // Process a subset of search results to extract links
    const resultsToProcess = searchResults.slice(0, 5); // Process first 5 search results

    for (const result of resultsToProcess) {
      try {
        // Scrape the search result page to extract links
        const pageData = await this.webScrapingService.scrapePage(
          result.url,
          0
        );

        if (pageData.links && pageData.links.length > 0) {
          // Score and filter links for relevance
          const scoredLinks = await this.scoreLinksForRelevance(
            pageData.links,
            query
          );

          // Take top relevant links
          const topLinks = scoredLinks
            .filter((link) => link.relevanceScore >= 0.4) // Higher threshold for extracted links
            .slice(0, 8) // Limit per page
            .filter((link) => !seenUrls.has(link.url));

          for (const link of topLinks) {
            seenUrls.add(link.url);
            extractedLinks.push({
              url: link.url,
              relevance: link.relevanceScore,
            });
          }
        }
      } catch (error) {
        this.emitLogEntry({
          timestamp: Date.now(),
          type: "warning",
          message: `Failed to extract links from ${result.url}: ${error instanceof Error ? error.message : "Unknown error"}`,
        });
      }
    }

    return extractedLinks;
  }

  private async aiDecideContinueResearch(
    currentDepth: number,
    options: DeepResearchOptions
  ): Promise<{
    continue: boolean;
    reason: string;
    confidence: number;
    informationQuality: string;
  }> {
    try {
      // Assess information completeness first
      const completenessAssessment = await this.assessInformationCompleteness(
        options.query
      );

      // Analyze current information state

      const pendingLinks = this.linkQueue.filter(
        (link) => link.depth > currentDepth
      ).length;
      const highQualityLinks = this.linkQueue.filter(
        (link) => link.depth > currentDepth && link.relevance >= 0.7
      ).length;

      const systemPrompt = `
You are an AI research coordinator. 
Analyze the current research state and decide whether to continue deeper research.
`;

      const currentKnowledge: AIMessage[] = this.allPageData
        .filter((page) => page.relevanceScore >= 0.5)
        .map((page, index) => ({
          role: "user",
          content: `[source: ${index}] ${page.title}: ${page.content}`,
        }));

      const messages: AIMessage[] = [
        { role: "system", content: systemPrompt },
        {
          role: "user",
          content: `${this.customInstructions ? `\nResearch Instructions:\n${this.customInstructions}` : ""}`,
        },
        {
          role: "assistant",
          content: `
          Research Query: "${options.query}"
Current Depth: ${currentDepth}
Pages Processed: ${this.allPageData.length}
High-Quality Sources: ${this.allPageData.filter((p) => p.relevanceScore >= 0.7).length}
Pending Links: ${pendingLinks} (${highQualityLinks} high-quality)

Information Completeness Assessment:
- Completeness Score: ${(completenessAssessment.completeness * 100).toFixed(1)}%
- Missing Aspects: ${completenessAssessment.missingAspects.join(", ")}
- AI Recommendation: ${completenessAssessment.recommendation}

Decision Factors:
1. Information completeness (current: ${(completenessAssessment.completeness * 100).toFixed(1)}%)
2. Quality of sources found (${this.allPageData.filter((p) => p.relevanceScore >= 0.7).length} high-quality)
3. Potential value of deeper research (${highQualityLinks} high-quality pending links)
4. Risk of diminishing returns (current depth: ${currentDepth})
5. Custom instruction requirements
`,
        },
        ...currentKnowledge,
        {
          role: "user",
          content: `
Respond with JSON:
{
  "continue": boolean,
  "reason": "Brief explanation for decision",
  "confidence": 0.0-1.0,
  "informationQuality": "poor|fair|good|excellent"
}

Decision criteria:
- STOP if completeness >85% or no high-quality pending links
- CONTINUE if completeness <70% and high-quality links available
- Consider custom instructions requirements for specific output format
`,
        },
      ];
      const response = await this.aiService.generateText(messages, {
        temperature: 0.2,
        maxTokens: 400,
      });
      // const response = await this.aiService.generateResponse(decisionPrompt, {
      //   temperature: 0.2,
      //   maxTokens: 400
      // });

      // Clean JSON response manually
      let cleanedResponse = response.content.trim();
      if (cleanedResponse.includes("```")) {
        cleanedResponse = cleanedResponse
          .replace(/```json\s*\n?/gi, "")
          .replace(/```\s*$/g, "");
      }

      const decision = JSON.parse(cleanedResponse);

      // Apply some safety logic
      let shouldContinue = decision.continue || false;

      // Force stop conditions
      if (currentDepth >= 6 || completenessAssessment.completeness >= 0.9) {
        shouldContinue = false;
      }

      // Force continue conditions
      if (
        currentDepth <= 2 &&
        this.allPageData.length < 5 &&
        pendingLinks > 0
      ) {
        shouldContinue = true;
      }

      return {
        continue: shouldContinue,
        reason: decision.reason || "No reason provided",
        confidence: Math.max(0, Math.min(1, decision.confidence || 0.5)),
        informationQuality: decision.informationQuality || "unknown",
      };
    } catch (error) {
      // Enhanced fallback decision logic
      const hasGoodQualitySources =
        this.allPageData.filter((p) => p.relevanceScore >= 0.7).length >= 3;
      const hasEnoughSources = this.allPageData.length >= 8;
      const pendingLinks = this.linkQueue.filter(
        (link) => link.depth > currentDepth
      ).length;

      const shouldContinue =
        !hasGoodQualitySources &&
        !hasEnoughSources &&
        currentDepth < 5 &&
        pendingLinks > 0;

      return {
        continue: shouldContinue,
        reason: `Fallback decision: ${hasGoodQualitySources ? "sufficient quality sources" : hasEnoughSources ? "sufficient total sources" : "more research needed"}`,
        confidence: 0.6,
        informationQuality: hasGoodQualitySources ? "good" : "fair",
      };
    }
  }

  private calculateLinkLimitForDepth(
    depth: number,
    pageRelevance: number
  ): number {
    // Higher quality pages get more links extracted
    const baseLimit = Math.max(3, 8 - depth); // Decreasing limit with depth
    const qualityMultiplier =
      pageRelevance >= 0.8 ? 1.5 : pageRelevance >= 0.6 ? 1.2 : 1.0;
    return Math.floor(baseLimit * qualityMultiplier);
  }

  private calculateRelevanceThresholdForDepth(depth: number): number {
    // Higher threshold for deeper levels to maintain quality
    const baseThreshold = 0.3;
    const depthPenalty = (depth - 1) * 0.1;
    return Math.min(0.8, baseThreshold + depthPenalty);
  }

  private async assessInformationCompleteness(query: string): Promise<{
    completeness: number;
    missingAspects: string[];
    recommendation: "continue" | "stop" | "refocus";
  }> {
    try {
      const systemPrompt = `
Analyze the information completeness for this research query.

Query: "${query}"
${this.customInstructions ? `\nRequired Output Format:\n${this.customInstructions}...` : ""}

Assess:
1. How complete is the information for the query?
2. What key aspects are still missing?
3. Should research continue, stop, or change focus?

Current Knowledge Base will be provided in the user messages.
`;
      const knowledgeBase: AIMessage[] = this.allPageData
        .filter((page) => page.relevanceScore >= 0.5)
        .map((page) => ({ role: "user", content: page.content }));
      const Messages: AIMessage[] = [
        {
          role: "system",
          content: systemPrompt,
        },
        ...knowledgeBase,
        {
          role: "user",
          content: `
Respond with JSON:
{
  "completeness": 0.0-1.0,
  "missingAspects": ["aspect1", "aspect2"],
  "recommendation": "continue|stop|refocus"
}
`,
        },
      ];

      const response = await this.aiService.generateText(Messages, {
        temperature: 0.3,
        maxTokens: 400,
      });

      // const response = await this.aiService.generateResponse(assessmentPrompt, {
      //   temperature: 0.3,
      //   maxTokens: 400,
      // });

      let cleanedResponse = response.content.trim();
      if (cleanedResponse.includes("```")) {
        cleanedResponse = cleanedResponse
          .replace(/```json\s*\n?/gi, "")
          .replace(/```\s*$/g, "");
      }

      const assessment = JSON.parse(cleanedResponse);

      return {
        completeness: Math.max(0, Math.min(1, assessment.completeness || 0.5)),
        missingAspects: Array.isArray(assessment.missingAspects)
          ? assessment.missingAspects
          : [],
        recommendation: ["continue", "stop", "refocus"].includes(
          assessment.recommendation
        )
          ? assessment.recommendation
          : "continue",
      };
    } catch (error) {
      return {
        completeness: this.allPageData.length >= 5 ? 0.7 : 0.4,
        missingAspects: ["Unable to assess missing aspects"],
        recommendation: this.allPageData.length >= 10 ? "stop" : "continue",
      };
    }
  }

  private createFinalAnalysisPrompt(query: string): string {
    const contentSummary = this.allPageData
      .filter((page) => page.relevanceScore >= 0.6)
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, 20)
      .map(
        (item, index) =>
          `[${index + 1}] ${item.title} (Relevance: ${item.relevanceScore.toFixed(2)})\nURL: ${item.url}\nContent: ${item.content.substring(0, 1000)}...`
      )
      .join("\n\n---\n\n");

    return `Research Query: "${query}"\n\nCollected and processed data from ${this.allPageData.length} sources:\n\n${contentSummary}`;
  }

  private async finalizeSession(
    status: "completed" | "cancelled" | "failed"
  ): Promise<ResearchSession> {
    this.currentSession!.status = status;
    this.currentSession!.endTime = Date.now();

    await this.storageService.saveSession(this.currentSession!);
    await this.storageService.addToHistory(this.currentSession!);

    this.emitLogEntry({
      timestamp: Date.now(),
      type: status === "completed" ? "info" : "error",
      message: `Research ${status} (${this.currentSession!.totalPages} pages processed)`,
    });

    return this.currentSession!;
  }

  // User interaction methods
  public stop(): void {
    this.shouldStop = true;
  }

  public skip(): void {
    this.shouldSkip = true;
  }

  public provideGuidance(guidance: string): void {
    this.userInstructions = guidance;
  }

  // Utility methods
  private emitLogEntry(entry: LogEntry): void {
    this.emit("logEntry", entry);
  }

  private truncateUrl(url: string, maxLength: number = 60): string {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength - 3) + "...";
  }

  private async processPageContent(
    pageData: PageData,
    query: string
  ): Promise<PageData> {
    try {
      // Create a comprehensive summary following custom instructions
      const summaryPrompt = this.createSummaryPrompt(pageData.content, query);

      const summary = await this.aiService.generateResponse(summaryPrompt);

      // Update page data with processed content
      pageData.aiContent = summary;
      pageData.content = pageData.content;
      pageData.processingTime = Date.now();

      return pageData;
    } catch (error) {
      this.emitLogEntry({
        timestamp: Date.now(),
        type: "warning",
        message: `Content processing failed for ${pageData.url}: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
      return pageData;
    }
  }

  private createSummaryPrompt(content: string, query: string): string {
    const basePrompt = `
You are a web search summarizer, tasked with summarizing content retrieved from web search. Your job is to summarize the
text into a detailed, 2-4 paragraph explanation that captures the main ideas and provides a comprehensive answer to the query.

- **Journalistic tone**: The summary should sound professional and journalistic, not too casual or vague.
- **Thorough and detailed**: Ensure that every key point from the text is captured and that the summary directly answers the query.
- **Not too lengthy, but detailed**: The summary should be informative but not excessively long. Focus on providing detailed information in a concise format.

Query: ${query}

Content to summarize:
${content}

${this.customInstructions ? `\nAdditional Instructions:\n${this.customInstructions}` : ""}

Please provide a comprehensive summary that directly addresses the query and follows the above guidelines.`;

    return basePrompt;
  }

  // Getters
  public getCurrentSession(): ResearchSession | null {
    return this.currentSession;
  }

  public isResearchRunning(): boolean {
    return this.isRunning;
  }

  public getVisitedUrls(): string[] {
    return Array.from(this.visitedUrls);
  }

  public getAllPageData(): PageData[] {
    return [...this.allPageData];
  }
}
