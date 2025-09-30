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

### Installation & Setup

1. **Clone and install dependencies**:
```bash
cd cli
npm install
# or
yarn install
```

2. **Run automated setup** (sets up SearxNG with Docker):
```bash
npm run setup
```
This will:
- ✅ Check Docker/OrbStack installation
- ✅ Pull and start SearxNG search engine
- ✅ Test the installation
- ✅ Create `.env.example` template

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your AI API keys
```

4. **Build and run**:
```bash
npm run build
npm start
```

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

The CLI supports custom instructions that allow you to personalize the AI's research behavior and analysis style.

#### Setting Up Custom Instructions

1. **Create an instructions file** (e.g., `custom_instructions.txt`):
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

2. **Add to your .env file**:
```env
CUSTOM_INSTRUCTIONS_FILE=./custom_instructions.txt
```

3. **Verify configuration**:
```bash
npm start config
```

#### Features
- ✅ **Automatic integration** - Instructions are prepended to all AI prompts
- ✅ **File validation** - CLI validates file exists and is readable
- ✅ **Error handling** - Graceful fallback if file is missing
- ✅ **Real-time loading** - Instructions loaded at startup
- ✅ **Configuration display** - See loaded instructions in config command

For detailed examples and best practices, see [CUSTOM_INSTRUCTIONS.md](./CUSTOM_INSTRUCTIONS.md).

## 💻 Usage

### Interactive Mode (Default)

Simply run the CLI without arguments to start interactive mode:

```bash
npm start
```

This will:
1. Prompt you for a research query
2. Allow you to set custom instructions
3. Configure research parameters
4. Start the beautiful terminal UI
5. Show real-time progress and logs

### Command Line Options

```bash
# Run setup (install SearxNG)
npm run setup

# Start interactive research
npm start research

# Direct research mode
npm start direct "your research query"

# Show current configuration
npm start config

# View research history
npm start history

# Show statistics
npm start stats

# Clean up old data
npm start clean --days 30
```

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

## 🐛 Troubleshooting

### Common Issues

**"Configuration errors" on startup**
- Check your `.env` file
- Ensure all required AI API keys are set
- Verify AI provider configuration
- Run `npm run setup` if SearxNG not configured

**"Docker not found" during setup**
- Install Docker Desktop or OrbStack
- Make sure Docker daemon is running
- Try `docker --version` to verify installation

**"SearxNG not responding"**
- Run `npm run setup` to reinstall SearxNG
- Check if container is running: `docker ps`
- Restart container: `docker restart mass-searxng`
- Check logs: `docker logs mass-searxng`

**"Search failed, using fallback"**
- Check SearxNG instance is running at http://localhost:8080
- Verify SEARXNG_BASE_URL is correct in `.env`
- Ensure network connectivity

**"Failed to fetch page" errors**
- Check proxy configuration
- Verify target sites are accessible
- Increase timeout values if needed

**"AI service error"**
- Verify API key is valid
- Check model availability
- Ensure sufficient API credits

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
