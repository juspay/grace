import * as fs from "fs-extra";
import * as path from "path";
import { ResearchSession, PageData } from "../types";
import chalk from "chalk";

export class ResultOutputService {
  private outputDir: string;
  private outputFormat: string;

  constructor() {
    this.outputDir = process.env.RESULT_OUTPUT_DIR || "./cli/result";
    this.outputFormat = process.env.RESULT_OUTPUT_FORMAT || "markdown";
  }

  async saveResults(
    session: ResearchSession,
    name: string,
    allPages: PageData[]
  ): Promise<{
    htmlPath?: string;
    jsonPath?: string;
    markdownPath?: string;
  }> {
    // Ensure output directory exists
    await fs.ensureDir(this.outputDir);

    const sessionDir = path.join(
      this.outputDir,
      name || `session_${session.id}`
    );
    await fs.ensureDir(sessionDir);
    let result = {
      htmlPath: "",
      jsonPath: "",
      markdownPath: "",
    };

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const baseName = `research_${name || timestamp}`;

    // Save as JSON
    if (this.outputFormat.includes("json")) {
      const jsonPath = path.join(sessionDir, `${baseName}.json`);

      await fs.writeJson(
        jsonPath,
        {
          session,
          pages: allPages,
          metadata: {
            generatedAt: new Date().toISOString(),
            version: "1.0.0",
          },
        },
        { spaces: 2 }
      );
      result.jsonPath = jsonPath;
    }

    // Save as Markdown
    if (!this.outputFormat.includes("markdown")) {
      const markdownPath = path.join(sessionDir, `${baseName}.md`);
      const markdownContent = this.generateMarkdownReport(session, allPages);
      await fs.writeFile(markdownPath, markdownContent);
      result.markdownPath = markdownPath;
    }

    // Save as HTML
    if (!this.outputFormat.includes("html")) {
      const htmlPath = path.join(sessionDir, `${baseName}.html`);
      const htmlContent = this.generateHTMLReport(session, allPages);
      await fs.writeFile(htmlPath, htmlContent);
      result.htmlPath = htmlPath;
    }

    return result;
  }

  private generateMarkdownReport(
    session: ResearchSession,
    pages: PageData[]
  ): string {
    const duration = session.endTime
      ? (session.endTime - session.startTime) / 1000
      : 0;
    const successfulPages = pages.filter((p) => !p.error);
    const averageRelevance =
      successfulPages.length > 0
        ? successfulPages.reduce((sum, p) => sum + p.relevanceScore, 0) /
          successfulPages.length
        : 0;

    let markdown = `# Deep Research Report\n\n`;
    markdown += `**Query:** ${session.query}\n\n`;
    markdown += `**Session ID:** \`${session.id}\`\n\n`;
    markdown += `**Status:** ${this.getStatusBadge(session.status)}\n\n`;

    if (session.confidence !== undefined) {
      markdown += `**Confidence Level:** ${(session.confidence * 100).toFixed(1)}%\n\n`;
    }

    // Statistics
    markdown += `## 📊 Research Statistics\n\n`;
    markdown += `| Metric | Value |\n`;
    markdown += `|--------|-------|\n`;
    markdown += `| Duration | ${duration.toFixed(1)} seconds |\n`;
    markdown += `| Pages Processed | ${session.totalPages} |\n`;
    markdown += `| Max Depth Reached | ${session.maxDepthReached} |\n`;
    markdown += `| Total Links Found | ${session.metadata.totalLinksFound} |\n`;
    markdown += `| Successful Fetches | ${successfulPages.length} |\n`;
    markdown += `| Failed Fetches | ${session.metadata.errorCount} |\n`;
    markdown += `| Average Relevance | ${(averageRelevance * 100).toFixed(1)}% |\n`;
    markdown += `| AI Tokens Used | ${session.metadata.aiTokensUsed} |\n\n`;

    // Final Answer
    if (session.finalAnswer) {
      markdown += `## 🎯 Research Findings\n\n`;
      markdown += `${session.finalAnswer}\n\n`;
    }

    // Source Analysis
    markdown += `## 📚 Sources Analyzed (${pages.length})\n\n`;

    // Group sources by depth
    const sourcesByDepth = new Map<number, PageData[]>();
    pages.forEach((page) => {
      if (!sourcesByDepth.has(page.depth)) {
        sourcesByDepth.set(page.depth, []);
      }
      sourcesByDepth.get(page.depth)!.push(page);
    });

    Array.from(sourcesByDepth.keys())
      .sort()
      .forEach((depth) => {
        const depthPages = sourcesByDepth
          .get(depth)!
          .sort((a, b) => b.relevanceScore - a.relevanceScore);

        markdown += `### Depth Level ${depth}\n\n`;

        depthPages.forEach((page, index) => {
          const relevancePercent = (page.relevanceScore * 100).toFixed(1);
          const statusIcon = page.error ? "❌" : "✅";
          const relevanceIcon =
            page.relevanceScore >= 0.7
              ? "🟢"
              : page.relevanceScore >= 0.4
                ? "🟡"
                : "🔴";

          markdown += `#### ${index + 1}. ${page.title} ${statusIcon}\n\n`;
          markdown += `- **URL:** [${page.url}](${page.url})\n`;
          markdown += `- **Relevance:** ${relevanceIcon} ${relevancePercent}%\n`;
          markdown += `- **Fetch Time:** ${page.fetchTime}ms\n`;
          markdown += `- **Content Length:** ${page.content.length.toLocaleString()} characters\n`;

          if (page.error) {
            markdown += `- **Error:** ${page.error}\n`;
          } else {
            markdown += `- **Links Found:** ${page.links.length}\n`;
          }

          if (page.content && !page.error) {
            const preview = page.content.substring(0, 300).replace(/\n/g, " ");
            markdown += `\n**Content Preview:**\n> ${preview}...\n`;
          }

          markdown += `\n---\n\n`;
        });
      });

    // Research Timeline
    markdown += `## ⏱️ Research Timeline\n\n`;
    markdown += `| Time | Event | Details |\n`;
    markdown += `|------|-------|--------|\n`;

    const startTime = new Date(session.startTime);
    markdown += `| ${startTime.toLocaleTimeString()} | Research Started | Query: "${session.query}" |\n`;

    if (session.endTime) {
      const endTime = new Date(session.endTime);
      markdown += `| ${endTime.toLocaleTimeString()} | Research ${session.status} | Duration: ${duration.toFixed(1)}s |\n`;
    }

    markdown += `\n## 🔧 Technical Details\n\n`;
    markdown += `- **Generated:** ${new Date().toISOString()}\n`;
    markdown += `- **CLI Version:** 1.0.0\n`;
    markdown += `- **Research Method:** Deep Web Research with AI Analysis\n`;

    return markdown;
  }

  private generateHTMLReport(
    session: ResearchSession,
    pages: PageData[]
  ): string {
    const duration = session.endTime
      ? (session.endTime - session.startTime) / 1000
      : 0;
    const successfulPages = pages.filter((p) => !p.error);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Research Report - ${session.query}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8fafc;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }
        .session-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .info-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .info-card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status-completed { background: #10b981; color: white; }
        .status-failed { background: #ef4444; color: white; }
        .status-cancelled { background: #f59e0b; color: white; }
        .status-running { background: #3b82f6; color: white; }
        .final-answer {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .sources-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .source-item {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .source-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .relevance-high { border-left: 4px solid #10b981; }
        .relevance-medium { border-left: 4px solid #f59e0b; }
        .relevance-low { border-left: 4px solid #ef4444; }
        .depth-badge {
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .error-text {
            color: #ef4444;
            font-style: italic;
        }
        .content-preview {
            background: #f8fafc;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #6b7280;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-item {
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #6b7280;
            font-size: 0.9em;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .header { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Deep Research Report</h1>
        <p><strong>Query:</strong> ${this.escapeHtml(session.query)}</p>
        <p><strong>Session ID:</strong> <code>${session.id}</code></p>
        <p><strong>Status:</strong> <span class="status-badge status-${session.status}">${session.status.toUpperCase()}</span></p>
        ${session.confidence !== undefined ? `<p><strong>Confidence:</strong> ${(session.confidence * 100).toFixed(1)}%</p>` : ""}
    </div>

    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-value">${duration.toFixed(1)}s</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${session.totalPages}</div>
            <div class="stat-label">Pages</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${session.maxDepthReached}</div>
            <div class="stat-label">Max Depth</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${successfulPages.length}</div>
            <div class="stat-label">Successful</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${session.metadata.errorCount}</div>
            <div class="stat-label">Errors</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${session.metadata.aiTokensUsed}</div>
            <div class="stat-label">AI Tokens</div>
        </div>
    </div>

    ${
      session.finalAnswer
        ? `
    <div class="final-answer">
        <h2>🎯 Research Findings</h2>
        <div>${this.formatTextAsHtml(session.finalAnswer)}</div>
    </div>
    `
        : ""
    }

    <div class="sources-section">
        <h2>📚 Sources Analyzed (${pages.length})</h2>
        ${this.generateSourcesHTML(pages)}
    </div>

    <div style="text-align: center; margin-top: 30px; color: #6b7280; font-size: 0.9em;">
        <p>Generated on ${new Date().toLocaleString()} by Grace Deep Research CLI v1.0.0</p>
    </div>

    <script>
        // Add click handlers for collapsible content
        document.querySelectorAll('.source-item').forEach(item => {
            const preview = item.querySelector('.content-preview');
            if (preview) {
                preview.style.cursor = 'pointer';
                preview.addEventListener('click', () => {
                    if (preview.style.maxHeight === '100px') {
                        preview.style.maxHeight = 'none';
                        preview.style.overflow = 'visible';
                    } else {
                        preview.style.maxHeight = '100px';
                        preview.style.overflow = 'hidden';
                    }
                });
            }
        });
    </script>
</body>
</html>`;
  }

  private generateSourcesHTML(pages: PageData[]): string {
    const sourcesByDepth = new Map<number, PageData[]>();
    pages.forEach((page) => {
      if (!sourcesByDepth.has(page.depth)) {
        sourcesByDepth.set(page.depth, []);
      }
      sourcesByDepth.get(page.depth)!.push(page);
    });

    let html = "";
    Array.from(sourcesByDepth.keys())
      .sort()
      .forEach((depth) => {
        const depthPages = sourcesByDepth
          .get(depth)!
          .sort((a, b) => b.relevanceScore - a.relevanceScore);

        html += `<h3>Depth Level ${depth} (${depthPages.length} sources)</h3>`;

        depthPages.forEach((page, index) => {
          const relevanceClass =
            page.relevanceScore >= 0.7
              ? "relevance-high"
              : page.relevanceScore >= 0.4
                ? "relevance-medium"
                : "relevance-low";

          const statusIcon = page.error ? "❌" : "✅";
          const relevancePercent = (page.relevanceScore * 100).toFixed(1);

          html += `
        <div class="source-item ${relevanceClass}">
            <h4>${statusIcon} ${this.escapeHtml(page.title)} <span class="depth-badge">Depth ${page.depth}</span></h4>
            <p><strong>URL:</strong> <a href="${page.url}" target="_blank">${this.escapeHtml(page.url)}</a></p>
            <p><strong>Relevance:</strong> ${relevancePercent}% | <strong>Fetch Time:</strong> ${page.fetchTime}ms | <strong>Content:</strong> ${page.content.length.toLocaleString()} chars</p>
            ${page.error ? `<p class="error-text"><strong>Error:</strong> ${this.escapeHtml(page.error)}</p>` : ""}
            ${
              page.content && !page.error
                ? `
            <div class="content-preview" style="max-height: 100px; overflow: hidden;">
                <strong>Content Preview:</strong><br>
                ${this.escapeHtml(page.content.substring(0, 500))}...
                <br><small><em>Click to expand/collapse</em></small>
            </div>
            `
                : ""
            }
        </div>
        `;
        });
      });

    return html;
  }

  private getStatusBadge(status: string): string {
    const badges = {
      completed: "✅ Completed",
      failed: "❌ Failed",
      cancelled: "⚠️ Cancelled",
      running: "🔄 Running",
    };
    return badges[status as keyof typeof badges] || status;
  }

  private escapeHtml(text: string): string {
    // Node.js environment - use manual escaping
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  private formatTextAsHtml(text: string): string {
    return text
      .split("\n")
      .map((line) => {
        if (line.startsWith("#")) {
          const level = line.match(/^#+/)?.[0].length || 1;
          const content = line.replace(/^#+\s*/, "");
          return `<h${Math.min(level + 1, 6)}>${this.escapeHtml(content)}</h${Math.min(level + 1, 6)}>`;
        }
        if (line.trim() === "") {
          return "<br>";
        }
        return `<p>${this.escapeHtml(line)}</p>`;
      })
      .join("");
  }

  public getOutputDirectory(): string {
    return this.outputDir;
  }

  public async openResult(htmlPath: string): Promise<void> {
    const absolutePath = path.resolve(htmlPath);
    console.log("\n" + chalk.green("📁 Research results saved:"));
    console.log(chalk.cyan(`   HTML Report: ${absolutePath}`));
    console.log(
      chalk.cyan(`   JSON Data: ${htmlPath.replace(".html", ".json")}`)
    );
    console.log(chalk.cyan(`   Markdown: ${htmlPath.replace(".html", ".md")}`));
    console.log("\n" + chalk.yellow("💡 To view the HTML report:"));
    console.log(chalk.white(`   open "${absolutePath}"`));
    console.log(chalk.gray("   (or paste the path into your browser)"));
  }
}
