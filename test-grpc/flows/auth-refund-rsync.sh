#!/bin/bash
# Flow: Authorization (Automatic) + Refund + Refund Sync

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source libraries
source "$ROOT_DIR/lib/logger.sh"
source "$ROOT_DIR/lib/utils.sh"

# Source operations
source "$ROOT_DIR/operations/auth.sh"
source "$ROOT_DIR/operations/refund.sh"
source "$ROOT_DIR/operations/rsync.sh"

# Execute Auth + Refund + RSync flow
execute_flow_auth_refund_rsync() {
    local connector="$1"
    local interactive="${2:-false}"

    log_step "Starting Auth (automatic) + Refund + RSync flow for $connector"

    # Create output directory
    local output_dir=$(create_output_directory "$connector")
    log_info "Output directory: $output_dir"

    # Step 1: Authorization with auto-capture
    log_step "Step 1/3: Authorization (automatic capture)"
    local tx_id
    tx_id=$(execute_auth "$connector" "$output_dir" "AUTOMATIC" "5000")

    if [[ $? -ne 0 || -z "$tx_id" ]]; then
        log_error "Authorization failed, aborting flow"
        generate_flow_summary "$output_dir" "auth-refund-rsync" "FAILURE"
        return 1
    fi

    # Interactive mode: pause for user confirmation
    if [[ "$interactive" == "true" ]]; then
        wait_for_user "Authorization completed. Transaction ID: $tx_id. Continue with refund?"
    fi

    # Step 2: Refund (partial or full)
    log_step "Step 2/3: Refund"
    local refund_id
    refund_id=$(execute_refund "$connector" "$output_dir" "$tx_id" "2500" "customer_return")

    if [[ $? -ne 0 || -z "$refund_id" ]]; then
        log_error "Refund failed, aborting flow"
        generate_flow_summary "$output_dir" "auth-refund-rsync" "FAILURE"
        return 1
    fi

    # Interactive mode: pause for user confirmation
    if [[ "$interactive" == "true" ]]; then
        wait_for_user "Refund completed. Refund ID: $refund_id. Continue with refund sync?"
    fi

    # Step 3: Refund Sync
    log_step "Step 3/3: Refund Sync"
    if ! execute_rsync "$connector" "$output_dir" "$refund_id" "$tx_id"; then
        log_error "Refund sync failed"
        generate_flow_summary "$output_dir" "auth-refund-rsync" "FAILURE"
        return 1
    fi

    # Generate summary
    generate_flow_summary "$output_dir" "auth-refund-rsync" "SUCCESS"

    log_success "Auth + Refund + RSync flow completed successfully"
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

    execute_flow_auth_refund_rsync "$connector" "$interactive"
fi
