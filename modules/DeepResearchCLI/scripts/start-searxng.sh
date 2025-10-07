#!/bin/bash
# Start local SearxNG instance
# This script starts the locally installed SearxNG server

set -e

# Get the directory where this script is located (parent of scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
SEARXNG_DIR="$SCRIPT_DIR/searxng-local"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}    Starting Local SearxNG Instance${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check if SearxNG is installed
if [ ! -d "$SEARXNG_DIR" ]; then
    echo -e "${RED}❌ SearxNG not found at: $SEARXNG_DIR${NC}"
    echo ""
    echo "Please run ./setup.sh first to install SearxNG"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$SEARXNG_DIR/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo ""
    echo "Please run ./setup.sh to complete installation"
    exit 1
fi

# Navigate to SearxNG directory
cd "$SEARXNG_DIR"

echo -e "${GREEN}✅ Found SearxNG installation${NC}"
echo "   Location: $SEARXNG_DIR"
echo ""

# Activate virtual environment
echo -e "${CYAN}Activating virtual environment...${NC}"
source venv/bin/activate

# Set settings path
export SEARXNG_SETTINGS_PATH="$SEARXNG_DIR/searx/settings.yml"

# Check port (default: 32768 to match Docker)
PORT=${1:-32768}

echo -e "${GREEN}✅ Environment configured${NC}"
echo "   Settings: $SEARXNG_SETTINGS_PATH"
echo "   Port: $PORT"
echo ""

# Update .env with correct URL
if [ -f "$SCRIPT_DIR/.env" ]; then
    if grep -q "SEARXNG_BASE_URL=" "$SCRIPT_DIR/.env"; then
        sed -i.bak "s|SEARXNG_BASE_URL=.*|SEARXNG_BASE_URL=http://localhost:$PORT|" "$SCRIPT_DIR/.env"
        rm -f "$SCRIPT_DIR/.env.bak"
        echo -e "${GREEN}✅ Updated .env with SearxNG URL${NC}"
    fi
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}🚀 Starting SearxNG Server${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${YELLOW}Access SearxNG at: http://localhost:$PORT${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start SearxNG
python -m searx.webapp

# Deactivate on exit (if we get here)
deactivate
