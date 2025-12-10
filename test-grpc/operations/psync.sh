#!/bin/bash
# Payment Sync Operation - Get payment status

set -euo pipefail

# Get script directory and root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source all libraries
source "$ROOT_DIR/lib/logger.sh"
source "$ROOT_DIR/lib/utils.sh"
source "$ROOT_DIR/lib/config-loader.sh"
source "$ROOT_DIR/lib/header-builder.sh"
source "$ROOT_DIR/lib/grpc-executor.sh"
source "$ROOT_DIR/lib/response-parser.sh"
source "$ROOT_DIR/lib/template-engine.sh"

# Execute payment sync operation
# Args: connector output_dir transaction_id amount
execute_psync() {
    local connector="$1"
    local output_dir="$2"
    local transaction_id="$3"
    local amount="${4:-}"

    log_operation "Payment Sync"

    # Load connector config
    if ! load_connector_config "$connector"; then
        log_error "Failed to load connector config"
        return 1
    fi

    # Initialize template variables
    init_template_vars

    # Set operation-specific variables
    local ref_id=$(generate_reference_id "$connector" "psync")
    add_template_var "REFERENCE_ID" "$ref_id"
    add_template_var "TRANSACTION_ID" "$transaction_id"

    # Set amount
    if [[ -z "$amount" ]]; then
        amount=$(get_default_amount "auth" "$connector")
    fi
    add_template_var "AMOUNT" "$amount"

    # Process template
    local template_file="$ROOT_DIR/templates/psync.json.tpl"
    local payload
    payload=$(process_template "$template_file")

    if [[ $? -ne 0 ]]; then
        log_error "Failed to process template"
        return 1
    fi

    # Build headers
    local -a headers=()
    build_grpc_headers "$AUTH_TYPE" "$connector" headers
    add_reference_id_header "$ref_id" headers

    # Execute gRPC call
    log_step "Executing payment sync request"
    local response
    response=$(execute_grpc_call_and_save \
        "$PROTO_SERVICE" \
        "Get" \
        "$payload" \
        "$BASE_URL" \
        "$output_dir/psync.json" \
        "${headers[@]}")

    if [[ $? -ne 0 ]]; then
        log_error "Payment sync failed"
        return 1
    fi

    # Extract and log status
    local status
    status=$(extract_status "$response")

    log_success "Payment sync completed"
    log_info "Transaction ID: $transaction_id"
    log_info "Status: $status"

    return 0
}

# Main execution (if run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 3 ]]; then
        echo "Usage: $0 <connector> <output_dir> <transaction_id> [amount]"
        exit 1
    fi

    execute_psync "$@"
fi
