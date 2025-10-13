#!/bin/bash
# Deep Research CLI - Complete Setup Script
# This script installs and configures the GRACE Deep Research CLI with SearxNG

set -e  # Exit on error

# Get the directory where this script is located (absolute path)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

CONTAINER_NAME="searxng"
SEARXNG_PORT=32768
SEARXNG_LOCAL_PORT=32768

# Setup mode flags (can be set via command-line arguments)
FORCE_DOCKER=false
FORCE_LOCAL=false
AUTO_START=false
SKIP_SEARXNG=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            FORCE_DOCKER=true
            shift
            ;;
        --local)
            FORCE_LOCAL=true
            shift
            ;;
        --auto-start)
            AUTO_START=true
            shift
            ;;
        --skip-searxng)
            SKIP_SEARXNG=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker         Force Docker/OrbStack for SearxNG"
            echo "  --local          Force local SearxNG installation"
            echo "  --auto-start     Automatically start local SearxNG (no prompt)"
            echo "  --skip-searxng   Skip SearxNG setup entirely"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Interactive mode (recommended)"
            echo "  $0 --docker           # Use Docker without asking"
            echo "  $0 --local --auto-start  # Local install and auto-start"
            echo "  $0 --skip-searxng     # Skip SearxNG setup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}    GRACE Deep Research CLI - Setup Script${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Find available port
find_available_port() {
    local start_port=$1
    local end_port=$2

    for port in $(seq $start_port $end_port); do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done

    echo $start_port
}

# Check Docker/OrbStack installation
check_docker() {
    print_status "Checking for Docker/OrbStack..."

    if command_exists docker; then
        # Check if Docker daemon is running
        if docker info >/dev/null 2>&1; then
            if command_exists orb; then
                print_success "OrbStack detected and running!"
                return 0
            else
                print_success "Docker detected and running!"
                return 0
            fi
        else
            print_warning "Docker is installed but not running"
            return 1
        fi
    else
        print_warning "Docker/OrbStack not found"
        return 1
    fi
}

# Setup SearxNG with Docker
setup_searxng_docker() {
    print_status "Setting up SearxNG with Docker..."
    echo "------------------------------------------------------------"

    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_warning "Existing SearxNG container found. Stopping and removing..."
        docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
        docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
    fi

    # Pull latest SearxNG image
    print_status "Pulling SearxNG Docker image..."
    if docker pull searxng/searxng:latest; then
        print_success "SearxNG image pulled successfully"
    else
        print_error "Failed to pull SearxNG image"
        return 1
    fi

    # Find available port
    SEARXNG_PORT=$(find_available_port 32768 32800)
    print_status "Using port: $SEARXNG_PORT"

    # Use script directory for config (already set at top of script)
    CONFIG_DIR="$SCRIPT_DIR"
    CONFIG_FILE="searxng-config.yml"

    # Check if config exists
    if [ ! -f "$CONFIG_DIR/$CONFIG_FILE" ]; then
        print_status "Creating default SearxNG configuration..."
        create_searxng_config
    fi

    # Start SearxNG container
    print_status "Starting SearxNG container..."

    if docker run -d \
        --name $CONTAINER_NAME \
        -p $SEARXNG_PORT:8080 \
        -v "$CONFIG_DIR/$CONFIG_FILE:/etc/searxng/settings.yml:ro" \
        --restart unless-stopped \
        searxng/searxng:latest >/dev/null 2>&1; then

        print_success "SearxNG container started successfully!"
        echo "   URL: http://localhost:$SEARXNG_PORT"

        # Wait for SearxNG to be ready
        print_status "Waiting for SearxNG to initialize..."
        sleep 5

        # Test SearxNG
        if test_searxng "http://localhost:$SEARXNG_PORT"; then
            print_success "SearxNG is ready and responding!"
            return 0
        else
            print_warning "SearxNG started but may not be fully ready yet"
            return 0
        fi
    else
        print_error "Failed to start SearxNG container"
        return 1
    fi
}

# Setup SearxNG locally (without Docker)
setup_searxng_local() {
    print_status "Setting up SearxNG locally (without Docker)..."
    echo "------------------------------------------------------------"

    # Check Python version for SearxNG
    if ! command_exists python3; then
        print_error "Python 3 is required for local SearxNG installation"
        return 1
    fi

    # Use absolute path relative to script directory
    SEARXNG_DIR="$SCRIPT_DIR/searxng-local"

    # Clone SearxNG if not exists
    if [ ! -d "$SEARXNG_DIR" ]; then
        print_status "Cloning SearxNG repository..."
        if git clone https://github.com/searxng/searxng.git "$SEARXNG_DIR"; then
            print_success "SearxNG cloned successfully"
        else
            print_error "Failed to clone SearxNG repository"
            return 1
        fi
    else
        print_success "SearxNG directory already exists"
    fi

    cd "$SEARXNG_DIR"

    # Install dependencies
    print_status "Installing SearxNG dependencies..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    source venv/bin/activate

    uv pip install -U pip setuptools wheel >/dev/null 2>&1
    uv pip install -e . >/dev/null 2>&1

    # Create settings if not exists
    if [ ! -f "searxng/settings.yml" ]; then
        print_status "Creating SearxNG settings..."
        cp searxng/settings.yml.example searxng/settings.yml 2>/dev/null || true
    fi

    # Find available port (starting from 32768)
    SEARXNG_LOCAL_PORT=$(find_available_port 32768 32800)

    print_success "SearxNG installed locally!"

    # Return to script directory
    cd "$SCRIPT_DIR" >/dev/null

    # Ask user if they want to start SearxNG now (or auto-start if flag set)
    echo ""
    local start_now="y"

    if [ "$AUTO_START" = true ]; then
        print_status "Auto-starting SearxNG (forced by --auto-start flag)"
        start_now="y"
    else
        read -p "Would you like to start SearxNG now in the background? (Y/n): " start_now
    fi

    if [ "$start_now" != "n" ] && [ "$start_now" != "N" ]; then
        print_status "Starting SearxNG in background..."

        # Start SearxNG in background using nohup
        cd "$SEARXNG_DIR"
        source venv/bin/activate
        export SEARXNG_SETTINGS_PATH="$SEARXNG_DIR/searx/settings.yml"

        # Start in background with nohup
        nohup python -m searx.webapp > "$SCRIPT_DIR/logs/searxng.log" 2>&1 &
        SEARXNG_PID=$!

        # Save PID for later
        echo $SEARXNG_PID > "$SCRIPT_DIR/searxng.pid"

        deactivate
        cd "$SCRIPT_DIR"

        # Wait a moment for startup
        sleep 3

        # Test if it's running
        if test_searxng "http://localhost:$SEARXNG_LOCAL_PORT"; then
            print_success "SearxNG started successfully!"
            echo "   URL: http://localhost:$SEARXNG_LOCAL_PORT"
            echo "   PID: $SEARXNG_PID (saved to searxng.pid)"
            echo "   Logs: $SCRIPT_DIR/logs/searxng.log"
            echo ""
            print_warning "To stop SearxNG, run: kill \$(cat searxng.pid)"
        else
            print_warning "SearxNG started but may not be ready yet"
            echo "   Check logs: tail -f $SCRIPT_DIR/logs/searxng.log"
        fi
    else
        print_warning "To start SearxNG manually, run:"
        echo "   ./scripts/start-searxng.sh"
        echo "   OR"
        echo "   cd $SEARXNG_DIR"
        echo "   source venv/bin/activate"
        echo "   export SEARXNG_SETTINGS_PATH=searx/settings.yml"
        echo "   python -m searx.webapp"
    fi

    echo "http://localhost:$SEARXNG_LOCAL_PORT"
    return 0
}

# Create default SearxNG config
create_searxng_config() {
    cat > "$SCRIPT_DIR/searxng-config.yml" << 'EOF'
use_default_settings: true

general:
  debug: false
  instance_name: "GRACE Research SearxNG"

search:
  safe_search: 0
  autocomplete: ""
  default_lang: "en"
  formats:
    - html
    - json

server:
  secret_key: "CHANGE_THIS_SECRET_KEY_PLEASE"
  limiter: false
  public_instance: false

ui:
  static_use_hash: true

enabled_plugins:
  - 'Hash plugin'
  - 'Self Information'
  - 'Tracker URL remover'

engines:
  - name: google
    disabled: false
  - name: bing
    disabled: false
  - name: duckduckgo
    disabled: false
  - name: wikipedia
    disabled: false
  - name: wikidata
    disabled: true
EOF
    print_success "Created searxng-config.yml"
}

# Test SearxNG connectivity
test_searxng() {
    local url=$1
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            return 0
        fi
        retry=$((retry + 1))
        sleep 2
    done

    return 1
}

# Setup SearxNG (ask user preference, Docker or local)
setup_searxng() {
    echo ""
    print_status "Setting up SearxNG search engine..."
    echo "============================================================"

    local searxng_url=""
    local use_docker="y"

    # Check if Docker is available
    if check_docker; then
        # Force Docker mode
        if [ "$FORCE_DOCKER" = true ]; then
            print_status "Using Docker/OrbStack (forced by --docker flag)"
            if setup_searxng_docker; then
                searxng_url="http://localhost:$SEARXNG_PORT"
            else
                print_error "Docker setup failed and --docker was forced"
                exit 1
            fi
        # Force Local mode
        elif [ "$FORCE_LOCAL" = true ]; then
            print_status "Using local installation (forced by --local flag)"
            searxng_url=$(setup_searxng_local)
        # Interactive mode
        else
            echo ""
            echo "Docker/OrbStack detected! You have two options:"
            echo ""
            echo "1. Docker/OrbStack (Recommended)"
            echo "   ✅ Easy to manage"
            echo "   ✅ Isolated environment"
            echo "   ✅ Auto-restart on boot"
            echo "   ✅ Simple commands (docker start/stop)"
            echo ""
            echo "2. Local Installation"
            echo "   ✅ No Docker required"
            echo "   ✅ Direct Python control"
            echo "   ✅ Easy debugging"
            echo ""
            read -p "Use Docker/OrbStack for SearxNG? (Y/n): " use_docker

            if [ "$use_docker" = "n" ] || [ "$use_docker" = "N" ]; then
                print_status "User selected local installation"
                searxng_url=$(setup_searxng_local)
            else
                print_status "User selected Docker/OrbStack"
                if setup_searxng_docker; then
                    searxng_url="http://localhost:$SEARXNG_PORT"
                else
                    print_warning "Docker setup failed, trying local installation..."
                    searxng_url=$(setup_searxng_local)
                fi
            fi
        fi
    else
        # Docker not available
        if [ "$FORCE_DOCKER" = true ]; then
            print_error "Docker/OrbStack not available but --docker was forced"
            exit 1
        fi

        print_warning "Docker/OrbStack not available"

        # Offer to install Docker/OrbStack
        echo ""
        echo "Docker/OrbStack is recommended for easier SearxNG setup."
        echo ""
        echo "Install options:"
        echo "  • Docker Desktop: https://docs.docker.com/get-docker/"
        echo "  • OrbStack (macOS): https://orbstack.dev/"
        echo ""

        if [ "$FORCE_LOCAL" = true ]; then
            print_status "Using local installation (forced by --local flag)"
            searxng_url=$(setup_searxng_local)
        else
            read -p "Continue with local SearxNG installation? (Y/n): " continue_local

            if [ "$continue_local" = "n" ] || [ "$continue_local" = "N" ]; then
                print_warning "SearxNG setup skipped. You can set SEARXNG_BASE_URL manually in .env"
                searxng_url="http://localhost:8080"
            else
                searxng_url=$(setup_searxng_local)
            fi
        fi
    fi

    echo "$searxng_url"
}

# Main setup flow
echo ""
print_status "Starting GRACE Deep Research CLI setup..."
echo "Script location: $SCRIPT_DIR"
echo ""

# Check Python version
print_status "Checking Python installation..."
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Check uv
print_status "Checking uv installation..."
if ! command_exists uv; then
    print_error "uv is not installed. Please install uv."
    echo ""
    echo "Install uv using:"
    echo -e "  ${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi
print_success "uv is available"

# Install Python dependencies using uv
echo ""
print_status "Installing Python dependencies with uv..."
echo "------------------------------------------------------------"
if [ -f "requirements.txt" ]; then
    uv pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install the package using uv
echo ""
print_status "Installing grace-research CLI command with uv..."
echo "------------------------------------------------------------"
uv pip install -e .
print_success "grace-research command installed"

# Install Playwright browsers
echo ""
print_status "Installing Playwright browsers..."
echo "------------------------------------------------------------"
print_warning "This will download ~200MB of browser binaries"
playwright install chromium
print_success "Playwright browsers installed"

# Setup SearxNG (unless skipped)
if [ "$SKIP_SEARXNG" = true ]; then
    print_warning "Skipping SearxNG setup (forced by --skip-searxng flag)"
    SEARXNG_URL="http://localhost:32768"
else
    SEARXNG_URL=$(setup_searxng)
    # Trim any whitespace/newlines
    SEARXNG_URL=$(echo "$SEARXNG_URL" | tr -d '\n' | xargs)
fi

# Check .env file
echo ""
print_status "Checking environment configuration..."
echo "------------------------------------------------------------"

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        print_warning ".env file not found. You can create it from .env.example:"
        echo "   cp .env.example .env"
    else
        print_warning ".env file not found. Please create it with your configuration."
    fi
    echo ""
    echo "SearxNG is configured at: $SEARXNG_URL"
    echo "Make sure to set SEARXNG_BASE_URL=$SEARXNG_URL in your .env file"
else
    print_success ".env file already exists"
    echo "SearxNG is configured at: $SEARXNG_URL"
    echo "Update SEARXNG_BASE_URL in .env if needed"
fi

# Get Python bin path
PYTHON_BIN_PATH=$(python3 -c "import site; print(site.USER_BASE + '/bin')" 2>/dev/null || echo "$HOME/.local/bin")

# Check if command is in PATH
echo ""
print_status "Checking command availability..."
echo "------------------------------------------------------------"
if command_exists grace-research; then
    print_success "grace-research command is available in PATH"
    COMMAND_PATH=$(which grace-research)
    echo "   Location: $COMMAND_PATH"
else
    print_warning "grace-research command not found in PATH"
    echo ""
    echo "   The command is installed at: $PYTHON_BIN_PATH/grace-research"
    echo ""
    echo "   To add it to your PATH, run one of these commands:"
    echo ""

    # Detect shell
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/Library/Python/3.9/bin:\$PATH\"' >> ~/.zshrc${NC}"
        echo -e "   ${CYAN}source ~/.zshrc${NC}"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
        echo -e "   ${CYAN}echo 'export PATH=\"\$HOME/Library/Python/3.9/bin:\$PATH\"' >> ~/.bashrc${NC}"
        echo -e "   ${CYAN}source ~/.bashrc${NC}"
    else
        echo "   export PATH=\"$PYTHON_BIN_PATH:\$PATH\""
        echo "   (Add this to your shell's RC file)"
    fi
fi

# Test the installation
echo ""
print_status "Testing installation..."
echo "------------------------------------------------------------"

if command_exists grace-research; then
    grace-research --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Installation test passed!"
    else
        print_error "Installation test failed"
    fi
else
    $PYTHON_BIN_PATH/grace-research --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Installation test passed (using full path)!"
    else
        print_error "Installation test failed"
    fi
fi

# Final summary
echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

if check_docker && docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}SearxNG (Docker):${NC}"
    echo "  • Running at: $SEARXNG_URL"
    echo "  • Container: $CONTAINER_NAME"
    echo "  • Management:"
    echo "    - Stop: docker stop $CONTAINER_NAME"
    echo "    - Start: docker start $CONTAINER_NAME"
    echo "    - Logs: docker logs $CONTAINER_NAME"
    echo "    - Remove: docker rm -f $CONTAINER_NAME"
    echo ""
fi

echo "Next steps:"
echo ""
echo "1. Configure your .env file:"
echo -e "   ${CYAN}nano .env${NC}  # or your preferred editor"
echo ""
echo "2. Add your AI provider credentials:"
echo "   - AI_PROVIDER (litellm, vertex, or anthropic)"
echo "   - API keys and base URLs"
echo "   - Model configuration"
echo ""
echo "3. (Optional) Set up custom instructions:"
echo -e "   ${CYAN}nano custom_instructions.txt${NC}"
echo ""
echo "4. Verify configuration:"
if command_exists grace-research; then
    echo -e "   ${CYAN}grace-research config${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace-research config${NC}"
fi
echo ""
echo "5. Test SearxNG connectivity:"
if command_exists grace-research; then
    echo -e "   ${CYAN}grace-research test-search${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace-research test-search${NC}"
fi
echo ""
echo "6. Run your first research:"
if command_exists grace-research; then
    echo -e "   ${CYAN}grace-research research \"your research query\"${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace-research research \"your research query\"${NC}"
fi
echo ""
echo "For help and documentation:"
if command_exists grace-research; then
    echo -e "   ${CYAN}grace-research --help${NC}"
else
    echo -e "   ${CYAN}$PYTHON_BIN_PATH/grace-research --help${NC}"
fi
echo ""
echo -e "${YELLOW}Note:${NC} If the command is not in your PATH, restart your terminal"
echo "      or source your shell configuration file."
echo ""
