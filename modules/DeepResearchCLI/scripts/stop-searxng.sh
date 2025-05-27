#!/bin/bash
# Stop local SearxNG instance

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}    Stopping Local SearxNG Instance${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$SCRIPT_DIR/searxng.pid" ]; then
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
    echo ""
    echo "SearxNG may not be running, or was not started by setup.sh"
    echo ""
    echo "To find and stop manually:"
    echo "  ps aux | grep searx"
    echo "  kill <pid>"
    exit 0
fi

# Read PID
PID=$(cat "$SCRIPT_DIR/searxng.pid")

echo -e "${CYAN}Found SearxNG PID: $PID${NC}"

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}Stopping SearxNG (PID: $PID)...${NC}"
    kill $PID

    # Wait for process to stop
    sleep 2

    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Process still running, force killing...${NC}"
        kill -9 $PID
    fi

    echo -e "${GREEN}✅ SearxNG stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Process not running${NC}"
fi

# Remove PID file
rm -f "$SCRIPT_DIR/searxng.pid"
echo -e "${GREEN}✅ Cleaned up PID file${NC}"

echo ""
echo -e "${CYAN}SearxNG has been stopped${NC}"
