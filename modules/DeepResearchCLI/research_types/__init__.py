"""Type definitions for Deep Research CLI."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum


@dataclass
class ResearchConfig:
    """Research configuration settings."""
    max_depth: int = 10
    max_pages_per_depth: int = 10
    max_total_pages: int = 100
    max_concurrent_pages: int = 3
    link_relevance_threshold: float = 0.2
    timeout_per_page: int = 30000
    respect_robots_txt: bool = True
    data_directory: str = "./research_data"
    history_file: str = "./research_history.json"
    interactive_mode: bool = True
    enable_deep_link_crawling: bool = True
    max_links_per_page: int = 10
    deep_crawl_depth: int = 10
    ai_driven_crawling: bool = False
    ai_link_ranking: bool = False
    ai_completeness_check: bool = False
    search_results_per_query: int = 15


@dataclass
class AIConfig:
    """AI provider configuration."""
    provider: Literal['litellm', 'vertex', 'anthropic'] = 'litellm'
    api_key: Optional[str] = None
    base_url: Optional[str] = "http://localhost:4000/v1"
    model_id: str = "gpt-4"
    project_id: Optional[str] = None
    location: Optional[str] = "us-east5"
    custom_instructions_file: Optional[str] = None
    custom_instructions: Optional[str] = None


@dataclass
class SearchResult:
    """Search result from search engine."""
    title: str
    url: str
    snippet: str
    engine: str
    score: float


@dataclass
class ExtractedLink:
    """Link extracted from a web page."""
    url: str
    text: str
    context: Optional[str] = None
    relevance_score: float = 0.5


@dataclass
class PageData:
    """Data extracted from a web page."""
    url: str
    title: str
    content: str
    links: List[ExtractedLink]
    depth: int
    relevance_score: float
    fetch_time: int
    processing_time: int
    ai_content: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResearchSessionMetadata:
    """Metadata for a research session."""
    total_links_found: int = 0
    error_count: int = 0
    ai_tokens_used: int = 0


@dataclass
class ResearchSession:
    """Research session information."""
    id: str
    query: str
    start_time: int
    status: Literal['running', 'completed', 'cancelled', 'failed']
    total_pages: int
    max_depth_reached: int
    metadata: ResearchSessionMetadata
    end_time: Optional[int] = None
    final_answer: Optional[str] = None
    confidence: Optional[float] = None


class LogType(str, Enum):
    """Type of log entry."""
    SEARCH = 'search'
    FETCH = 'fetch'
    PROCESS = 'process'
    ANALYSIS = 'analysis'
    ERROR = 'error'
    INFO = 'info'
    WARNING = 'warning'


@dataclass
class LogEntry:
    """Log entry for terminal UI."""
    timestamp: int
    type: LogType
    message: str
    data: Optional[Any] = None
    depth: Optional[int] = None
    url: Optional[str] = None
    expandable: bool = False
    expanded: bool = False
    children: List['LogEntry'] = field(default_factory=list)


class UserActionType(str, Enum):
    """Type of user action."""
    SKIP = 'skip'
    CANCEL = 'cancel'
    INPUT = 'input'
    EXPAND = 'expand'
    COLLAPSE = 'collapse'
    NEXT = 'next'


@dataclass
class UserAction:
    """User action in interactive mode."""
    type: UserActionType
    data: Optional[Any] = None


@dataclass
class AIMessage:
    """Message for AI conversation."""
    role: Literal['system', 'user', 'assistant']
    content: str


@dataclass
class AIResponse:
    """Response from AI service."""
    content: str
    tokens_used: int
