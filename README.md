# GRACE

**Global Rapid Agentic Connector Exchange**

A comprehensive toolkit for building and managing connector integrations through intelligent automation and code generation. GRACE provides specialized modules for research, specification generation, and automated code generation - all accessible through a unified CLI.

# Quick Setup

**Prerequisites:** Ensure you're in the `grace/` directory for setup

Step 1: To install grace CLI

```bash
./setup.sh
# or inside grace folder use uv or pip after step 2 is done

pip install -e . && pip install -e ./modules/TechSpecGenerator

```

Step 2: To activate Grace CLI

```bash
source ./venv/bin/activate  # from grace folder
```

Step 3: To use GRACE CLI

```bash
grace --help

# to setup techspec
grace ts --create-config

# to generate techspec from links
grace ts
# or
grace techspec

#or
api-doc-processor
```

## USAGE

### Step 1: Activate Grace CLI if venv is not active

```bash
source ./grace/venv/bin/activate
# or
source ./venv/bin/activate  # from grace folder
```

### Step 2: use GRACE CLI

```bash
# to generate techspec from links
grace ts
# or
grace techspec
# or
api-doc-processor
```

### Step 3: Codegen

**Prerequisites:** Move the markdown file generated inside the **techspec-output** folder to grace/modules/Codegen/reference/**{Connector_name}**/

To use Codegen, You need to use the cline or claude code for generating code

**Claude code is recommended for this**

run the claude code
and prompt this

> Integrate the {ConnectorName} using .grace/modules/Codegen/.gracerules

### OR

use this command

```bash
 claude "Integrate {ConnectorName} using
grace/modules/Codegen/.gracerules" --dangerously-skip-permissions
```

**Note**: replace the ConnectorName to the actual connector name you are integrating.

## Available Modules

<!-- ### 1. **DeepResearchCLI** - AI-Powered Research Assistant

Deep research with AI analysis and web scraping capabilities. Conduct comprehensive research on payment connectors, APIs, and integration patterns.

**Commands:**

- `grace research` or `grace r` - Start research session
- `grace research "connector name"` - Research specific connector
- `grace research config` - Configure research settings
- `grace research history` - View research history
- `grace research clear` - Clear research history -->
<!--
**Examples:**

```bash
grace research "worldpay"
grace r "finix authorise flow"
grace research config
``` -->

### 1. **TechSpecGenerator** - API Documentation Processor

Generate technical specifications from API documentation. Converts API docs into structured specifications for connector implementation.

**Commands:**

- `grace techspec` or `grace ts` - Run TechSpec Generator
- `grace ts --create-config` - Create configuration file
- `grace ts --test-only` - Run in test mode
- `grace ts --verbose` - Verbose output

**Examples:**

```bash
grace techspec
grace ts --create-config
```

### 2. **Codegen** - Automated Connector Code Generation

Automated code generation for UCS connector implementations. Generates complete connector code from specifications.

**Features:**

- Template-based code generation
- Connector integration scaffolding
- Guided setup with interactive prompts
- Custom rules via `.gracerules`

**Location:** `modules/Codegen/`

### 3. **CodegenLegacy** - Legacy Connector Code Generation

Previous generation of the code generator with alternative implementation patterns.

**Features:**

- Legacy template support
- Alternative code patterns
- Custom CLI rules via `.clinerules`

**Location:** `modules/CodegenLegacy/`

## 📋 Command Reference

| Command          | Aliases | Description                       |
| ---------------- | ------- | --------------------------------- |
| `grace techspec` | `ts`    | Generate technical specifications |
| `grace list`     | -       | List all available commands       |

## 🔧 Configuration

GRACE uses a centralized configuration system via `commands.json`. Each module can be configured independently through its own setup scripts and configuration files.

## 📖 Module Documentation

For detailed documentation on each module:

<!-- - **DeepResearchCLI:** See `modules/DeepResearchCLI/README.md` -->

- **TechSpecGenerator:** See `modules/TechSpecGenerator/README.md`
- **Codegen:** See `modules/Codegen/README.md`
- **CodegenLegacy:** See `modules/CodegenLegacy/README.md`

## 🛠️ Development

**Project Structure:**

```
grace/
├── scripts/           # Core CLI scripts
├── modules/           # Individual feature modules
│   ├── TechSpecGenerator/
│   ├── Codegen/
│   └── CodegenLegacy/
├── commands.json      # Command registry
├── setup.sh          # Main installation script
└── README.md         # This file
```
