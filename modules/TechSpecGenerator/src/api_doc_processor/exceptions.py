"""Custom exceptions for API Documentation Processor."""


class APIDocProcessorError(Exception):
    """Base exception for API Documentation Processor."""
    pass


class ConfigurationError(APIDocProcessorError):
    """Raised when there's an issue with configuration."""
    pass


class FirecrawlError(APIDocProcessorError):
    """Raised when there's an issue with Firecrawl API."""
    pass


class LLMError(APIDocProcessorError):
    """Raised when there's an issue with LLM processing."""
    pass


class ValidationError(APIDocProcessorError):
    """Raised when validation fails."""
    pass


class NetworkError(APIDocProcessorError):
    """Raised when there's a network-related issue."""
    pass