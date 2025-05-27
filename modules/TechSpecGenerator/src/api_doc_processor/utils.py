"""Utility functions for API Documentation Processor."""

import re
from urllib.parse import urlparse
from typing import List, Tuple


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate a URL and return (is_valid, error_message).
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not url:
        return False, "URL cannot be empty"
    
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "URL must contain a valid domain"
        if not parsed.scheme in ('http', 'https'):
            return False, "URL scheme must be http or https"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def sanitize_filename(url: str) -> str:
    """
    Convert a URL to a safe filename for markdown files.
    
    Args:
        url: The URL to convert
        
    Returns:
        A safe filename string
    """
    # Remove protocol
    filename = url.replace('https://', '').replace('http://', '')
    
    # Replace unsafe characters with underscores
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    # Ensure it ends with .md
    if not filename.endswith('.md'):
        filename += '.md'
    
    return filename


def deduplicate_urls(urls: List[str]) -> List[str]:
    """
    Remove duplicate URLs while preserving order.
    
    Args:
        urls: List of URLs
        
    Returns:
        List of unique URLs in original order
    """
    seen = set()
    unique_urls = []
    
    for url in urls:
        # Normalize URL for comparison (remove trailing slashes, etc.)
        normalized = url.rstrip('/')
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(url)
    
    return unique_urls


def validate_urls_batch(urls: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Validate a batch of URLs.
    
    Args:
        urls: List of URLs to validate
        
    Returns:
        Tuple of (valid_urls, invalid_urls_with_errors)
    """
    valid_urls = []
    invalid_urls = []
    
    for url in urls:
        is_valid, error = validate_url(url)
        if is_valid:
            valid_urls.append(url)
        else:
            invalid_urls.append((url, error))
    
    return valid_urls, invalid_urls