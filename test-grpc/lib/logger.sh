#!/bin/bash
# Logger Module - Color-coded logging utilities
# Provides consistent logging across all test scripts

# Source guard - prevent multiple sourcing
[[ -n "${LOGGER_SH_LOADED:-}" ]] && return 0
readonly LOGGER_SH_LOADED=1

set -euo pipefail

# Color constants
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_RESET='\033[0m'

# Log file (set by caller if needed)
LOG_FILE="${LOG_FILE:-}"

# Log to file if LOG_FILE is set
log_to_file() {
    local message="$1"
    if [[ -n "$LOG_FILE" ]]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $message" >> "$LOG_FILE"
    fi
}

# Info message (blue)
log_info() {
    echo -e "${COLOR_BLUE}ℹ️  INFO: $1${COLOR_RESET}"
    log_to_file "INFO: $1"
}

# Success message (green)
log_success() {
    echo -e "${COLOR_GREEN}✅ SUCCESS: $1${COLOR_RESET}"
    log_to_file "SUCCESS: $1"
}

# Error message (red)
log_error() {
    echo -e "${COLOR_RED}❌ ERROR: $1${COLOR_RESET}" >&2
    log_to_file "ERROR: $1"
}

# Warning message (yellow)
log_warning() {
    echo -e "${COLOR_YELLOW}⚠️  WARNING: $1${COLOR_RESET}"
    log_to_file "WARNING: $1"
}

# Step marker (cyan)
log_step() {
    echo -e "${COLOR_CYAN}▶ STEP: $1${COLOR_RESET}"
    log_to_file "STEP: $1"
}

# Debug message (purple) - only shown if DEBUG=true
log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${COLOR_PURPLE}🔍 DEBUG: $1${COLOR_RESET}"
        log_to_file "DEBUG: $1"
    fi
}

# Operation start message
log_operation() {
    echo -e "${COLOR_CYAN}═══════════════════════════════════════════${COLOR_RESET}"
    echo -e "${COLOR_CYAN}▶ $1${COLOR_RESET}"
    echo -e "${COLOR_CYAN}═══════════════════════════════════════════${COLOR_RESET}"
    log_to_file "OPERATION: $1"
}

# Response log (for gRPC responses)
log_response() {
    local operation="$1"
    local status="$2"
    log_debug "Response from $operation: status=$status"
}

# Validation log
log_validation() {
    local check="$1"
    local result="$2"
    if [[ "$result" == "passed" || "$result" == "success" ]]; then
        log_success "Validation: $check - PASSED"
    else
        log_error "Validation: $check - FAILED"
    fi
}
