# GRACE
**Global Rapid Agentic Connector Exchange**

A comprehensive toolkit for building and managing connector integrations through intelligent automation and code generation. GRACE provides specialized modules for research, specification generation, and automated code generation - all accessible through a unified CLI.

## 🚀 Quick Start

```bash
# Run setup and activate virtual environment
./setup.sh
source venv/bin/activate

# Verify installation
grace --version
grace list

# Setup modules as needed
grace setup-d  # DeepResearchCLI
grace setup-t  # TechSpecGenerator
```

## 📋 CLI Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `grace list` | - | List all commands with status |
| `grace info <command>` | - | Show command details |
| `grace research [query]` | `r`, `dr` | AI-driven web research |
| `grace techspec` | `ts` | Process API documentation |
| `grace setup-d` | - | Setup DeepResearchCLI |
| `grace setup-t` | - | Setup TechSpecGenerator |
| `grace reload` | - | Reload command registry |
| `grace --help` | - | Show help |

## 🎯 Modules

### 🔍 DeepResearchCLI
AI-driven web research tool with intelligent depth control, multi-stage content processing, and support for multiple AI providers (LiteLLM, Vertex AI). Exports to HTML, JSON, or Markdown.

```bash
grace setup-d
grace research "Stripe payment API integration"
```

### 📋 TechSpecGenerator
Automates API integration research using LangGraph workflows. Crawls API documentation, extracts content, generates technical specifications, and creates Express.js mock servers.

```bash
grace setup-t
grace techspec
```

### 🔌 CodeGenForHSConnector
Template-based code generation for Hyperswitch connectors with support for all payment flows and step-by-step implementation guidance.

```bash
# Use with AI assistant in Hyperswitch repository
integrate [ConnectorName] using .gracerules
```

### 🔗 CodeGenForUCSConnector
AI-assisted UCS connector development with support for resuming partial implementations, all payment flows, and UCS-specific gRPC patterns.

```bash
# Use with AI assistant in connector-service repository
# New connector
integrate [ConnectorName] using .graceucs

# Resume work
continue implementing [ConnectorName] connector in .graceucs

# Add flows
add [flow_names] flows to existing [ConnectorName] connector in .graceucs
```

## 📖 Workflow Examples

### Complete Connector Integration
```bash
# 1. Research
grace research
# → Saves comprehensive research report

# 2. Process documentation
grace techspec
# → Generates tech spec and mock server

# 3. Implement (with AI assistant)
integrate Klarna using .graceucs
# → Complete UCS connector
```

### Adding Payment Methods
```bash
grace r "worldpay Apple Pay flow"

# Use with AI assistant in UCS repository
add Apple Pay support to existing Stripe connector using .graceucs
```

## 🛠️ Prerequisites
- Python 3.8+
- API keys for AI services (OpenAI, Anthropic, Google, etc.)
- AI assistant with code execution (Claude, GPT-4, etc.)
- Hyperswitch/UCS repository (for code generation modules)

## 🔧 Custom Commands

Edit `commands.json` and reload:
```bash
grace reload
```

## 🎯 Tool Selection Guide

| Task | Tool |
|------|------|
| Research payment provider | `grace research` |
| Process API documentation | `grace techspec` |
| Build Hyperswitch connector | CodeGenForHSConnector |
| Build/extend UCS connector | CodeGenForUCSConnector |

## 🐛 Troubleshooting

**Command not found:**
```bash
source venv/bin/activate
# Or add to PATH: export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

**Module not installed:**
```bash
grace setup-d  # install deepresearch cli
grace setup-t  # install TechSpecGenerator cli
```

**Registry issues:**
```bash
grace reload # if Grace fails to use the commands properly
```