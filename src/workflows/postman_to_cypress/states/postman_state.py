from typing import Dict, Any, List, Optional, TypedDict, Literal
from pathlib import Path
from typing_extensions import TypedDict
from src.config import TechSpecConfig


class APIEndpoint(TypedDict):
    """Represents a single API endpoint from Postman collection."""
    name: str
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    query_params: Dict[str, str]
    auth_type: Optional[str]
    folder: str
    description: Optional[str]
    category: Optional[Literal["authorize", "capture", "psync", "other"]]
    execution_order: Optional[int]


class CredentialRequirement(TypedDict):
    """Represents authentication requirements extracted from collection."""
    auth_type: Literal["bearer", "basic", "api_key", "oauth2", "custom"]
    required_fields: List[str]
    description: str
    example_value: Optional[str]


class TestStructure(TypedDict):
    """Generated test structure for execution."""
    test_name: str
    test_file: str
    dependencies: List[str]
    api_endpoint: APIEndpoint
    assertions: List[Dict[str, Any]]
    pre_conditions: List[str]
    post_conditions: List[str]


class WorkflowMetadata(TypedDict, total=False):
    """Metadata about the workflow execution."""
    start_time: float
    end_time: float
    duration: float
    total_endpoints: int
    categorized_endpoints: int
    generated_tests: int
    collected_credentials: int
    execution_success: bool
    workflow_started: bool
    timestamp: str


class PostmanWorkflowState(TypedDict, total=False):
    """Complete state for the Postman to Cypress workflow."""

    # Configuration
    config: TechSpecConfig
    output_dir: Path
    
    # Workflow control
    collection_file: Path
    connector_name: str
    headless: bool
    verbose: bool
    
    # Input data - Postman collection
    raw_collection: Dict[str, Any]
    collection_info: Dict[str, str]
    collection_variables: Dict[str, str]
    
    # Parsed endpoints
    api_endpoints: List[APIEndpoint]
    categorized_endpoints: Dict[str, List[APIEndpoint]]
    execution_sequence: List[APIEndpoint]
    
    # Authentication and credentials
    credential_requirements: List[CredentialRequirement]
    collected_credentials: Dict[str, str]
    auth_config: Dict[str, Any]
    
    # Generated test structures
    test_structures: List[TestStructure]
    test_files: Dict[str, str]
    test_config: Dict[str, Any]
    
    # Execution results
    execution_results: List[Dict[str, Any]]
    test_results: Dict[str, Dict[str, Any]]
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    error: Optional[str]
    
    # Workflow metadata
    metadata: WorkflowMetadata
    
    # Output
    final_output: Dict[str, Any]
    success: bool
    
    # Node control flags
    node_config: Dict[str, Dict[str, Any]]