import * as fs from 'fs-extra';
import * as path from 'path';

export class DebugLogger {
  private static instance: DebugLogger;
  private isDebugEnabled: boolean;
  private debugLogFile: string;
  private logStream: fs.WriteStream | null = null;

  private constructor() {
    this.isDebugEnabled = process.env.IS_DEBUG === 'true';
    this.debugLogFile = process.env.DEBUG_LOG_FILE || './search_query_time.log';

    if (this.isDebugEnabled) {
      this.initializeLogStream();
    }
  }

  static getInstance(): DebugLogger {
    if (!DebugLogger.instance) {
      DebugLogger.instance = new DebugLogger();
    }
    return DebugLogger.instance;
  }

  private async initializeLogStream(): Promise<void> {
    try {
      // Ensure directory exists
      await fs.ensureDir(path.dirname(this.debugLogFile));

      // Create or append to log file
      this.logStream = fs.createWriteStream(this.debugLogFile, { flags: 'a' });

      // Add session separator
      this.writeToStream(`\n${'='.repeat(80)}\n`);
      this.writeToStream(`DEBUG SESSION STARTED: ${new Date().toISOString()}\n`);
      this.writeToStream(`${'='.repeat(80)}\n\n`);
    } catch (error) {
      console.warn('Failed to initialize debug log stream:', error);
      this.isDebugEnabled = false;
    }
  }

  private writeToStream(message: string): void {
    if (this.logStream && !this.logStream.destroyed) {
      this.logStream.write(message);
    }
  }

  public logSearchQuery(query: string, startTime: number): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `[${timestamp}] SEARCH_QUERY_START: "${query}"\n`;
    this.writeToStream(message);
  }

  public logSearchResult(query: string, results: any[], duration: number): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `[${timestamp}] SEARCH_QUERY_END: "${query}" | Results: ${results.length} | Duration: ${duration}ms\n`;
    this.writeToStream(message);

    // Log top 3 results
    results.slice(0, 3).forEach((result, index) => {
      this.writeToStream(`  ${index + 1}. ${result.title} (${result.url}) - Score: ${result.score}\n`);
    });
    this.writeToStream('\n');
  }

  public logPageFetch(url: string, startTime: number): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `[${timestamp}] PAGE_FETCH_START: ${url}\n`;
    this.writeToStream(message);
  }

  public logPageFetchResult(url: string, success: boolean, duration: number, contentLength?: number, error?: string): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const status = success ? 'SUCCESS' : 'FAILED';
    const message = `[${timestamp}] PAGE_FETCH_END: ${url} | Status: ${status} | Duration: ${duration}ms`;

    if (success && contentLength !== undefined) {
      this.writeToStream(`${message} | Content: ${contentLength} chars\n`);
    } else if (!success && error) {
      this.writeToStream(`${message} | Error: ${error}\n`);
    } else {
      this.writeToStream(`${message}\n`);
    }
  }

  public logAICall(operation: string, inputLength: number, startTime: number): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `[${timestamp}] AI_CALL_START: ${operation} | Input: ${inputLength} chars\n`;
    this.writeToStream(message);
  }

  public logAICallResult(operation: string, success: boolean, duration: number, tokensUsed?: number, outputLength?: number, error?: string): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const status = success ? 'SUCCESS' : 'FAILED';
    let message = `[${timestamp}] AI_CALL_END: ${operation} | Status: ${status} | Duration: ${duration}ms`;

    if (success) {
      if (tokensUsed !== undefined) message += ` | Tokens: ${tokensUsed}`;
      if (outputLength !== undefined) message += ` | Output: ${outputLength} chars`;
    } else if (error) {
      message += ` | Error: ${error}`;
    }

    this.writeToStream(`${message}\n`);
  }

  public logDepthTransition(fromDepth: number, toDepth: number, linksFound: number): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `[${timestamp}] DEPTH_TRANSITION: ${fromDepth} → ${toDepth} | Links: ${linksFound}\n`;
    this.writeToStream(message);
  }

  public logSessionSummary(sessionId: string, totalPages: number, maxDepth: number, duration: number, status: string): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const message = `\n[${timestamp}] SESSION_SUMMARY: ${sessionId}\n`;
    this.writeToStream(message);
    this.writeToStream(`  Status: ${status}\n`);
    this.writeToStream(`  Duration: ${duration}ms (${(duration / 1000).toFixed(2)}s)\n`);
    this.writeToStream(`  Pages Processed: ${totalPages}\n`);
    this.writeToStream(`  Max Depth: ${maxDepth}\n`);
    this.writeToStream(`${'='.repeat(50)}\n\n`);
  }

  public logUserAction(action: string, data?: any): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    let message = `[${timestamp}] USER_ACTION: ${action}`;
    if (data) {
      message += ` | Data: ${JSON.stringify(data)}`;
    }
    this.writeToStream(`${message}\n`);
  }

  public logError(context: string, error: Error | string): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    const errorMessage = error instanceof Error ? error.message : error;
    const stackTrace = error instanceof Error ? error.stack : '';

    this.writeToStream(`[${timestamp}] ERROR: ${context} | ${errorMessage}\n`);
    if (stackTrace) {
      this.writeToStream(`Stack Trace:\n${stackTrace}\n`);
    }
    this.writeToStream('\n');
  }

  /**
   * Generic logging method for any message
   */
  public log(message: string): void {
    if (!this.isDebugEnabled) return;

    const timestamp = new Date().toISOString();
    this.writeToStream(`[${timestamp}] ${message}\n`);
  }

  public close(): void {
    if (this.logStream && !this.logStream.destroyed) {
      const timestamp = new Date().toISOString();
      this.writeToStream(`\n[${timestamp}] DEBUG SESSION ENDED\n`);
      this.writeToStream(`${'='.repeat(80)}\n\n`);
      this.logStream.end();
      this.logStream = null;
    }
  }

  public isEnabled(): boolean {
    return this.isDebugEnabled;
  }

  public getLogFilePath(): string {
    return this.debugLogFile;
  }
}