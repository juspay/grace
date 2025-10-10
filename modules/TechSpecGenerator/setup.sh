#!/bin/bash

# TechSpecGenerator Setup Script
# This script automates the installation and configuration of the API Documentation Processor

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}TechSpecGenerator Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.8 or higher is required (found: $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"
echo ""

# Determine grace root directory (two levels up from this script)
GRACE_ROOT="$SCRIPT_DIR/../.."
GRACE_VENV="$GRACE_ROOT/venv"
GRACE_REGISTRY="$GRACE_ROOT/.grace_registry.json"

# Remove .grace_registry.json if it exists
# if [ -f "$GRACE_REGISTRY" ]; then
#     echo -e "${YELLOW}Removing existing .grace_registry.json...${NC}"
#     rm -f "$GRACE_REGISTRY"
#     echo -e "${GREEN}✓ .grace_registry.json removed${NC}"
#     echo ""
# fi

# Check if parent grace virtual environment exists
if [ ! -d "$GRACE_VENV" ]; then
    echo -e "${RED}Error: Grace virtual environment not found at $GRACE_VENV${NC}"
    echo -e "${YELLOW}Please run setup.sh from the grace root directory first:${NC}"
    echo -e "${YELLOW}  cd $GRACE_ROOT && ./setup.sh${NC}"
    exit 1
fi

# Activate grace virtual environment
echo -e "${YELLOW}Using grace virtual environment...${NC}"
source "$GRACE_VENV/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install package in development mode
echo -e "${YELLOW}Installing package in development mode...${NC}"
pip install -e ".[dev]"
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

# Create configuration file if it doesn't exist
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}Creating configuration file...${NC}"
    api-doc-processor --create-config
    echo -e "${GREEN}✓ Configuration file created${NC}"
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}IMPORTANT: Please configure your API keys${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "Edit config.json and add your API keys:"
    echo "1. Firecrawl API Key (from https://firecrawl.dev)"
    echo "2. LLM API Key (OpenAI, Anthropic, or Google)"
    echo ""
    echo "Example:"
    echo '{
  "firecrawl": {
    "api_key": "your-firecrawl-api-key"
  },
  "litellm": {
    "api_key": "your-llm-api-key",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}'
    echo ""
else
    echo -e "${GREEN}✓ Configuration file already exists${NC}"
    echo ""
fi

# Test setup
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing setup...${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

if [ -f "config.json" ]; then
    # Check if config has been updated from template
    if grep -q "your-actual-firecrawl-api-key\|your-actual-openai-api-key\|your-firecrawl-api-key\|your-llm-api-key" config.json 2>/dev/null; then
        echo -e "${YELLOW}⚠ Please update config.json with your actual API keys before testing${NC}"
    else
        echo -e "${YELLOW}Running connection test...${NC}"
        if api-doc-processor --test-only; then
            echo -e "${GREEN}✓ All tests passed!${NC}"
        else
            echo -e "${YELLOW}⚠ Tests failed. Please check your API keys in config.json${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your API keys (if not already done)"
echo "2. Make sure grace virtual environment is activated:"
echo -e "   ${YELLOW}source $GRACE_VENV/bin/activate${NC}"
echo "3. Run 'api-doc-processor' to start using the tool"
echo ""
echo "For more information, see:"
echo "- README.md for usage guide"
echo "- INSTALL.md for detailed installation instructions"
echo ""

echo "Create config.json with your API keys if you haven't already."
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}You can create a config file by running:${NC}"
    echo -e "${YELLOW}  api-doc-processor --create-config${NC}"
    api-doc-processor --create-config
    echo ""
fi

