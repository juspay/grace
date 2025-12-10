#!/bin/bash
# Refund Operation - Refund a payment

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

# Execute refund operation
# Args: connector output_dir transaction_id refund_amount reason
execute_refund() {
    local connector="$1"
    local output_dir="$2"
    local transaction_id="$3"
    local refund_amount="${4:-}"
    local reason="${5:-customer_return}"

    log_operation "Refund"

    # Load connector config
    if ! load_connector_config "$connector"; then
        log_error "Failed to load connector config"
        return 1
    fi

    # Initialize template variables
    init_template_vars

    # Set operation-specific variables
    local ref_id=$(generate_reference_id "$connector" "refund")
    add_template_var "REFERENCE_ID" "$ref_id"
    add_template_var "TRANSACTION_ID" "$transaction_id"
    add_template_var "REFUND_REASON" "$reason"

    # Set refund amount
    if [[ -z "$refund_amount" ]]; then
        refund_amount=$(get_default_amount "refund" "$connector")
    fi
    add_template_var "REFUND_AMOUNT" "$refund_amount"

    # Process template
    local template_file="$ROOT_DIR/templates/refund.json.tpl"
    local payload
    payload=$(process_template "$template_file")

    if [[ $? -ne 0 ]]; then
        log_error "Failed to process template"
        return 1
    fi

    # Build headers - read output into array
    local -a headers=()
    while IFS= read -r line; do
        headers+=("$line")
    done < <(build_grpc_headers "$AUTH_TYPE" "$connector"; add_reference_id_header "$ref_id")

    # Execute gRPC call
    log_step "Executing refund request"
    local response
    response=$(execute_grpc_call_and_save \
        "$PROTO_SERVICE" \
        "Refund" \
        "$payload" \
        "$BASE_URL" \
        "$output_dir/refund.json" \
        "${headers[@]}")

    if [[ $? -ne 0 ]]; then
        log_error "Refund failed"
        return 1
    fi

    # Extract refund ID
    local refund_id
    refund_id=$(extract_refund_id "$response")

    if [[ $? -ne 0 || -z "$refund_id" ]]; then
        log_error "Failed to extract refund ID"
        return 1
    fi

    # Extract and log status
    local status
    status=$(extract_status "$response")

    log_success "Refund completed"
    log_info "Transaction ID: $transaction_id"
    log_info "Refund ID: $refund_id"
    log_info "Amount refunded: $refund_amount $CURRENCY"
    log_info "Status: $status"

    # Return refund ID on stdout
    echo "$refund_id"
    return 0
}

# Main execution (if run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 3 ]]; then
        echo "Usage: $0 <connector> <output_dir> <transaction_id> [refund_amount] [reason]"
        exit 1
    fi

    execute_refund "$@"
fi
