# API Documentation Processor

A command-line tool that automates the research and planning phase of API integration workflows by crawling multiple related REST API documentation pages, extracting content, and generating consolidated technical specifications using AI.

## Features

- Interactive URL collection for API documentation
- Automated document crawling and processing via Firecrawl
- AI-powered tech spec generation using LiteLLM
- Configurable prompts and LLM parameters
- Organized output management

## Installation
```bash
pip install -e .  
```

or 
```bash
pip install api-doc-processor
```

## Usage
```bash 
api-doc-processor --create-config
```
add your keys and then use 

```bash
api-doc-processor
```

Follow the interactive prompts to:
1. Enter API documentation URLs
2. Process and crawl the documentation
3. Generate consolidated technical specifications

## Configuration

The tool uses a `config.json` file for API keys and settings:

```json
{
  "firecrawl": {
    "api_key": "your-firecrawl-api-key"
  },
  "litellm": {
    "api_key": "your-llm-api-key",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "prompt": {
    "template": "Generate a comprehensive technical specification..."
  }
}
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

## License

MIT License
