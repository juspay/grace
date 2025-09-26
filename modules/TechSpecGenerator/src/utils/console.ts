/**
 * Console utilities with colored output (similar to Rich console)
 */

import chalk from 'chalk';

export class Console {
  print(message: string): void {
    // Parse Rich-style markup and convert to chalk
    const parsed = this.parseRichMarkup(message);
    process.stdout.write(parsed + '\n');
  }

  private parseRichMarkup(text: string): string {
    return text
      // Combined styles (order matters - do combined first)
      .replace(/\[bold blue\](.*?)\[\/bold blue\]/g, chalk.bold.blue('$1'))
      .replace(/\[bold red\](.*?)\[\/bold red\]/g, chalk.bold.red('$1'))
      .replace(/\[bold green\](.*?)\[\/bold green\]/g, chalk.bold.green('$1'))
      .replace(/\[bold yellow\](.*?)\[\/bold yellow\]/g, chalk.bold.yellow('$1'))
      .replace(/\[bold cyan\](.*?)\[\/bold cyan\]/g, chalk.bold.cyan('$1'))
      .replace(/\[bold magenta\](.*?)\[\/bold magenta\]/g, chalk.bold.magenta('$1'))
      
      // Single styles
      .replace(/\[bold\](.*?)\[\/bold\]/g, chalk.bold('$1'))
      .replace(/\[red\](.*?)\[\/red\]/g, chalk.red('$1'))
      .replace(/\[green\](.*?)\[\/green\]/g, chalk.green('$1'))
      .replace(/\[yellow\](.*?)\[\/yellow\]/g, chalk.yellow('$1'))
      .replace(/\[blue\](.*?)\[\/blue\]/g, chalk.blue('$1'))
      .replace(/\[dim\](.*?)\[\/dim\]/g, chalk.dim('$1'))
      .replace(/\[cyan\](.*?)\[\/cyan\]/g, chalk.cyan('$1'))
      .replace(/\[magenta\](.*?)\[\/magenta\]/g, chalk.magenta('$1'));
  }

  error(message: string): void {
    this.print(`[red]Error:[/red] ${message}`);
  }

  warn(message: string): void {
    this.print(`[yellow]Warning:[/yellow] ${message}`);
  }

  success(message: string): void {
    this.print(`[green]✓[/green] ${message}`);
  }

  info(message: string): void {
    this.print(`[blue]ℹ[/blue] ${message}`);
  }
}

export const console = new Console();