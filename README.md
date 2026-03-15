# Grace

AI-assisted UCS connector code generation using pure markdown rulesets.

## Overview

Grace is a collection of structured markdown rules and guides that AI coding agents (Claude, OpenCode, Cursor) follow to generate, extend, and validate UCS payment connector implementations.

**No Python. No API keys. No dependencies.** Just markdown instructions that AI agents consume directly.

## Getting Started

1. Start with [codegen.md](codegen.md) -- the main orchestrator that routes you to the right workflow
2. Ensure your coding tool has the **Playwright MCP server** configured (see [codegen.md#prerequisites](codegen.md#playwright-mcp-server))

## Workflows

| File | Purpose |
|------|---------|
| [codegen.md](codegen.md) | Main orchestrator -- start here |
| [techspec.md](techspec.md) | Generate a tech spec from API documentation |
| [link_fetcher.md](link_fetcher.md) | Scrape API docs using Playwright MCP |
| [integrate_connector.md](integrate_connector.md) | Build a new connector from scratch |
| [add_flow.md](add_flow.md) | Add a flow to an existing connector |
| [add_pm.md](add_pm.md) | Add a payment method to an existing connector |
| [connector_checklist.md](connector_checklist.md) | Post-implementation validation |
| [field_analysis.md](field_analysis.md) | API field dependency analysis |

## Quick Example

```
# Tell your AI coding agent:
Follow grace/codegen.md to integrate Stripe
```

The agent will:
1. Read `codegen.md` to understand the delegation policy and workflow
2. Follow `integrate_connector.md` for the full implementation sequence
3. Delegate each phase to subagents for actual code generation
4. Validate using `connector_checklist.md`

## Directory Structure

```
grace/
├── codegen.md                  # Main orchestrator
├── integrate_connector.md      # Full connector integration
├── add_flow.md                 # Add flow workflow
├── add_pm.md                   # Add payment method workflow
├── techspec.md                 # Tech spec generation
├── link_fetcher.md             # Playwright MCP scraping
├── field_analysis.md           # Field dependency analysis
├── connector_checklist.md      # Validation checklist
├── add_connector.sh            # Foundation scaffold script
├── guides/                     # Implementation guides & patterns
├── connector_integration/      # Templates
├── template-generation/        # Rust code templates
└── references/                 # Connector tech specs (gitignored)
```
