/**
 * URL Collection Node - TypeScript implementation (matching Python interactive behavior)
 */

import * as readlineSync from 'readline-sync';
import { WorkflowState } from '../types/workflow-state';
import { console } from '../utils/console';
import { validateUrl, deduplicateUrls, validateUrlsBatch } from '../utils/validation';

export async function urlCollectionNode(state: WorkflowState): Promise<WorkflowState> {
  console.print('[bold]Enter API documentation URLs[/bold]');
  console.print('(Press Enter without typing a URL to finish)');
  console.print('');
  
  const urls: string[] = [];
  
  try {
    while (true) {
      const url = readlineSync.question('URL: ').trim();
      
      if (!url) {
        break;
      }
      
      const validation = validateUrl(url);
      if (!validation.isValid) {
        console.print(`[red]Invalid URL:[/red] ${validation.error}`);
        state.errors.push(`Invalid URL: ${url} - ${validation.error}`);
        continue;
      }
      
      urls.push(url);
      console.print(`[green]✓[/green] Added: ${url}`);
    }
    
    // Remove duplicates while preserving order
    const deduplicatedUrls = deduplicateUrls(urls);
    
    // Final validation
    const { validUrls, invalidUrls } = validateUrlsBatch(deduplicatedUrls);
    
    if (invalidUrls.length > 0) {
      console.print('\n[yellow]Warning: Some URLs failed validation:[/yellow]');
      for (const { url, error } of invalidUrls) {
        console.print(`  [red]✗[/red] ${url}: ${error}`);
        state.warnings.push(`URL validation warning: ${url} - ${error}`);
      }
    }
    
    // Update state
    const newState = { ...state };
    newState.urls = validUrls;
    newState.metadata.total_urls = validUrls.length;
    
    if (validUrls.length > 0) {
      console.print(`\n[bold]Processing ${validUrls.length} URL(s):[/bold]`);
      for (let i = 0; i < validUrls.length; i++) {
        console.print(`  ${i + 1}. ${validUrls[i]}`);
      }
    } else {
      console.print('[yellow]No valid URLs provided.[/yellow]');
      newState.errors.push('No valid URLs collected');
    }
    
    return newState;
    
  } catch (error) {
    const errorMsg = `URL collection failed: ${error}`;
    console.error(errorMsg);
    state.errors.push(errorMsg);
    return state;
  }
}