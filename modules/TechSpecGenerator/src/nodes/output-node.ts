/**
 * Output Node - TypeScript implementation
 */

import * as path from 'path';
import { WorkflowState } from '../types/workflow-state';
import { console } from '../utils/console';

export async function outputNode(state: WorkflowState): Promise<WorkflowState> {
  console.print('\n[bold]Step 5: Workflow Summary[/bold]');
  
  const metadata = state.metadata;
  const duration = metadata.end_time && metadata.start_time 
    ? (metadata.end_time - metadata.start_time) / 1000 
    : 0;

  // Display summary
  console.print('\n[bold]📊 Execution Summary[/bold]');
  console.print(`[dim]Duration: ${duration.toFixed(2)}s[/dim]`);
  
  // URL Collection Summary
  console.print('\n[bold]🔗 URL Collection[/bold]');
  console.print(`Total URLs: ${metadata.total_urls || 0}`);
  
  // Crawling Summary
  if (metadata.total_urls && metadata.total_urls > 0) {
    console.print('\n[bold]🕷️ Crawling Results[/bold]');
    console.print(`[green]✓[/green] Successful: ${metadata.successful_crawls || 0}`);
    console.print(`[red]✗[/red] Failed: ${metadata.failed_crawls || 0}`);
    
    const successRate = metadata.total_urls > 0 
      ? ((metadata.successful_crawls || 0) / metadata.total_urls * 100).toFixed(1)
      : '0';
    console.print(`Success Rate: ${successRate}%`);
  }
  
  // LLM Processing Summary
  console.print('\n[bold]🤖 LLM Processing[/bold]');
  if (metadata.spec_generated) {
    console.print('[green]✓[/green] Technical specification generated');
    if (state.spec_filepath) {
      console.print(`[dim]Location: ${state.spec_filepath}[/dim]`);
    }
    
    if (metadata.estimated_tokens) {
      console.print(`[dim]Estimated tokens - Input: ${metadata.estimated_tokens.input}, Output: ${metadata.estimated_tokens.output}[/dim]`);
    }
  } else {
    console.print('[red]✗[/red] Technical specification generation failed');
  }
  
  // Mock Server Summary
  console.print('\n[bold]🚀 Mock Server Generation[/bold]');
  if (metadata.mock_server_generated) {
    console.print('[green]✓[/green] Mock server generated successfully');
    if (state.mock_server_dir) {
      console.print(`[dim]Location: ${state.mock_server_dir}[/dim]`);
    }
    if (state.mock_server_process) {
      console.print(`[dim]Server running with PID: ${state.mock_server_process.pid}[/dim]`);
      console.print('[cyan]🌐[/cyan] Server should be accessible at http://localhost:5000');
    }
  } else {
    console.print('[red]✗[/red] Mock server generation failed');
  }
  
  // Output Files Summary
  console.print('\n[bold]📁 Generated Files[/bold]');
  console.print(`Output directory: ${state.output_dir}`);
  
  if (state.markdown_files.length > 0) {
    console.print(`Markdown files: ${state.markdown_files.length}`);
    for (const file of state.markdown_files.slice(0, 3)) { // Show first 3
      console.print(`[dim]  • ${path.basename(file)}[/dim]`);
    }
    if (state.markdown_files.length > 3) {
      console.print(`[dim]  • ... and ${state.markdown_files.length - 3} more[/dim]`);
    }
  }
  
  // Errors and Warnings
  if (state.errors.length > 0) {
    console.print('\n[bold][red]❌ Errors[/red][/bold]');
    for (const error of state.errors) {
      console.print(`[red]•[/red] ${error}`);
    }
  }
  
  if (state.warnings.length > 0) {
    console.print('\n[bold][yellow]⚠️ Warnings[/yellow][/bold]');
    for (const warning of state.warnings) {
      console.print(`[yellow]•[/yellow] ${warning}`);
    }
  }
  
  // Next Steps
  console.print('\n[bold]🎯 Next Steps[/bold]');
  
  if (metadata.mock_server_generated && state.mock_server_dir) {
    console.print('1. Test the mock server endpoints');
    console.print('2. Customize the generated responses as needed');
    console.print('3. Integrate with your application');
    console.print(`4. View API documentation: ${path.join(state.mock_server_dir, 'api_docs.md')}`);
  } else if (metadata.spec_generated && state.spec_filepath) {
    console.print('1. Review the generated technical specification');
    console.print('2. Enable mock server generation in configuration');
    console.print('3. Re-run the workflow to generate the mock server');
  } else {
    console.print('1. Check the errors above');
    console.print('2. Verify your configuration');
    console.print('3. Ensure URLs are accessible');
    console.print('4. Re-run the workflow');
  }
  
  // Success indicator
  const overallSuccess = metadata.spec_generated || metadata.mock_server_generated;
  if (overallSuccess) {
    console.print('\n[green][bold]🎉 Workflow completed successfully![/bold][/green]');
  } else {
    console.print('\n[red][bold]❌ Workflow completed with errors[/bold][/red]');
  }
  
  return state;
}