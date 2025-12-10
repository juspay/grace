#!/bin/bash
# Flow: Authorization (Manual) + Capture

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source libraries
source "$ROOT_DIR/lib/logger.sh"
source "$ROOT_DIR/lib/utils.sh"

# Source operations
source "$ROOT_DIR/operations/auth.sh"
source "$ROOT_DIR/operations/capture.sh"

# Execute Auth + Capture flow
execute_flow_auth_capture() {
    local connector="$1"
    local interactive="${2:-false}"

    log_step "Starting Auth (manual) + Capture flow for $connector"

    # Create output directory
    local output_dir=$(create_output_directory "$connector")
    log_info "Output directory: $output_dir"

    # Step 1: Authorization (manual capture)
    log_step "Step 1/2: Authorization (manual capture)"
    log_debug "About to call execute_auth with: connector=$connector, output_dir=$output_dir"
    local tx_id
    log_debug "Calling execute_auth..."
    tx_id=$(execute_auth "$connector" "$output_dir" "MANUAL")
    log_debug "execute_auth returned with exit code: $?"

    if [[ $? -ne 0 || -z "$tx_id" ]]; then
        log_error "Authorization failed, aborting flow"
        generate_flow_summary "$output_dir" "auth-capture" "FAILURE"
        return 1
    fi

    # Interactive mode: pause for user confirmation
    if [[ "$interactive" == "true" ]]; then
        wait_for_user "Authorization completed. Transaction ID: $tx_id. Continue with capture?"
    fi

    # Step 2: Capture
    log_step "Step 2/2: Capture"
    if ! execute_capture "$connector" "$output_dir" "$tx_id"; then
        log_error "Capture failed"
        generate_flow_summary "$output_dir" "auth-capture" "FAILURE"
        return 1
    fi

    # Generate summary
    generate_flow_summary "$output_dir" "auth-capture" "SUCCESS"

    log_success "Auth + Capture flow completed successfully"
    log_info "Results saved to: $output_dir"
    return 0
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <connector> [--interactive]"
        echo "  connector: Connector name (e.g., bambora)"
        echo "  --interactive: Optional flag to pause between operations"
        exit 1
    fi

    connector="$1"
    interactive="false"

    if [[ "${2:-}" == "--interactive" ]]; then
        interactive="true"
    fi

    execute_flow_auth_capture "$connector" "$interactive"
fi
