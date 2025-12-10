#!/bin/bash
# Authorization Operation - Execute payment authorization

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

# Execute authorization operation
# Args: connector output_dir capture_method amount
# capture_method: MANUAL or AUTOMATIC
execute_auth() {
    local connector="$1"
    local output_dir="$2"
    local capture_method="${3:-MANUAL}"
    local amount="${4:-}"

    log_operation "Authorization (capture: $capture_method)"

    # Load connector config
    if ! load_connector_config "$connector"; then
        log_error "Failed to load connector config"
        return 1
    fi

    # Initialize template variables
    init_template_vars

    # Load variables from config
    load_template_vars_from_config "$connector"

    # Set operation-specific variables
    local ref_id=$(generate_reference_id "$connector" "auth")
    add_template_var "REFERENCE_ID" "$ref_id"
    add_template_var "CONNECTOR_NAME" "$connector"
    add_template_var "CAPTURE_METHOD" "$capture_method"

    # Set amount (use provided value or default)
    if [[ -z "$amount" ]]; then
        amount=$(get_default_amount "auth" "$connector")
    fi
    add_template_var "AMOUNT" "$amount"

    # Process template
    local template_file="$ROOT_DIR/templates/auth.json.tpl"
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
    log_step "Executing authorization request"
    local response
    response=$(execute_grpc_call_and_save \
        "$PROTO_SERVICE" \
        "Authorize" \
        "$payload" \
        "$BASE_URL" \
        "$output_dir/auth.json" \
        "${headers[@]}")

    if [[ $? -ne 0 ]]; then
        log_error "Authorization failed"
        return 1
    fi

    # Extract transaction ID
    local tx_id
    tx_id=$(extract_transaction_id "$response")

    if [[ $? -ne 0 || -z "$tx_id" ]]; then
        log_error "Failed to extract transaction ID"
        return 1
    fi

    # Extract and log status
    local status
    status=$(extract_status "$response")

    log_success "Authorization completed"
    log_info "Transaction ID: $tx_id"
    log_info "Status: $status"
    log_info "Amount: $amount $CURRENCY"

    # Return transaction ID on stdout
    echo "$tx_id"
    return 0
}

# Main execution (if run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 2 ]]; then
        echo "Usage: $0 <connector> <output_dir> [capture_method] [amount]"
        echo "  capture_method: MANUAL or AUTOMATIC (default: MANUAL)"
        echo "  amount: optional amount in minor units (default: from config)"
        exit 1
    fi

    execute_auth "$@"
fi
