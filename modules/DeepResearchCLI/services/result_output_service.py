"""Result output service for generating reports."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from research_types import ResearchSession, PageData


class ResultOutputService:
    """Service for outputting research results."""

    def __init__(self):
        """Initialize result output service."""
        self.output_dir = os.getenv('RESULT_OUTPUT_DIR', './cli/result')
        self.output_format = os.getenv('RESULT_OUTPUT_FORMAT', 'markdown')

    async def save_results(
        self,
        session: ResearchSession,
        name: str,
        all_pages: List[PageData]
    ) -> Dict[str, str]:
        """Save research results.

        Args:
            session: Research session
            name: Name/description for output files
            all_pages: All scraped pages

        Returns:
            Dict with paths to generated files
        """
        # Ensure output directory exists
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        session_dir = output_path / (name or f"session_{session.id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        base_name = f"research_{name or timestamp}"

        result = {}

        # Save as JSON
        if 'json' in self.output_format:
            json_path = session_dir / f"{base_name}.json"
            await self._save_json(json_path, session, all_pages)
            result['jsonPath'] = str(json_path)

        # Save as Markdown
        if 'markdown' not in self.output_format or True:  # Always save markdown
            markdown_path = session_dir / f"{base_name}.md"
            await self._save_markdown(markdown_path, session, all_pages)
            result['markdownPath'] = str(markdown_path)

        # Save as HTML
        if 'html' not in self.output_format or True:  # Always save HTML
            html_path = session_dir / f"{base_name}.html"
            await self._save_html(html_path, session, all_pages)
            result['htmlPath'] = str(html_path)

        return result

    async def _save_json(
        self,
        path: Path,
        session: ResearchSession,
        pages: List[PageData]
    ):
        """Save results as JSON."""
        data = {
            'session': {
                'id': session.id,
                'query': session.query,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'status': session.status,
                'total_pages': session.total_pages,
                'max_depth_reached': session.max_depth_reached,
                'final_answer': session.final_answer,
                'confidence': session.confidence,
                'metadata': {
                    'total_links_found': session.metadata.total_links_found,
                    'error_count': session.metadata.error_count,
                    'ai_tokens_used': session.metadata.ai_tokens_used,
                }
            },
            'pages': [
                {
                    'url': page.url,
                    'title': page.title,
                    'content': page.content[:1000],  # Truncate for JSON
                    'depth': page.depth,
                    'relevance_score': page.relevance_score,
                    'fetch_time': page.fetch_time,
                    'error': page.error,
                }
                for page in pages
            ],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def _save_markdown(
        self,
        path: Path,
        session: ResearchSession,
        pages: List[PageData]
    ):
        """Save results as Markdown."""
        duration = (session.end_time - session.start_time) / 1000 if session.end_time else 0
        successful_pages = [p for p in pages if not p.error]
        avg_relevance = (
            sum(p.relevance_score for p in successful_pages) / len(successful_pages)
            if successful_pages else 0
        )

        markdown = f"""# Deep Research Report

**Query:** {session.query}

**Session ID:** `{session.id}`

**Status:** {self._get_status_badge(session.status)}

"""

        if session.confidence is not None:
            markdown += f"**Confidence Level:** {session.confidence * 100:.1f}%\n\n"

        # Statistics
        markdown += """## 📊 Research Statistics

| Metric | Value |
|--------|-------|
"""
        markdown += f"| Duration | {duration:.1f} seconds |\n"
        markdown += f"| Pages Processed | {session.total_pages} |\n"
        markdown += f"| Max Depth Reached | {session.max_depth_reached} |\n"
        markdown += f"| Total Links Found | {session.metadata.total_links_found} |\n"
        markdown += f"| Successful Fetches | {len(successful_pages)} |\n"
        markdown += f"| Failed Fetches | {session.metadata.error_count} |\n"
        markdown += f"| Average Relevance | {avg_relevance * 100:.1f}% |\n"
        markdown += f"| AI Tokens Used | {session.metadata.ai_tokens_used} |\n\n"

        # Final Answer
        if session.final_answer:
            markdown += """## 🎯 Research Findings

"""
            markdown += f"{session.final_answer}\n\n"

        # Sources
        markdown += f"## 📚 Sources Analyzed ({len(pages)})\n\n"

        # Group by depth
        by_depth: Dict[int, List[PageData]] = {}
        for page in pages:
            if page.depth not in by_depth:
                by_depth[page.depth] = []
            by_depth[page.depth].append(page)

        for depth in sorted(by_depth.keys()):
            depth_pages = sorted(by_depth[depth], key=lambda p: p.relevance_score, reverse=True)
            markdown += f"### Depth Level {depth}\n\n"

            for page in depth_pages:
                rel_pct = page.relevance_score * 100
                status_icon = "❌" if page.error else "✅"
                rel_icon = "🟢" if page.relevance_score >= 0.7 else "🟡" if page.relevance_score >= 0.4 else "🔴"

                markdown += f"#### {status_icon} {page.title}\n\n"
                markdown += f"- **URL:** [{page.url}]({page.url})\n"
                markdown += f"- **Relevance:** {rel_icon} {rel_pct:.1f}%\n"
                markdown += f"- **Fetch Time:** {page.fetch_time}ms\n"
                markdown += f"- **Content Length:** {len(page.content):,} characters\n"

                if page.error:
                    markdown += f"- **Error:** {page.error}\n"
                else:
                    markdown += f"- **Links Found:** {len(page.links)}\n"

                if page.content and not page.error:
                    preview = page.content[:300].replace('\n', ' ')
                    markdown += f"\n**Content Preview:**\n> {preview}...\n"

                markdown += "\n---\n\n"

        # Timeline
        markdown += """## ⏱️ Research Timeline

| Time | Event | Details |
|------|-------|--------|
"""
        start_time = datetime.fromtimestamp(session.start_time / 1000)
        markdown += f"| {start_time.strftime('%H:%M:%S')} | Research Started | Query: \"{session.query}\" |\n"

        if session.end_time:
            end_time = datetime.fromtimestamp(session.end_time / 1000)
            markdown += f"| {end_time.strftime('%H:%M:%S')} | Research {session.status} | Duration: {duration:.1f}s |\n"

        markdown += f"""

## 🔧 Technical Details

- **Generated:** {datetime.now().isoformat()}
- **CLI Version:** 1.0.0
- **Research Method:** Deep Web Research with AI Analysis
"""

        with open(path, 'w', encoding='utf-8') as f:
            f.write(markdown)

    async def _save_html(
        self,
        path: Path,
        session: ResearchSession,
        pages: List[PageData]
    ):
        """Save results as HTML."""
        duration = (session.end_time - session.start_time) / 1000 if session.end_time else 0
        successful_pages = [p for p in pages if not p.error]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Research Report - {self._escape_html(session.query)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8fafc;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-item {{
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #6b7280;
            font-size: 0.9em;
        }}
        .final-answer {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            white-space: pre-wrap;
        }}
        .sources-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .source-item {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .relevance-high {{ border-left: 4px solid #10b981; }}
        .relevance-medium {{ border-left: 4px solid #f59e0b; }}
        .relevance-low {{ border-left: 4px solid #ef4444; }}
        .content-preview {{
            background: #f8fafc;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Deep Research Report</h1>
        <p><strong>Query:</strong> {self._escape_html(session.query)}</p>
        <p><strong>Session ID:</strong> <code>{session.id}</code></p>
        <p><strong>Status:</strong> {session.status.upper()}</p>
"""

        if session.confidence is not None:
            html += f"        <p><strong>Confidence:</strong> {session.confidence * 100:.1f}%</p>\n"

        html += f"""    </div>

    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-value">{duration:.1f}s</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{session.total_pages}</div>
            <div class="stat-label">Pages</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{session.max_depth_reached}</div>
            <div class="stat-label">Max Depth</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{len(successful_pages)}</div>
            <div class="stat-label">Successful</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{session.metadata.error_count}</div>
            <div class="stat-label">Errors</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{session.metadata.ai_tokens_used}</div>
            <div class="stat-label">AI Tokens</div>
        </div>
    </div>
"""

        if session.final_answer:
            html += f"""
    <div class="final-answer">
        <h2>🎯 Research Findings</h2>
        <div>{self._escape_html(session.final_answer)}</div>
    </div>
"""

        html += f"""
    <div class="sources-section">
        <h2>📚 Sources Analyzed ({len(pages)})</h2>
"""

        # Group by depth
        by_depth: Dict[int, List[PageData]] = {}
        for page in pages:
            if page.depth not in by_depth:
                by_depth[page.depth] = []
            by_depth[page.depth].append(page)

        for depth in sorted(by_depth.keys()):
            depth_pages = sorted(by_depth[depth], key=lambda p: p.relevance_score, reverse=True)
            html += f"        <h3>Depth Level {depth} ({len(depth_pages)} sources)</h3>\n"

            for page in depth_pages:
                rel_class = "relevance-high" if page.relevance_score >= 0.7 else "relevance-medium" if page.relevance_score >= 0.4 else "relevance-low"
                status_icon = "❌" if page.error else "✅"
                rel_pct = page.relevance_score * 100

                html += f"""
        <div class="source-item {rel_class}">
            <h4>{status_icon} {self._escape_html(page.title)}</h4>
            <p><strong>URL:</strong> <a href="{page.url}" target="_blank">{self._escape_html(page.url)}</a></p>
            <p><strong>Relevance:</strong> {rel_pct:.1f}% | <strong>Fetch Time:</strong> {page.fetch_time}ms | <strong>Content:</strong> {len(page.content):,} chars</p>
"""

                if page.error:
                    html += f"            <p style='color: #ef4444;'><strong>Error:</strong> {self._escape_html(page.error)}</p>\n"

                if page.content and not page.error:
                    preview = page.content[:300].replace('\n', ' ')
                    html += f"""            <div class="content-preview">{self._escape_html(preview)}...</div>\n"""

                html += "        </div>\n"

        html += """    </div>

    <div style="text-align: center; margin-top: 30px; color: #6b7280; font-size: 0.9em;">
        <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """ by Grace Deep Research CLI v1.0.0</p>
    </div>
</body>
</html>"""

        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _get_status_badge(self, status: str) -> str:
        """Get status badge for markdown."""
        badges = {
            'completed': '✅ COMPLETED',
            'failed': '❌ FAILED',
            'cancelled': '⚠️  CANCELLED',
            'running': '🔄 RUNNING'
        }
        return badges.get(status, status.upper())

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
