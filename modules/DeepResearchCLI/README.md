# 🔍 MASS Deep Research CLI

A powerful command-line interface for conducting comprehensive, AI-driven web research with beautiful terminal UI and intelligent deep research capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.4.3-blue.svg)

## ✨ Features

### 🤖 Intelligent Deep Research
- **AI-driven depth control** - AI decides when to stop researching for optimal accuracy
- **Link extraction from pages** - Discovers and follows links from search result pages
- **Multi-stage content processing** - Extracts, processes, and summarizes content following custom instructions
- **Information completeness assessment** - Continuously evaluates research completeness
- **Smart stopping criteria** - Prevents low-quality rabbit holes and maintains high accuracy
- **Adaptive link selection** - Prioritizes high-relevance links with depth-based thresholds

### 🧠 Advanced AI Integration
- **Custom instruction following** - Loads and follows your specific research instructions
- **Content summarization** - AI processes each page following your requirements
- **Relevance scoring** - AI rates content and link relevance in real-time
- **Research decision making** - AI evaluates whether to continue deeper or stop
- **Multi-depth web crawling** with configurable depth levels (up to 7 levels deep)
- **Final synthesis** with confidence scoring and specialized output formatting

### 🎨 Beautiful Terminal UI
- **Interactive terminal interface** built with blessed and terminal-kit
- **Real-time progress visualization** with expandable/collapsible logs
- **Beautiful tree-structure logging** showing research progression
- **Live status updates** with color-coded information
- **Keyboard shortcuts** for quick actions (skip, cancel, expand/collapse)

### 🔧 Advanced Configuration
- **Environment-based configuration** with `.env` support
- **Multiple AI providers** (LiteLLM, Vertex AI)
- **Custom AI instructions** from file for personalized research behavior
- **Proxy support** for enhanced privacy and bot prevention
- **Stealth browsing** with randomized user agents and viewport sizes
- **Configurable timeouts, depths, and page limits**

### 📊 Comprehensive Output
- **Multiple export formats**: HTML, JSON, Markdown
- **Beautiful HTML reports** with responsive design
- **Detailed statistics** and metadata
- **Debug logging** for development and troubleshooting
- **Research history** with search capabilities

### 🛡️ Bot Prevention & Stealth
- **Advanced stealth techniques** to avoid detection
- **Rotating proxy support** for IP diversity
- **Realistic browsing patterns** with random delays
- **robots.txt compliance** (configurable)
- **JavaScript-enabled scraping** with Playwright

## 🚀 Quick Start

### Prerequisites
- Node.js 18.0.0 or higher
- npm or yarn
- Docker Desktop or OrbStack (for SearxNG search engine)

### ⚡ Fast Setup (3 steps)

1. **Install dependencies**:
```bash
npm install
```

2. **Run automated setup** (configures SearxNG JSON API):
```bash
npm run setup
```
This will:
- ✅ Check Docker/OrbStack installation
- ✅ Configure and start SearxNG with optimized JSON API settings
- ✅ Test both web interface and JSON API functionality
- ✅ Find available ports automatically (cross-platform)
- ✅ Create `.env.example` with correct configuration

3. **Configure AI and start researching**:
```bash
# Copy and edit environment file
cp .env.example .env
# Add your AI API keys to .env

# Build the project
npm run build

# Start researching (follows your custom_instructions.txt)
npm start research "your research query"
```

### ✨ What You Get
- **Custom instruction support** - Research outputs in your specified format (OpenAPI, JSON, etc.)
- **Real web search** - Powered by SearxNG with Google, Bing, DuckDuckGo engines
- **Cross-platform compatibility** - Works on Windows, Mac, and Linux
- **Intelligent depth control** - AI decides when to stop researching for optimal results

### Alternative Manual Setup

If you prefer manual setup or already have SearxNG running:

1. **Install dependencies**: `npm install`
2. **Copy environment**: `cp .env.example .env`
3. **Configure your AI provider** in `.env`
4. **Set SearxNG URL** in `.env` (if using external instance)
5. **Build and run**: `npm run build && npm start`

For detailed setup instructions, see [SETUP.md](./SETUP.md).

## 📋 Configuration

### Environment Variables

Create a `.env` file in the cli directory with the following configuration:

```env
# AI Configuration
AI_PROVIDER=litellm
LITELLM_API_KEY=your_api_key_here
LITELLM_BASE_URL=http://localhost:4000/v1
LITELLM_MODEL_ID=gpt-4

# Custom Instructions (optional)
CUSTOM_INSTRUCTIONS_FILE=./custom_instructions.txt

# Research Configuration
MAX_DEPTH=5
MAX_PAGES_PER_DEPTH=10
MAX_TOTAL_PAGES=50
CONCURRENT_PAGES=3
LINK_RELEVANCE_THRESHOLD=0.6
TIMEOUT_PER_PAGE_MS=30000
RESPECT_ROBOTS_TXT=true

# Data Storage
RESEARCH_DATA_DIR=./research_data
HISTORY_FILE=./research_history.json

# SearXNG Configuration (configured by setup script)
SEARXNG_BASE_URL=http://localhost:8080

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT_MS=30000

# Proxy Configuration (optional)
PROXY_LIST=http://proxy1:port,http://proxy2:port,socks5://proxy3:port

# Debug Configuration
IS_DEBUG=false
DEBUG_LOG_FILE=./search_query_time.log
RESULT_OUTPUT_DIR=./cli/result
```

### AI Provider Setup

#### LiteLLM (Recommended)
1. Set up LiteLLM server or use a hosted instance
2. Configure `LITELLM_API_KEY` and `LITELLM_BASE_URL`
3. Set your preferred model in `LITELLM_MODEL_ID`

#### Vertex AI
1. Set up Google Cloud Project
2. Enable Vertex AI API
3. Configure authentication
4. Set `AI_PROVIDER=vertex` and configure project details

### 📝 Custom Instructions

The CLI now properly supports custom instructions that allow you to personalize the AI's research behavior and output format. **Recent fixes ensure instructions are consistently followed.**

#### Recent Fixes Applied
- ✅ **Fixed conflicting format requirements** - No more JSON vs custom format conflicts
- ✅ **Removed duplicate loading logic** - Single source of truth for instructions
- ✅ **Enhanced format detection** - AI now respects custom output formats (OpenAPI YAML, etc.)
- ✅ **Improved content passing** - Full research data available for custom formatting

#### Setting Up Custom Instructions

1. **Create an instructions file** (e.g., `custom_instructions.txt`):

**Example: General Research Instructions**
```txt
You are an expert AI research assistant specializing in deep web research and analysis.

## Core Instructions:
- Always prioritize accuracy and factual information over speed
- When analyzing web content, focus on authoritative sources
- Provide detailed, well-structured analysis with clear reasoning
- Identify potential biases or limitations in sources
- Use markdown formatting for better readability

## Research Approach:
- Start with the most authoritative and recent sources
- Look for primary sources when possible
- Consider multiple perspectives on controversial topics
```

**Example: OpenAPI Specification Instructions (for Payment Gateway Integration)**
```txt
You are an expert AI agent to do deep research to gather technical information for integrating payment gateways. Your goal is to produce a detailed, structured OpenAPI spec for the connector in the specified format.

Format of the OUTPUT:

openapi: 3.0.3
info:
  title: "{{CONNECTOR_NAME}} Connector Integration Specification"
  description: |
    Minimal specification for perfect codegen of a {{CONNECTOR_NAME}} connector.
  version: 1.0.0

components:
  schemas:
    CONNECTOR_NAME\ConnectorSpec:
      type: object
      required:
        - connector_name
        - auth_type
        - supported_flows
        - api_endpoints
      properties:
        connector_name:
          type: string
          example: "{{CONNECTOR_NAME}}"
        auth_type:
          $ref: '#/components/schemas/AuthConfig'
        # ... (continue with your specific format)
```

2. **Add to your .env file**:
```env
CUSTOM_INSTRUCTIONS_FILE=./custom_instructions.txt
```

3. **Verify configuration**:
```bash
npm start config
```

#### How to Use Custom Instructions

**✅ Correct way (follows custom instructions):**
```bash
npm start research "stripe payment gateway integration"
```

**❌ Wrong way (ignores custom instructions):**
```bash
npm run dev  # This is for interactive mode, prompts for custom instructions
```

#### Features
- ✅ **Fixed format conflicts** - No more JSON vs custom format issues
- ✅ **Consistent application** - Instructions applied to all research phases
- ✅ **Full data access** - Custom instructions receive complete research data
- ✅ **Format detection** - AI detects and follows output format requirements
- ✅ **Error handling** - Graceful fallback if file is missing
- ✅ **Configuration display** - See loaded instructions in config command

#### Troubleshooting Custom Instructions

**Instructions not being followed:**
1. Ensure using `npm start research "query"` (not `npm run dev`)
2. Check file exists: `ls -la custom_instructions.txt`
3. Verify configuration: `npm start config`
4. Check file permissions: `chmod 644 custom_instructions.txt`

**Format conflicts:**
- The recent fixes eliminate JSON vs custom format conflicts
- AI now prioritizes custom instructions over default formatting
- Full research data is passed to custom instruction processing

For detailed examples and best practices, see [CUSTOM_INSTRUCTIONS.md](./CUSTOM_INSTRUCTIONS.md).

## 💻 Usage

### 🔧 Setup (One-time)

Before using the CLI, run the automated setup to configure SearxNG:

```bash
npm run setup
```

This will:
- ✅ Check Docker/OrbStack installation
- ✅ Configure and start SearxNG with optimized JSON API settings
- ✅ Test both web interface and JSON API functionality
- ✅ Find available ports automatically (cross-platform support)
- ✅ Create `.env.example` template with correct SearxNG URL

### 🎯 Research Commands

#### Direct Research (Recommended)
Use this for research following your custom instructions:

```bash
# Research with custom instructions from file
npm start research "stripe payment gateway integration"

# Research with specific query
npm start research "GraphQL vs REST performance comparison"
```

#### Interactive Mode
For guided research with prompts:

```bash
# Start interactive mode (no arguments)
npm run dev

# Or explicit interactive mode
npm start
```

#### Testing & Diagnostics

```bash
# Test SearxNG connectivity and JSON API
npm start test-search

# Test with custom query
npm start test-search -q "payment gateways"

# Show current configuration
npm start config

# View research history
npm start history

# Show research statistics
npm start stats

# Clean up old data
npm start clean --days 30
```

### 🚨 Important Usage Notes

**For Custom Instructions (OpenAPI, specific formats):**
- Use `npm start research "your query"` - this follows your `custom_instructions.txt`
- Avoid `npm run dev` for formatted output - this is for interactive/general research

**SearxNG JSON API:**
- The setup automatically configures SearxNG for proper JSON API responses
- If you see "Search failed, using fallback" - run `npm start test-search` to diagnose
- SearxNG must be running for real web search (fallback provides limited mock results)

### Terminal UI Controls

During research, you can use these controls:

- **`1`** - Skip current operation
- **`2`** - Cancel research
- **`3`** - Show research history
- **`Ctrl+O`** - Expand/collapse log entries
- **`Enter`** - Provide custom input/guidance
- **`Tab`** - Switch between log and input areas
- **`Escape/Q/Ctrl+C`** - Exit application

## 📊 Output Formats

### HTML Report
Beautiful, responsive HTML report with:
- Executive summary with statistics
- Interactive source analysis
- Collapsible content sections
- Professional styling

### JSON Export
Complete structured data including:
- Session metadata
- All page data with content
- Link analysis results
- AI scoring and insights

### Markdown Report
Clean markdown format perfect for:
- Documentation
- Sharing findings
- Integration with other tools

## 🔧 Advanced Features

### Debug Mode

Enable debug mode for detailed logging:

```env
IS_DEBUG=true
DEBUG_LOG_FILE=./search_query_time.log
```

Debug logs include:
- Search query timing
- Page fetch performance
- AI call details
- Error tracking
- Session summaries

### Proxy Configuration

For enhanced privacy and bot prevention:

```env
PROXY_LIST=http://user:pass@proxy1:8080,socks5://proxy2:1080
```

The system will automatically rotate through proxies for different requests.

### Custom Research Flows

The CLI supports mid-research guidance:
- AI will occasionally ask for direction
- You can provide custom instructions
- Research adapts based on your input
- Skip or cancel operations as needed

## 📁 File Structure

```
cli/
├── src/
│   ├── services/           # Core research services
│   │   ├── AIService.ts           # AI integration
│   │   ├── SearchService.ts       # Web search
│   │   ├── WebScrapingService.ts  # Content extraction
│   │   ├── ConfigService.ts       # Configuration management
│   │   ├── StorageService.ts      # Data persistence
│   │   ├── ResultOutputService.ts # Result formatting
│   │   └── DeepResearchOrchestrator.ts # Main orchestrator
│   ├── ui/                # Terminal UI components
│   │   └── TerminalUI.ts          # Interactive interface
│   ├── utils/             # Utility functions
│   │   └── DebugLogger.ts         # Debug logging
│   ├── types/             # TypeScript definitions
│   │   └── index.ts               # Type definitions
│   └── index.ts           # Main CLI application
├── research_data/         # Generated research data
├── cli/result/           # HTML/JSON/MD outputs
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## 🎯 Intelligent Research Workflow

The CLI follows a sophisticated AI-driven research workflow:

### Phase 1: Initial Search & Link Extraction
```
|--> Search --> "Your Query"
      |--> [+] Found 15 search results [Ctrl+O to expand]
           ├── Wikipedia: Topic Overview
           ├── Academic Paper: Deep Analysis
           └── News Article: Recent Developments
      |--> Processing search result pages...
      |--> Extracted 24 links from search result pages
      └── Total 39 links queued for processing
```

### Phase 2: AI-Driven Deep Research
```
|--> Depth Level 1 (Processing 12 pages)
     ├── Fetching: example.com/article
     │    ├── Processing content (15,000 chars)
     │    ├── Relevance: 87.3% | Insights: 4 | Processed: ✓
     │    └── Found 8 links for depth 2 (3 priority, 5 standard)
     ├── 🤖 AI Decision: Continue to depth 2 (information gaps exist)
     │
|--> Depth Level 2 (Processing 8 pages)
     ├── Fetching: research.org/study
     │    ├── Processing content (12,400 chars)
     │    ├── Relevance: 92.1% | Insights: 6 | Processed: ✓
     │    └── Found 5 links for depth 3 (2 priority, 3 standard)
     ├── 🤖 AI Completeness Assessment: 73% complete
     ├── 🤖 AI Decision: Continue to depth 3 (high-quality links available)
     │
|--> Depth Level 3 (Processing 5 pages)
     ├── 🤖 AI Completeness Assessment: 89% complete
     ├── 🤖 AI Decision: Stopping research at depth 3
     │    ├── Reason: Comprehensive coverage achieved
     │    ├── Confidence: 91.2%
     │    └── Information Quality: excellent
```

### Phase 3: AI Synthesis with Custom Instructions
```
|--> Synthesizing research findings...
     ├── Processing 25 high-quality sources for final analysis
     ├── Loading custom research instructions... ✓
     ├── Extracting key insights following custom format
     ├── Cross-referencing information
     ├── Generating specialized response (OpenAPI specification format)
     └── Analysis complete (confidence: 91.2%) | Custom instructions: ✓
```

### Key Intelligence Features:
- **🧠 Smart Link Discovery**: Extracts links from pages, not just search results
- **🎯 AI Stopping Criteria**: Decides when to stop based on information completeness
- **📊 Adaptive Processing**: Adjusts strategy based on content quality and depth
- **📋 Custom Instructions**: Follows your specific output format requirements
- **⚡ Priority Systems**: Processes highest-value content first

## 🔍 Example Research Sessions

### Payment Gateway Integration Research
```
Query: "Stripe payment gateway OpenAPI specification"
Custom Instructions: OpenAPI spec format for connector integration
AI Decisions: Stopped at depth 4 (comprehensive coverage achieved)
Pages Processed: 28 pages
Links Extracted: 67 links from search result pages
Results: Complete OpenAPI specification with endpoints, auth, and data models
```

### Academic Research
```
Query: "Impact of AI on software development productivity"
AI Decisions: Continued to depth 5 (information gaps detected)
Pages Processed: 35 pages
Links Extracted: 94 links from research papers and articles
Results: Comprehensive analysis with academic citations and statistical data
```

### Technical Investigation
```
Query: "GraphQL vs REST API performance comparison"
AI Decisions: Stopped at depth 3 (sufficient benchmarks found)
Pages Processed: 42 pages
Links Extracted: 156 links from technical documentation and blogs
Results: Technical comparison with performance benchmarks and use cases
```

### Market Research
```
Query: "Electric vehicle market trends 2024"
AI Decisions: Continued to depth 4 (market data completeness: 76%)
Pages Processed: 31 pages
Links Extracted: 78 links from market reports and news sources
Results: Market analysis with statistical data, forecasts, and competitive landscape
```

## 🔧 SearxNG JSON API Configuration

The CLI now includes enhanced SearxNG configuration for reliable JSON API responses across different environments.

### What's Included
- ✅ **Optimized `searxng-config.yml`** with JSON API focus
- ✅ **Cross-platform Docker setup** (Windows/Mac/Linux)
- ✅ **Dynamic port allocation** (32768-32800 range)
- ✅ **API response validation** with detailed error reporting
- ✅ **Comprehensive testing tools** for connectivity diagnosis

### Key Configuration Features

**JSON API Optimization:**
```yaml
search:
  formats:
    - html
    - json  # ✅ Properly configured for API use
    - rss

engines:
  # ✅ Reliable engines for API responses
  - name: google
  - name: bing
  - name: duckduckgo
  - name: startpage

disabled_engines:
  # ✅ Disabled problematic engines
  - wikidata
  - mediawiki
```

**Docker Improvements:**
- ✅ **Windows path conversion** for Docker volume mounting
- ✅ **Port conflict resolution** with automatic fallback
- ✅ **Cross-platform shell execution** (cmd.exe/bash)
- ✅ **Enhanced error handling** with Windows-specific fallbacks

### Troubleshooting SearxNG Issues

**Test SearxNG connectivity:**
```bash
npm start test-search -q "test query"
```

**Common SearxNG issues and fixes:**

1. **"SearxNG returned HTML instead of JSON"**
   ```bash
   # Restart SearxNG with correct config
   docker stop searxng && docker rm searxng
   npm run setup
   ```

2. **"Port already in use"**
   - Setup automatically finds available ports (32768-32800)
   - Check current port: `npm start config`
   - Restart setup if needed: `npm run setup`

3. **"Docker volume mounting failed"**
   ```bash
   # On Windows, ensure Docker Desktop is running
   # On Mac, ensure OrbStack/Docker Desktop is running
   # Check Docker status
   docker info
   ```

4. **"Container starts but API doesn't work"**
   ```bash
   # Check container logs
   docker logs searxng

   # Test API directly
   curl "http://localhost:$(grep SEARXNG_BASE_URL .env | cut -d: -f3)/search?q=test&format=json"
   ```

## 🐛 Troubleshooting

### Common Issues

**"Configuration errors" on startup**
- Check your `.env` file exists and has AI API keys
- Ensure `CUSTOM_INSTRUCTIONS_FILE` points to existing file
- Verify AI provider configuration
- Run `npm start config` to see current settings

**"Custom instructions not being followed"**
- Ensure you're using `npm start research "query"` (not `npm run dev`)
- Verify `CUSTOM_INSTRUCTIONS_FILE` in `.env` points to correct file
- Check file permissions - must be readable
- Run `npm start config` to verify instructions are loaded

**"Docker not found" during setup**
- Install Docker Desktop or OrbStack
- Make sure Docker daemon is running
- Try `docker --version` to verify installation
- On Windows: Ensure Docker Desktop is configured for Linux containers

**"SearxNG not responding"**
- Run `npm start test-search` to diagnose API issues
- Check if container is running: `docker ps`
- Restart container: `docker restart searxng`
- Check logs: `docker logs searxng`
- Re-run setup: `npm run setup`

**"Search failed, using fallback"**
- This means SearxNG isn't returning valid JSON
- Run `npm start test-search` for detailed diagnosis
- Check SearxNG URL: `npm start config`
- Verify container status: `docker ps | grep searxng`

**"Failed to fetch page" errors**
- Check proxy configuration in `.env`
- Verify target sites are accessible from your network
- Increase timeout values: `TIMEOUT_PER_PAGE=60000`
- Check if sites block automated requests

**"AI service error"**
- Verify API key is valid and has credits
- Check model availability (some models have regional restrictions)
- Test connection: run research with simple query first
- Check AI provider status/documentation

### Debug Mode

Enable detailed logging:

```env
IS_DEBUG=true
```

Check the debug log file for detailed information:
```bash
tail -f ./search_query_time.log
```

## 🔒 Privacy & Ethics

### Responsible Usage
- Respect robots.txt files (enabled by default)
- Use reasonable delays between requests
- Don't overwhelm target servers
- Respect website terms of service

### Privacy Features
- Proxy support for IP rotation
- Stealth browsing techniques
- No personal data collection
- Local data storage only

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for JavaScript-enabled web scraping
- [Blessed](https://github.com/chjj/blessed) for terminal UI components
- [Inquirer.js](https://github.com/SBoudrias/Inquirer.js) for interactive prompts
- [Chalk](https://github.com/chalk/chalk) for terminal styling

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the debug logs
- Consult the configuration documentation

---

**Happy Researching! 🔍✨**
