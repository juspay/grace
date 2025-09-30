import chalk from 'chalk';
import { ConfigService } from './ConfigService';
import { AIService } from './AIService';
import { SearchService } from './SearchService';
import { WebScrapingService } from './WebScrapingService';
import { ResultOutputService } from './ResultOutputService';
import { StorageService } from './StorageService';
import { ResearchSession, PageData, ExtractedLink } from '../types';
import { v4 as uuidv4 } from 'uuid';

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

  constructor() {
    this.config = ConfigService.getInstance();

    const aiConfig = this.config.getAIConfig();
    this.aiService = new AIService(aiConfig);

    this.searchService = new SearchService(process.env.SEARXNG_BASE_URL);

    const researchConfig = this.config.getResearchConfig();
    const proxies = process.env.PROXY_LIST ? process.env.PROXY_LIST.split(',') : [];
    this.webScrapingService = new WebScrapingService({
      maxConcurrentPages: researchConfig.maxConcurrentPages,
      timeout: researchConfig.timeoutPerPage,
      respectRobotsTxt: researchConfig.respectRobotsTxt,
      proxies
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
    console.log(chalk.cyan.bold(`\n🔍 Starting Direct Research: "${query}"`));
    console.log(chalk.gray('━'.repeat(60)));

    const startTime = Date.now();
    const session: ResearchSession = {
      id: uuidv4(),
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

    try {
      // Step 1: Generate search queries
      console.log(chalk.yellow('📋 Step 1: Generating search queries...'));
      const searchQueries = await this.aiService.generateSearchQueries(query, 0);
      console.log(chalk.green(`   ✓ Generated ${searchQueries.length} search queries`));

      // Step 2: Perform searches
      console.log(chalk.yellow('🔍 Step 2: Performing web searches...'));
      const allSearchResults = [];
      for (const searchQuery of searchQueries) {
        console.log(chalk.gray(`   • Searching: "${searchQuery}"`));
        const results = await this.searchService.search(searchQuery);
        allSearchResults.push(...results);
      }
      console.log(chalk.green(`   ✓ Found ${allSearchResults.length} search results`));

      // Step 3: Initial page crawling
      console.log(chalk.yellow('📄 Step 3: Crawling initial pages...'));
      const researchConfig = this.config.getResearchConfig();
      const initialUrls = allSearchResults
        .slice(0, researchConfig.maxPagesPerDepth)
        .map(result => result.url);

      const initialPages = await this.webScrapingService.scrapeMultiplePages(initialUrls);
      const validPages = initialPages.filter((page: any) => page.content.length > 100);
      console.log(chalk.green(`   ✓ Successfully crawled ${validPages.length} pages`));

      // Step 4: Deep link crawling (if enabled)
      let allPages = validPages;
      if (researchConfig.enableDeepLinkCrawling) {
        console.log(chalk.yellow('🔗 Step 4: Deep link crawling...'));
        const deepPages = await this.performDeepLinkCrawling(validPages);
        allPages = [...validPages, ...deepPages];
        console.log(chalk.green(`   ✓ Found ${deepPages.length} additional pages through deep crawling`));
      } else {
        console.log(chalk.gray('   • Deep link crawling disabled'));
      }

      // Step 5: AI Analysis
      console.log(chalk.yellow('🤖 Step 5: AI analysis and synthesis...'));
      const pageDataForAI = allPages.map((page: any) => ({
        url: page.url,
        title: page.title,
        content: page.content.substring(0, 4000), // Limit content for AI
        relevanceScore: page.relevanceScore || 0.5,
        depth: page.depth || 0
      }));

      const analysis = await this.aiService.synthesizeResults(query, pageDataForAI);
      console.log(chalk.green(`   ✓ Analysis complete (confidence: ${Math.round(analysis.confidence * 100)}%)`));

      // Step 6: Save results
      console.log(chalk.yellow('💾 Step 6: Saving results...'));
      session.endTime = Date.now();
      session.status = 'completed';
      session.finalAnswer = analysis.answer;
      session.confidence = analysis.confidence;
      session.totalPages = allPages.length;
      session.metadata.totalLinksFound = allPages.reduce((sum: any, page: any) => sum + (page.links?.length || 0), 0);

      await this.storageService.saveSession(session);
      const outputPaths = await this.resultOutputService.saveResults(session, allPages);

      console.log(chalk.green('   ✓ Results saved'));

      // Step 7: Display results
      console.log(chalk.cyan.bold('\n📊 Research Results:'));
      console.log(chalk.gray('━'.repeat(60)));
      console.log(chalk.white('\n' + analysis.answer));
      console.log(chalk.gray('\n━'.repeat(60)));
      console.log(chalk.cyan(`📄 Pages analyzed: ${allPages.length}`));
      console.log(chalk.cyan(`🔗 Links found: ${session.metadata.totalLinksFound}`));
      console.log(chalk.cyan(`🎯 Confidence: ${Math.round(analysis.confidence * 100)}%`));
      console.log(chalk.cyan(`⏱️  Time taken: ${Math.round((Date.now() - startTime) / 1000)}s`));
      console.log(chalk.green(`\n💾 Results saved to:`));
      console.log(chalk.gray(`   • HTML: ${outputPaths.htmlPath}`));
      console.log(chalk.gray(`   • JSON: ${outputPaths.jsonPath}`));
      console.log(chalk.gray(`   • Markdown: ${outputPaths.markdownPath}`));

    } catch (error) {
      session.endTime = Date.now();
      session.status = 'failed';
      console.error(chalk.red('\n❌ Research failed:'), error);
      throw error;
    }
  }

  /**
   * Perform deep link crawling on pages
   */
  private async performDeepLinkCrawling(initialPages: PageData[]): Promise<PageData[]> {
    const researchConfig = this.config.getResearchConfig();
    const deepPages: PageData[] = [];
    const visitedUrls = new Set(initialPages.map(page => page.url));

    for (let depth = 1; depth <= researchConfig.deepCrawlDepth; depth++) {
      console.log(chalk.gray(`   • Crawling depth ${depth}...`));

      const pagesToCrawl = depth === 1 ? initialPages : deepPages.filter(p => p.depth === depth - 1);
      const urlsToCrawl: string[] = [];

      // Extract links from pages at current depth
      for (const page of pagesToCrawl) {
        if (page.links) {
          const relevantLinks = page.links
            .filter(link => link.relevanceScore > researchConfig.linkRelevanceThreshold)
            .slice(0, researchConfig.maxLinksPerPage)
            .map(link => link.url)
            .filter(url => !visitedUrls.has(url));

          urlsToCrawl.push(...relevantLinks);
          relevantLinks.forEach(url => visitedUrls.add(url));
        }
      }

      if (urlsToCrawl.length === 0) {
        console.log(chalk.gray(`   • No more relevant links found at depth ${depth}`));
        break;
      }

      // Limit URLs per depth
      const limitedUrls = urlsToCrawl.slice(0, researchConfig.maxPagesPerDepth);
      console.log(chalk.gray(`   • Crawling ${limitedUrls.length} URLs at depth ${depth}`));

      try {
        const newPages = await this.webScrapingService.scrapeMultiplePages(limitedUrls);
        const validNewPages = newPages
          .filter((page: any) => page.content.length > 100)
          .map((page: any) => ({ ...page, depth }));

        deepPages.push(...validNewPages);
        console.log(chalk.gray(`   • Found ${validNewPages.length} valid pages at depth ${depth}`));

      } catch (error) {
        console.warn(chalk.yellow(`   ⚠️  Error crawling depth ${depth}:`, error));
      }
    }

    return deepPages;
  }
}