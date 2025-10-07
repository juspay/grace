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

# Check pip
print_status "Checking pip installation..."
if ! command_exists pip && ! command_exists pip3; then
    print_error "pip is required. Please install pip."
    exit 1
fi
print_success "pip is available"

# Install grace CLI
echo ""
print_status "Installing grace CLI..."
if pip install -e . >/dev/null 2>&1; then
    print_success "Grace CLI installed successfully"
else
    print_error "Failed to install Grace CLI"
    exit 1
fi

# Initialize registry
echo ""
print_status "Initializing command registry..."
python3 scripts/register_commands.py
print_success "Command registry initialized"

# Get Python bin path
PYTHON_BIN_PATH=$(python3 -c "import site; print(site.USER_BASE + '/bin')" 2>/dev/null || echo "$HOME/.local/bin")

# Check PATH
echo ""
print_status "Checking command availability..."
if command_exists grace; then
    print_success "grace command is available in PATH"
    echo "   Location: $(which grace)"
else
    echo -e "${YELLOW}⚠️  grace command not found in PATH${NC}"
    echo ""
    echo "   To add it to your PATH:"

    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        PYTHON_MAJOR_MINOR=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/Library/Python/$PYTHON_MAJOR_MINOR/bin:\$PATH\"' >> ~/.zshrc${NC}"
        echo -e "   ${CYAN}source ~/.zshrc${NC}"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
        PYTHON_MAJOR_MINOR=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/Library/Python/$PYTHON_MAJOR_MINOR/bin:\$PATH\"' >> ~/.bashrc${NC}"
        echo -e "   ${CYAN}source ~/.bashrc${NC}"
    else
        echo "   export PATH=\"$PYTHON_BIN_PATH:\$PATH\""
    fi
fi

# Test installation
echo ""
print_status "Testing installation..."
if command_exists grace; then
    grace --version > /dev/null 2>&1 && print_success "Installation test passed!" || print_error "Installation test failed"
else
    $PYTHON_BIN_PATH/grace --version > /dev/null 2>&1 && print_success "Installation test passed (using full path)!" || print_error "Installation test failed"
fi

# Summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}✅ Grace CLI Setup Complete!${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo "Next Steps:"
echo ""
echo "1. List available commands:"
if command_exists grace; then
    echo -e "   ${CYAN}grace list${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace list${NC}"
fi
echo ""
echo "2. Install module CLIs:"
echo "   Each module has its own setup script in modules/<module>/setup.sh"
echo ""
echo "3. View help:"
if command_exists grace; then
    echo -e "   ${CYAN}grace --help${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace --help${NC}"
fi
echo ""
echo -e "${YELLOW}Note:${NC} If grace is not in PATH, restart your terminal or source your shell config."
echo ""
