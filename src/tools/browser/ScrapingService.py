from src.config import get_config
from .BrowserService import BrowserService
from rich.console import Console
import asyncio
from typing import List, Optional, Callable, Any

class ScrappingService:
    def __init__(self):
        self.browser_service = BrowserService(headless=True)
        self.pages_data = []
        self.console = Console()
        self.config = get_config().getResearchConfig()
    async def scrape(self, url: str, browser_service: BrowserService = None) -> Optional[dict]:
        service = browser_service or self.browser_service
        try:
            if service.browser is None:
                await service.start()
            await service.wait_for_load(1000)
            if not await service.navigate_to(url):
                self.console.print(f"Failed to navigate to {url}")
                return None
            await service.wait_for_load(1000)
            page_info = await service.get_page_info()
            html_content = await service.get_markdown_content()
            page_data = {
                'url': url,
                'title': page_info.get('title', ''),
                'html_content': html_content,
                'status': 'success'
            }
            return page_data

        except Exception as e:
            self.console.log(f"Error occurred while scraping {url}: {e}")
            error_data = {
                'url': url,
                'error': str(e),
                'status': 'error'
            }
            return error_data

    # Ai Browsing Logic using vision-based AI models can be integrated here
    async def scrape_with_ai(self, url: str, browser_service: BrowserService = None) -> Optional[dict]:
        service = browser_service or self.browser_service
        try:
            result = await self.scrape(url, service)
            return result
        except Exception as e:
            self.console.log(f"Error occurred while AI scraping {url}: {e}")
            return None
        finally:
            if not browser_service is None:
                await service.close()

    async def _scrape_with_browser(self, url: str) -> Optional[dict]:
        browser_service = BrowserService()
        try:
            if self.config.with_ai_browser:
                result = await self.scrape_with_ai(url, browser_service)
            else:
                result = await self.scrape(url, browser_service)
            return result
        finally:
            await browser_service.close()

    async def scrape_multiple_pages(self, urls: List[str], callback: Optional[Callable[[Any], None]] = None, parallel_count: int = 1):
        with_ai_browser = self.config.with_ai_browser
        if not urls:
            self.console.print("No URLs provided for scraping")
            return
        self.pages_data = []
        if parallel_count <= 1:
            for url in urls:
                result = None
                if with_ai_browser:
                    result = await self.scrape_with_ai(url)
                else:
                    result = await self.scrape(url)
                self.pages_data.append(result)
                if callback and result:
                    try:
                        await callback(result) if asyncio.iscoroutinefunction(callback) else callback(result)
                    except Exception as e:
                        self.console.log(f"Error in callback for {url}: {e}")
            await self.browser_service.close()
            return self.pages_data
        else:
            semaphore = asyncio.Semaphore(parallel_count)
            async def scrape_with_semaphore(url: str):
                async with semaphore:
                    result = await self._scrape_with_browser(url)
                    if callback and result:
                        try:
                            await callback(result) if asyncio.iscoroutinefunction(callback) else callback(result)
                        except Exception as e:
                            self.console.log(f"Error in callback for {url}: {e}")
                    return result
            
            tasks = [scrape_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                self.pages_data.append(result)
            successful_count = 0
            error_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.console.log(f"Exception occurred while scraping {urls[i]}: {result}")
                    error_count += 1
                elif result and result.get('status') == 'success':
                    successful_count += 1
                else:
                    error_count += 1            
            await self.browser_service.close()
            return self.pages_data