# LangGraph API Documentation Processor

A powerful TypeScript CLI tool that automates API integration research and planning using real LangGraph workflows. This tool crawls API documentation, extracts content, generates technical specifications using AI, and creates mock servers - all with an interactive command-line interface.

## Features

- **Real LangGraph**: Uses the official @langchain/langgraph TypeScript package for robust workflow management
- **Interactive CLI**: Easy-to-use command-line interface with the same UX as the original Python version
- **URL Collection**: Gather API documentation URLs with validation and deduplication
- **Web Crawling**: Extract and convert content from API documentation pages to markdown
- **LLM Processing**: Generate comprehensive technical specifications using AI (OpenAI, Claude, etc.)
- **Mock Server Generation**: Create Express.js mock servers with realistic endpoints
- **TypeScript**: Full type safety and modern JavaScript features

## Installation

### NPM Global Installation (Recommended)
```bash
npm install -g langgraph-api-doc-processor
```

### Verify Installation
```bash
api-doc-processor --help
```

### Alternative: Clone and Build
```bash
git clone <repository-url>
cd langgraph-api-doc-processor
npm install
npm run build
npm link  # For global CLI access
```

## Usage

**EXACTLY like the Python version:**

### 1. Create configuration file
```bash
api-doc-processor --create-config
```

### 2. Update your API keys in config.json

### 3. Run the interactive workflow
```bash
api-doc-processor
```
Follow the interactive prompts to:
1. Enter API documentation URLs
2. Process and crawl the documentation  
3. Generate consolidated technical specifications

### Additional Options (same as Python)

```bash
# Test API connections
api-doc-processor --test-only

# Generate mock server after tech spec
api-doc-processor --generate-mock-server

# Custom output directory
api-doc-processor --output-dir "my-output"

# Verbose output
api-doc-processor --verbose

# Custom config file
api-doc-processor --config "my-config.json"

# Get help
api-doc-processor --help
```

### Development Usage
```bash
# If cloned from source
npm run dev -- --create-config
npm run dev
```

## Configuration

The tool uses a `config.json` file for API keys and settings (same format as Python version):

```json
{
  "firecrawl": {
    "api_key": "your-firecrawl-api-key"
  },
  "litellm": {
    "api_key": "your-llm-api-key",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7,
    "max_tokens": 50000,
    "base_url": "https://grid.ai.juspay.net",
    "custom_headers": {
      "X-Custom-Header": "value"
    }
  },
  "prompt": {
    "template": "Generate a comprehensive technical specification..."
  }
}
```

## Workflow Steps

1. **URL Collection**: Collects URLs from command line or environment
2. **Crawling**: Downloads and converts web content to markdown
3. **LLM Processing**: Generates technical specifications using AI
4. **Mock Server Generation**: Creates Express.js server with endpoints
5. **Output**: Displays summary and results

## Project Structure

```
src/
├── core/           # Core workflow engine
│   ├── state-graph.ts    # Real LangGraph integration
│   └── workflow.ts       # Main workflow orchestrator
├── nodes/          # Individual workflow nodes
│   ├── url-collection-node.ts
│   ├── crawling-node.ts
│   ├── llm-processing-node.ts
│   ├── mock-server-node.ts
│   └── output-node.ts
├── types/          # TypeScript type definitions
│   └── workflow-state.ts
├── utils/          # Utility functions
│   ├── console.ts        # Rich-like console output
│   ├── progress.ts       # Progress tracking
│   └── config.ts         # Configuration management
└── index.ts        # Main entry point
```

## Differences from Python Version

### Key Changes Made for TypeScript:

1. **Real LangGraph**: Uses official @langchain/langgraph TypeScript package
2. **Type Safety**: Full TypeScript interfaces for all data structures
3. **Async/Await**: Consistent promise-based async handling
4. **Modern Node.js**: Uses current Node.js APIs and best practices
5. **Error Handling**: Proper TypeScript error handling patterns

### Maintained Compatibility:

- **Identical LangGraph workflow**: Same StateGraph, conditional edges, and execution flow
- Same workflow state structure
- Identical node execution order
- Compatible configuration format
- Same output file structure
- Equivalent functionality

## Development

### Scripts

- `npm run build`: Compile TypeScript to JavaScript
- `npm run dev`: Run with ts-node for development
- `npm start`: Run compiled JavaScript
- `npm test`: Run tests (when implemented)
- `npm run lint`: Run ESLint
- `npm run clean`: Clean dist directory

### Adding New Nodes

1. Create a new file in `src/nodes/`
2. Implement the node function with signature: `(state: WorkflowState) => Promise<WorkflowState>`
3. Add the node to the workflow in `src/core/workflow.ts`
4. Export the node in `src/nodes/index.ts`

## Requirements

- Node.js 16+ 
- TypeScript 5+
- OpenAI API key or compatible LLM API

## License

MIT License
