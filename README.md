# GRACE
**Global Rapid Agentic Connector Exchange**

A comprehensive toolkit for building and managing connector integrations through intelligent automation and code generation. GRACE provides specialized modules for research, specification generation, and automated code generation - all accessible through a unified CLI.

## Quick Start

1. **Install GRACE CLI:**
```bash
./setup.sh # it will install all the cli
# source to the env file it created or activate using 
source grace/venv/bin/activate # from the connector-service repo
source venv/bin/active # from grace repo
```

2. **Verify Installation:**
```bash
grace list
```

3. **View Available Commands:**
```bash
grace --help
```


## Available Modules

### 1. **DeepResearchCLI** - AI-Powered Research Assistant
Deep research with AI analysis and web scraping capabilities. Conduct comprehensive research on payment connectors, APIs, and integration patterns.

**Commands:**
- `grace research` or `grace r` - Start research session
- `grace research "connector name"` - Research specific connector
- `grace research config` - Configure research settings
- `grace research history` - View research history
- `grace research clear` - Clear research history


**Examples:**
```bash
grace research "worldpay"
grace r "finix authorise flow"
grace research config
```

### 2. **TechSpecGenerator** - API Documentation Processor
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

### 3. **Codegen** - Automated Connector Code Generation
Automated code generation for UCS connector implementations. Generates complete connector code from specifications.

**Features:**
- Template-based code generation
- Connector integration scaffolding
- Guided setup with interactive prompts
- Custom rules via `.gracerules`

**Location:** `modules/Codegen/`

### 4. **CodegenLegacy** - Legacy Connector Code Generation
Previous generation of the code generator with alternative implementation patterns.

**Features:**
- Legacy template support
- Alternative code patterns
- Custom CLI rules via `.clinerules`

**Location:** `modules/CodegenLegacy/`


## 📋 Command Reference

| Command | Aliases | Description |
|---------|---------|-------------|
| `grace research` | `r`, `deepresearch`, `dr` | Deep research with AI analysis |
| `grace techspec` | `ts` | Generate technical specifications |
| `grace list` | - | List all available commands |

## 🔧 Configuration

GRACE uses a centralized configuration system via `commands.json`. Each module can be configured independently through its own setup scripts and configuration files.

## 📖 Module Documentation

For detailed documentation on each module:
- **DeepResearchCLI:** See `modules/DeepResearchCLI/README.md`
- **TechSpecGenerator:** See `modules/TechSpecGenerator/README.md`
- **Codegen:** See `modules/Codegen/README.md`
- **CodegenLegacy:** See `modules/CodegenLegacy/README.md`

## 🛠️ Development

**Project Structure:**
```
grace/
├── scripts/           # Core CLI scripts
├── modules/           # Individual feature modules
│   ├── DeepResearchCLI/
│   ├── TechSpecGenerator/
│   ├── Codegen/
│   └── CodegenLegacy/
├── commands.json      # Command registry
├── setup.sh          # Main installation script
└── README.md         # This file
```

