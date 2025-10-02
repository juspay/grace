import { chromium, Browser, Page, BrowserContext } from 'playwright';
import { AIService } from './AIService';
import { ConfigService } from './ConfigService';
import { PageData, ExtractedLink } from '../types';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface BrowserAction {
  type: 'click' | 'scroll' | 'wait' | 'extract' | 'screenshot' | 'navigate';
  selector?: string;
  coordinates?: { x: number; y: number };
  direction?: 'up' | 'down' | 'left' | 'right';
  pixels?: number;
  duration?: number;
  url?: string;
  reason: string;
}

export interface VisualAnalysis {
  hasInteractiveElements: boolean;
  isSPA: boolean;
  hasAccordions: boolean;
  hasDropdowns: boolean;
  hasInfiniteScroll: boolean;
  hasLoadMoreButtons: boolean;
  hiddenContentDetected: boolean;
  suggestedActions: BrowserAction[];
  reasoning: string;
  confidence: number;
}

export interface BrowserConfig {
  headless: boolean;
  recordingEnabled: boolean;
  screenshotAnalysisEnabled: boolean;
  maxNavigationAttempts: number;
  respectRobotsTxt: boolean;
  viewportWidth: number;
  viewportHeight: number;
  navigationTimeout: number;
}

/**
 * AI-Powered Visual Browser Service
 *
 * This service uses AI to visually analyze websites and intelligently navigate
 * interactive elements like accordions, dropdowns, SPAs, and dynamic content.
 * It takes screenshots, analyzes them with AI, and performs human-like actions.
 */
export class AIBrowserService {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private currentPage: Page | null = null;
  private aiService: AIService;
  private config: ConfigService;
  private browserConfig: BrowserConfig;
  private recordingDir: string = '';
  private screenshotDir: string = '';
  private isRecording: boolean = false;
  private recordingFrame: number = 0;

  constructor(aiService: AIService) {
    this.aiService = aiService;
    this.config = ConfigService.getInstance();
    this.browserConfig = this.loadBrowserConfig();

    if (this.browserConfig.recordingEnabled) {
      this.recordingDir = path.join(process.cwd(), 'temp', 'recordings', this.generateSessionId());
      this.ensureDirectory(this.recordingDir);
    }

    this.screenshotDir = path.join(process.cwd(), 'temp', 'screenshots', this.generateSessionId());
    this.ensureDirectory(this.screenshotDir);
  }

  private loadBrowserConfig(): BrowserConfig {
    return {
      headless: process.env.AI_BROWSER_HEADLESS !== 'false',
      recordingEnabled: process.env.AI_BROWSER_RECORDING === 'true',
      screenshotAnalysisEnabled: process.env.AI_BROWSER_SCREENSHOTS === 'true',
      maxNavigationAttempts: parseInt(process.env.AI_BROWSER_MAX_ATTEMPTS || '3'),
      respectRobotsTxt: false, // Default false for browser mode (as requested)
      viewportWidth: parseInt(process.env.AI_BROWSER_WIDTH || '1920'),
      viewportHeight: parseInt(process.env.AI_BROWSER_HEIGHT || '1080'),
      navigationTimeout: parseInt(process.env.AI_BROWSER_TIMEOUT || '30000')
    };
  }

  private ensureDirectory(dir: string): void {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  async initialize(): Promise<void> {
    if (this.browser) return;

    const launchOptions: any = {
      headless: this.browserConfig.headless,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-blink-features=AutomationControlled',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-extensions',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        `--window-size=${this.browserConfig.viewportWidth},${this.browserConfig.viewportHeight}`
      ]
    };

    // Enable devtools for non-headless mode for debugging
    if (!this.browserConfig.headless) {
      launchOptions.devtools = true;
    }

    this.browser = await chromium.launch(launchOptions);

    const contextOptions: any = {
      viewport: {
        width: this.browserConfig.viewportWidth,
        height: this.browserConfig.viewportHeight
      },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    };

    // Enable video recording if configured
    if (this.browserConfig.recordingEnabled) {
      contextOptions.recordVideo = {
        dir: this.recordingDir,
        size: { width: this.browserConfig.viewportWidth, height: this.browserConfig.viewportHeight }
      };
    }

    this.context = await this.browser.newContext(contextOptions);

    // Enable recording if configured
    if (this.browserConfig.recordingEnabled) {
      await this.startRecording();
    }
  }

  private async startRecording(): Promise<void> {
    if (!this.context) return;

    try {
      // Start browser tracing for detailed recording
      await this.context.tracing.start({
        screenshots: true,
        snapshots: true,
        sources: true,
        title: `DeepResearch Browser Session - ${new Date().toISOString()}`
      });

      // If video recording is supported, enable it per page
      this.isRecording = true;
      console.log(`📹 Browser recording started: ${this.recordingDir}`);
    } catch (error) {
      console.warn('Failed to start recording:', error);
    }
  }

  private async stopRecording(): Promise<string | null> {
    if (!this.context || !this.isRecording) return null;

    try {
      const tracePath = path.join(this.recordingDir, 'trace.zip');
      await this.context.tracing.stop({ path: tracePath });
      this.isRecording = false;
      return tracePath;
    } catch (error) {
      console.warn('Failed to stop recording:', error);
      return null;
    }
  }

  /**
   * Intelligently scrape a page using AI-guided visual navigation
   */
  async intelligentScrape(url: string, customInstructions?: string): Promise<PageData> {
    await this.initialize();

    const startTime = Date.now();

    try {
      // Create new page with video recording if enabled
      this.currentPage = await this.context!.newPage();

      // Enable video recording for this page if recording is enabled
      if (this.browserConfig.recordingEnabled) {
        try {
          const videoPath = path.join(this.recordingDir, `page_${Date.now()}.webm`);
          await this.currentPage.video()?.saveAs(videoPath);
        } catch (error) {
          console.warn('Video recording setup failed:', error);
        }
      }

      // Navigate to URL
      await this.currentPage.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: this.browserConfig.navigationTimeout
      });

      // Wait for initial load
      await this.currentPage.waitForTimeout(3000);

      // Take initial screenshot and analyze
      const initialScreenshot = await this.takeScreenshot('initial');
      const visualAnalysis = await this.analyzePageVisually(initialScreenshot, url, customInstructions);

      console.log(`🤖 Visual Analysis: ${visualAnalysis.isSPA ? 'SPA' : 'Traditional'} | Interactive: ${visualAnalysis.hasInteractiveElements}`);

      let extractedContent = '';
      let extractedLinks: ExtractedLink[] = [];

      // Decide whether to use AI browser mode
      if (this.shouldUseAIBrowser(visualAnalysis)) {
        console.log('🤖 AI Browser Mode: ENABLED - Interactive elements detected');

        // Perform AI-guided navigation and extraction
        const result = await this.performAIGuidedExtraction(visualAnalysis, customInstructions);
        extractedContent = result.content;
        extractedLinks = result.links;
      } else {
        console.log('📄 Standard Mode: Static content extraction');

        // Use standard content extraction
        const standardResult = await this.extractStandardContent();
        extractedContent = standardResult.content;
        extractedLinks = standardResult.links;
      }

      const fetchTime = Date.now() - startTime;

      // Take final screenshot
      await this.takeScreenshot('final');

      return {
        url,
        title: await this.currentPage.title(),
        content: extractedContent,
        links: extractedLinks,
        depth: 0,
        relevanceScore: 0.5,
        fetchTime,
        processingTime: 0,
        metadata: {
          isAIBrowserMode: this.shouldUseAIBrowser(visualAnalysis),
          visualAnalysis,
          recordingPath: this.isRecording ? this.recordingDir : undefined
        }
      };

    } catch (error) {
      const fetchTime = Date.now() - startTime;

      return {
        url,
        title: this.extractTitleFromUrl(url),
        content: '',
        links: [],
        depth: 0,
        relevanceScore: 0.1,
        fetchTime,
        processingTime: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    } finally {
      if (this.currentPage) {
        await this.currentPage.close();
        this.currentPage = null;
      }
    }
  }

  private shouldUseAIBrowser(analysis: VisualAnalysis): boolean {
    // Use AI browser if screenshots are enabled and interactive elements detected
    return this.browserConfig.screenshotAnalysisEnabled && (
      analysis.hasInteractiveElements ||
      analysis.isSPA ||
      analysis.hasAccordions ||
      analysis.hasDropdowns ||
      analysis.hiddenContentDetected
    );
  }

  private async analyzePageVisually(screenshotPath: string, url: string, customInstructions?: string): Promise<VisualAnalysis> {
    if (!this.browserConfig.screenshotAnalysisEnabled) {
      // Fallback analysis without screenshot
      return this.performBasicPageAnalysis();
    }

    try {
      const analysisPrompt = `
You are an AI browser navigation specialist. Analyze this screenshot of a webpage and determine the best strategy for content extraction.

URL: ${url}
${customInstructions ? `Custom Instructions: ${customInstructions}` : ''}

Analyze the screenshot and identify:
1. Is this a Single Page Application (SPA) or React app?
2. Are there interactive elements that might hide content?
3. Do you see accordions, dropdowns, tabs, or collapsible sections?
4. Is there infinite scroll or "Load More" functionality?
5. Are there navigation elements that might lead to more content?
6. Does the page appear to have hidden or dynamically loaded content?

Respond with JSON only:
{
  "hasInteractiveElements": boolean,
  "isSPA": boolean,
  "hasAccordions": boolean,
  "hasDropdowns": boolean,
  "hasInfiniteScroll": boolean,
  "hasLoadMoreButtons": boolean,
  "hiddenContentDetected": boolean,
  "suggestedActions": [
    {
      "type": "click|scroll|wait|extract",
      "selector": "CSS selector if applicable",
      "coordinates": {"x": number, "y": number},
      "reason": "Why this action is needed"
    }
  ],
  "reasoning": "Detailed explanation of analysis",
  "confidence": 0.0-1.0
}

Focus on identifying elements that need interaction to reveal content relevant to: ${customInstructions || 'general research purposes'}.
`;

      // Read screenshot as base64
      const screenshotBuffer = await fs.promises.readFile(screenshotPath);
      const base64Image = screenshotBuffer.toString('base64');

      // Send to AI for analysis (this would need to be implemented in AIService for vision models)
      const response = await this.aiService.analyzeScreenshot(analysisPrompt, base64Image);

      const analysis = this.parseVisualAnalysis(response);
      return analysis;

    } catch (error) {
      console.warn('Visual analysis failed, using basic analysis:', error);
      return this.performBasicPageAnalysis();
    }
  }

  private async performBasicPageAnalysis(): Promise<VisualAnalysis> {
    if (!this.currentPage) {
      return this.getDefaultAnalysis();
    }

    try {
      // Check for common SPA indicators
      const isSPA = await this.currentPage.evaluate(() => {
        // Check for React, Vue, Angular
        return !!((window as any).React || (window as any).Vue || (window as any).ng || (window as any).angular ||
                 document.querySelector('[data-reactroot]') ||
                 document.querySelector('[ng-app]') ||
                 document.querySelector('[data-ng-app]') ||
                 document.querySelector('.ng-scope'));
      });

      // Check for interactive elements
      const interactiveElements = await this.currentPage.evaluate(() => {
        const accordions = document.querySelectorAll('[class*="accordion"], [class*="collapse"], [class*="expand"]');
        const dropdowns = document.querySelectorAll('[class*="dropdown"], [class*="select"], select');
        const tabs = document.querySelectorAll('[class*="tab"], [role="tab"]');
        const loadMore = document.querySelectorAll('[class*="load-more"], [class*="show-more"]');

        return {
          hasAccordions: accordions.length > 0,
          hasDropdowns: dropdowns.length > 0,
          hasTabs: tabs.length > 0,
          hasLoadMoreButtons: loadMore.length > 0,
          hasInteractiveElements: accordions.length + dropdowns.length + tabs.length + loadMore.length > 0
        };
      });

      return {
        hasInteractiveElements: interactiveElements.hasInteractiveElements || isSPA,
        isSPA,
        hasAccordions: interactiveElements.hasAccordions,
        hasDropdowns: interactiveElements.hasDropdowns,
        hasInfiniteScroll: false, // Would need scroll detection
        hasLoadMoreButtons: interactiveElements.hasLoadMoreButtons,
        hiddenContentDetected: interactiveElements.hasInteractiveElements,
        suggestedActions: [],
        reasoning: 'Basic DOM analysis performed due to screenshot analysis being disabled',
        confidence: 0.7
      };

    } catch (error) {
      return this.getDefaultAnalysis();
    }
  }

  private getDefaultAnalysis(): VisualAnalysis {
    return {
      hasInteractiveElements: false,
      isSPA: false,
      hasAccordions: false,
      hasDropdowns: false,
      hasInfiniteScroll: false,
      hasLoadMoreButtons: false,
      hiddenContentDetected: false,
      suggestedActions: [],
      reasoning: 'Default analysis - no detailed analysis available',
      confidence: 0.3
    };
  }

  private parseVisualAnalysis(response: string): VisualAnalysis {
    try {
      const cleaned = this.cleanJsonResponse(response);
      const parsed = JSON.parse(cleaned);

      return {
        hasInteractiveElements: parsed.hasInteractiveElements ?? false,
        isSPA: parsed.isSPA ?? false,
        hasAccordions: parsed.hasAccordions ?? false,
        hasDropdowns: parsed.hasDropdowns ?? false,
        hasInfiniteScroll: parsed.hasInfiniteScroll ?? false,
        hasLoadMoreButtons: parsed.hasLoadMoreButtons ?? false,
        hiddenContentDetected: parsed.hiddenContentDetected ?? false,
        suggestedActions: Array.isArray(parsed.suggestedActions) ? parsed.suggestedActions : [],
        reasoning: parsed.reasoning || 'No reasoning provided',
        confidence: Math.max(0, Math.min(1, parsed.confidence ?? 0.5))
      };
    } catch (error) {
      return this.getDefaultAnalysis();
    }
  }

  private async performAIGuidedExtraction(analysis: VisualAnalysis, customInstructions?: string): Promise<{
    content: string;
    links: ExtractedLink[];
  }> {
    if (!this.currentPage) {
      throw new Error('No active page for AI-guided extraction');
    }

    let allContent = '';
    let allLinks: ExtractedLink[] = [];
    let attempts = 0;
    const maxAttempts = this.browserConfig.maxNavigationAttempts;

    console.log(`🤖 Starting AI-guided extraction with ${analysis.suggestedActions.length} suggested actions`);

    // Perform initial content extraction
    const initialContent = await this.extractStandardContent();
    allContent += initialContent.content;
    allLinks.push(...initialContent.links);

    // Execute AI-suggested actions
    for (const action of analysis.suggestedActions) {
      if (attempts >= maxAttempts) {
        console.log(`🛑 Max attempts (${maxAttempts}) reached`);
        break;
      }

      try {
        console.log(`🎯 Executing action: ${action.type} - ${action.reason}`);

        await this.executeAction(action);
        attempts++;

        // Wait for content to load after action
        await this.currentPage.waitForTimeout(2000);

        // Take screenshot after action for debugging
        await this.takeScreenshot(`action_${attempts}_${action.type}`);

        // Extract content after action
        const actionContent = await this.extractStandardContent();

        // Only add new content (simple deduplication)
        const newContent = this.getNewContent(allContent, actionContent.content);
        if (newContent.length > 100) {
          allContent += '\n\n--- After ' + action.type + ' ---\n' + newContent;
          console.log(`✅ New content extracted: ${newContent.length} characters`);
        }

        // Add new links
        const newLinks = actionContent.links.filter(link =>
          !allLinks.some(existingLink => existingLink.url === link.url)
        );
        allLinks.push(...newLinks);

        // Check if we should continue based on success
        if (newContent.length < 50 && attempts > 1) {
          console.log('🔄 Minimal new content, continuing with next action');
        }

      } catch (error) {
        console.warn(`⚠️ Action failed: ${action.type} - ${error}`);
        attempts++;
      }
    }

    // Perform additional intelligent actions if needed
    if (analysis.hasInfiniteScroll || analysis.hasLoadMoreButtons) {
      await this.handleInfiniteScrollAndLoadMore();
      const finalContent = await this.extractStandardContent();
      const newContent = this.getNewContent(allContent, finalContent.content);
      if (newContent.length > 100) {
        allContent += '\n\n--- After Scroll/Load More ---\n' + newContent;
      }
    }

    return {
      content: allContent,
      links: allLinks
    };
  }

  private async executeAction(action: BrowserAction): Promise<void> {
    if (!this.currentPage) return;

    switch (action.type) {
      case 'click':
        if (action.selector) {
          await this.currentPage.click(action.selector);
        } else if (action.coordinates) {
          await this.currentPage.mouse.click(action.coordinates.x, action.coordinates.y);
        }
        break;

      case 'scroll':
        if (action.direction === 'down') {
          await this.currentPage.mouse.wheel(0, action.pixels || 500);
        } else if (action.direction === 'up') {
          await this.currentPage.mouse.wheel(0, -(action.pixels || 500));
        }
        break;

      case 'wait':
        await this.currentPage.waitForTimeout(action.duration || 2000);
        break;

      case 'navigate':
        if (action.url) {
          await this.currentPage.goto(action.url, { waitUntil: 'domcontentloaded' });
        }
        break;

      default:
        console.warn(`Unknown action type: ${action.type}`);
    }
  }

  private async handleInfiniteScrollAndLoadMore(): Promise<void> {
    if (!this.currentPage) return;

    try {
      // Handle infinite scroll
      let previousHeight = 0;
      let currentHeight = await this.currentPage.evaluate(() => document.body.scrollHeight);
      let scrollAttempts = 0;

      while (previousHeight !== currentHeight && scrollAttempts < 3) {
        previousHeight = currentHeight;

        await this.currentPage.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight);
        });

        await this.currentPage.waitForTimeout(2000);

        currentHeight = await this.currentPage.evaluate(() => document.body.scrollHeight);
        scrollAttempts++;
      }

      // Handle load more buttons
      const loadMoreSelectors = [
        'button[class*="load-more"]',
        'button[class*="show-more"]',
        '.load-more',
        '.show-more',
        '[data-testid*="load-more"]'
      ];

      for (const selector of loadMoreSelectors) {
        try {
          const button = await this.currentPage.$(selector);
          if (button && await button.isVisible()) {
            await button.click();
            await this.currentPage.waitForTimeout(3000);
            break;
          }
        } catch (e) {
          // Continue with next selector
        }
      }

    } catch (error) {
      console.warn('Infinite scroll handling failed:', error);
    }
  }

  private async extractStandardContent(): Promise<{ content: string; links: ExtractedLink[] }> {
    if (!this.currentPage) {
      return { content: '', links: [] };
    }

    try {
      const result = await this.currentPage.evaluate(() => {
        // Extract content
        const title = document.title;
        const metaDescription = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';

        // Remove unwanted elements
        const elementsToRemove = document.querySelectorAll('script, style, nav, header, footer, aside, .advertisement, .ads');
        elementsToRemove.forEach(el => el.remove());

        // Extract main content
        const contentSelectors = [
          'main article',
          'main .content',
          'article',
          '.main-content',
          '.post-content',
          '.entry-content',
          '[role="main"]',
          'main'
        ];

        let mainContent = '';
        for (const selector of contentSelectors) {
          const element = document.querySelector(selector);
          if (element) {
            const text = element.textContent?.trim() || '';
            if (text.length > 200) {
              mainContent = text;
              break;
            }
          }
        }

        if (!mainContent) {
          mainContent = document.body.textContent?.trim() || '';
        }

        // Extract headings and key points
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4'))
          .map(h => h.textContent?.trim())
          .filter(h => h && h.length > 0)
          .join('. ');

        const lists = Array.from(document.querySelectorAll('ul li, ol li'))
          .map(li => li.textContent?.trim())
          .filter(li => li && li.length > 0)
          .slice(0, 20) // Limit list items
          .join('. ');

        // Combine content
        let fullContent = '';
        if (title) fullContent += `Title: ${title}\n\n`;
        if (metaDescription) fullContent += `Description: ${metaDescription}\n\n`;
        if (headings) fullContent += `Key Topics: ${headings}\n\n`;
        if (mainContent) fullContent += `Content: ${mainContent}`;
        if (lists) fullContent += `\n\nKey Points: ${lists}`;

        // Extract links
        const links = Array.from(document.querySelectorAll('a[href]'))
          .map(a => {
            const href = a.getAttribute('href');
            const text = a.textContent?.trim();
            const context = a.parentElement?.textContent?.trim()?.substring(0, 200);

            if (href && text && href.length > 0) {
              try {
                return {
                  url: new URL(href, window.location.href).toString(),
                  text: text.substring(0, 100),
                  context: context || '',
                  relevanceScore: 0.5
                } as ExtractedLink;
              } catch (e) {
                return null;
              }
            }
            return null;
          })
          .filter((link): link is ExtractedLink => link !== null && typeof link.context === 'string')
          .slice(0, 50);

        return {
          content: fullContent.replace(/\s+/g, ' ').trim().substring(0, 15000),
          links
        };
      });

      return result;
    } catch (error) {
      console.warn('Content extraction failed:', error);
      return { content: '', links: [] };
    }
  }

  private getNewContent(existingContent: string, newContent: string): string {
    // Simple deduplication - find content that's not already present
    const existingWords = new Set(existingContent.toLowerCase().split(/\s+/));
    const newWords = newContent.toLowerCase().split(/\s+/);

    const uniqueWords = newWords.filter(word => !existingWords.has(word));

    // If more than 30% of the content is new, consider it valuable
    if (uniqueWords.length > newWords.length * 0.3) {
      return newContent;
    }

    return '';
  }

  private async takeScreenshot(label: string): Promise<string> {
    if (!this.currentPage || !this.browserConfig.screenshotAnalysisEnabled) {
      return '';
    }

    try {
      const filename = `${Date.now()}_${label}.png`;
      const filepath = path.join(this.screenshotDir, filename);

      await this.currentPage.screenshot({
        path: filepath,
        fullPage: true,
        type: 'png'
      });

      this.recordingFrame++;

      return filepath;
    } catch (error) {
      console.warn('Screenshot failed:', error);
      return '';
    }
  }

  private cleanJsonResponse(content: string): string {
    let cleaned = content
      .replace(/```json\s*\n?/gi, '')
      .replace(/```\s*$/g, '')
      .trim();

    const jsonMatch = cleaned.match(/[\{\[]/);
    if (jsonMatch) {
      cleaned = cleaned.substring(jsonMatch.index!);
    }

    return cleaned;
  }

  private extractTitleFromUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(part => part.length > 0);
      return pathParts.length > 0 ? pathParts[pathParts.length - 1].replace(/[-_]/g, ' ') : urlObj.hostname;
    } catch {
      return 'Unknown Title';
    }
  }

  async dispose(): Promise<void> {
    try {
      if (this.isRecording) {
        const tracePath = await this.stopRecording();
        if (tracePath) {
          console.log(`📹 Recording saved: ${tracePath}`);
        }
      }

      if (this.currentPage) {
        await this.currentPage.close();
        this.currentPage = null;
      }

      if (this.context) {
        await this.context.close();
        this.context = null;
      }

      if (this.browser) {
        await this.browser.close();
        this.browser = null;
      }

      console.log(`📸 Screenshots saved to: ${this.screenshotDir}`);
    } catch (error) {
      console.warn('Cleanup failed:', error);
    }
  }

  // Getter methods
  getBrowserConfig(): BrowserConfig {
    return { ...this.browserConfig };
  }

  getRecordingDir(): string {
    return this.recordingDir;
  }

  getScreenshotDir(): string {
    return this.screenshotDir;
  }
}