#!/bin/bash
# Void Operation - Cancel/void an authorization

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

# Execute void operation
# Args: connector output_dir transaction_id
execute_void() {
    local connector="$1"
    local output_dir="$2"
    local transaction_id="$3"

    log_operation "Void (Cancel Authorization)"

    # Load connector config
    if ! load_connector_config "$connector"; then
        log_error "Failed to load connector config"
        return 1
    fi

    # Initialize template variables
    init_template_vars

    # Set operation-specific variables
    local ref_id=$(generate_reference_id "$connector" "void")
    add_template_var "REFERENCE_ID" "$ref_id"
    add_template_var "TRANSACTION_ID" "$transaction_id"

    # Process template
    local template_file="$ROOT_DIR/templates/void.json.tpl"
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
    log_step "Executing void request"
    local response
    response=$(execute_grpc_call_and_save \
        "$PROTO_SERVICE" \
        "Void" \
        "$payload" \
        "$BASE_URL" \
        "$output_dir/void.json" \
        "${headers[@]}")

    if [[ $? -ne 0 ]]; then
        log_error "Void failed"
        return 1
    fi

    # Extract and log status
    local status
    status=$(extract_status "$response")

    log_success "Void completed"
    log_info "Transaction ID: $transaction_id"
    log_info "Status: $status"

    return 0
}

# Main execution (if run directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 3 ]]; then
        echo "Usage: $0 <connector> <output_dir> <transaction_id>"
        exit 1
    fi

    execute_void "$@"
fi
