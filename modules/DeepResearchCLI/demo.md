# 🎬 MASS Deep Research CLI Demo

## Quick Demo Guide

### 1. Setup (One-time)

```bash
# Navigate to CLI directory
cd cli

# Run setup script
./setup.sh

# Edit configuration
nano .env  # Add your API keys
```

### 2. Start Your First Research

```bash
# Start interactive research
npm start

# You'll see:
? What would you like to research? › AI impact on software development
? Any specific instructions? › Focus on productivity metrics
? Maximum research depth: › 3
? Maximum pages per depth level: › 8
```

### 3. Watch the Magic Happen

The beautiful terminal UI will show:

```
🔍 MASS Deep Research CLI
================================
Status: ✅ Research in progress...

Progress: 45% ████████████████████░░░░

|--> Search --> "AI impact on software development"
      |--> [+] Found 12 results [Ctrl+O to expand]
           ├── Wikipedia: Artificial Intelligence in Software Engineering
           ├── Academic: AI-Assisted Programming Productivity Study
           └── Industry: GitHub Copilot Impact Report
      |--> Extracting Information
           ├── Page 1: Wikipedia AI in Software (Relevance: 89.2%)
           │    ├── Processing content (3,247 chars)
           │    ├── Found 6 insights using AI
           │    └── Extracted 4 relevant links for depth 2
           ├── Page 2: Academic Study (Relevance: 94.1%)
           │    ├── Processing content (5,892 chars)
           │    └── Found productivity metrics data
           └── Going deeper with promising links...
                ├── Depth 2: Developer productivity benchmarks
                └── Depth 3: Case studies and implementations

Options: [1] Skip | [2] Cancel | [3] History | [Ctrl+O] Expand | [Enter] Custom Input
```

### 4. Get Comprehensive Results

After completion, you'll get:

```
🎉 Research Complete!
Query: "AI impact on software development"
Status: completed
Pages Processed: 24
Max Depth: 3
Confidence: 87.4%

📁 Research results saved:
   HTML Report: /path/to/cli/result/session-id/research_2024-01-15.html
   JSON Data: /path/to/cli/result/session-id/research_2024-01-15.json
   Markdown: /path/to/cli/result/session-id/research_2024-01-15.md

💡 To view the HTML report:
   open "/path/to/cli/result/session-id/research_2024-01-15.html"
```

### 5. Explore Other Commands

```bash
# View research history
npm start history

# Show configuration
npm start config

# View statistics
npm start stats

# Clean old data
npm start clean --days 30
```

## Sample Research Topics

Try these interesting research queries:

### Technology
- "GraphQL vs REST API performance 2024"
- "Quantum computing practical applications"
- "WebAssembly adoption in enterprise"

### Business
- "Remote work productivity statistics"
- "Electric vehicle market growth projections"
- "Cryptocurrency regulation global trends"

### Science
- "CRISPR gene editing recent breakthroughs"
- "Climate change mitigation technologies"
- "Space exploration private companies"

### Academic
- "Machine learning bias detection methods"
- "Sustainable energy storage solutions"
- "Digital privacy legislation worldwide"

## Interactive Features Demo

### During Research:
1. **Press `1`** - Skip current operation
2. **Press `2`** - Cancel research
3. **Press `3`** - Show research history
4. **Press `Ctrl+O`** - Expand/collapse log entries
5. **Press `Enter`** - Provide custom guidance
6. **Press `Tab`** - Switch between areas

### Custom Guidance Examples:
When prompted, you can provide:
- "Focus more on academic sources"
- "Look for recent 2024 data"
- "Find comparison studies"
- "Search for case studies"

## Debug Mode Demo

Enable detailed logging:

```bash
# Edit .env
IS_DEBUG=true

# Run research and watch debug log
tail -f search_query_time.log
```

You'll see detailed logs like:
```
[2024-01-15T10:30:15.123Z] SEARCH_QUERY_START: "AI impact on software development"
[2024-01-15T10:30:16.456Z] SEARCH_QUERY_END: "AI impact on software development" | Results: 12 | Duration: 1333ms
[2024-01-15T10:30:17.789Z] PAGE_FETCH_START: https://en.wikipedia.org/wiki/AI_in_software
[2024-01-15T10:30:19.012Z] PAGE_FETCH_END: https://en.wikipedia.org/wiki/AI_in_software | Status: SUCCESS | Duration: 1223ms | Content: 3247 chars
[2024-01-15T10:30:20.345Z] AI_CALL_START: relevance_scoring | Input: 500 chars
[2024-01-15T10:30:21.678Z] AI_CALL_END: relevance_scoring | Status: SUCCESS | Duration: 1333ms | Tokens: 150 | Output: 0.89
```

## Example Output

### HTML Report Features:
- 📊 Interactive statistics dashboard
- 🎯 Executive summary with confidence scores
- 📚 Source analysis by depth level
- 🔍 Expandable content previews
- 📱 Responsive design for all devices

### JSON Export Includes:
- Complete session metadata
- All page content and analysis
- AI scoring results
- Link relationship mapping
- Performance metrics

### Markdown Format:
- Clean, readable format
- Perfect for documentation
- Easy to share and edit
- Compatible with all markdown tools

Ready to explore the depths of knowledge? Start your research journey! 🚀