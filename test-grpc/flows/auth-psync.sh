#!/bin/bash
# Flow: Authorization + Payment Sync

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source libraries
source "$ROOT_DIR/lib/logger.sh"
source "$ROOT_DIR/lib/utils.sh"

# Source operations
source "$ROOT_DIR/operations/auth.sh"
source "$ROOT_DIR/operations/psync.sh"

# Execute Auth + PSync flow
execute_flow_auth_psync() {
    local connector="$1"
    local interactive="${2:-false}"

    log_step "Starting Auth + PSync flow for $connector"

    # Create output directory
    local output_dir=$(create_output_directory "$connector")
    log_info "Output directory: $output_dir"

    # Step 1: Authorization (automatic capture)
    log_step "Step 1/2: Authorization (automatic capture)"
    local tx_id
    tx_id=$(execute_auth "$connector" "$output_dir" "AUTOMATIC")

    if [[ $? -ne 0 || -z "$tx_id" ]]; then
        log_error "Authorization failed, aborting flow"
        generate_flow_summary "$output_dir" "auth-psync" "FAILURE"
        return 1
    fi

    # Interactive mode: pause for user confirmation
    if [[ "$interactive" == "true" ]]; then
        wait_for_user "Authorization completed. Transaction ID: $tx_id. Continue with payment sync?"
    fi

    # Step 2: Payment Sync
    log_step "Step 2/2: Payment Sync"
    if ! execute_psync "$connector" "$output_dir" "$tx_id"; then
        log_error "Payment sync failed"
        generate_flow_summary "$output_dir" "auth-psync" "FAILURE"
        return 1
    fi

    # Generate summary
    generate_flow_summary "$output_dir" "auth-psync" "SUCCESS"

    log_success "Auth + PSync flow completed successfully"
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

    execute_flow_auth_psync "$connector" "$interactive"
fi
