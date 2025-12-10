#!/bin/bash
# gRPC Test Automation - Main Entry Point
# Provides CLI interface for running automated gRPC tests

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ROOT_DIR="$SCRIPT_DIR"

# Source libraries
source "$SCRIPT_DIR/lib/logger.sh"
source "$SCRIPT_DIR/lib/utils.sh"

# Display usage information
show_usage() {
    cat << EOF
gRPC Test Automation - Generic Test Runner

USAGE:
  ./test-grpc.sh <connector> <flow> [options]

FLOWS:
  auth-psync          Authorization + Payment Sync
  auth-capture        Authorization (manual) + Capture
  auth-refund-rsync   Authorization (auto) + Refund + Refund Sync
  auth-void           Authorization (manual) + Void

OPTIONS:
  --interactive       Pause between operations for confirmation
  --debug            Enable debug logging
  -h, --help         Show this help message

EXAMPLES:
  # Run auth + capture flow for bambora
  ./test-grpc.sh bambora auth-capture

  # Run auth + refund + rsync flow with interactive mode
  ./test-grpc.sh bambora auth-refund-rsync --interactive

  # Run void flow with debug logging
  ./test-grpc.sh bambora auth-void --debug

ENVIRONMENT SETUP:
  1. Copy .env.example to .env
  2. Set connector-specific credentials:
       BAMBORA_API_KEY=your_api_key
       BAMBORA_KEY1=your_merchant_key

  See .env.example for more auth type examples

OUTPUT:
  Results saved to: ./output/<connector>/<timestamp>/
  - Individual operation JSONs (auth.json, capture.json, etc.)
  - Summary JSON with complete flow results
  - Detailed execution log (test.log)

PREREQUISITES:
  - grpcurl: brew install grpcurl
  - jq: brew install jq

For more information, see README.md

EOF
}

# Display version information
show_version() {
    echo "gRPC Test Automation v1.0.0"
    echo "Generic test runner for payment connector gRPC APIs"
}

# Main function
main() {
    # Check for help flag first
    if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
        show_usage
        exit 0
    fi

    if [[ "${1:-}" == "-v" || "${1:-}" == "--version" ]]; then
        show_version
        exit 0
    fi

    # Validate arguments
    if [[ $# -lt 2 ]]; then
        log_error "Missing required arguments"
        echo ""
        show_usage
        exit 1
    fi

    local connector="$1"
    local flow="$2"
    shift 2

    # Parse options
    local interactive="false"
    local debug="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --interactive)
                interactive="true"
                shift
                ;;
            --debug)
                export DEBUG="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Display header
    echo ""
    log_info "gRPC Test Automation - Starting"
    log_info "Connector: $connector"
    log_info "Flow: $flow"
    log_info "Interactive: $interactive"
    echo ""

    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi

    # Validate connector config exists
    local config_file="$SCRIPT_DIR/configs/${connector}.json"
    if [[ ! -f "$config_file" ]]; then
        log_error "Connector config not found: configs/${connector}.json"
        log_info "Available connectors:"
        ls -1 "$SCRIPT_DIR/configs/"*.json 2>/dev/null | xargs -n1 basename | sed 's/.json$//' | sed 's/^/  - /' || log_info "  (none)"
        exit 1
    fi

    # Execute the requested flow
    case "$flow" in
        auth-psync)
            source "$SCRIPT_DIR/flows/auth-psync.sh"
            execute_flow_auth_psync "$connector" "$interactive"
            ;;
        auth-capture)
            source "$SCRIPT_DIR/flows/auth-capture.sh"
            execute_flow_auth_capture "$connector" "$interactive"
            ;;
        auth-refund-rsync)
            source "$SCRIPT_DIR/flows/auth-refund-rsync.sh"
            execute_flow_auth_refund_rsync "$connector" "$interactive"
            ;;
        auth-void)
            source "$SCRIPT_DIR/flows/auth-void.sh"
            execute_flow_auth_void "$connector" "$interactive"
            ;;
        *)
            log_error "Unknown flow: $flow"
            log_info "Available flows: auth-psync, auth-capture, auth-refund-rsync, auth-void"
            exit 1
            ;;
    esac

    local exit_code=$?

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        log_success "Flow completed successfully!"
    else
        log_error "Flow failed with errors"
    fi
    echo ""

    exit $exit_code
}

# Run main function
main "$@"
