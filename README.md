# GRACE
**Global Rapid Agentic Connector Exchange**

GRACE is a comprehensive toolkit for building and managing connector integrations through intelligent automation and code generation.

## Overview

GRACE provides a modular architecture with specialized tools for different aspects of connector development, from research and specification generation to automated code generation and testing.

## Modules

The `modules/` directory contains four specialized tools for connector development:

### 🔍 DeepResearchCLI
A powerful command-line interface for conducting comprehensive, AI-driven web research with beautiful terminal UI and intelligent deep research capabilities.

**Key Features:**
- AI-driven depth control with smart stopping criteria
- Multi-stage content processing and summarization
- Interactive terminal interface with real-time progress visualization
- Multiple AI providers support (LiteLLM, Vertex AI)
- Stealth browsing with proxy support and bot prevention
- Multiple export formats (HTML, JSON, Markdown)
- Configurable research parameters and custom instructions

### 📋 TechSpecGenerator
A powerful TypeScript CLI tool that automates API integration research and planning using real LangGraph workflows. This module crawls API documentation, extracts content, generates technical specifications using AI, and creates mock servers with an interactive command-line interface.

**Key Features:**
- Real LangGraph workflow management with @langchain/langgraph
- Interactive CLI for API documentation processing
- Web crawling and content extraction to markdown
- AI-powered technical specification generation
- Express.js mock server generation
- Full TypeScript support with type safety

### 🔌 CodeGenForHSConnector
Code generation tools specifically designed for Hyperswitch connector development. Provides a structured, step-by-step process to ensure connectors are added accurately and efficiently to the Hyperswitch ecosystem.

**Key Features:**
- Comprehensive integration guide with reusable framework
- Support for all payment flows (authorize, capture, refund, sync, etc.)
- Template-based connector generation
- Integration planning and technical specification templates
- Step-by-step implementation guidance

### 🔗 CodeGenForUCSConnector
A specialized AI-assisted system for UCS (Universal Connector Service) connector development that supports complete connector lifecycle management - from initial implementation to continuation of partially completed work.

**Key Features:**
- Resume partial implementations where developers left off
- Complete flow coverage (authorize, capture, void, refund, sync, webhooks, etc.)
- All payment method support (cards, wallets, bank transfers, BNPL, etc.)
- UCS-specific patterns tailored for gRPC-based stateless architecture
- Flow-specific pattern files with real-world examples
- Template generation for consistent implementations

## 🚀 Usage Guide

GRACE provides different tools for different stages of connector development. Choose the appropriate workflow based on your needs:

### 🔍 For Research & Discovery
**Use DeepResearchCLI when you need to:**
- Research payment provider APIs and documentation
- Gather comprehensive information about payment flows
- Analyze competitor implementations
- Create detailed research reports for planning

```bash
cd modules/DeepResearchCLI
npm install
npm run setup    # Sets up SearxNG search engine
npm start       # Interactive research mode
```

**Example Usage:**
```bash
# Research a payment provider
npm start research
# Enter query: "Stripe payment API integration guide"
# AI will conduct deep research and generate comprehensive reports
```

### 📋 For API Documentation Processing
**Use TechSpecGenerator when you need to:**
- Process existing API documentation
- Generate technical specifications from docs
- Create mock servers for testing
- Convert documentation to structured formats

```bash
cd modules/TechSpecGenerator
npm install
npm run build
api-doc-processor --create-config  # Create config file
api-doc-processor                  # Interactive workflow
```

**Example Usage:**
```bash
# Process PayPal API documentation
api-doc-processor
# Enter URLs: https://developer.paypal.com/docs/api/
# AI will crawl, extract, and generate tech specs
```

### 🔌 For Hyperswitch Connector Development
**Use CodeGenForHSConnector when you need to:**
- Integrate new payment connectors into Hyperswitch
- Follow Hyperswitch-specific patterns and flows
- Generate connector code for the main Hyperswitch repository

```bash
# In your Hyperswitch repository
git clone https://github.com/juspay/grace.git
# Use with AI assistant:
integrate [ConnectorName] using .gracerules
```

**Example Usage:**
```bash
# AI command for new connector
integrate Razorpay using .gracerules
# AI will create tech spec, implementation plan, and generate code
```

### 🔗 For UCS Connector Development
**Use CodeGenForUCSConnector when you need to:**
- Develop connectors for UCS (Universal Connector Service)
- Resume partial implementations
- Add specific payment flows to existing connectors
- Work with gRPC-based stateless architecture

```bash
# For new UCS connector
integrate [ConnectorName] using grace-ucs/.gracerules

# For resuming work
continue implementing [ConnectorName] connector in UCS - I have [existing_flows] and need [missing_flows]

# For adding specific flows
add [flow_names] flows to existing [ConnectorName] connector in UCS
```

**Example Usage:**
```bash
# Start new UCS connector
integrate Adyen using grace-ucs/.gracerules

# Resume partial work
continue implementing Stripe connector in UCS - I have authorization and need capture, refund flows

# Add payment methods
add wallet payments to PayPal connector in UCS
```

## 📖 Detailed Workflow Examples

### Complete Connector Integration Workflow

#### 1. Research Phase (DeepResearchCLI)
```bash
cd modules/DeepResearchCLI
npm start
# Query: "Klarna payments API integration guide"
# Result: Comprehensive research report with API details
```

#### 2. Documentation Processing (TechSpecGenerator)
```bash
cd modules/TechSpecGenerator
api-doc-processor
# Input: Klarna developer documentation URLs
# Result: Structured tech spec and mock server
```

#### 3. Implementation (CodeGenForUCSConnector)
```bash
# Place research results in grace-ucs/references/klarna/
integrate Klarna using grace-ucs/.gracerules
# Result: Complete UCS connector implementation
```

### Troubleshooting Existing Connector

#### 1. Debug with UCS Tools
```bash
fix Stripe connector issues in UCS - getting timeout errors on authorization flow
# AI will analyze code and provide fixes
```

#### 2. Research Solutions (DeepResearchCLI)
```bash
cd modules/DeepResearchCLI
npm start
# Query: "Stripe API timeout handling best practices"
# Result: Research on timeout handling strategies
```

### Adding New Payment Methods

#### 1. Research Payment Method (DeepResearchCLI)
```bash
# Research specific payment method requirements
npm start
# Query: "Apple Pay integration requirements and flows"
```

#### 2. Implement in UCS (CodeGenForUCSConnector)
```bash
add Apple Pay support to existing Stripe connector in UCS
# AI will add wallet payment method support
```

## 🎯 Choosing the Right Tool

| Task | Recommended Tool | When to Use |
|------|------------------|-------------|
| Initial research on new payment provider | DeepResearchCLI | Need comprehensive information gathering |
| Processing existing API documentation | TechSpecGenerator | Have documentation URLs to analyze |
| Building new Hyperswitch connector | CodeGenForHSConnector | Working with main Hyperswitch repository |
| Building/extending UCS connector | CodeGenForUCSConnector | Working with UCS connector-service |
| Debugging connector issues | CodeGenForUCSConnector | Need to fix or enhance existing UCS connectors |
| Adding payment methods | CodeGenForUCSConnector | Extending existing connector capabilities |

## 🛠️ Prerequisites

### General Requirements
- Node.js 18.0.0 or higher
- npm or yarn
- AI assistant with code execution capabilities (Claude, GPT-4, etc.)

### Module-Specific Requirements
- **DeepResearchCLI**: Docker Desktop or OrbStack (for SearxNG)
- **TechSpecGenerator**: TypeScript 5+, API keys for LLM services
- **CodeGenForHSConnector**: Hyperswitch repository cloned
- **CodeGenForUCSConnector**: UCS connector-service repository

## Getting Started

1. Clone the repository
2. Choose the appropriate module based on your task (see table above)
3. Navigate to the module directory in `modules/`
4. Follow the module-specific setup instructions
5. Use the provided commands and examples above

Each module contains its own README.md with detailed installation and usage instructions.

## Project Structure

```
grace/
├── modules/                    # Core modules and tools
│   ├── DeepResearchCLI/        # AI-driven web research tool
│   ├── TechSpecGenerator/      # LangGraph-based API doc processor
│   ├── CodeGenForHSConnector/  # Hyperswitch connector tools
│   └── CodeGenForUCSConnector/ # UCS connector tools
├── .git/                      # Git repository metadata
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## Module Details

### DeepResearchCLI Structure
- Full TypeScript CLI with services, UI, and utilities
- Research data storage and history management
- Distributed build artifacts and source code

### TechSpecGenerator Structure
- LangGraph workflow implementation
- Node-based processing architecture
- Configuration management and TypeScript compilation

### CodeGenForHSConnector Structure
- Connector integration templates and guides
- Error handling patterns and type definitions
- Integration examples and learnings

### CodeGenForUCSConnector Structure
- UCS-specific implementation patterns
- Flow-specific guides (authorize, capture, etc.)
- Template generation and learning documentation

## Contributing

Please refer to the individual module documentation for specific contribution guidelines and development setup instructions.