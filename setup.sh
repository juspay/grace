#!/bin/bash
# Grace CLI - Global Setup Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() { echo -e "${CYAN}==>${NC} $1"; }
print_success() { echo -e "${GREEN}✅${NC} $1"; }
print_error() { echo -e "${RED}❌${NC} $1"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}    Grace CLI - Setup Script${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check Python
print_status "Checking Python installation..."
if ! command_exists python3; then
    print_error "Python 3 is required. Please install Python 3.8 or higher."
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Check for uv package manager
echo ""
print_status "Checking for uv package manager..."
if ! command_exists uv; then
    print_error "uv package manager is not installed."
    echo ""
    echo "uv is a fast Python package installer and resolver."
    echo "Please install it using one of the following methods:"
    echo ""
    echo "On macOS/Linux:"
    echo -e "  ${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    echo ""
    echo "On Windows:"
    echo -e "  ${CYAN}powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"${NC}"
    echo ""
    echo "Using pip:"
    echo -e "  ${CYAN}pip install uv${NC}"
    echo ""
    echo "For more information, visit: https://docs.astral.sh/uv/getting-started/installation/"
    echo ""
    exit 1
fi
print_success "uv package manager found"

# Remove .grace_registry.json if it exists
if [ -f ".grace_registry.json" ]; then
    print_status "Removing existing .grace_registry.json..."
    rm -f ".grace_registry.json"
    print_success ".grace_registry.json removed"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        print_status "Removing existing virtual environment..."
        rm -rf venv
        print_success "Virtual environment removed"
    fi
fi

# Create virtual environment using uv if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    print_status "Creating virtual environment with uv..."
    uv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
echo ""
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install grace CLI using uv
echo ""
print_status "Installing grace CLI with uv..."
uv pip install -e . > /dev/null 2>&1
print_success "Grace CLI installed successfully"

# Install dependencies
echo ""
print_status "Installing dependencies..."
print_status "Installing DeepResearchCLI..."
./modules/DeepResearchCLI/setup.sh
print_status "Installing TechSpecGenerator..."
./modules/TechSpecGenerator/setup.sh


# Initialize registry
echo ""
print_status "Initializing command registry..."
python3 scripts/register_commands.py
print_success "Command registry initialized"

# Test installation
echo ""
print_status "Testing installation..."
if venv/bin/grace --version > /dev/null 2>&1; then
    print_success "Installation test passed!"
else
    print_error "Installation test failed"
fi

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}✅ Grace CLI Setup Complete!${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo "Next Steps:"
echo ""
echo "1. Activate the virtual environment:"
echo -e "   ${CYAN}source venv/bin/activate${NC}"
echo ""
echo "2. List available commands:"
echo -e "   ${CYAN}grace list${NC}"
echo ""
echo "3. Install module CLIs:"
echo "   Each module has its own setup script in modules/<module>/setup.sh"
echo ""
echo "4. View help:"
echo -e "   ${CYAN}grace --help${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} Always activate the virtual environment before using grace:"
echo -e "   ${CYAN}source $SCRIPT_DIR/venv/bin/activate${NC}"
echo ""
