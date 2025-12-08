#!/usr/bin/env bash

# Logger module - Color logging utilities
# Pattern from: add-connector.sh lines 152-223

# Color constants
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_RESET='\033[0m'

# Log file
LOG_FILE=""

# Initialize logger
init_logger() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    LOG_FILE="${OUTPUT_DIR}/logs/test_${timestamp}.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
}

# Internal logging function
_log() {
    local color="$1"
    local prefix="$2"
    local message="$3"

    echo -e "${color}${prefix}${COLOR_RESET} ${message}"

    # Log to file if initialized
    if [[ -n "$LOG_FILE" ]]; then
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] ${prefix} ${message}" >> "$LOG_FILE"
    fi
}

# Public logging functions
log_info() {
    _log "$COLOR_BLUE" "ℹ" "$1"
}

log_success() {
    _log "$COLOR_GREEN" "✓" "$1"
}

log_error() {
    _log "$COLOR_RED" "✗" "$1"
}

log_warning() {
    _log "$COLOR_YELLOW" "⚠" "$1"
}

log_step() {
    _log "$COLOR_PURPLE" "▸" "$1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        _log "$COLOR_CYAN" "⚙" "$1"
    fi
}

# Fatal error - log and exit
fatal_error() {
    log_error "$1"
    exit 1
}

# Log to file only (no console output)
log_to_file() {
    if [[ -n "$LOG_FILE" ]]; then
        echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" >> "$LOG_FILE"
    fi
}

# Pretty print JSON with jq
log_json() {
    local json="$1"
    local label="${2:-}"

    if [[ -n "$label" ]]; then
        log_info "$label"
    fi

    if command -v jq &> /dev/null; then
        echo "$json" | jq '.' 2>/dev/null || echo "$json"
    else
        echo "$json"
    fi

    # Log to file
    log_to_file "JSON: $json"
}

# Section header
log_section() {
    local message="$1"
    local line_length=60
    local padding=$(printf '%*s' $((($line_length - ${#message} - 2) / 2)) '')

    echo ""
    echo -e "${COLOR_PURPLE}================================================${COLOR_RESET}"
    echo -e "${COLOR_PURPLE}${padding} ${message}${COLOR_RESET}"
    echo -e "${COLOR_PURPLE}================================================${COLOR_RESET}"
    echo ""
}

# Progress indicator
log_progress() {
    local current=$1
    local total=$2
    local message="$3"

    local percent=$((current * 100 / total))
    log_step "[${current}/${total}] ${message} (${percent}%)"
}
