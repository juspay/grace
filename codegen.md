# GRACE-UCS Codegen Orchestrator

This is the main entry point for AI-assisted UCS connector code generation. Read this file first to determine which workflow to follow.

---

## Delegation Policy

**CRITICAL -- This section applies to ALL workflows referenced from this file.**

You are a **workflow controller**, not a code implementer. This is a strict separation of concerns that applies regardless of which AI model you are running on (Claude, GPT, Gemini, Kimi, GLM, or any other).

### Rules

1. **NEVER implement code directly** -- Always delegate to subagents via the `Task` tool
2. **ONLY use the Task tool** -- Do not use Read, Edit, Write, Glob, Grep, Bash, or any other tool directly
3. **Subagents do the actual work** -- You coordinate, sequence, and validate results
4. **Model capability is irrelevant** -- Even if you could implement faster, you must delegate
5. **Wait for completion** -- Each subagent must finish before you proceed to the next step
6. **Validate before proceeding** -- Check subagent output before moving to the next phase

### Allowed Tools (Controller Only)

| Tool | Usage |
|------|-------|
| `Task` | Delegate work to subagents (results returned inline) |
| `TaskOutput` | Retrieve results from background subagents (if supported by your platform -- otherwise Task returns results directly) |

### Forbidden Tools (Use via Subagent Only)

Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, and all other tools. The subagent uses these -- you do not.

### Why This Design

- Ensures consistent workflow execution across all AI models
- Maintains clear separation of concerns (controller vs. implementer)
- Makes debugging and auditing easier
- Allows the workflow to scale with more capable models

---

## Prerequisites

### Playwright MCP Server

All scraping workflows require a **Playwright MCP server** to be configured in your coding tool. This replaces the old Firecrawl API dependency -- no API keys needed.

**Claude Desktop** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**OpenCode** (`.opencode/config.json`):
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

### Target Codebase

You must have access to the HyperSwitch/UCS codebase where the connector will be implemented:
```
backend/connector-integration/src/connectors/
```

---

## Workflow Selection

Use the decision tree below to determine which workflow to follow.

```
What do you need to do?
|
|-- Generate a tech spec from API documentation?
|   -> Follow techspec.md
|   Input: API documentation URLs or pre-scraped markdown files
|   Output: references/{connector_name}/technical_specification.md
|
|-- Scrape API documentation URLs to markdown?
|   -> Follow link_fetcher.md
|   Input: One or more URLs
|   Output: Markdown files in references/{connector_name}/
|
|-- Build a new connector from scratch?
|   -> Follow integrate_connector.md
|   Prerequisite: Tech spec at references/{connector_name}/technical_specification.md
|   Output: Complete connector with all core flows
|
|-- Add a flow to an existing connector?
|   -> Follow add_flow.md
|   Input: Flow name(s) and connector name
|   Output: Requested flow(s) added to existing connector
|
|-- Add a payment method to an existing connector?
|   -> Follow add_pm.md
|   Input: Payment method(s) and connector name
|   Output: Requested payment method(s) added to existing connector
|
|-- Validate an implementation?
|   -> Follow connector_checklist.md
|   Input: Connector name
|   Output: Pass/fail validation report
```

> **Tip**: If you receive a generic prompt like "Integrate X", see [Auto-Detect Pipeline](#auto-detect-pipeline) below to determine the correct starting point automatically.

### Typical End-to-End Flow

For a brand new connector integration, the typical sequence is:

1. **Scrape** -- Use `link_fetcher.md` to scrape the connector's API documentation
2. **Generate Tech Spec** -- Use `techspec.md` to create a structured technical specification
3. **Implement** -- Use `integrate_connector.md` to generate the full connector code
4. **Validate** -- Use `connector_checklist.md` to verify completeness

### Command Examples

```
# Generate a tech spec from documentation URLs
Follow techspec.md to create a tech spec for Stripe using these URLs:
- https://docs.stripe.com/api/charges
- https://docs.stripe.com/api/refunds

# Build a new connector
Follow integrate_connector.md to integrate Finix

# Add a specific flow
Follow add_flow.md to add Refund flow to Stripe

# Add a payment method
Follow add_pm.md to add Wallet:ApplePay,GooglePay to Stripe
```

### Auto-Detect Pipeline

When you receive a generic prompt like "Integrate {connector}" without explicit workflow instructions, use this decision tree to auto-detect the correct starting point:

```
Is there a tech spec at references/{connector}/technical_specification.md?
├── YES → Skip to integrate_connector.md (Phase 3 onward)
├── NO
│   Are there scraped docs in references/{connector}/?
│   ├── YES → Skip to techspec.md to generate tech spec, then integrate
│   └── NO
│       Were URLs provided in the prompt?
│       ├── YES → Start with link_fetcher.md, then techspec.md, then integrate
│       └── NO → Ask the user for API documentation URLs
```

### Prompt Templates

Use these exact prompts to trigger specific workflows:

| Scenario | Prompt |
|----------|--------|
| Full pipeline with URLs | `Read grace/codegen.md. Integrate {name} using: {url1}, {url2}` |
| Full pipeline auto-detect | `Read grace/codegen.md. Integrate {name}.` |
| Tech spec is ready | `Read grace/codegen.md. Integrate {name}. Tech spec is ready.` |
| Add flow(s) to existing | `Read grace/codegen.md. Add {Flow1},{Flow2} to {name}.` |
| Add payment method | `Read grace/codegen.md. Add {PM}:{variants} to {name}.` |

### Script Usage

The `add_connector.sh` script scaffolds a new connector:

| Mode | Command | What it does |
|------|---------|--------------|
| Full scaffold | `./grace/add_connector.sh {name} {base_url}` | Scaffolds connector skeleton with all 6 core flows and registers ConnectorSpecificConfig (does not implement flow logic) |

### Pipeline Diagram

```
Full Integration (integrate_connector.md):

  ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌────────────┐   ┌────────────────┐   ┌───────────┐
  │  Scrape  │──>│ TechSpec │──>│  Scaffold   │──>│ Implement  │──>│ Quality Review │──>│ Validate  │
  │  (MCP)   │   │  (AI)    │   │  (script)   │   │   (AI)     │   │    (AI)        │   │  (cargo)  │
  └──────────┘   └──────────┘   └─────────────┘   └────────────┘   └────────────────┘   └───────────┘

Add Flow (add_flow.md):

  ┌──────────┐   ┌─────────────┐   ┌────────────┐   ┌────────────────┐   ┌───────────┐
  │ TechSpec │──>│  Scaffold   │──>│ Implement  │──>│ Quality Review │──>│ Validate  │
  │  (read)  │   │  (manual)   │   │   (AI)     │   │    (AI)        │   │  (cargo)  │
  └──────────┘   └─────────────┘   └────────────┘   └────────────────┘   └───────────┘
```

---

### Security Requirements

All generated connectors MUST adhere to the following security baseline:

- **Webhook signature verification** — every connector that handles webhooks must verify the HMAC/signature before processing the payload (see `SEC-003` in `guides/feedback.md`).
- **No secrets in code** — API keys, merchant secrets, and other credentials must come from configuration / environment only.
- **TLS enforcement** — all outbound HTTP calls must use HTTPS; plain HTTP endpoints are not permitted.
- Refer to `guides/feedback.md` Section 8 (Security Guidelines) for the full checklist.

---

## File Map

| File | Purpose |
|------|---------|
| `codegen.md` | This file -- main orchestrator and delegation policy |
| `integrate_connector.md` | Full connector integration workflow (all core flows) |
| `add_flow.md` | Add specific flow(s) to an existing connector |
| `add_pm.md` | Add specific payment method(s) to an existing connector |
| `techspec.md` | Generate a technical specification from API documentation |
| `link_fetcher.md` | Scrape API documentation URLs using Playwright MCP |
| `field_analysis.md` | API field dependency analysis across flows |
| `connector_checklist.md` | Post-implementation validation checklist |
| `add_connector.sh` | Shell script to scaffold a new connector (full scaffold with all core flows) |

### Guides and References

| Directory | Contents |
|-----------|----------|
| `guides/patterns/` | Flow-specific implementation patterns (authorize, capture, refund, etc.) |
| `guides/patterns/authorize/` | Payment-method-specific patterns (card, wallet, bank_transfer, etc.) |
| `guides/types/` | UCS type system documentation |
| `guides/learnings/` | Lessons from previous integrations |
| `guides/quality/` | Quality review templates and processes |
| `guides/reference/` | Reference connector implementations <!-- TODO: populate with at least one reference connector --> |
| `connector_integration/template/` | Planner steps template |
| `template-generation/` | Rust code templates (connector.rs, transformers.rs, test.rs) |
| `references/` | Connector-specific tech specs and scraped documentation |
