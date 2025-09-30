import { chromium, Browser, Page } from 'playwright';
import * as cheerio from 'cheerio';
import { PageData, ExtractedLink } from '../types';

export class WebScrapingService {
  private browser: Browser | null = null;
  private maxConcurrentPages: number;
  private timeout: number;
  private respectRobotsTxt: boolean;

  private proxyList: string[];
  private currentProxyIndex: number = 0;

  constructor(options?: {
    maxConcurrentPages?: number;
    timeout?: number;
    respectRobotsTxt?: boolean;
    proxies?: string[];
  }) {
    this.maxConcurrentPages = options?.maxConcurrentPages || 3;
    this.timeout = options?.timeout || 30000;
    this.respectRobotsTxt = options?.respectRobotsTxt !== false;
    this.proxyList = options?.proxies || [];
  }

  async initialize(): Promise<void> {
    if (!this.browser) {
      const launchOptions: any = {
        headless: true,
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
          '--disable-plugins',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding',
          '--window-size=1920,1080'
        ]
      };

      // Add proxy if available
      if (this.proxyList.length > 0) {
        const proxy = this.getNextProxy();
        launchOptions.args.push(`--proxy-server=${proxy}`);
      }

      this.browser = await chromium.launch(launchOptions);
    }
  }

  private getNextProxy(): string {
    if (this.proxyList.length === 0) return '';
    const proxy = this.proxyList[this.currentProxyIndex];
    this.currentProxyIndex = (this.currentProxyIndex + 1) % this.proxyList.length;
    return proxy;
  }

  private getRandomUserAgent(): string {
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ];
    return userAgents[Math.floor(Math.random() * userAgents.length)];
  }

  private async addStealthHeaders(page: Page): Promise<void> {
    // Remove automation indicators using string-based script injection
    await page.addInitScript(`
      // Browser environment script - will only run in browser context
      try {
        if (typeof navigator !== 'undefined') {
          Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
          });

          Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
          });

          Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
          });
        }

        if (typeof window !== 'undefined' && window.chrome) {
          delete window.chrome.runtime;
        }
      } catch (e) {
        // Ignore errors in browser context
      }
    `);

    // Set realistic headers
    await page.setExtraHTTPHeaders({
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
      'Accept-Encoding': 'gzip, deflate, br',
      'Accept-Language': 'en-US,en;q=0.9',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1',
      'Upgrade-Insecure-Requests': '1',
      'User-Agent': this.getRandomUserAgent()
    });
  }

  private async handleDynamicContent(page: Page): Promise<void> {
    try {
      // Try to handle infinite scroll or "load more" content
      let previousHeight = 0;
      let currentHeight = await page.evaluate(() => {
        return document.body.scrollHeight;
      });
      let attempts = 0;
      const maxAttempts = 3;

      while (previousHeight !== currentHeight && attempts < maxAttempts) {
        previousHeight = currentHeight;

        // Scroll to bottom
        await page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight);
        });

        // Wait for potential content to load
        await page.waitForTimeout(2000);

        // Check for "Load More" or "Show More" buttons
        const loadMoreSelectors = [
          'button[class*="load-more"]',
          'button[class*="show-more"]',
          'a[class*="load-more"]',
          'a[class*="show-more"]',
          '.load-more',
          '.show-more',
          '[data-testid*="load-more"]',
          '[data-testid*="show-more"]'
        ];

        for (const selector of loadMoreSelectors) {
          try {
            const button = await page.$(selector);
            if (button) {
              const isVisible = await button.isVisible();
              if (isVisible) {
                await button.click();
                await page.waitForTimeout(2000);
                break;
              }
            }
          } catch (e) {
            // Continue with next selector
          }
        }

        currentHeight = await page.evaluate(() => {
          return document.body.scrollHeight;
        });
        attempts++;
      }

      // Scroll back to top
      await page.evaluate(() => {
        window.scrollTo(0, 0);
      });

    } catch (error) {
      // If dynamic content handling fails, continue with regular scraping
    }
  }

  async scrapePage(url: string, depth: number = 0): Promise<PageData> {
    if (!this.browser) {
      await this.initialize();
    }

    const startTime = Date.now();
    let page: Page | null = null;

    try {
      // Check robots.txt if enabled
      if (this.respectRobotsTxt && depth > 0) {
        const isAllowed = await this.checkRobotsTxt(url);
        if (!isAllowed) {
          throw new Error('Blocked by robots.txt');
        }
      }

      page = await this.browser!.newPage();

      // Set stealth headers and realistic viewport
      await page.setViewportSize({
        width: 1920 + Math.floor(Math.random() * 100),
        height: 1080 + Math.floor(Math.random() * 100)
      });

      await this.addStealthHeaders(page);

      // Add random delay to appear more human-like
      await page.waitForTimeout(500 + Math.random() * 1000);

      // Navigate to page with timeout
      await page.goto(url, {
        waitUntil: 'domcontentloaded',
        timeout: this.timeout
      });

      // Wait for dynamic content and any lazy loading
      await page.waitForTimeout(3000);

      // Handle potential infinite scroll or "load more" buttons
      await this.handleDynamicContent(page);

      // Get page content
      const content = await page.content();
      const title = await page.title();

      // Extract comprehensive content and links
      const { textContent, links } = this.extractContentAndLinks(content, url);

      const fetchTime = Date.now() - startTime;

      return {
        url,
        title: title || this.extractTitleFromUrl(url),
        content: textContent,
        links,
        depth,
        relevanceScore: 0.5, // Will be scored later by AI
        fetchTime,
        processingTime: 0 // Will be set during processing
      };

    } catch (error) {
      const fetchTime = Date.now() - startTime;

      return {
        url,
        title: this.extractTitleFromUrl(url),
        content: '',
        links: [],
        depth,
        relevanceScore: 0.1,
        fetchTime,
        processingTime: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };

    } finally {
      if (page) {
        await page.close();
      }
    }
  }

  async scrapeMultiplePages(urls: string[], depth: number = 0): Promise<PageData[]> {
    const results: PageData[] = [];
    const semaphore = new Semaphore(this.maxConcurrentPages);

    const promises = urls.map(async (url) => {
      const release = await semaphore.acquire();
      try {
        const result = await this.scrapePage(url, depth);
        results.push(result);
      } finally {
        release();
      }
    });

    await Promise.allSettled(promises);
    return results;
  }

  private extractContentAndLinks(html: string, baseUrl: string): {
    textContent: string;
    links: ExtractedLink[];
  } {
    const $ = cheerio.load(html);

    // Remove script, style, and other non-content elements
    $('script, style, nav, header, footer, aside, .advertisement, .ads, .sidebar, .comments').remove();

    // Extract comprehensive content - not just from main areas
    // Get the title first
    const title = $('title').text().trim();

    // Extract meta description for additional context
    const metaDescription = $('meta[name="description"]').attr('content') || '';

    // Extract structured content sections
    const contentSections = [];

    // Priority content selectors in order of importance
    const contentSelectors = [
      'main article',
      'main .content',
      'article',
      '.main-content',
      '.post-content',
      '.entry-content',
      '.content-area',
      '.page-content',
      '[role="main"]',
      'main',
      '#content',
      '.content'
    ];

    let primaryContent = '';
    for (const selector of contentSelectors) {
      const element = $(selector).first();
      if (element.length > 0) {
        const content = element.text().trim();
        if (content.length > 200) {
          primaryContent = content;
          break;
        }
      }
    }

    // If no primary content found, extract from body but be smarter about it
    if (!primaryContent) {
      // Try to get paragraph content
      const paragraphs = $('p').map((_, el) => $(el).text().trim()).get().join(' ');
      if (paragraphs.length > 200) {
        primaryContent = paragraphs;
      } else {
        primaryContent = $('body').text().trim();
      }
    }

    // Extract additional structured content
    const headings = $('h1, h2, h3, h4').map((_, el) => $(el).text().trim()).get().join('. ');
    const lists = $('ul li, ol li').map((_, el) => $(el).text().trim()).get().join('. ');

    // Combine all content with structure preservation
    let fullContent = '';
    if (title) fullContent += `Title: ${title}\n\n`;
    if (metaDescription) fullContent += `Description: ${metaDescription}\n\n`;
    if (headings) fullContent += `Key Topics: ${headings}\n\n`;
    if (primaryContent) fullContent += `Content: ${primaryContent}`;
    if (lists) fullContent += `\n\nKey Points: ${lists}`;

    // Clean up text content but preserve more structure
    const textContent = fullContent
      .replace(/\s+/g, ' ')
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .trim()
      .substring(0, 15000); // Increased limit for better content capture

    // Extract links
    const links: ExtractedLink[] = [];
    const seenUrls = new Set<string>();

    $('a[href]').each((_, element) => {
      const href = $(element).attr('href');
      const text = $(element).text().trim();

      if (href && text && href.length > 0) {
        try {
          const absoluteUrl = new URL(href, baseUrl).toString();

          // Filter out unwanted links
          if (this.isValidLink(absoluteUrl) && !seenUrls.has(absoluteUrl)) {
            seenUrls.add(absoluteUrl);

            // Get surrounding context
            const context = $(element).parent().text().trim().substring(0, 200);

            links.push({
              url: absoluteUrl,
              text: text.substring(0, 100),
              context,
              relevanceScore: 0.5 // Will be scored by AI
            });
          }
        } catch (error) {
          // Invalid URL, skip
        }
      }
    });

    return { textContent, links: links.slice(0, 50) }; // Limit to 50 links
  }

  private isValidLink(url: string): boolean {
    try {
      const urlObj = new URL(url);

      // Only HTTP/HTTPS
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return false;
      }

      // Skip common non-content file types
      const path = urlObj.pathname.toLowerCase();
      const skipExtensions = ['.pdf', '.doc', '.docx', '.zip', '.rar', '.mp3', '.mp4', '.avi', '.jpg', '.jpeg', '.png', '.gif'];
      if (skipExtensions.some(ext => path.endsWith(ext))) {
        return false;
      }

      // Skip social media and other non-content URLs
      const skipDomains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com'];
      if (skipDomains.some(domain => urlObj.hostname.includes(domain))) {
        return false;
      }

      // Skip fragments and javascript links
      if (url.includes('#') || url.startsWith('javascript:')) {
        return false;
      }

      return true;
    } catch {
      return false;
    }
  }

  private async checkRobotsTxt(url: string): Promise<boolean> {
    try {
      const urlObj = new URL(url);
      const robotsUrl = `${urlObj.protocol}//${urlObj.host}/robots.txt`;

      const page = await this.browser!.newPage();
      const response = await page.goto(robotsUrl, { timeout: 5000 });

      if (response && response.ok()) {
        const robotsContent = await page.content();
        // Simple robots.txt check - this could be more sophisticated
        const disallowedPaths = this.parseRobotsTxt(robotsContent);
        const path = urlObj.pathname;

        for (const disallowedPath of disallowedPaths) {
          if (path.startsWith(disallowedPath)) {
            await page.close();
            return false;
          }
        }
      }

      await page.close();
      return true;
    } catch (error) {
      // If robots.txt can't be fetched, allow the request
      return true;
    }
  }

  private parseRobotsTxt(content: string): string[] {
    const lines = content.split('\n');
    const disallowed: string[] = [];
    let inUserAgentSection = false;

    for (const line of lines) {
      const trimmed = line.trim().toLowerCase();

      if (trimmed.startsWith('user-agent:')) {
        const userAgent = trimmed.split(':')[1].trim();
        inUserAgentSection = userAgent === '*' || userAgent.includes('bot');
      } else if (inUserAgentSection && trimmed.startsWith('disallow:')) {
        const path = trimmed.split(':')[1].trim();
        if (path && path !== '') {
          disallowed.push(path);
        }
      }
    }

    return disallowed;
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
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
}

// Simple semaphore for concurrency control
class Semaphore {
  private permits: number;
  private waitQueue: Array<() => void> = [];

  constructor(permits: number) {
    this.permits = permits;
  }

  async acquire(): Promise<() => void> {
    return new Promise((resolve) => {
      if (this.permits > 0) {
        this.permits--;
        resolve(() => this.release());
      } else {
        this.waitQueue.push(() => {
          this.permits--;
          resolve(() => this.release());
        });
      }
    });
  }

  private release(): void {
    this.permits++;
    if (this.waitQueue.length > 0) {
      const next = this.waitQueue.shift();
      if (next) next();
    }
  }
}