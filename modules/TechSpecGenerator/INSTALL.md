# Installation Guide

## Quick Start

### 1. Install the Package

```bash
# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### 2. Create Configuration

```bash
# Create a sample configuration file
api-doc-processor --create-config

# Edit the configuration file with your API keys
nano config.json
```

### 3. Configure API Keys

Edit `config.json` with your actual API keys:

```json
{
  "firecrawl": {
    "api_key": "your-actual-firecrawl-api-key"
  },
  "litellm": {
    "api_key": "your-actual-openai-api-key",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

### 4. Test Your Setup

```bash
# Test API connections
api-doc-processor --test-only
```

### 5. Process Documentation

```bash
# Run the interactive tool
api-doc-processor
```

## API Key Setup

### Firecrawl API Key

1. Sign up at [firecrawl.dev](https://firecrawl.dev)
2. Get your API key from the dashboard
3. Add it to your `config.json`

### LLM API Keys

#### OpenAI (GPT models)
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Generate an API key
3. Use models like: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`

#### Anthropic (Claude models)
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key
3. Use models like: `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`

#### Google (Gemini models)
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Use models like: `gemini-pro`, `gemini-pro-vision`

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Development Installation

```bash
# Clone or navigate to the project directory
cd api-doc-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/api_doc_processor

# Run specific test file
pytest tests/test_config.py
```

### Code Formatting

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src
```

## Troubleshooting

### Common Issues

1. **Import Error for litellm**: Install with `pip install litellm`
2. **API Key Errors**: Verify your API keys are correct and have proper permissions
3. **Network Errors**: Check your internet connection and firewall settings
4. **File Permission Errors**: Ensure you have write permissions in the output directory

### Verbose Mode

Use the `--verbose` flag for detailed error information:

```bash
api-doc-processor --verbose
```

### Output Directory

By default, files are saved to `api-doc-processor-data/`. You can change this:

```bash
api-doc-processor --output-dir /path/to/your/directory
```

## Configuration Options

### LLM Model Configuration

You can use different LLM providers and models:

```json
{
  "litellm": {
    "api_key": "your-key",
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 8000
  }
}
```

### Custom Prompts

Customize the prompt template in your config:

```json
{
  "prompt": {
    "template": "Your custom prompt template here. Use {content} where you want the documentation content inserted."
  }
}
```

## Command Line Options

```bash
api-doc-processor --help
```

Available options:
- `--config PATH`: Specify configuration file path
- `--create-config`: Create sample configuration and exit
- `--output-dir PATH`: Specify output directory
- `--test-only`: Test API connections and exit
- `--verbose`: Enable verbose output