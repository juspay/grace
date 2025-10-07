"""State management for the LangGraph workflow."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict, NotRequired

from .config import Config


class CrawlResult(TypedDict):
    """Result from crawling a single URL."""
    success: bool
    filepath: Optional[str]
    content_length: int
    error: Optional[str]
    url: str


class WorkflowMetadata(TypedDict):
    """Metadata about the workflow execution."""
    start_time: NotRequired[float]
    end_time: NotRequired[float]
    duration: NotRequired[float]
    total_urls: NotRequired[int]
    successful_crawls: NotRequired[int]
    failed_crawls: NotRequired[int]
    spec_generated: NotRequired[bool]
    estimated_tokens: NotRequired[Dict[str, int]]
    mock_server_generated: NotRequired[bool]


class WorkflowState(TypedDict):
    """Complete state for the API documentation processing workflow."""
    
    # Configuration
    config: Config
    output_dir: Path
    
    # Input data
    urls: List[str]
    
    # Processing results
    crawl_results: Dict[str, CrawlResult]
    markdown_files: List[Path]
    tech_spec: NotRequired[str]
    spec_filepath: NotRequired[Path]
    
    # Mock server results
    mock_server_dir: NotRequired[Path]
    mock_server_process: NotRequired[Any]
    mock_server_data: NotRequired[Dict[str, Any]]
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    
    # Workflow metadata
    metadata: WorkflowMetadata
    
    # Node control flags
    node_config: NotRequired[Dict[str, Dict[str, Any]]]


class NodeConfig(TypedDict):
    """Configuration for individual workflow nodes."""
    enabled: bool
    retry_count: NotRequired[int]
    timeout: NotRequired[float]
    parallel: NotRequired[bool]
    custom_params: NotRequired[Dict[str, Any]]


class WorkflowConfig(TypedDict):
    """Configuration for the entire workflow."""
    url_collection: NotRequired[NodeConfig]
    crawling: NotRequired[NodeConfig] 
    llm_processing: NotRequired[NodeConfig]
    mock_server_generation: NotRequired[NodeConfig]
    output_management: NotRequired[NodeConfig]