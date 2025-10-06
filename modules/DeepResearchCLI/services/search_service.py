"""Search service using SearxNG."""

import os
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import httpx

from research_types import SearchResult
from utils.debug_logger import DebugLogger


class SearchService:
    """Service for performing web searches using SearxNG."""

    def __init__(self, searxng_base_url: Optional[str] = None):
        """Initialize search service.

        Args:
            searxng_base_url: Base URL for SearxNG instance
        """
        self.searxng_base_url = searxng_base_url or os.getenv('SEARXNG_BASE_URL', 'http://localhost:8080')
        self.debug_logger = DebugLogger.get_instance()

    async def search(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Perform a search query.

        Args:
            query: Search query string
            engines: List of search engines to use
            categories: List of search categories
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        start_time = time.time()
        self.debug_logger.log(f"Search query: {query}")

        try:
            params = {
                'q': query,
                'format': 'json',
                'engines': ','.join(engines or ['google', 'bing', 'duckduckgo']),
                'categories': ','.join(categories or ['general']),
                'results_on_new_tab': '1',
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.searxng_base_url}/search",
                    params=params,
                    headers={
                        'User-Agent': 'GRACE-Research/1.0',
                        'Accept': 'application/json',
                    }
                )

            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                print(f"Warning: SearxNG returned HTML instead of JSON")
                raise Exception("SearxNG returned HTML instead of JSON - configuration issue")

            data = response.json()
            if not isinstance(data, dict):
                raise Exception("Invalid JSON response from SearxNG")

            results = data.get('results', [])
            if not isinstance(results, list):
                raise Exception("Invalid results format from SearxNG")

            search_results = [
                SearchResult(
                    title=result.get('title', 'Untitled'),
                    url=result['url'],
                    snippet=result.get('content') or result.get('snippet', ''),
                    engine=result.get('engine', 'unknown'),
                    score=self._calculate_score(result, index)
                )
                for index, result in enumerate(results)
                if result.get('url') and result.get('title')
            ][:limit]

            duration = time.time() - start_time
            self.debug_logger.log(f"Search completed: {len(search_results)} results in {duration:.2f}s")

            print(f"Search completed: {len(search_results)} results for \"{query}\"")
            return search_results

        except Exception as error:
            print(f"Warning: Search failed: {str(error)}")
            print("Using fallback search...")
            return await self._fallback_search(query, limit)

    def _calculate_score(self, result: Dict[str, Any], index: int) -> float:
        """Calculate relevance score for a search result.

        Args:
            result: Search result data
            index: Position in results list

        Returns:
            Relevance score between 0 and 1
        """
        # Simple scoring based on position and metadata
        score = 1.0 - index * 0.05

        # Boost score for quality indicators
        if result.get('title') and len(result['title']) > 10:
            score += 0.1
        if result.get('content') and len(result['content']) > 100:
            score += 0.1
        if 'https://' in result.get('url', ''):
            score += 0.05

        # Prefer certain domains
        url = result.get('url', '').lower()
        if any(keyword in url for keyword in ['reference', 'docs', 'api']):
            score += 0.2

        return max(0.1, min(1.0, score))

    async def _fallback_search(self, query: str, limit: int) -> List[SearchResult]:
        """Fallback search when SearxNG is not available.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of fallback search results
        """
        print("Using fallback search - SearxNG not available")

        from urllib.parse import quote

        mock_results = [
            SearchResult(
                title=f"Wikipedia: {query}",
                url=f"https://en.wikipedia.org/wiki/{quote(query.replace(' ', '_'))}",
                snippet=f"Wikipedia article about {query}",
                engine='fallback',
                score=0.9
            ),
            # SearchResult(
            #     title=f"Research about {query}",
            #     url=f"https://scholar.google.com/scholar?q={quote(query)}",
            #     snippet=f"Academic research and papers about {query}",
            #     engine='fallback',
            #     score=0.8
            # ),
        ]

        return mock_results[:limit]

    async def search_multiple_queries(
        self,
        queries: List[str],
        max_results_per_query: int = 10,
        engines: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search multiple queries and deduplicate results.

        Args:
            queries: List of search queries
            max_results_per_query: Maximum results per query
            engines: Search engines to use

        Returns:
            Deduplicated list of search results sorted by score
        """
        all_results: List[SearchResult] = []
        seen_urls = set()

        for query in queries:
            try:
                results = await self.search(
                    query,
                    engines=engines,
                    limit=max_results_per_query
                )

                # Deduplicate by URL
                for result in results:
                    if result.url not in seen_urls:
                        seen_urls.add(result.url)
                        all_results.append(result)

            except Exception as error:
                print(f"Warning: Failed to search for query \"{query}\": {str(error)}")

        # Sort by score and return
        return sorted(all_results, key=lambda r: r.score, reverse=True)

    async def is_engine_available(self, engine: str) -> bool:
        """Check if a specific search engine is available.

        Args:
            engine: Engine name to check

        Returns:
            True if engine is available
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.searxng_base_url}/config")
                data = response.json()
                engines = data.get('engines', {})
                return engine in engines
        except Exception:
            return False

    async def get_available_engines(self) -> List[str]:
        """Get list of available search engines.

        Returns:
            List of available engine names
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.searxng_base_url}/config")
                data = response.json()
                engines = data.get('engines', {})
                return [
                    name for name, config in engines.items()
                    if config.get('enabled', False)
                ]
        except Exception:
            return ['google', 'bing', 'duckduckgo']  # fallback engines
