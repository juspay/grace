import axios from 'axios';
import { SearchResult } from '../types';
import { DebugLogger } from '../utils/DebugLogger';

export class SearchService {
  private searxngBaseUrl: string;
  private debugLogger: DebugLogger;

  constructor(searxngBaseUrl: string = 'http://localhost:8080') {
    this.searxngBaseUrl = searxngBaseUrl;
    this.debugLogger = DebugLogger.getInstance();
  }

  async search(query: string, options?: {
    engines?: string[];
    categories?: string[];
    limit?: number;
  }): Promise<SearchResult[]> {
    const startTime = Date.now();
    this.debugLogger.logSearchQuery(query, startTime);

    try {
      const params = new URLSearchParams({
        q: query,
        format: 'json',
        engines: options?.engines?.join(',') || 'google,bing,duckduckgo',
        categories: options?.categories?.join(',') || 'general',
        results_on_new_tab: '1'
      });

      const response = await axios.get(`${this.searxngBaseUrl}/search?${params}`, {
        timeout: 30000,
        headers: {
          'User-Agent': 'MASS-CLI-Research/1.0'
        }
      });

      const results = response.data.results || [];

      const searchResults = results
        .filter((result: any) => result.url && result.title)
        .slice(0, options?.limit || 20)
        .map((result: any, index: number) => ({
          title: result.title || 'Untitled',
          url: result.url,
          snippet: result.content || result.snippet || '',
          engine: result.engine || 'unknown',
          score: this.calculateScore(result, index)
        }));

      const duration = Date.now() - startTime;
      this.debugLogger.logSearchResult(query, searchResults, duration);

      return searchResults;
    } catch (error) {
      console.warn('Search failed, using fallback:', error);
      return this.fallbackSearch(query, options?.limit || 20);
    }
  }

  private calculateScore(result: any, index: number): number {
    // Simple scoring based on position and metadata
    let score = 1.0 - (index * 0.05); // Decrease score by position

    // Boost score for certain indicators of quality
    if (result.title && result.title.length > 10) score += 0.1;
    if (result.content && result.content.length > 100) score += 0.1;
    if (result.url.includes('https://')) score += 0.05;

    // Prefer certain domains
    const url = result.url.toLowerCase();
    if (url.includes('wikipedia.org') || url.includes('.edu') || url.includes('.gov')) {
      score += 0.2;
    }

    return Math.max(0.1, Math.min(1.0, score));
  }

  private async fallbackSearch(query: string, limit: number): Promise<SearchResult[]> {
    // Fallback to a simple mock search if SearXNG is not available
    console.log('Using fallback search - SearXNG not available');

    const mockResults: SearchResult[] = [
      {
        title: `Wikipedia: ${query}`,
        url: `https://en.wikipedia.org/wiki/${encodeURIComponent(query.replace(/\s+/g, '_'))}`,
        snippet: `Wikipedia article about ${query}`,
        engine: 'fallback',
        score: 0.9
      },
      {
        title: `Research about ${query}`,
        url: `https://scholar.google.com/scholar?q=${encodeURIComponent(query)}`,
        snippet: `Academic research and papers about ${query}`,
        engine: 'fallback',
        score: 0.8
      }
    ];

    return mockResults.slice(0, limit);
  }

  async searchMultipleQueries(queries: string[], options?: {
    maxResultsPerQuery?: number;
    engines?: string[];
  }): Promise<SearchResult[]> {
    const allResults: SearchResult[] = [];
    const seenUrls = new Set<string>();

    for (const query of queries) {
      try {
        const results = await this.search(query, {
          engines: options?.engines,
          limit: options?.maxResultsPerQuery || 10
        });

        // Deduplicate by URL
        for (const result of results) {
          if (!seenUrls.has(result.url)) {
            seenUrls.add(result.url);
            allResults.push(result);
          }
        }
      } catch (error) {
        console.warn(`Failed to search for query "${query}":`, error);
      }
    }

    // Sort by score and return
    return allResults.sort((a, b) => b.score - a.score);
  }

  async isEngineAvailable(engine: string): Promise<boolean> {
    try {
      const response = await axios.get(`${this.searxngBaseUrl}/config`, {
        timeout: 5000
      });

      const engines = response.data?.engines || {};
      return engine in engines;
    } catch (error) {
      return false;
    }
  }

  async getAvailableEngines(): Promise<string[]> {
    try {
      const response = await axios.get(`${this.searxngBaseUrl}/config`, {
        timeout: 5000
      });

      const engines = response.data?.engines || {};
      return Object.keys(engines).filter(engine => engines[engine].enabled);
    } catch (error) {
      return ['google', 'bing', 'duckduckgo']; // fallback engines
    }
  }
}