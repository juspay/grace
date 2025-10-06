"""Storage service for managing research sessions and data."""

import json
import os
import base64
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from research_types import ResearchSession, PageData


class StorageService:
    """Service for storing and retrieving research data."""

    def __init__(self, data_directory: str, history_file: str):
        """Initialize storage service.

        Args:
            data_directory: Directory for storing research data
            history_file: Path to history JSON file
        """
        self.data_directory = Path(data_directory)
        self.history_file = Path(history_file)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    async def save_session(self, session: ResearchSession):
        """Save research session data.

        Args:
            session: Research session to save
        """
        session_dir = self.data_directory / session.id
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / 'session.json'
        session_dict = {
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
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, indent=2, ensure_ascii=False)

    async def load_session(self, session_id: str) -> Optional[ResearchSession]:
        """Load research session data.

        Args:
            session_id: Session ID to load

        Returns:
            Research session or None if not found
        """
        try:
            session_file = self.data_directory / session_id / 'session.json'
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            from research_types import ResearchSessionMetadata
            return ResearchSession(
                id=data['id'],
                query=data['query'],
                start_time=data['start_time'],
                end_time=data.get('end_time'),
                status=data['status'],
                total_pages=data['total_pages'],
                max_depth_reached=data['max_depth_reached'],
                final_answer=data.get('final_answer'),
                confidence=data.get('confidence'),
                metadata=ResearchSessionMetadata(**data['metadata'])
            )
        except Exception:
            return None

    async def save_page_data(self, session_id: str, page_data: PageData):
        """Save page data for a session.

        Args:
            session_id: Session ID
            page_data: Page data to save
        """
        session_dir = self.data_directory / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        pages_dir = session_dir / 'pages'
        pages_dir.mkdir(exist_ok=True)

        # Create safe filename from URL
        url_hash = base64.urlsafe_b64encode(page_data.url.encode()).decode()
        filename = f"{url_hash}.json"
        filepath = pages_dir / filename

        page_dict = {
            'url': page_data.url,
            'title': page_data.title,
            'content': page_data.content,
            'links': [
                {
                    'url': link.url,
                    'text': link.text,
                    'context': link.context,
                    'relevance_score': link.relevance_score
                }
                for link in page_data.links
            ],
            'depth': page_data.depth,
            'relevance_score': page_data.relevance_score,
            'fetch_time': page_data.fetch_time,
            'processing_time': page_data.processing_time,
            'ai_content': page_data.ai_content,
            'error': page_data.error,
            'metadata': page_data.metadata
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(page_dict, f, indent=2, ensure_ascii=False)

    async def load_page_data(self, session_id: str, url: str) -> Optional[PageData]:
        """Load page data for a specific URL.

        Args:
            session_id: Session ID
            url: URL of page to load

        Returns:
            Page data or None if not found
        """
        try:
            url_hash = base64.urlsafe_b64encode(url.encode()).decode()
            filename = f"{url_hash}.json"
            filepath = self.data_directory / session_id / 'pages' / filename

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            from research_types import ExtractedLink
            return PageData(
                url=data['url'],
                title=data['title'],
                content=data['content'],
                links=[ExtractedLink(**link) for link in data['links']],
                depth=data['depth'],
                relevance_score=data['relevance_score'],
                fetch_time=data['fetch_time'],
                processing_time=data['processing_time'],
                ai_content=data.get('ai_content'),
                error=data.get('error'),
                metadata=data.get('metadata')
            )
        except Exception:
            return None

    async def load_all_page_data(self, session_id: str) -> List[PageData]:
        """Load all page data for a session.

        Args:
            session_id: Session ID

        Returns:
            List of page data sorted by depth and fetch time
        """
        try:
            pages_dir = self.data_directory / session_id / 'pages'
            pages: List[PageData] = []

            for filepath in pages_dir.glob('*.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                from research_types import ExtractedLink
                page = PageData(
                    url=data['url'],
                    title=data['title'],
                    content=data['content'],
                    links=[ExtractedLink(**link) for link in data['links']],
                    depth=data['depth'],
                    relevance_score=data['relevance_score'],
                    fetch_time=data['fetch_time'],
                    processing_time=data['processing_time'],
                    ai_content=data.get('ai_content'),
                    error=data.get('error'),
                    metadata=data.get('metadata')
                )
                pages.append(page)

            return sorted(pages, key=lambda p: (p.depth, p.fetch_time))
        except Exception:
            return []

    async def save_final_answer(
        self,
        session_id: str,
        answer: str,
        summary: str,
        confidence: float
    ):
        """Save final analysis answer.

        Args:
            session_id: Session ID
            answer: Final answer text
            summary: Summary text
            confidence: Confidence score
        """
        session_dir = self.data_directory / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        analysis_file = session_dir / 'final_analysis.json'
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                'answer': answer,
                'summary': summary,
                'confidence': confidence,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }, f, indent=2, ensure_ascii=False)

        # Save as Markdown
        markdown_file = session_dir / 'final_analysis.md'
        markdown_content = f"""# Research Analysis

## Summary

{summary}

## Detailed Analysis

{answer}

---

**Confidence Level:** {confidence * 100:.1f}%
**Generated:** {datetime.now().isoformat()}
"""
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    async def add_to_history(self, session: ResearchSession):
        """Add session to history.

        Args:
            session: Session to add
        """
        history: List[Dict[str, Any]] = []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            # File doesn't exist or is invalid
            pass

        # Add session to history
        session_dict = {
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
        }
        history.insert(0, session_dict)

        # Keep only last 100 sessions
        history = history[:100]

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    async def get_history(self, limit: int = 20) -> List[ResearchSession]:
        """Get research history.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of research sessions
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            if not isinstance(history, list):
                return []

            from research_types import ResearchSessionMetadata
            sessions = []
            for data in history[:limit]:
                session = ResearchSession(
                    id=data['id'],
                    query=data['query'],
                    start_time=data['start_time'],
                    end_time=data.get('end_time'),
                    status=data['status'],
                    total_pages=data['total_pages'],
                    max_depth_reached=data['max_depth_reached'],
                    final_answer=data.get('final_answer'),
                    confidence=data.get('confidence'),
                    metadata=ResearchSessionMetadata(**data['metadata'])
                )
                sessions.append(session)

            return sessions
        except Exception:
            return []

    async def search_history(self, query: str, limit: int = 10) -> List[ResearchSession]:
        """Search research history.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching research sessions
        """
        history = await self.get_history(100)
        search_term = query.lower()

        return [
            session for session in history
            if search_term in session.query.lower() or
            (session.final_answer and search_term in session.final_answer.lower())
        ][:limit]

    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about research sessions.

        Returns:
            Dictionary with statistics
        """
        try:
            history = await self.get_history(1000)

            total_sessions = len(history)
            completed_sessions = len([s for s in history if s.status == 'completed'])
            total_pages = sum(s.total_pages for s in history)
            total_depth = sum(s.max_depth_reached for s in history)

            average_pages = total_pages / max(total_sessions, 1)
            average_depth = total_depth / max(total_sessions, 1)

            # Calculate storage size
            total_storage_size = self._get_directory_size(self.data_directory)

            return {
                'totalSessions': total_sessions,
                'completedSessions': completed_sessions,
                'averagePages': round(average_pages, 1),
                'averageDepth': round(average_depth, 1),
                'totalStorageSize': total_storage_size
            }
        except Exception:
            return {
                'totalSessions': 0,
                'completedSessions': 0,
                'averagePages': 0,
                'averageDepth': 0,
                'totalStorageSize': 0
            }

    def _get_directory_size(self, dir_path: Path) -> int:
        """Calculate total size of directory recursively.

        Args:
            dir_path: Directory path

        Returns:
            Total size in bytes
        """
        total_size = 0

        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass

        return total_size

    async def cleanup_old_sessions(self, max_age: int = 30 * 24 * 60 * 60 * 1000) -> int:
        """Clean up old sessions.

        Args:
            max_age: Maximum age in milliseconds (default 30 days)

        Returns:
            Number of sessions deleted
        """
        import shutil

        deleted_count = 0
        cutoff_time = datetime.now().timestamp() * 1000 - max_age

        try:
            for session_dir in self.data_directory.iterdir():
                if session_dir.is_dir():
                    mtime = session_dir.stat().st_mtime * 1000
                    if mtime < cutoff_time:
                        shutil.rmtree(session_dir)
                        deleted_count += 1

            # Clean up history
            history = await self.get_history(1000)
            filtered_history = [
                s for s in history
                if s.start_time > cutoff_time
            ]

            if len(filtered_history) != len(history):
                history_dicts = [
                    {
                        'id': s.id,
                        'query': s.query,
                        'start_time': s.start_time,
                        'end_time': s.end_time,
                        'status': s.status,
                        'total_pages': s.total_pages,
                        'max_depth_reached': s.max_depth_reached,
                        'final_answer': s.final_answer,
                        'confidence': s.confidence,
                        'metadata': {
                            'total_links_found': s.metadata.total_links_found,
                            'error_count': s.metadata.error_count,
                            'ai_tokens_used': s.metadata.ai_tokens_used,
                        }
                    }
                    for s in filtered_history
                ]
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(history_dicts, f, indent=2, ensure_ascii=False)

        except Exception as error:
            print(f"Warning: Failed to cleanup old sessions: {error}")

        return deleted_count

    async def export_session(
        self,
        session_id: str,
        format: str = 'json'
    ) -> str:
        """Export session in specified format.

        Args:
            session_id: Session ID to export
            format: Export format ('json', 'markdown', or 'csv')

        Returns:
            Path to exported file

        Raises:
            Exception: If session not found
        """
        session = await self.load_session(session_id)
        if not session:
            raise Exception('Session not found')

        pages = await self.load_all_page_data(session_id)

        export_path = self.data_directory / session_id / f"export.{format}"

        if format == 'json':
            session_dict = {
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
            }
            pages_dict = [
                {
                    'url': p.url,
                    'title': p.title,
                    'content': p.content,
                    'depth': p.depth,
                    'relevance_score': p.relevance_score,
                    'fetch_time': p.fetch_time,
                    'processing_time': p.processing_time,
                    'error': p.error,
                }
                for p in pages
            ]
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump({'session': session_dict, 'pages': pages_dict}, f, indent=2, ensure_ascii=False)

        elif format == 'markdown':
            markdown = self._generate_markdown_report(session, pages)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

        elif format == 'csv':
            csv = self._generate_csv_report(session, pages)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(csv)

        return str(export_path)

    def _generate_markdown_report(self, session: ResearchSession, pages: List[PageData]) -> str:
        """Generate markdown report for session."""
        duration = (session.end_time - session.start_time) / 1000 if session.end_time else 0

        markdown = f"# Research Report: {session.query}\n\n"
        markdown += f"**Session ID:** {session.id}\n"
        markdown += f"**Status:** {session.status}\n"
        markdown += f"**Duration:** {duration:.1f} seconds\n"
        markdown += f"**Pages Processed:** {session.total_pages}\n"
        markdown += f"**Max Depth:** {session.max_depth_reached}\n"
        markdown += f"**Started:** {datetime.fromtimestamp(session.start_time / 1000).isoformat()}\n\n"

        if session.final_answer:
            markdown += f"## Final Answer\n\n{session.final_answer}\n\n"

        markdown += f"## Sources ({len(pages)})\n\n"

        for index, page in enumerate(pages):
            markdown += f"### {index + 1}. {page.title}\n\n"
            markdown += f"**URL:** {page.url}\n"
            markdown += f"**Depth:** {page.depth}\n"
            markdown += f"**Relevance:** {page.relevance_score:.2f}\n"
            markdown += f"**Fetch Time:** {page.fetch_time}ms\n\n"

            if page.content:
                markdown += f"**Content:**\n{page.content[:500]}...\n\n"

            if page.error:
                markdown += f"**Error:** {page.error}\n\n"

            markdown += "---\n\n"

        return markdown

    def _generate_csv_report(self, session: ResearchSession, pages: List[PageData]) -> str:
        """Generate CSV report for session."""
        csv = 'URL,Title,Depth,Relevance,FetchTime,Error,ContentLength\n'

        for page in pages:
            title = (page.title or '').replace('"', '""')
            error = (page.error or '').replace('"', '""')

            csv += f'"{page.url}","{title}",{page.depth},{page.relevance_score},{page.fetch_time},"{error}",{len(page.content)}\n'

        return csv
