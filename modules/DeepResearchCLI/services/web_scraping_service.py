"""Web scraping service using Playwright and BeautifulSoup."""

import asyncio
import time
import random
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Browser, Page, Playwright
from bs4 import BeautifulSoup
import httpx

from research_types import PageData, ExtractedLink


class WebScrapingService:
    """Service for scraping web pages."""

    def __init__(
        self,
        max_concurrent_pages: int = 3,
        timeout: int = 30000,
        respect_robots_txt: bool = True,
        proxies: Optional[List[str]] = None
    ):
        """Initialize web scraping service.

        Args:
            max_concurrent_pages: Maximum concurrent pages to scrape
            timeout: Timeout per page in milliseconds
            respect_robots_txt: Whether to respect robots.txt
            proxies: List of proxy servers
        """
        self.max_concurrent_pages = max_concurrent_pages
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt
        self.proxy_list = proxies or []
        self.current_proxy_index = 0
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.semaphore = asyncio.Semaphore(max_concurrent_pages)

    async def initialize(self):
        """Initialize browser."""
        if not self.browser:
            self.playwright = await async_playwright().start()

            launch_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--window-size=1920,1080",
            ]

            # Add proxy if available
            if self.proxy_list:
                proxy = self._get_next_proxy()
                launch_args.append(f"--proxy-server={proxy}")

            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=launch_args
            )

    def _get_next_proxy(self) -> str:
        """Get next proxy from list."""
        if not self.proxy_list:
            return ""
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def _get_random_user_agent(self) -> str:
        """Get random user agent."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    async def _add_stealth_headers(self, page: Page):
        """Add stealth headers to page."""
        # Add init script to remove automation indicators
        await page.add_init_script("""
        try {
            if (typeof navigator !== 'undefined') {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            }
            if (typeof window !== 'undefined' && window.chrome) {
                delete window.chrome.runtime;
            }
        } catch (e) {}
        """)

        # Set realistic headers
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self._get_random_user_agent(),
        })

    async def _handle_dynamic_content(self, page: Page):
        """Handle dynamic content loading."""
        try:
            # Try to handle infinite scroll or "load more" content
            previous_height = 0
            current_height = await page.evaluate("() => document.body.scrollHeight")
            attempts = 0
            max_attempts = 5

            while previous_height != current_height and attempts < max_attempts:
                previous_height = current_height

                # Scroll to bottom
                await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")

                # Wait for potential content to load
                await page.wait_for_timeout(2000)

                # Check for "Load More" or "Show More" buttons
                load_more_selectors = [
                    'button[class*="load-more"]',
                    'button[class*="show-more"]',
                    'a[class*="load-more"]',
                    'a[class*="show-more"]',
                    '.load-more',
                    '.show-more',
                ]

                for selector in load_more_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button:
                            is_visible = await button.is_visible()
                            if is_visible:
                                await button.click()
                                await page.wait_for_timeout(2000)
                                break
                    except Exception:
                        continue

                current_height = await page.evaluate("() => document.body.scrollHeight")
                attempts += 1

            # Scroll back to top
            await page.evaluate("() => window.scrollTo(0, 0)")
        except Exception:
            # If dynamic content handling fails, continue with regular scraping
            pass

    async def scrape_page(self, url: str, depth: int = 0) -> PageData:
        """Scrape a single page.

        Args:
            url: URL to scrape
            depth: Depth level

        Returns:
            Page data
        """
        if not self.browser:
            await self.initialize()
            print("Browser initialized for scraping.")

        start_time = time.time()
        page: Optional[Page] = None

        try:
            print(f"\n[WebScraping] Fetching: {url}")
            print(f"   Depth: {depth}, Timeout: {self.timeout}ms")

            # Check if URL is a PDF or other document
            doc_type = self._get_document_type(url)
            if doc_type:
                print(f"   {doc_type.upper()} file detected, downloading and extracting content...")
                return await self._scrape_document(url, depth, doc_type)

            page = await self.browser.new_page()

            # Set viewport with random variation
            await page.set_viewport_size({
                'width': 1920 + random.randint(0, 100),
                'height': 1080 + random.randint(0, 100),
            })

            await self._add_stealth_headers(page)

            # Add random delay
            await page.wait_for_timeout(500 + int(random.random() * 1000))

            print(f"Navigating to {url}")

            # Navigate to page
            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)

            # Handle dynamic content
            await self._handle_dynamic_content(page)

            # Get page content
            content = await page.content()
            title = await page.title()

            print(f"   Page loaded: \"{title}\"")
            print(f"   HTML size: {len(content)} chars")

            # Extract content and links
            text_content, links = self._extract_content_and_links(content, url)

            print(f"     Extracted content: {len(text_content)} chars")
            print(f"     Found links: {len(links)}")

            if len(text_content) < 100:
                print(f"   WARNING: Very short content extracted!")
                print(f"   Content preview: \"{text_content[:200]}\"")
            else:
                print(f"   Content preview: \"{text_content[:200]}...\"")

            fetch_time = int((time.time() - start_time) * 1000)
            print(f"   Fetch time: {fetch_time}ms")

            return PageData(
                url=url,
                title=title or self._extract_title_from_url(url),
                content=text_content,
                links=links,
                depth=depth,
                relevance_score=0.5,
                fetch_time=fetch_time,
                processing_time=0
            )

        except Exception as error:
            fetch_time = int((time.time() - start_time) * 1000)
            error_msg = str(error)

            # Provide more helpful error messages
            if 'timeout' in error_msg.lower() or 'Timeout' in error_msg:
                error_msg = f"Timeout after {self.timeout}ms"
            elif 'net::ERR' in error_msg or 'ERR_' in error_msg:
                error_msg = "Network error or page blocked"
            elif '403' in error_msg or 'forbidden' in error_msg.lower():
                error_msg = "Access forbidden (403)"
            elif '404' in error_msg:
                error_msg = "Page not found (404)"
            elif 'SSL' in error_msg or 'certificate' in error_msg.lower():
                error_msg = "SSL/Certificate error"

            print(f"   Error scraping page: {error_msg}")
            print(f"   Failed after: {fetch_time}ms")

            return PageData(
                url=url,
                title=self._extract_title_from_url(url),
                content="",
                links=[],
                depth=depth,
                relevance_score=0.1,
                fetch_time=fetch_time,
                processing_time=0,
                error=error_msg
            )

        finally:
            if page:
                await page.close()

    async def scrape_multiple_pages(self, urls: List[str], depth: int = 0) -> List[PageData]:
        """Scrape multiple pages concurrently.

        Args:
            urls: List of URLs to scrape
            depth: Depth level

        Returns:
            List of page data
        """
        results: List[PageData] = []

        async def scrape_with_semaphore(url: str):
            async with self.semaphore:
                result = await self.scrape_page(url, depth)
                results.append(result)

        tasks = [scrape_with_semaphore(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def _extract_content_and_links(
        self,
        html: str,
        base_url: str
    ) -> tuple[str, List[ExtractedLink]]:
        """Extract content and links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            Tuple of (text_content, links)
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove non-content elements
        for element in soup.select('script, style, nav, header, footer, aside, .advertisement, .ads, .sidebar, .comments'):
            element.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title else ""

        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')

        # Try to find main content
        content_selectors = [
            'main article',
            'main .content',
            'article',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.content-area',
            '.page-content',
            '[role="main"]',
            'main',
            '#content',
            '.content',
        ]

        primary_content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                if len(content) > 200:
                    primary_content = content
                    break

        # Fallback to paragraphs or body
        if not primary_content:
            paragraphs = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
            if len(paragraphs) > 200:
                primary_content = paragraphs
            else:
                primary_content = soup.body.get_text(strip=True) if soup.body else ""

        # Extract headings and lists
        headings = '. '.join([h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])])
        lists = '. '.join([li.get_text(strip=True) for li in soup.find_all('li')])

        # Combine all content
        full_content = ""
        if title:
            full_content += f"Title: {title}\n\n"
        if meta_desc:
            full_content += f"Description: {meta_desc}\n\n"
        if headings:
            full_content += f"Key Topics: {headings}\n\n"
        if primary_content:
            full_content += f"Content: {primary_content}"
        if lists:
            full_content += f"\n\nKey Points: {lists}"

        # Clean up text
        text_content = re.sub(r'\s+', ' ', full_content)
        text_content = re.sub(r'\n\s*\n\s*\n', '\n\n', text_content)
        text_content = text_content.strip()[:15000]

        # Extract links
        links: List[ExtractedLink] = []
        seen_urls = set()

        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href', '')
            text = anchor.get_text(strip=True)

            if href and text:
                try:
                    absolute_url = urljoin(base_url, href)

                    # Filter out non-http(s) URLs and fragments
                    if not absolute_url.startswith(('http://', 'https://')):
                        continue
                    if '#' in absolute_url:
                        absolute_url = absolute_url.split('#')[0]
                    if not absolute_url:
                        continue

                    # Avoid duplicates
                    if absolute_url in seen_urls:
                        continue
                    seen_urls.add(absolute_url)

                    # Get context
                    parent = anchor.parent
                    context = parent.get_text(strip=True)[:200] if parent else ""

                    links.append(ExtractedLink(
                        url=absolute_url,
                        text=text[:200],
                        context=context,
                        relevance_score=0.5
                    ))

                except Exception:
                    continue

        return text_content, links

    def _get_document_type(self, url: str) -> Optional[str]:
        """Get document type from URL."""
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.yaml', '.yml')):
            return 'yaml'
        elif url_lower.endswith('.json'):
            return 'json'
        elif url_lower.endswith('.xml'):
            return 'xml'
        return None

    async def _scrape_document(self, url: str, depth: int, doc_type: str) -> PageData:
        """Scrape document (PDF, YAML, JSON, XML).

        Args:
            url: Document URL
            depth: Depth level
            doc_type: Document type

        Returns:
            Page data
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                content = response.content

            if doc_type == 'pdf':
                text_content = await self._extract_pdf_text(content)
            elif doc_type in ['yaml', 'yml']:
                text_content = content.decode('utf-8', errors='ignore')
            elif doc_type == 'json':
                text_content = content.decode('utf-8', errors='ignore')
            elif doc_type == 'xml':
                text_content = content.decode('utf-8', errors='ignore')
            else:
                text_content = content.decode('utf-8', errors='ignore')

            fetch_time = int((time.time() - start_time) * 1000)

            return PageData(
                url=url,
                title=self._extract_title_from_url(url),
                content=text_content[:15000],
                links=[],
                depth=depth,
                relevance_score=0.5,
                fetch_time=fetch_time,
                processing_time=0,
                metadata={'document_type': doc_type}
            )

        except Exception as error:
            fetch_time = int((time.time() - start_time) * 1000)

            return PageData(
                url=url,
                title=self._extract_title_from_url(url),
                content="",
                links=[],
                depth=depth,
                relevance_score=0.1,
                fetch_time=fetch_time,
                processing_time=0,
                error=str(error)
            )

    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            import pdfplumber
            from io import BytesIO

            with pdfplumber.open(BytesIO(content)) as pdf:
                text_parts = []
                for page in pdf.pages[:50]:  # Limit to first 50 pages
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                return '\n\n'.join(text_parts)
        except Exception as error:
            print(f"Warning: Failed to extract PDF text: {error}")
            return f"[PDF document - extraction failed: {str(error)}]"

    def _extract_title_from_url(self, url: str) -> str:
        """Extract title from URL."""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        if path:
            title = path.split('/')[-1]
            title = title.replace('-', ' ').replace('_', ' ')
            return title.title()
        return parsed.netloc

    async def close(self):
        """Close browser and playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
