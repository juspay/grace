"""Configuration management for API Documentation Processor."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class FirecrawlConfig(BaseModel):
    """Firecrawl API configuration."""
    api_key: str = Field(..., description="Firecrawl API key")


class LiteLLMConfig(BaseModel):
    """LiteLLM configuration."""
    api_key: str = Field(..., description="LLM provider API key or proxy token")
    model: str = Field(default="gpt-3.5-turbo", description="LLM model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for LLM")
    max_tokens: int = Field(default=4000, gt=0, description="Maximum tokens for LLM response")
    base_url: Optional[str] = Field(default=None, description="Custom base URL for proxy endpoints")
    custom_headers: Optional[dict] = Field(default=None, description="Custom headers for proxy requests")


class PromptConfig(BaseModel):
    """Prompt configuration."""
    template: str = Field(
        default="""You are tasked with creating comprehensive API documentation by extracting information from the provided context. Your role is to structure the available information into a standardized documentation format without making any modifications, assumptions, or interpretations.

## Core Requirements:
- Extract ALL available endpoints from the following documentation
- Maintain exact 1:1 correspondence between source content and documentation
- Do not modify, enhance, or assume any missing information
- Structure only what is explicitly present in the source material
- Cover all API flows mentioned in the context, not just specific ones

## Documentation Structure:

### Connector Information
- Extract connector name and basic details as provided
- List all base URLs (production, sandbox, testing) mentioned
- Include any additional URLs found (webhooks, status endpoints, documentation links, etc.)

### Authentication Details
- Document authentication methods exactly as described
- Include all authentication parameters, headers, and configurations mentioned
- Preserve exact format of API keys, tokens, or credentials structure

### Complete Endpoint Inventory
For EVERY endpoint found in the context, document:
- Exact endpoint URL/path
- HTTP method
- All headers mentioned
- Complete request payload structure (as provided)
- Complete response payload structure (as provided)
- Any curl examples if present
- Error responses if documented

### Flow Categories to Extract:
Document all flows present, which may include:
- Payment/Authorization flows
- Capture operations
- Refund processes
- Status/sync endpoints
- Dispute handling
- Tokenization/vaulting
- Webhook endpoints
- Account/configuration endpoints
- Any other flows mentioned

### Configuration Parameters
- List all configuration requirements mentioned
- Environment variables or settings
- Supported features, currencies, regions as stated
- Integration requirements

## Output Guidelines:
- Use the exact field names, values, and structures from the source
- Preserve original JSON formatting and data types
- Include all optional and required parameters as marked
- Maintain original error codes and messages
- Do not fill gaps or make educated guesses
- If information is partially available, document only what's explicitly provided
- Use "Not specified in source" for clearly missing but relevant information

Generate documentation that serves as a faithful representation of the API capabilities based solely on the provided context.

API Documentation:
{content}""",
        description="Template for extracting and structuring API documentation without modifications or assumptions"
    )   


class WorkflowNodeConfig(BaseModel):
    """Configuration for individual workflow nodes."""
    enabled: bool = Field(default=True, description="Whether this node is enabled")
    retry_count: int = Field(default=1, description="Number of retries for this node")
    timeout: float = Field(default=300.0, description="Timeout in seconds")


class WorkflowConfig(BaseModel):
    """Configuration for workflow behavior."""
    url_collection: WorkflowNodeConfig = Field(default_factory=WorkflowNodeConfig)
    crawling: WorkflowNodeConfig = Field(default_factory=WorkflowNodeConfig)
    llm_processing: WorkflowNodeConfig = Field(default_factory=WorkflowNodeConfig)
    mock_server_generation: WorkflowNodeConfig = Field(default_factory=lambda: WorkflowNodeConfig(enabled=False))
    output_management: WorkflowNodeConfig = Field(default_factory=WorkflowNodeConfig)


class Config(BaseModel):
    """Main configuration model."""
    firecrawl: FirecrawlConfig
    litellm: LiteLLMConfig
    prompt: PromptConfig = Field(default_factory=PromptConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = Path("config.json")
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please create a config.json file with your API keys."
        )
    
    try:
        with open(config_path) as f:
            config_data = json.load(f)
        return Config(**config_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")


def create_sample_config(config_path: Optional[Path] = None) -> None:
    """Create a sample configuration file."""
    if config_path is None:
        config_path = Path("config.json")
    
    sample_config = {
        "firecrawl": {
            "api_key": "your-firecrawl-api-key-here"
        },
        "litellm": {
            "api_key": "your-llm-api-key-here",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 50000,
            "_comment": "For proxy setups, add base_url and optionally custom_headers",
            "base_url": "https://grid.ai.juspay.net",
            "custom_headers": {
                "X-Custom-Header": "value"
            }
            
        },
        "prompt": {
            "template": "You are tasked with creating comprehensive API documentation by extracting information from the provided context. Your role is to structure the available information into a standardized documentation format without making any modifications, assumptions, or interpretations.\n\n## Core Requirements:\n- Extract ALL available endpoints from the following documentation\n- Maintain exact 1:1 correspondence between source content and documentation\n- Do not modify, enhance, or assume any missing information\n- Structure only what is explicitly present in the source material\n- Cover all API flows mentioned in the context, not just specific ones\n\n## Documentation Structure:\n\n### Connector Information\n- Extract connector name and basic details as provided\n- List all base URLs (production, sandbox, testing) mentioned\n- Include any additional URLs found (webhooks, status endpoints, documentation links, etc.)\n\n### Authentication Details\n- Document authentication methods exactly as described\n- Include all authentication parameters, headers, and configurations mentioned\n- Preserve exact format of API keys, tokens, or credentials structure\n\n### Complete Endpoint Inventory\nFor EVERY endpoint found in the context, document:\n- Exact endpoint URL/path\n- HTTP method\n- All headers mentioned\n- Complete request payload structure (as provided)\n- Complete response payload structure (as provided)\n- Any curl examples if present\n- Error responses if documented\n\n### Flow Categories to Extract:\nDocument all flows present, which may include:\n- Payment/Authorization flows\n- Capture operations\n- Refund processes\n- Status/sync endpoints\n- Dispute handling\n- Tokenization/vaulting\n- Webhook endpoints\n- Account/configuration endpoints\n- Any other flows mentioned\n\n### Configuration Parameters\n- List all configuration requirements mentioned\n- Environment variables or settings\n- Supported features, currencies, regions as stated\n- Integration requirements\n\n## Output Guidelines:\n- Use the exact field names, values, and structures from the source\n- Preserve original JSON formatting and data types\n- Include all optional and required parameters as marked\n- Maintain original error codes and messages\n- Do not fill gaps or make educated guesses\n- If information is partially available, document only what's explicitly provided\n- Use \"Not specified in source\" for clearly missing but relevant information\n\nGenerate documentation that serves as a faithful representation of the API capabilities based solely on the provided context.\n\nAPI Documentation:\n{content}"
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Sample configuration created at: {config_path}")
    print("Please update the API keys before running the tool.")