"""Firecrawl API client for document crawling and processing."""

import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time

from .config import FirecrawlConfig
from .utils import sanitize_filename


class FirecrawlClient:
    """Client for interacting with Firecrawl API."""
    
    def __init__(self, config: FirecrawlConfig):
        """Initialize the Firecrawl client."""
        self.api_key = config.api_key
        self.base_url = "https://api.firecrawl.dev/v0"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def scrape_url(self, url: str) -> Tuple[bool, str, str]:
        """
        Scrape a single URL and return markdown content.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Tuple of (success: bool, content: str, error_message: str)
        """
        try:
            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "includeTags": ["title", "meta"],
                "excludeTags": ["nav", "footer", "aside", "script", "style"]
            }
            
            response = self.session.post(f"{self.base_url}/scrape", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    markdown_content = data.get("data", {}).get("markdown", "")
                    if markdown_content:
                        return True, markdown_content, ""
                    else:
                        return False, "", "No markdown content returned"
                else:
                    error_msg = data.get("error", "Unknown error")
                    return False, "", f"Firecrawl API error: {error_msg}"
            else:
                return False, "", f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, "", f"Network error: {str(e)}"
        except Exception as e:
            return False, "", f"Unexpected error: {str(e)}"
    
    def scrape_urls_batch(self, urls: List[str], output_dir: Path) -> Dict[str, Dict]:
        """
        Scrape multiple URLs and save to markdown files.
        
        Args:
            urls: List of URLs to scrape
            output_dir: Directory to save markdown files
            
        Returns:
            Dictionary mapping URLs to their processing results
        """
        results = {}
        
        for url in urls:
            success, content, error = self.scrape_url(url)
            
            if success:
                # Save markdown content to file
                filename = sanitize_filename(url)
                filepath = output_dir / filename
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# Documentation for {url}\n\n")
                        f.write(f"**Source URL:** {url}\n\n")
                        f.write("---\n\n")
                        f.write(content)
                    
                    results[url] = {
                        "success": True,
                        "filepath": str(filepath),
                        "content_length": len(content),
                        "error": None
                    }
                except Exception as e:
                    results[url] = {
                        "success": False,
                        "filepath": None,
                        "content_length": 0,
                        "error": f"File write error: {str(e)}"
                    }
            else:
                results[url] = {
                    "success": False,
                    "filepath": None,
                    "content_length": 0,
                    "error": error
                }
            
            # Small delay to be respectful to the API
            time.sleep(0.5)
        
        return results
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the Firecrawl API connection and authentication.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Test with a simple URL
            test_url = "https://httpbin.org/html"
            success, content, error = self.scrape_url(test_url)
            
            if success:
                return True, "Firecrawl API connection successful"
            else:
                return False, f"Firecrawl API test failed: {error}"
                
        except Exception as e:
            return False, f"Connection test error: {str(e)}"