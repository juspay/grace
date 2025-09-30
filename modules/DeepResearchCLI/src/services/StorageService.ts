import * as fs from 'fs-extra';
import * as path from 'path';
import { ResearchSession, PageData } from '../types';

export class StorageService {
  private dataDirectory: string;
  private historyFile: string;

  constructor(dataDirectory: string, historyFile: string) {
    this.dataDirectory = dataDirectory;
    this.historyFile = historyFile;
    this.ensureDirectories();
  }

  private async ensureDirectories(): Promise<void> {
    await fs.ensureDir(this.dataDirectory);
    await fs.ensureDir(path.dirname(this.historyFile));
  }

  async saveSession(session: ResearchSession): Promise<void> {
    const sessionDir = path.join(this.dataDirectory, session.id);
    await fs.ensureDir(sessionDir);

    const sessionFile = path.join(sessionDir, 'session.json');
    await fs.writeJson(sessionFile, session, { spaces: 2 });
  }

  async loadSession(sessionId: string): Promise<ResearchSession | null> {
    try {
      const sessionFile = path.join(this.dataDirectory, sessionId, 'session.json');
      return await fs.readJson(sessionFile);
    } catch (error) {
      return null;
    }
  }

  async savePageData(sessionId: string, pageData: PageData): Promise<void> {
    const sessionDir = path.join(this.dataDirectory, sessionId);
    await fs.ensureDir(sessionDir);

    const pagesDir = path.join(sessionDir, 'pages');
    await fs.ensureDir(pagesDir);

    // Create a safe filename from URL
    const urlHash = Buffer.from(pageData.url).toString('base64url');
    const filename = `${urlHash}.json`;
    const filepath = path.join(pagesDir, filename);

    await fs.writeJson(filepath, pageData, { spaces: 2 });
  }

  async loadPageData(sessionId: string, url: string): Promise<PageData | null> {
    try {
      const urlHash = Buffer.from(url).toString('base64url');
      const filename = `${urlHash}.json`;
      const filepath = path.join(this.dataDirectory, sessionId, 'pages', filename);
      return await fs.readJson(filepath);
    } catch (error) {
      return null;
    }
  }

  async loadAllPageData(sessionId: string): Promise<PageData[]> {
    try {
      const pagesDir = path.join(this.dataDirectory, sessionId, 'pages');
      const files = await fs.readdir(pagesDir);
      const pages: PageData[] = [];

      for (const file of files) {
        if (file.endsWith('.json')) {
          const filepath = path.join(pagesDir, file);
          const pageData = await fs.readJson(filepath);
          pages.push(pageData);
        }
      }

      return pages.sort((a, b) => a.depth - b.depth || a.fetchTime - b.fetchTime);
    } catch (error) {
      return [];
    }
  }

  async saveFinalAnswer(sessionId: string, answer: string, summary: string, confidence: number): Promise<void> {
    const sessionDir = path.join(this.dataDirectory, sessionId);
    await fs.ensureDir(sessionDir);

    const analysisFile = path.join(sessionDir, 'final_analysis.json');
    await fs.writeJson(analysisFile, {
      answer,
      summary,
      confidence,
      timestamp: Date.now()
    }, { spaces: 2 });

    // Also save as markdown for easy reading
    const markdownFile = path.join(sessionDir, 'final_analysis.md');
    const markdownContent = `# Research Analysis\n\n## Summary\n\n${summary}\n\n## Detailed Analysis\n\n${answer}\n\n---\n\n**Confidence Level:** ${(confidence * 100).toFixed(1)}%\n**Generated:** ${new Date().toISOString()}`;
    await fs.writeFile(markdownFile, markdownContent);
  }

  async addToHistory(session: ResearchSession): Promise<void> {
    let history: ResearchSession[] = [];

    try {
      history = await fs.readJson(this.historyFile);
    } catch (error) {
      // File doesn't exist or is invalid, start with empty array
    }

    // Add session to history
    history.unshift(session);

    // Keep only last 100 sessions
    history = history.slice(0, 100);

    await fs.writeJson(this.historyFile, history, { spaces: 2 });
  }

  async getHistory(limit: number = 20): Promise<ResearchSession[]> {
    try {
      const history = await fs.readJson(this.historyFile);
      return Array.isArray(history) ? history.slice(0, limit) : [];
    } catch (error) {
      return [];
    }
  }

  async searchHistory(query: string, limit: number = 10): Promise<ResearchSession[]> {
    const history = await this.getHistory(100);
    const searchTerm = query.toLowerCase();

    return history
      .filter(session =>
        session.query.toLowerCase().includes(searchTerm) ||
        session.finalAnswer?.toLowerCase().includes(searchTerm)
      )
      .slice(0, limit);
  }

  async getSessionStatistics(): Promise<{
    totalSessions: number;
    completedSessions: number;
    averagePages: number;
    averageDepth: number;
    totalStorageSize: number;
  }> {
    try {
      const history = await this.getHistory(1000);

      const totalSessions = history.length;
      const completedSessions = history.filter(s => s.status === 'completed').length;
      const averagePages = history.reduce((sum, s) => sum + s.totalPages, 0) / Math.max(totalSessions, 1);
      const averageDepth = history.reduce((sum, s) => sum + s.maxDepthReached, 0) / Math.max(totalSessions, 1);

      // Calculate storage size
      let totalStorageSize = 0;
      try {
        const stat = await fs.stat(this.dataDirectory);
        totalStorageSize = await this.getDirectorySize(this.dataDirectory);
      } catch (error) {
        // Directory doesn't exist or can't be accessed
      }

      return {
        totalSessions,
        completedSessions,
        averagePages: Math.round(averagePages * 10) / 10,
        averageDepth: Math.round(averageDepth * 10) / 10,
        totalStorageSize
      };
    } catch (error) {
      return {
        totalSessions: 0,
        completedSessions: 0,
        averagePages: 0,
        averageDepth: 0,
        totalStorageSize: 0
      };
    }
  }

  private async getDirectorySize(dirPath: string): Promise<number> {
    let totalSize = 0;

    try {
      const items = await fs.readdir(dirPath);

      for (const item of items) {
        const itemPath = path.join(dirPath, item);
        const stat = await fs.stat(itemPath);

        if (stat.isDirectory()) {
          totalSize += await this.getDirectorySize(itemPath);
        } else {
          totalSize += stat.size;
        }
      }
    } catch (error) {
      // Error reading directory, return 0
    }

    return totalSize;
  }

  async cleanupOldSessions(maxAge: number = 30 * 24 * 60 * 60 * 1000): Promise<number> {
    // Clean up sessions older than maxAge (default 30 days)
    let deletedCount = 0;

    try {
      const sessions = await fs.readdir(this.dataDirectory);
      const cutoffTime = Date.now() - maxAge;

      for (const sessionDir of sessions) {
        const sessionPath = path.join(this.dataDirectory, sessionDir);
        const stat = await fs.stat(sessionPath);

        if (stat.isDirectory() && stat.mtime.getTime() < cutoffTime) {
          await fs.remove(sessionPath);
          deletedCount++;
        }
      }

      // Also clean up history
      const history = await this.getHistory(1000);
      const filteredHistory = history.filter(session => session.startTime > cutoffTime);

      if (filteredHistory.length !== history.length) {
        await fs.writeJson(this.historyFile, filteredHistory, { spaces: 2 });
      }
    } catch (error) {
      console.warn('Failed to cleanup old sessions:', error);
    }

    return deletedCount;
  }

  async exportSession(sessionId: string, format: 'json' | 'markdown' | 'csv' = 'json'): Promise<string> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    const pages = await this.loadAllPageData(sessionId);

    const exportPath = path.join(this.dataDirectory, sessionId, `export.${format}`);

    if (format === 'json') {
      await fs.writeJson(exportPath, { session, pages }, { spaces: 2 });
    } else if (format === 'markdown') {
      const markdown = this.generateMarkdownReport(session, pages);
      await fs.writeFile(exportPath, markdown);
    } else if (format === 'csv') {
      const csv = this.generateCSVReport(session, pages);
      await fs.writeFile(exportPath, csv);
    }

    return exportPath;
  }

  private generateMarkdownReport(session: ResearchSession, pages: PageData[]): string {
    const duration = session.endTime ? (session.endTime - session.startTime) / 1000 : 0;

    let markdown = `# Research Report: ${session.query}\n\n`;
    markdown += `**Session ID:** ${session.id}\n`;
    markdown += `**Status:** ${session.status}\n`;
    markdown += `**Duration:** ${duration.toFixed(1)} seconds\n`;
    markdown += `**Pages Processed:** ${session.totalPages}\n`;
    markdown += `**Max Depth:** ${session.maxDepthReached}\n`;
    markdown += `**Started:** ${new Date(session.startTime).toISOString()}\n\n`;

    if (session.finalAnswer) {
      markdown += `## Final Answer\n\n${session.finalAnswer}\n\n`;
    }

    markdown += `## Sources (${pages.length})\n\n`;

    pages.forEach((page, index) => {
      markdown += `### ${index + 1}. ${page.title}\n\n`;
      markdown += `**URL:** ${page.url}\n`;
      markdown += `**Depth:** ${page.depth}\n`;
      markdown += `**Relevance:** ${page.relevanceScore.toFixed(2)}\n`;
      markdown += `**Fetch Time:** ${page.fetchTime}ms\n\n`;

      if (page.content) {
        markdown += `**Content:**\n${page.content.substring(0, 500)}...\n\n`;
      }

      if (page.error) {
        markdown += `**Error:** ${page.error}\n\n`;
      }

      markdown += `---\n\n`;
    });

    return markdown;
  }

  private generateCSVReport(session: ResearchSession, pages: PageData[]): string {
    let csv = 'URL,Title,Depth,Relevance,FetchTime,Error,ContentLength\n';

    pages.forEach(page => {
      const title = (page.title || '').replace(/"/g, '""');
      const error = (page.error || '').replace(/"/g, '""');

      csv += `"${page.url}","${title}",${page.depth},${page.relevanceScore},${page.fetchTime},"${error}",${page.content.length}\n`;
    });

    return csv;
  }
}