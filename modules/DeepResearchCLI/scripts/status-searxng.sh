#!/bin/bash
# Check SearxNG status (Docker or local)

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
echo -e "${CYAN}    SearxNG Status Check${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    SEARXNG_URL=$(grep "SEARXNG_BASE_URL=" "$SCRIPT_DIR/.env" | cut -d= -f2)
    echo -e "${CYAN}Configured URL:${NC} $SEARXNG_URL"
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    SEARXNG_URL="http://localhost:8080"
fi

echo ""

# Check Docker container
echo -e "${CYAN}Checking Docker/OrbStack...${NC}"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^searxng$"; then
    echo -e "${GREEN}✅ Docker container running${NC}"
    CONTAINER_ID=$(docker ps --format '{{.ID}}' --filter name=searxng)
    CONTAINER_PORT=$(docker port searxng 2>/dev/null | grep "8080/tcp" | cut -d: -f2)
    echo "   Container ID: $CONTAINER_ID"
    echo "   Port: $CONTAINER_PORT"
    echo "   URL: http://localhost:$CONTAINER_PORT"
else
    if command -v docker >/dev/null 2>&1; then
        if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^searxng$"; then
            echo -e "${YELLOW}⚠️  Docker container exists but not running${NC}"
            echo "   Start with: docker start searxng"
        else
            echo -e "${YELLOW}⚠️  No Docker container found${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Docker not available${NC}"
    fi
fi

echo ""

# Check local installation
echo -e "${CYAN}Checking local installation...${NC}"
if [ -d "$SCRIPT_DIR/searxng-local" ]; then
    echo -e "${GREEN}✅ Local installation found${NC}"
    echo "   Location: $SCRIPT_DIR/searxng-local"

    # Check if running
    if [ -f "$SCRIPT_DIR/searxng.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/searxng.pid")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Local SearxNG running${NC}"
            echo "   PID: $PID"
            echo "   Logs: $SCRIPT_DIR/logs/searxng.log"
        else
            echo -e "${YELLOW}⚠️  PID file exists but process not running${NC}"
            echo "   Stale PID: $PID"
        fi
    else
        echo -e "${YELLOW}⚠️  Not running${NC}"
        echo "   Start with: ./start-searxng.sh"
    fi
else
    echo -e "${YELLOW}⚠️  No local installation found${NC}"
fi

echo ""

# Test connectivity
echo -e "${CYAN}Testing connectivity...${NC}"
if curl -s -f "$SEARXNG_URL" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ SearxNG is accessible at $SEARXNG_URL${NC}"

    # Test JSON API
    if curl -s "$SEARXNG_URL/search?q=test&format=json" 2>/dev/null | grep -q "results"; then
        echo -e "${GREEN}✅ JSON API is working${NC}"
    else
        echo -e "${YELLOW}⚠️  JSON API may not be properly configured${NC}"
    fi
else
    echo -e "${RED}❌ Cannot connect to $SEARXNG_URL${NC}"
    echo ""
    echo "Possible solutions:"
    echo "  1. Start Docker container: docker start searxng"
    echo "  2. Start local SearxNG: ./start-searxng.sh"
    echo "  3. Run setup: ./setup.sh"
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
