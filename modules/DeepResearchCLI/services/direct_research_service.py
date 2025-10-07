"""Direct research service - main orchestrator."""

import os
import asyncio
import time
import uuid
from typing import List, Dict, Any, Set, Optional
from rich.console import Console

from .config_service import ConfigService
from .ai_service import AIService
from .search_service import SearchService
from .web_scraping_service import WebScrapingService
from .result_output_service import ResultOutputService
from .storage_service import StorageService
from research_types import ResearchSession, ResearchSessionMetadata, PageData
from utils.debug_logger import DebugLogger


console = Console()


class DirectResearchService:
    """Direct research service for non-interactive research."""

    def __init__(self):
        """Initialize direct research service."""
        self.config = ConfigService.get_instance()
        self.debug_logger = DebugLogger.get_instance()

        ai_config = self.config.get_ai_config()
        self.ai_service = AIService(ai_config)

        searxng_url = os.getenv('SEARXNG_BASE_URL', 'http://localhost:32768')
        self.search_service = SearchService(searxng_url)

        research_config = self.config.get_research_config()
        proxies = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
        self.web_scraping_service = WebScrapingService(
            max_concurrent_pages=research_config.max_concurrent_pages,
            timeout=research_config.timeout_per_page,
            respect_robots_txt=research_config.respect_robots_txt,
            proxies=proxies
        )

        self.result_output_service = ResultOutputService()
        self.storage_service = StorageService(
            research_config.data_directory,
            research_config.history_file
        )

    async def research(self, query: str):
        """Main research flow.

        Args:
            query: Research query
        """
        console.print(f"\n[cyan bold]Starting Grace Deep Research: \"{query}\"[/cyan bold]")
        console.print("[grey]" + "━" * 60 + "[/grey]")

        start_time = int(time.time() * 1000)
        session = ResearchSession(
            id=str(uuid.uuid4()),
            query=query,
            start_time=start_time,
            status='running',
            total_pages=0,
            max_depth_reached=0,
            metadata=ResearchSessionMetadata()
        )

        # Global URL tracker
        global_visited_urls: Set[str] = set()

        # Load custom instructions
        link_quality_prompt: Optional[str] = None
        custom_instructions = self.config.get_ai_config().custom_instructions
        if custom_instructions:
            try:
                link_quality_prompt = await self.ai_service.generate_link_quality_prompt(
                    custom_instructions,
                    query
                )
                if self.config.is_debug_mode():
                    console.print(f"[green]   Loaded custom instructions and generated link quality prompt[/green]")
            except Exception as error:
                console.print(f"[yellow]Custom instructions not found: {error}[/yellow]")

        try:
            # Step 1: Generate search queries
            console.print("[yellow]Generating search queries...[/yellow]")
            search_queries = await self.ai_service.generate_search_queries(query, 0)
            if self.config.is_debug_mode():
                console.print(f"[green]  Generated {len(search_queries)} search queries[/green]")
                for idx, q in enumerate(search_queries):
                    console.print(f"[grey]      {idx + 1}. {q}[/grey]")

            # Step 2: Perform searches
            console.print("[yellow]Performing web searches...[/yellow]")
            all_search_results = []
            for search_query in search_queries:
                console.print(f"[grey]   Searching: \"{search_query}\"[/grey]")
                results = await self.search_service.search(search_query, limit=10)
                all_search_results.extend(results)

            console.print(f"[green]   Found {len(all_search_results)} search results[/green]")

            # Step 3: Initial page crawling
            research_config = self.config.get_research_config()
            initial_urls = [
                r.url for r in all_search_results[:research_config.max_pages_per_depth]
                if r.url not in global_visited_urls
            ]

            for url in initial_urls:
                global_visited_urls.add(url)

            # AI analysis of search results
            analyzed_results = initial_urls
            if len(all_search_results) > 10:
                console.print("[yellow]Analyzing search results with AI...[/yellow]")
                ai_analyzed = await self.ai_service.analyze_search_results(
                    query,
                    [{'title': r.title, 'snippet': r.snippet, 'url': r.url} for r in all_search_results]
                )

                # Fallback to initial URLs if AI returns too few results
                if ai_analyzed and len(ai_analyzed) >= 3:
                    analyzed_results = ai_analyzed
                    console.print(f"[green]   ✓ AI analysis complete, {len(analyzed_results)} relevant results[/green]")
                else:
                    console.print(f"[yellow]   ⚠ AI returned only {len(ai_analyzed)} URLs, using search results instead[/yellow]")
                    analyzed_results = initial_urls[:research_config.max_pages_per_depth]

            console.print("[yellow]Crawling initial pages...[/yellow]")
            console.print(f"[grey]   • Attempting to crawl {len(analyzed_results)} URLs[/grey]")
            initial_pages = await self.web_scraping_service.scrape_multiple_pages(analyzed_results)

            # Filter valid pages and show stats
            valid_pages = [page for page in initial_pages if len(page.content) > 100 and not page.error]
            failed_pages = [page for page in initial_pages if page.error]
            short_pages = [page for page in initial_pages if len(page.content) <= 100 and not page.error]

            console.print(f"[green]   ✓ Successfully crawled {len(valid_pages)} pages[/green]")
            if failed_pages:
                console.print(f"[yellow]   • Failed to crawl {len(failed_pages)} pages (errors)[/yellow]")
                if self.config.is_debug_mode():
                    for page in failed_pages[:3]:  # Show first 3 errors
                        console.print(f"[grey]     - {page.url}: {page.error}[/grey]")
            if short_pages:
                console.print(f"[yellow]   • Skipped {len(short_pages)} pages (content too short)[/yellow]")
                if self.config.is_debug_mode():
                    for page in short_pages[:3]:
                        console.print(f"[grey]     - {page.url}: {len(page.content)} chars[/grey]")

            # Step 4: Deep link crawling (if enabled)
            all_pages = valid_pages
            if research_config.enable_deep_link_crawling:
                console.print("[yellow]Crawling with links found in the pages.[/yellow]")
                deep_pages = await self._perform_deep_link_crawling(
                    valid_pages,
                    query,
                    global_visited_urls,
                    link_quality_prompt
                )
                all_pages = valid_pages + deep_pages
                console.print(f"[green]   ✓ Found {len(deep_pages)} additional pages through deep crawling[/green]")
            else:
                console.print("[grey]   • Deep link crawling DISABLED[/grey]")

            # Step 5: AI Analysis
            console.print("[yellow]AI analysis and synthesis...[/yellow]")

            # Check if we have any pages to analyze
            if not all_pages:
                console.print("[red]   ✗ No pages were successfully crawled[/red]")
                console.print("[yellow]   Possible issues:[/yellow]")
                console.print("[grey]     • Search results may not be accessible[/grey]")
                console.print("[grey]     • Pages may have blocked the scraper[/grey]")
                console.print("[grey]     • Network connectivity issues[/grey]")
                raise Exception("No pages were successfully crawled. Cannot proceed with analysis.")

            page_data_for_ai = [
                {
                    'url': page.url,
                    'title': page.title,
                    'content': page.content,
                    'relevance_score': page.relevance_score,
                    'depth': page.depth
                }
                for page in all_pages
            ]

            # Break into chunks
            CHUNK_SIZE = 5
            chunks = [page_data_for_ai[i:i + CHUNK_SIZE] for i in range(0, len(page_data_for_ai), CHUNK_SIZE)]

            console.print(f"[grey]     Processing {len(page_data_for_ai)} pages in {len(chunks)} chunks...[/grey]")

            # Process chunks
            chunk_insights = []
            for i, chunk in enumerate(chunks):
                console.print(f"[cyan]   Analyzing chunk {i + 1}/{len(chunks)} ({len(chunk)} pages)...[/cyan]")
                chunk_analysis = await self.ai_service.synthesize_results(query, chunk)
                chunk_insights.append(chunk_analysis['answer'])
                console.print(f"[green]   ✓ Chunk {i + 1}/{len(chunks)} complete[/green]")

            # Final synthesis
            console.print(f"[cyan]    Performing final synthesis of {len(chunks)} chunk results...[/cyan]")
            if len(chunks) > 1:
                combined_pages = [
                    {
                        'url': f'chunk-{idx + 1}',
                        'title': f'Analysis Chunk {idx + 1}',
                        'content': insight,
                        'relevance_score': 1.0,
                        'depth': 0
                    }
                    for idx, insight in enumerate(chunk_insights)
                ]
                final_analysis = await self.ai_service.synthesize_results(query, combined_pages)
            elif len(chunk_insights) > 0:
                final_analysis = {'answer': chunk_insights[0], 'confidence': 0.8, 'summary': 'Research completed'}
            else:
                raise Exception("No insights generated from crawled pages")

            console.print(f"[green]   ✓ Final analysis complete (confidence: {int(final_analysis['confidence'] * 100)}%)[/green]")

            # Step 6: Save results
            console.print("[yellow]Saving results...[/yellow]")
            session.end_time = int(time.time() * 1000)
            session.status = 'completed'
            session.final_answer = final_analysis['answer']
            session.confidence = final_analysis['confidence']
            session.total_pages = len(all_pages)
            session.metadata.total_links_found = sum(len(page.links) for page in all_pages)

            await self.storage_service.save_session(session)
            name = await self.ai_service.generate_named_description(query)
            output_paths = await self.result_output_service.save_results(session, name, all_pages)

            # Step 7: Display results
            if self.config.is_debug_mode():
                console.print("\n[cyan bold]  Research Results:[/cyan bold]")
                console.print("[grey]" + "━" * 60 + "[/grey]")
                console.print(f"\n[white]{final_analysis['answer']}[/white]")
                console.print("\n[grey]" + "━" * 60 + "[/grey]")
                console.print(f"[cyan] Pages analyzed: {len(all_pages)}[/cyan]")
                console.print(f"[cyan] Links found: {session.metadata.total_links_found}[/cyan]")
                console.print(f"[cyan] Confidence: {int(final_analysis['confidence'] * 100)}%[/cyan]")
                console.print(f"[cyan]   Time taken: {int((time.time() * 1000 - start_time) / 1000)}s[/cyan]")

            console.print(f"\n[green]  Results saved to:[/green]")
            if output_paths.get('htmlPath'):
                console.print(f"[grey]   • HTML: {output_paths['htmlPath']}[/grey]")
            if output_paths.get('jsonPath'):
                console.print(f"[grey]   • JSON: {output_paths['jsonPath']}[/grey]")
            if output_paths.get('markdownPath'):
                console.print(f"[grey]   • Markdown: {output_paths['markdownPath']}[/grey]")

        except Exception as error:
            session.end_time = int(time.time() * 1000)
            session.status = 'failed'
            console.print(f"\n[red]  Research failed: {error}[/red]")
            raise

        finally:
            # Cleanup
            await self.web_scraping_service.close()

    async def _perform_deep_link_crawling(
        self,
        initial_pages: List[PageData],
        query: str,
        global_visited_urls: Set[str],
        link_quality_prompt: Optional[str]
    ) -> List[PageData]:
        """Perform deep link crawling.

        Args:
            initial_pages: Initial pages
            query: Research query
            global_visited_urls: Set of visited URLs
            link_quality_prompt: Link quality prompt

        Returns:
            List of deep pages
        """
        research_config = self.config.get_research_config()
        deep_pages: List[PageData] = []

        for depth in range(1, research_config.deep_crawl_depth + 1):
            pages_to_crawl = initial_pages if depth == 1 else [p for p in deep_pages if p.depth == depth - 1]
            console.print(f"[grey]     • Processing {len(pages_to_crawl)} pages from previous depth[/grey]")

            # Check if AI wants to continue
            if research_config.ai_driven_crawling and depth > 1:
                console.print(f"[cyan]      AI evaluating whether to continue...[/cyan]")
                current_insights = [p.title for p in initial_pages + deep_pages if p.title]
                ai_decision = await self.ai_service.should_continue_crawling(
                    query,
                    depth - 1,
                    research_config.deep_crawl_depth,
                    len(initial_pages) + len(deep_pages),
                    current_insights
                )

                if ai_decision['shouldContinue']:
                    console.print(f"[green]     ✓ AI decision: CONTINUE to depth {depth} ({ai_decision['reason']})[/green]")
                else:
                    console.print(f"[red]     ✗ AI decision: STOP at depth {depth - 1} ({ai_decision['reason']})[/red]")
                    break

            console.print(f"\n[yellow]   Depth {depth}/{research_config.deep_crawl_depth}:[/yellow]")

            # Collect links
            all_links = []
            for page in pages_to_crawl:
                for link in page.links:
                    if link.url not in global_visited_urls:
                        all_links.append({'url': link.url, 'text': link.text, 'context': link.context})

            console.print(f"[grey]     • New unique URLs available: {len(all_links)}[/grey]")

            if not all_links:
                console.print(f"[yellow]     • No more links found at depth {depth}, stopping early[/yellow]")
                break

            # Filter links by quality if available
            if link_quality_prompt and all_links:
                console.print(f"[cyan]     • AI filtering links by quality ({len(all_links)} links)...[/cyan]")
                filtered_links = await self.ai_service.filter_links_by_quality(
                    all_links,
                    link_quality_prompt,
                    query
                )
                console.print(f"[grey]     • Quality filtering: {len(all_links)} → {len(filtered_links)} links[/grey]")
                all_links = filtered_links

                if not all_links:
                    console.print(f"[yellow]     • No quality links remaining at depth {depth}, stopping early[/yellow]")
                    break

            # Rank links if enabled
            urls_to_crawl = [link['url'] for link in all_links]
            if research_config.ai_link_ranking and all_links:
                console.print(f"[cyan]     • AI ranking {min(len(all_links), 20)} links...[/cyan]")
                current_context = ' '.join([p.title + ': ' + p.content[:200] for p in pages_to_crawl])
                ranked_links = await self.ai_service.rank_links_for_crawling(query, all_links, current_context)
                urls_to_crawl = [l['url'] for l in ranked_links[:research_config.max_pages_per_depth]]
                console.print(f"[grey]     • AI ranked {len(ranked_links)} links[/grey]")

            # Mark as visited
            for url in urls_to_crawl:
                global_visited_urls.add(url)

            if not urls_to_crawl:
                console.print(f"[yellow]     • No links to crawl at depth {depth}[/yellow]")
                break

            console.print(f"[cyan]     • Scraping {len(urls_to_crawl)} pages at depth {depth}...[/cyan]")

            # Scrape pages
            new_pages = await self.web_scraping_service.scrape_multiple_pages(urls_to_crawl, depth)
            valid_new_pages = [
                PageData(
                    url=p.url,
                    title=p.title,
                    content=p.content,
                    links=p.links,
                    depth=depth,
                    relevance_score=p.relevance_score,
                    fetch_time=p.fetch_time,
                    processing_time=p.processing_time,
                    error=p.error
                )
                for p in new_pages
                if len(p.content) > 100
            ]

            deep_pages.extend(valid_new_pages)
            console.print(f"[green]     ✓ Depth {depth} complete: {len(valid_new_pages)} valid pages[/green]")
            console.print(f"[grey]     • Total deep pages collected so far: {len(deep_pages)}[/grey]")

        console.print(f"\n[green]   ✓ Deep crawling complete: {len(deep_pages)} additional pages found[/green]")
        return deep_pages
