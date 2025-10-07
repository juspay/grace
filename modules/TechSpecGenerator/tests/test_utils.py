"""Tests for utility functions."""

from api_doc_processor.utils import (
    validate_url, 
    sanitize_filename, 
    deduplicate_urls, 
    validate_urls_batch
)


def test_validate_url_valid():
    """Test URL validation with valid URLs."""
    valid_urls = [
        "https://api.example.com/docs",
        "http://docs.example.com",
        "https://api.stripe.com/docs/api",
    ]
    
    for url in valid_urls:
        is_valid, error = validate_url(url)
        assert is_valid, f"URL {url} should be valid, but got error: {error}"
        assert error == ""


def test_validate_url_invalid():
    """Test URL validation with invalid URLs."""
    invalid_cases = [
        ("", "URL cannot be empty"),
        ("not-a-url", "URL must start with http:// or https://"),
        ("ftp://example.com", "URL must start with http:// or https://"),
        ("https://", "URL must contain a valid domain"),
    ]
    
    for url, expected_error_part in invalid_cases:
        is_valid, error = validate_url(url)
        assert not is_valid, f"URL {url} should be invalid"
        assert expected_error_part.lower() in error.lower()


def test_sanitize_filename():
    """Test filename sanitization."""
    test_cases = [
        ("https://api.example.com/docs", "api.example.com_docs.md"),
        ("http://docs.stripe.com/api", "docs.stripe.com_api.md"),
        ("https://api.github.com/v3/users", "api.github.com_v3_users.md"),
    ]
    
    for url, expected in test_cases:
        result = sanitize_filename(url)
        assert result == expected, f"Expected {expected}, got {result}"


def test_deduplicate_urls():
    """Test URL deduplication."""
    urls = [
        "https://api.example.com/docs",
        "https://api.example.com/docs/",  # Duplicate with trailing slash
        "https://api.stripe.com/docs",
        "https://api.example.com/docs",   # Exact duplicate
    ]
    
    result = deduplicate_urls(urls)
    
    assert len(result) == 2
    assert "https://api.example.com/docs" in result
    assert "https://api.stripe.com/docs" in result


def test_validate_urls_batch():
    """Test batch URL validation."""
    urls = [
        "https://api.example.com/docs",  # Valid
        "invalid-url",                   # Invalid
        "https://api.stripe.com/docs",   # Valid
        "",                             # Invalid
    ]
    
    valid_urls, invalid_urls = validate_urls_batch(urls)
    
    assert len(valid_urls) == 2
    assert len(invalid_urls) == 2
    
    assert "https://api.example.com/docs" in valid_urls
    assert "https://api.stripe.com/docs" in valid_urls
    
    invalid_url_list = [url for url, error in invalid_urls]
    assert "invalid-url" in invalid_url_list
    assert "" in invalid_url_list