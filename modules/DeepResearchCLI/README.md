# 🔍 GRACE Deep Research CLI

A powerful Python-based command-line interface for conducting comprehensive, AI-driven web research with intelligent deep research capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-%3E%3D3.8-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-blue.svg)

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

### 🔧 Advanced Configuration
- **Environment-based configuration** with `.env` support
- **Multiple AI providers** (LiteLLM, Vertex AI, Anthropic)
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
- Python 3.8 or higher
- pip (Python package installer)
- Docker Desktop or OrbStack (for SearxNG search engine - optional, auto-configured)

### ⚡ Fast Setup (Automated - Recommended)

**One-line installation** (handles everything automatically):

```bash
cd /path/to/DeepResearchCLI
./setup.sh
```

This automated setup script will:
- ✅ Check Python and pip installation
- ✅ Install Python dependencies from requirements.txt
- ✅ Install the `deep-research` command globally
- ✅ Install Playwright browsers for web scraping
- ✅ **Detect Docker/OrbStack and setup SearxNG automatically**
- ✅ **Fallback to local SearxNG if Docker not available**
- ✅ Create and configure .env file with correct SearxNG URL
- ✅ Test the installation
- ✅ Provide next steps and usage instructions

**What it does with SearxNG:**
1. **Docker/OrbStack detected** → Automatically pulls and starts SearxNG container
2. **No Docker** → Offers to clone and install SearxNG locally (from GitHub)
3. **Docker not running** → Provides installation instructions and retries

### 📋 Manual Setup (Alternative)

If you prefer manual installation:

1. **Install the CLI package**:
```bash
cd /path/to/DeepResearchCLI
pip install -e .
```

2. **Install Playwright browsers**:
```bash
playwright install chromium
```

3. **Configure environment**:
```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env and add your AI API keys and SearxNG URL
```

4. **Start researching**:
```bash
# Start a research session
deep-research research "your research query"

# Show configuration
deep-research config

# View help
deep-research --help
```

### 📦 Installation Options

**Option 1: Automated Setup (Recommended)**
```bash
./setup.sh
# Handles everything including SearxNG
```

**Option 2: Global Installation**
```bash
pip install -e .
# Command available system-wide: deep-research
```

**Option 3: Add Python bin to PATH**
```bash
# For zsh (macOS default)
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For Windows (PowerShell)
# Add Python Scripts directory to PATH environment variable
```

**Option 4: Direct Script Execution**
```bash
# Run directly without installation
python run_cli.py research "your query"
```

### ✨ What You Get
- **Simple command-line interface** - Just type `deep-research` from anywhere
- **Automated SearxNG setup** - Docker or local installation handled automatically
- **Custom instruction support** - Research outputs in your specified format (OpenAPI, JSON, etc.)
- **Real web search** - Powered by SearxNG with Google, Bing, DuckDuckGo engines
- **Cross-platform compatibility** - Works on Windows, Mac, and Linux
- **Intelligent depth control** - AI decides when to stop researching for optimal results

## 📋 Configuration

### Environment Variables

The setup script creates a `.env` file automatically. Here's what it contains:

```env
# AI Configuration
AI_PROVIDER=litellm                           # Options: litellm, vertex, anthropic
LITELLM_API_KEY=your_api_key_here
LITELLM_BASE_URL=http://localhost:4000/v1
LITELLM_MODEL_ID=claude-sonnet-4-20250514

# Vertex AI Configuration (if AI_PROVIDER=vertex)
# VERTEX_AI_PROJECT_ID=your_project_id
# VERTEX_AI_LOCATION=us-central1

# Anthropic Configuration (if AI_PROVIDER=anthropic)
# ANTHROPIC_API_KEY=your_api_key_here

# Custom Instructions (optional but recommended)
CUSTOM_INSTRUCTIONS_FILE=./custom_instructions.txt

# Research Configuration
MAX_DEPTH=5                                   # Maximum crawl depth
MAX_PAGES_PER_DEPTH=10                       # Pages to process per depth level
MAX_TOTAL_PAGES=50                           # Total pages limit
CONCURRENT_PAGES=10                          # Concurrent page processing
LINK_RELEVANCE_THRESHOLD=0.6                 # Link relevance threshold (0-1)
TIMEOUT_PER_PAGE_MS=30000                    # Timeout per page in milliseconds
RESPECT_ROBOTS_TXT=false                     # Respect robots.txt

# Data Storage
RESEARCH_DATA_DIR=./data                     # Research data directory
HISTORY_FILE=./data/research_history.json   # History file location

# SearxNG Configuration (auto-configured by setup.sh)
SEARXNG_BASE_URL=http://localhost:32768     # SearxNG URL

# Proxy Configuration (optional)
# PROXY_LIST=http://proxy1:port,http://proxy2:port

# Debug Configuration
IS_DEBUG=true                                 # Enable debug logging
DEBUG_LOG_FILE=./logs/debug.log              # Debug log file
```

### AI Provider Setup

#### LiteLLM (Recommended)
```env
AI_PROVIDER=litellm
LITELLM_API_KEY=your_api_key_here
LITELLM_BASE_URL=http://localhost:4000/v1
LITELLM_MODEL_ID=claude-sonnet-4-20250514
```

#### Vertex AI (Google Cloud)
```env
AI_PROVIDER=vertex
VERTEX_AI_PROJECT_ID=your_project_id
VERTEX_AI_LOCATION=us-central1
```

#### Anthropic (Claude)
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
```

### 📝 Custom Instructions

Custom instructions allow you to personalize the AI's research behavior and output format.

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

**Example: OpenAPI Specification Instructions**
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
deep-research config
```

**Important Notes:**
- ✅ **No need to rerun setup** - Custom instructions are loaded dynamically at runtime
- ✅ **Changes take effect immediately** - Just edit the file and run your next research
- ✅ **Multiple instruction files** - Create different files and switch by changing `CUSTOM_INSTRUCTIONS_FILE` in .env
- ✅ **No restart required** - Each research session loads instructions fresh from the file

#### How to Use Custom Instructions

**✅ Correct way (follows custom instructions):**
```bash
deep-research research "stripe payment gateway integration"
```

**Features:**
- ✅ **Consistent application** - Instructions applied to all research phases
- ✅ **Full data access** - Custom instructions receive complete research data
- ✅ **Format detection** - AI detects and follows output format requirements
- ✅ **Error handling** - Graceful fallback if file is missing
- ✅ **Configuration display** - See loaded instructions in config command

#### Troubleshooting Custom Instructions

**Instructions not being followed:**
1. Check file exists: `ls -la custom_instructions.txt`
2. Verify configuration: `deep-research config`
3. Check file permissions: `chmod 644 custom_instructions.txt`
4. Ensure file path is correct in `.env`

## 💻 Usage

### 🎯 Command Reference

Once installed, you can use the `deep-research` command from anywhere:

#### Research Commands

```bash
# Start a research session with your query
deep-research research "stripe payment gateway integration"

# Research with custom instructions (loaded from .env)
deep-research research "GraphQL vs REST performance comparison"

# Interactive mode - prompts for query if not provided
deep-research research
```

#### Configuration & Status

```bash
# Show current configuration
deep-research config

# View research history (last 20 sessions)
deep-research history

# Show research statistics
deep-research stats
```

#### Testing & Diagnostics

```bash
# Test SearxNG connectivity and JSON API
deep-research test-search

# Test with custom query
deep-research test-search -q "payment gateways"

# Clean up old data (coming soon)
deep-research clean --days 30

# Show help and available commands
deep-research --help
```

### 🚨 Important Usage Notes

**For Custom Instructions (OpenAPI, specific formats):**
- Set `CUSTOM_INSTRUCTIONS_FILE` in your `.env` to point to your instructions file
- The CLI will automatically load and follow these instructions during research
- Verify instructions are loaded: `deep-research config`

**SearxNG Configuration:**
- Automatically configured by `./setup.sh`
- Configure `SEARXNG_BASE_URL` in `.env` if using external instance
- SearxNG must be running for real web search
- Test connectivity: `deep-research test-search`

**Managing SearxNG (Docker):**
```bash
# Check if running
docker ps | grep searxng

# Stop SearxNG
docker stop searxng

# Start SearxNG
docker start searxng

# View logs
docker logs searxng

# Remove container
docker rm -f searxng
```

**Managing SearxNG (Local):**
```bash
# Navigate to SearxNG directory
cd searxng-local

# Activate virtual environment
source venv/bin/activate

# Set settings path
export SEARXNG_SETTINGS_PATH=searxng/settings.yml

# Start SearxNG
python searxng/webapp.py
```

### 🔧 Alternative Execution Methods

If you haven't added the command to PATH, you can still run the CLI:

```bash
# Using the full path (replace with your Python version)
/Users/username/Library/Python/3.9/bin/deep-research research "query"

# Using Python directly
python run_cli.py research "query"

# Using Python module syntax (won't work due to package structure)
cd /path/to/DeepResearchCLI
python -c "from cli import main; main()" research "query"
```

## 📊 Output Formats

The CLI automatically generates research outputs in multiple formats:

### HTML Report
Beautiful, responsive HTML report with:
- Executive summary with statistics
- All sources with relevance scores
- Page content and extracted information
- Links and relationships
- Professional styling

### JSON Export
Complete structured data including:
- Session metadata (ID, query, timestamps)
- All page data with content
- Link analysis results
- AI scoring and insights
- Full research tree structure

### Markdown Report
Clean markdown format perfect for:
- Documentation
- Sharing findings
- Integration with other tools
- Version control

**Output Location:**
All research outputs are saved to the directory specified by `RESEARCH_DATA_DIR` in your `.env` file (default: `./data`).

## 🔧 Advanced Features

### Debug Mode

Enable debug mode for detailed logging:

```env
IS_DEBUG=true
DEBUG_LOG_FILE=./logs/debug.log
```

Debug logs include:
- Search query timing
- Page fetch performance
- AI call details with token usage
- Error tracking with stack traces
- Session summaries
- Link extraction details

View debug logs:
```bash
tail -f ./logs/debug.log
```

### Proxy Configuration

For enhanced privacy and bot prevention:

```env
PROXY_LIST=http://user:pass@proxy1:8080,socks5://proxy2:1080,http://proxy3:9090
```

The system will automatically rotate through proxies for different requests.

### Research Configuration Tuning

Adjust research behavior in `.env`:

```env
# Aggressive research (deep, comprehensive)
MAX_DEPTH=7
MAX_PAGES_PER_DEPTH=15
MAX_TOTAL_PAGES=100
CONCURRENT_PAGES=15

# Conservative research (fast, focused)
MAX_DEPTH=3
MAX_PAGES_PER_DEPTH=5
MAX_TOTAL_PAGES=20
CONCURRENT_PAGES=5

# Balanced (recommended)
MAX_DEPTH=5
MAX_PAGES_PER_DEPTH=10
MAX_TOTAL_PAGES=50
CONCURRENT_PAGES=10
```

## 📁 File Structure

```
DeepResearchCLI/
├── cli.py                      # Main CLI application
├── run_cli.py                  # Entry point script
├── setup.py                    # Package installation config
├── setup.sh                    # Automated setup script
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── .env.example                # Example configuration
├── custom_instructions.txt     # AI research instructions
├── searxng-config.yml          # SearxNG configuration
│
├── services/                   # Core research services
│   ├── __init__.py
│   ├── config_service.py       # Configuration management
│   ├── ai_service.py           # AI integration (LiteLLM/Vertex/Anthropic)
│   ├── search_service.py       # SearxNG search integration
│   ├── web_scraping_service.py # Playwright web scraping
│   ├── storage_service.py      # Data persistence
│   ├── result_output_service.py# Result formatting (HTML/JSON/MD)
│   └── direct_research_service.py # Main research orchestrator
│
├── research_types/             # Type definitions
│   └── __init__.py             # Dataclasses for research data
│
├── utils/                      # Utility functions
│   └── debug_logger.py         # Debug logging utility
│
├── ui/                         # UI components (future)
│
├── data/                       # Research data (auto-created)
│   ├── research_history.json   # Research session history
│   └── [session_id]/           # Individual research sessions
│       ├── research.html       # HTML report
│       ├── research.json       # JSON export
│       └── research.md         # Markdown report
│
├── logs/                       # Debug logs (auto-created)
│   └── debug.log               # Debug log file
│
└── searxng-local/              # Local SearxNG (if installed)
    └── ...                     # SearxNG files
```

## 🎯 Intelligent Research Workflow

The CLI follows a sophisticated AI-driven research workflow:

### Phase 1: Initial Search & Link Extraction
```
Search Query: "Your Research Query"
   ↓
SearxNG Search
   ├─ Google results
   ├─ Bing results
   ├─ DuckDuckGo results
   └─ 15-20 initial results
   ↓
Processing Search Results
   ├─ Fetch each search result page
   ├─ Extract content and links
   └─ Queue 30-50 links for deep research
```

### Phase 2: AI-Driven Deep Research
```
Depth Level 1 (Processing 10-15 pages)
   ├─ Fetch page content with Playwright
   ├─ AI analyzes relevance (score 0-1)
   ├─ Extract key information
   ├─ Discover additional links
   └─ AI Decision: Continue deeper?
      ↓
Depth Level 2 (Processing 8-12 pages)
   ├─ Process high-relevance links
   ├─ AI completeness check: 60%
   └─ AI Decision: Continue to depth 3
      ↓
Depth Level 3 (Processing 5-8 pages)
   ├─ AI completeness check: 85%
   └─ AI Decision: Stop (sufficient coverage)
```

### Phase 3: AI Synthesis with Custom Instructions
```
Final Synthesis
   ├─ Load custom instructions from file
   ├─ Process all collected data
   ├─ Generate response following format
   ├─ Calculate confidence score
   └─ Export results (HTML/JSON/MD)
```

### Key Intelligence Features:
- **🧠 Smart Link Discovery**: Extracts links from pages, not just search results
- **🎯 AI Stopping Criteria**: Decides when to stop based on information completeness
- **📊 Adaptive Processing**: Adjusts strategy based on content quality and depth
- **📋 Custom Instructions**: Follows your specific output format requirements
- **⚡ Priority Systems**: Processes highest-value content first

## 🔧 SearxNG Setup

The setup script automatically handles SearxNG installation:

### Automatic Setup (via ./setup.sh)

**Docker/OrbStack available:**
- ✅ Pulls `searxng/searxng:latest` image
- ✅ Finds available port (32768-32800)
- ✅ Creates configuration file
- ✅ Starts container with proper settings
- ✅ Tests JSON API connectivity
- ✅ Updates `.env` with correct URL

**Docker not available:**
- ✅ Offers to clone SearxNG from GitHub
- ✅ Sets up Python virtual environment
- ✅ Installs SearxNG dependencies
- ✅ Creates settings configuration
- ✅ Provides manual start instructions

### Manual SearxNG Setup

**Using Docker:**
```bash
# Pull image
docker pull searxng/searxng:latest

# Start container
docker run -d \
  --name searxng \
  -p 32768:8080 \
  -v "$(pwd)/searxng-config.yml:/etc/searxng/settings.yml:ro" \
  --restart unless-stopped \
  searxng/searxng:latest

# Update .env
echo "SEARXNG_BASE_URL=http://localhost:32768" >> .env
```

**Local installation:**
```bash
# Clone repository
git clone https://github.com/searxng/searxng.git searxng-local
cd searxng-local

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .

# Start
export SEARXNG_SETTINGS_PATH=searxng/settings.yml
python searxng/webapp.py
```

## 🐛 Troubleshooting

### Installation Issues

**"Command not found: deep-research"**
```bash
# Option 1: Add Python bin to PATH
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Option 2: Use full path
~/.local/bin/deep-research --help

# Option 3: Reinstall the package
pip install -e .
```

**"ModuleNotFoundError" or import errors**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Reinstall in editable mode
pip uninstall deep-research-cli
pip install -e .
```

**"No module named 'types'"**
- This has been fixed by renaming the `types` directory to `research_types`
- Ensure you have the latest version: `git pull` and reinstall

### Common Issues

**"Configuration errors" on startup**
- Check your `.env` file exists and has AI API keys
- Ensure `CUSTOM_INSTRUCTIONS_FILE` points to existing file
- Verify AI provider configuration
- Run `deep-research config` to see current settings

**"Custom instructions not being followed"**
- Verify `CUSTOM_INSTRUCTIONS_FILE` in `.env` points to correct file
- Check file exists: `ls -la custom_instructions.txt`
- Check file permissions: `chmod 644 custom_instructions.txt`
- Run `deep-research config` to verify instructions are loaded
- Remember: Changes take effect immediately, no restart needed!

**"SearxNG not responding"**
- Check if Docker container is running: `docker ps | grep searxng`
- Start if stopped: `docker start searxng`
- Test connectivity: `deep-research test-search`
- Check logs: `docker logs searxng`
- Verify URL: `deep-research config`

**"Search failed, using fallback"**
- SearxNG isn't returning valid JSON
- Run `deep-research test-search` for detailed diagnosis
- Restart SearxNG: `docker restart searxng`
- Check configuration: `deep-research config`

**"Failed to fetch page" errors**
- Check proxy configuration in `.env`
- Verify target sites are accessible
- Increase timeout: `TIMEOUT_PER_PAGE_MS=60000`
- Install Playwright browsers: `playwright install chromium`

**"AI service error"**
- Verify API key is valid and has credits
- Check model availability
- Test connection with simple query first
- Verify provider configuration in `.env`

### Debug Mode

Enable detailed logging:

```env
IS_DEBUG=true
DEBUG_LOG_FILE=./logs/debug.log
```

Check the debug log:
```bash
tail -f ./logs/debug.log
```

## 🔒 Privacy & Ethics

### Responsible Usage
- Respect robots.txt files (configurable via `RESPECT_ROBOTS_TXT`)
- Use reasonable delays between requests
- Don't overwhelm target servers
- Respect website terms of service
- Use proxies responsibly

### Privacy Features
- Proxy support for IP rotation
- Stealth browsing techniques with Playwright
- No personal data collection
- All data stored locally
- No telemetry or tracking

## 🤝 Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/juspay/grace.git
cd grace/modules/DeepResearchCLI

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt

# Run tests (when available)
pytest

# Check code style
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for JavaScript-enabled web scraping
- [SearxNG](https://github.com/searxng/searxng) for privacy-respecting search
- [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Anthropic](https://www.anthropic.com/) for Claude AI capabilities
- [Google Cloud](https://cloud.google.com/) for Vertex AI

## 📞 Support

For support and questions:
- 📝 [Create an issue on GitHub](https://github.com/juspay/grace/issues)
- 📖 Check the troubleshooting section above
- 🔍 Review the debug logs
- 📚 Consult the configuration documentation

## 🗺️ Roadmap

- [ ] Enhanced UI with real-time progress visualization
- [ ] Support for more AI providers
- [ ] Advanced filtering and result ranking
- [ ] Research templates library
- [ ] API server mode
- [ ] Web interface
- [ ] Collaborative research features

---

**Happy Researching! 🔍✨**

*Built with ❤️ by the GRACE team*
