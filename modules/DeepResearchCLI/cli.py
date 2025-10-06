#!/usr/bin/env python3
"""Deep Research CLI - Main entry point."""

import sys
import os
import signal
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from services.config_service import ConfigService
from services.direct_research_service import DirectResearchService
from services.storage_service import StorageService
from utils.debug_logger import DebugLogger
import asyncio


console = Console()


class GraceResearchCLI:
    """Grace Research CLI application."""

    def __init__(self):
        """Initialize CLI application."""
        self.config = ConfigService.get_instance()
        self.debug_logger = DebugLogger.get_instance()

        # Setup event listeners
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            console.print("\n[yellow]Shutting down gracefully...[/yellow]")
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def cleanup(self):
        """Cleanup resources."""
        self.debug_logger.close()

    def show_config(self):
        """Display current configuration."""
        console.print("\n[cyan bold]🔧 Current Configuration[/cyan bold]")
        console.print("[white]" + "=" * 60 + "[/white]")

        research_config = self.config.get_research_config()
        ai_config = self.config.get_ai_config()

        # AI Configuration
        console.print("\n[yellow]AI Configuration:[/yellow]")
        console.print(f"  Provider: {ai_config.provider}")
        console.print(f"  Model: {ai_config.model_id}")
        console.print(f"  Base URL: {ai_config.base_url}")
        api_key_status = "***configured***" if ai_config.api_key else "NOT SET"
        console.print(f"  API Key: {api_key_status}")

        custom_instructions_file = ai_config.custom_instructions_file or "NOT SET"
        console.print(f"  Custom Instructions File: {custom_instructions_file}")

        if ai_config.custom_instructions:
            console.print(
                f"  Custom Instructions: [green]LOADED[/green] "
                f"({len(ai_config.custom_instructions)} characters)"
            )
        else:
            console.print("  Custom Instructions: [dim]NOT LOADED[/dim]")

        # Research Configuration
        console.print("\n[yellow]Research Configuration:[/yellow]")
        console.print(f"  Max Depth: {research_config.max_depth}")
        console.print(f"  Max Pages per Depth: {research_config.max_pages_per_depth}")
        console.print(f"  Max Total Pages: {research_config.max_total_pages}")
        console.print(f"  Concurrent Pages: {research_config.max_concurrent_pages}")
        console.print(f"  Link Relevance Threshold: {research_config.link_relevance_threshold}")
        console.print(f"  Timeout per Page: {research_config.timeout_per_page}ms")
        console.print(f"  Respect Robots.txt: {research_config.respect_robots_txt}")

        # Storage Configuration
        console.print("\n[yellow]Storage Configuration:[/yellow]")
        console.print(f"  Data Directory: {research_config.data_directory}")
        console.print(f"  History File: {research_config.history_file}")

        # Debug Configuration
        console.print("\n[yellow]Debug Configuration:[/yellow]")
        console.print(f"  Debug Enabled: {self.debug_logger.is_enabled()}")
        if self.debug_logger.is_enabled():
            console.print(f"  Debug Log File: {self.debug_logger.get_log_file_path()}")

    async def show_history_async(self):
        """Show research history (async)."""
        try:
            research_config = self.config.get_research_config()
            storage_service = StorageService(
                research_config.data_directory,
                research_config.history_file
            )
            history = await storage_service.get_history(20)

            if not history:
                console.print("[yellow]📝 No research history found.[/yellow]")
                return

            console.print("\n[cyan bold]📚 Research History[/cyan bold]")
            console.print("[white]" + "=" * 64 + "[/white]")

            for index, session in enumerate(history):
                duration = (session.end_time - session.start_time) / 1000 if session.end_time else 0
                status_icon = {
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '⚠️',
                    'running': '🔄'
                }.get(session.status, '❓')

                console.print(f"\n{index + 1}. {status_icon} [white]{session.query}[/white]")
                console.print(f"   [grey]Session ID:[/grey] {session.id}")
                console.print(f"   [grey]Status:[/grey] {session.status} [grey]|[/grey] [grey]Duration:[/grey] {duration:.1f}s")
                console.print(f"   [grey]Pages:[/grey] {session.total_pages} [grey]|[/grey] [grey]Depth:[/grey] {session.max_depth_reached}")
                from datetime import datetime
                start_dt = datetime.fromtimestamp(session.start_time / 1000)
                console.print(f"   [grey]Started:[/grey] {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as error:
            console.print(f"[red]❌ Failed to load history: {error}[/red]")

    def show_history(self):
        """Show research history."""
        asyncio.run(self.show_history_async())

    async def show_stats_async(self):
        """Show research statistics (async)."""
        try:
            research_config = self.config.get_research_config()
            storage_service = StorageService(
                research_config.data_directory,
                research_config.history_file
            )
            stats = await storage_service.get_session_statistics()

            console.print("\n[cyan bold]📊 Research Statistics[/cyan bold]")
            console.print("[white]" + "=" * 64 + "[/white]")

            console.print(f"[yellow]Total Sessions:[/yellow] {stats['totalSessions']}")
            console.print(f"[yellow]Completed Sessions:[/yellow] {stats['completedSessions']}")
            success_rate = (stats['completedSessions'] / stats['totalSessions'] * 100) if stats['totalSessions'] > 0 else 0
            console.print(f"[yellow]Success Rate:[/yellow] {success_rate:.1f}%")
            console.print(f"[yellow]Average Pages:[/yellow] {stats['averagePages']}")
            console.print(f"[yellow]Average Depth:[/yellow] {stats['averageDepth']}")
            console.print(f"[yellow]Storage Used:[/yellow] {stats['totalStorageSize'] / 1024 / 1024:.2f} MB")

        except Exception as error:
            console.print(f"[red]❌ Failed to load statistics: {error}[/red]")

    def show_stats(self):
        """Show research statistics."""
        asyncio.run(self.show_stats_async())

    async def start_research_async(self, query: str):
        """Start deep research session (async)."""
        console.print(Panel(
            f"[cyan bold]Grace Deep Research Mode[/cyan bold]\n"
            f"Query: [green]\"{query}\"[/green]",
            border_style="cyan"
        ))

        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            console.print("[red]Configuration errors:[/red]")
            for error in config_errors:
                console.print(f"[red]  • {error}[/red]")
            console.print(
                "\n[yellow]💡 Please check your .env file and fix the configuration.[/yellow]"
            )
            return

        # Test AI connection
        console.print("[cyan]Testing AI service connection...[/cyan]")
        from services.ai_service import AIService
        ai_config = self.config.get_ai_config()
        ai_service = AIService(ai_config)

        ai_test = await ai_service.test_connection()
        if not ai_test['success']:
            console.print(f"[red]AI service test failed: {ai_test.get('error', 'Unknown error')}[/red]")
            console.print("\n[yellow]Please check your AI configuration in .env file.[/yellow]")
            return
        console.print("[green]AI service connected[/green]")

        # Start research
        direct_research = DirectResearchService()
        await direct_research.research(query)

    def start_research(self, query: str):
        """Start deep research session."""
        asyncio.run(self.start_research_async(query))

    async def test_search_async(self, query: str):
        """Test SearxNG connectivity and JSON API (async)."""
        console.print("\n[cyan bold]🔍 Testing SearxNG Connectivity[/cyan bold]")
        console.print("[white]" + "=" * 60 + "[/white]\n")

        # Get SearxNG URL from config
        research_config = self.config.get_research_config()
        searxng_url = os.getenv('SEARXNG_BASE_URL', 'http://localhost:32768')

        console.print(f"[yellow]SearxNG URL:[/yellow] {searxng_url}")
        console.print(f"[yellow]Test Query:[/yellow] \"{query}\"\n")

        # Import search service
        from services.search_service import SearchService
        import httpx

        search_service = SearchService(searxng_url)

        # Test 1: Basic HTTP connectivity
        console.print("[cyan]Test 1:[/cyan] Basic HTTP connectivity...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(searxng_url)
                if response.status_code == 200:
                    console.print("[green]✅ SearxNG is reachable[/green]")
                else:
                    console.print(f"[yellow]⚠️  SearxNG returned status code: {response.status_code}[/yellow]")
        except httpx.ConnectError:
            console.print(f"[red]❌ Cannot connect to SearxNG at {searxng_url}[/red]")
            console.print("[yellow]💡 Make sure SearxNG is running:[/yellow]")
            console.print("   • Docker: docker start searxng")
            console.print("   • Local: ./scripts/start-searxng.sh")
            return
        except Exception as error:
            console.print(f"[red]❌ Connection error: {error}[/red]")
            return

        # Test 2: JSON API endpoint
        console.print("\n[cyan]Test 2:[/cyan] JSON API endpoint...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{searxng_url}/search",
                    params={'q': query, 'format': 'json'},
                    headers={'Accept': 'application/json'}
                )

                content_type = response.headers.get('content-type', '')

                if 'application/json' in content_type:
                    console.print("[green]✅ JSON API is working correctly[/green]")
                elif 'text/html' in content_type:
                    console.print("[red]❌ SearxNG returned HTML instead of JSON[/red]")
                    console.print("[yellow]💡 Check searxng-config.yml formats section[/yellow]")
                    return
                else:
                    console.print(f"[yellow]⚠️  Unexpected content type: {content_type}[/yellow]")

        except Exception as error:
            console.print(f"[red]❌ JSON API test failed: {error}[/red]")
            return

        # Test 3: Perform actual search
        console.print("\n[cyan]Test 3:[/cyan] Performing search query...")
        try:
            results = await search_service.search(query, limit=5)

            if not results:
                console.print("[yellow]⚠️  No results returned[/yellow]")
                return

            console.print(f"[green]✅ Found {len(results)} results[/green]\n")

            # Display results in a table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", style="white")
            table.add_column("Engine", style="yellow", width=12)
            table.add_column("Score", style="green", width=8)

            for idx, result in enumerate(results, 1):
                title = result.title[:60] + "..." if len(result.title) > 60 else result.title
                table.add_row(
                    str(idx),
                    title,
                    result.engine,
                    f"{result.score:.2f}"
                )

            console.print(table)
            console.print()

            # Show one example result in detail
            if results:
                console.print("[cyan]Example result details:[/cyan]")
                example = results[0]
                console.print(f"[yellow]Title:[/yellow] {example.title}")
                console.print(f"[yellow]URL:[/yellow] {example.url}")
                snippet = example.snippet[:150] + "..." if len(example.snippet) > 150 else example.snippet
                console.print(f"[yellow]Snippet:[/yellow] {snippet}")
                console.print(f"[yellow]Engine:[/yellow] {example.engine}")
                console.print(f"[yellow]Score:[/yellow] {example.score:.2f}")

        except Exception as error:
            console.print(f"[red]❌ Search failed: {error}[/red]")
            return

        # Test 4: Get available engines
        console.print("\n[cyan]Test 4:[/cyan] Checking available search engines...")
        try:
            engines = await search_service.get_available_engines()
            console.print(f"[green]✅ Available engines ({len(engines)}):[/green] {', '.join(engines[:10])}")
            if len(engines) > 10:
                console.print(f"   ... and {len(engines) - 10} more")
        except Exception as error:
            console.print(f"[yellow]⚠️  Could not fetch engines: {error}[/yellow]")

        # Final summary
        console.print("\n" + "[white]" + "=" * 60 + "[/white]")
        console.print("[green bold]✅ All tests passed! SearxNG is working correctly.[/green bold]")
        console.print("\n[cyan]You can now use:[/cyan]")
        console.print("  grace-research research \"your research query\"")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GRACE Deep Research CLI - Intelligent web research with AI analysis."""
    pass


@cli.command()
@click.argument('query', required=False)
def research(query: Optional[str]):
    """Start a direct research session."""
    app = GraceResearchCLI()

    if not query:
        query = click.prompt("Enter your research query")

    app.start_research(query)


@cli.command()
def config():
    """Show current configuration."""
    app = GraceResearchCLI()
    app.show_config()


@cli.command()
def history():
    """Show research history."""
    app = GraceResearchCLI()
    app.show_history()


@cli.command()
def stats():
    """Show research statistics."""
    app = GraceResearchCLI()
    app.show_stats()


@cli.command()
@click.option('--days', '-d', default=30, help='Clean data older than specified days')
def clean(days: int):
    """Clean up old research data."""
    console.print(f"\n[green]🧹 Cleanup feature coming soon![/green]")
    console.print(f"Will clean data older than {days} days.")


@cli.command()
@click.option('--query', '-q', default='test search', help='Test query to search for')
def test_search(query: str):
    """Test SearxNG connectivity and JSON API."""
    app = GraceResearchCLI()
    asyncio.run(app.test_search_async(query))


def main():
    """Main entry point."""
    # Show help if no arguments
    if len(sys.argv) == 1:
        cli.main(['--help'])
    else:
        cli()


if __name__ == '__main__':
    main()
