# Grace CLI - LangGraph Workflow System

Intelligent research and technical specification generator using LangGraph workflows.

## Features

- **Research Workflow**: Deep research with intelligent source discovery, content analysis, and synthesis
- **Techspec Workflow**: Automated connector code generation with validation and documentation
- **LangGraph Integration**: State-based workflow orchestration with parallel processing
- **Rich Output**: Multiple formats (Markdown, JSON, Text) with comprehensive metadata

## Requirements

- Python 3.9+ (Required for LangGraph compatibility)
- uv or pip for package management

## Installation

### Using uv (Recommended)
```bash
# Install from source
cd grace
uv sync

# Or install specific feature groups
uv sync --extra dev --extra ai --extra scraping
```

### Using pip
```bash
# Install in development mode
pip install -e .

# Or with optional dependencies
pip install -e ".[dev,ai,scraping,nlp]"
```

## Quick Start

### Research Workflow
```bash
# Basic research
grace research "machine learning trends 2024"

# Advanced research with options
grace research "AI in healthcare" \
  --depth 8 \
  --sources 15 \
  --format json \
  --output research_report.json \
  --verbose
```

### Techspec Workflow
```bash
# Generate connector for a payment processor
grace techspec stripe \
  --api-doc stripe_api.yaml \
  --output ./generated/stripe \
  --verbose

# Test mode (no file generation)
grace techspec paypal --test-only

# Create configuration template
grace techspec --create-config
```

## LangGraph Workflow Architecture

Both workflows use LangGraph for sophisticated state management and parallel processing:

### Research Workflow States
```
Query Analysis -> Source Discovery -> Content Extraction
                                            |
Format Output <- Synthesize Report <- Analyze Content
```

### Techspec Workflow States
```
API Analysis -> Schema Extract -> Code Generation
                                       |
Finalize Output <- Generate Docs <- Validate Code
```

## Usage Examples

### Research Examples
```bash
# Technology research with specific depth
grace research "blockchain scalability solutions" --depth 7

# Business research with JSON output
grace research "SaaS pricing strategies 2024" --sources 20 --format json

# Save to file
grace research "quantum computing applications" --output quantum_report.md
```

### Techspec Examples
```bash
# Payment processor connector
grace techspec adyen --api-doc adyen_openapi.yaml

# E-commerce platform with custom output
grace techspec shopify --output ./connectors/shopify --verbose

# Test without generating files
grace techspec test_connector --test-only
```

## Development

### Setup
```bash
git clone <repository-url>
cd grace
uv sync --extra dev
```


### Code Formatting
```bash
uv run black src/
uv run mypy src/
```

## Troubleshooting

### Dependency Resolution
If you get Python version conflicts:
```bash
# Check Python version
python --version  # Should be 3.9+

# Clear cache and reinstall
uv cache clean
uv sync
```

### Import Errors
If LangGraph imports fail:
```bash
# Install core dependencies
uv add langgraph langchain langchain-core
```

## API Reference

### Python API
```python
from grace_clio.research import run_research_workflow
from grace_clio.techspec import run_techspec_workflow

# Research workflow
result = await run_research_workflow(
    query="AI trends",
    format_type="markdown",
    depth=5,
    max_sources=10
)

# Techspec workflow
result = await run_techspec_workflow(
    connector_name="stripe",
    api_doc_path="stripe_api.yaml",
    output_dir="./generated"
)
```

## License

MIT License