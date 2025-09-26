/**
 * Crawling Node - TypeScript implementation
 */

import axios from 'axios';
import * as fs from 'fs-extra';
import * as path from 'path';
import { WorkflowState, CrawlResult } from '../types/workflow-state';
import { console } from '../utils/console';
import { Progress } from '../utils/progress';

export async function crawlingNode(state: WorkflowState): Promise<WorkflowState> {
  console.print('\n[bold]Step 2: Crawling URLs...[/bold]');
  
  if (state.urls.length === 0) {
    console.warn('No URLs to crawl');
    return state;
  }
  
  const progress = new Progress();
  const newState = { ...state };
  const markdownDir = path.join(state.output_dir, 'markdown');
  
  // Ensure markdown directory exists
  await fs.ensureDir(markdownDir);
  
  let successfulCrawls = 0;
  let failedCrawls = 0;
  
  for (const url of state.urls) {
    const taskId = progress.addTask(`Crawling ${url}`);
    
    try {
      const result = await crawlUrl(url, markdownDir);
      newState.crawl_results[url] = result;
      
      if (result.success && result.filepath) {
        newState.markdown_files.push(result.filepath);
        successfulCrawls++;
        progress.completeTask(taskId, `Crawled ${url} successfully`);
      } else {
        failedCrawls++;
        progress.failTask(taskId, `Failed to crawl ${url}: ${result.error}`);
      }
      
    } catch (error) {
      const errorMsg = `Crawling ${url} failed: ${error}`;
      newState.crawl_results[url] = {
        success: false,
        content_length: 0,
        error: errorMsg,
        url
      };
      failedCrawls++;
      progress.failTask(taskId, errorMsg);
    }
  }
  
  // Update metadata
  newState.metadata.successful_crawls = successfulCrawls;
  newState.metadata.failed_crawls = failedCrawls;
  
  console.print(`\n[bold]Crawling Summary:[/bold]`);
  console.print(`[green]✓[/green] Successful: ${successfulCrawls}`);
  console.print(`[red]✗[/red] Failed: ${failedCrawls}`);
  
  return newState;
}

async function crawlUrl(url: string, outputDir: string): Promise<CrawlResult> {
  try {
    // Simulate Firecrawl API behavior for now
    // In production, this would integrate with actual Firecrawl API
    const response = await axios.get(url, {
      timeout: 30000,
      headers: {
        'User-Agent': 'API-Doc-Processor/1.0'
      }
    });
    
    if (response.status !== 200) {
      return {
        success: false,
        content_length: 0,
        error: `HTTP ${response.status}: ${response.statusText}`,
        url
      };
    }
    
    // Convert HTML to markdown (simplified)
    const content = response.data;
    const markdown = convertHtmlToMarkdown(content);
    
    // Generate filename from URL
    const filename = generateFilename(url);
    const filepath = path.join(outputDir, filename);
    
    // Write to file
    await fs.writeFile(filepath, markdown, 'utf-8');
    
    return {
      success: true,
      filepath,
      content_length: markdown.length,
      url
    };
    
  } catch (error: any) {
    return {
      success: false,
      content_length: 0,
      error: error.message || 'Unknown error',
      url
    };
  }
}

function convertHtmlToMarkdown(html: string): string {
  // Simple HTML to Markdown conversion
  // In production, you'd use a proper library like turndown
  return html
    .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
    .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '') // Remove all other HTML tags
    .replace(/\n{3,}/g, '\n\n') // Normalize line breaks
    .trim();
}

function generateFilename(url: string): string {
  const urlObj = new URL(url);
  const domain = urlObj.hostname.replace(/[^a-zA-Z0-9]/g, '_');
  const path = urlObj.pathname.replace(/[^a-zA-Z0-9]/g, '_');
  const timestamp = Date.now();
  
  return `${domain}_${path}_${timestamp}.md`;
}