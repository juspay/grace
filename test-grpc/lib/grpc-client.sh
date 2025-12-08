#!/usr/bin/env bash

# gRPC Client module - grpcurl wrapper functions

# Generic grpcurl call
grpc_call() {
    local service="$1"
    local method="$2"
    local request_file="$3"
    local ref_id="${4:-$(generate_ref_id "$CONNECTOR_NAME" "$method")}"

    log_step "Calling $service/$method"

    # Build headers array
    local headers=(
        "-H" "x-connector: ${CONNECTOR_NAME}"
        "-H" "x-auth: ${AUTH_TYPE}"
        "-H" "x-api-key: ${API_KEY}"
        "-H" "x-key1: ${KEY1}"
        "-H" "x-merchant-id: ${MERCHANT_ID}"
        "-H" "x-reference-id: ${ref_id}"
    )

    # Add plaintext flag based on TLS setting
    local tls_flag=""
    if [[ "$SERVER_TLS" == "false" ]]; then
        tls_flag="-plaintext"
    fi

    # Make grpcurl call
    local response
    response=$(grpcurl $tls_flag \
        "${headers[@]}" \
        -d @"$request_file" \
        "${SERVER_ADDRESS}" \
        "$service/$method" 2>&1)

    local exit_code=$?

    # Log request to file
    log_to_file "=== Request: $service/$method ==="
    log_to_file "Headers: ${headers[*]}"
    log_to_file "Request file: $request_file"
    log_to_file "$(cat "$request_file")"

    # Log response to file
    log_to_file "=== Response ==="
    log_to_file "$response"
    log_to_file ""

    # Check exit code
    if [[ $exit_code -ne 0 ]]; then
        log_error "grpcurl call failed with exit code: $exit_code"
        log_error "$response"
        return $exit_code
    fi

    # Pretty print response
    log_json "$response" "Response:"

    echo "$response"
    return 0
}

# Call Authorize (automatic capture)
call_authorize_auto() {
    log_section "Authorize (Automatic Capture)"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "authorize_auto")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/authorize-auto-$$.json"
    generate_request "authorize-auto" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.PaymentService" "Authorize" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up temp file
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Authorize (auto) failed"
        return 1
    fi

    # Validate response
    validate_response "authorize" "$response" "$CONNECTOR_NAME"

    # Extract transaction ID
    local txn_id
    txn_id=$(extract_transaction_id "$response")

    if [[ -z "$txn_id" ]]; then
        log_error "Failed to extract transaction ID from response"
        return 1
    fi

    log_success "Authorize successful - Transaction ID: $txn_id"

    # Store in template context for next calls
    set_template_var "TRANSACTION_ID" "$txn_id"

    echo "$txn_id"
    return 0
}

# Call Authorize (manual capture)
call_authorize_manual() {
    log_section "Authorize (Manual Capture)"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "authorize_manual")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/authorize-manual-$$.json"
    generate_request "authorize-manual" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.PaymentService" "Authorize" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up temp file
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Authorize (manual) failed"
        return 1
    fi

    # Validate response
    validate_response "authorize" "$response" "$CONNECTOR_NAME"

    # Extract transaction ID
    local txn_id
    txn_id=$(extract_transaction_id "$response")

    if [[ -z "$txn_id" ]]; then
        log_error "Failed to extract transaction ID from response"
        return 1
    fi

    log_success "Authorize successful - Transaction ID: $txn_id"

    # Store in template context
    set_template_var "TRANSACTION_ID" "$txn_id"

    echo "$txn_id"
    return 0
}

# Call Payment Sync
call_payment_sync() {
    local txn_id="${1:-$(get_template_var "TRANSACTION_ID")}"

    if [[ -z "$txn_id" ]]; then
        fatal_error "Transaction ID required for payment sync"
    fi

    log_section "Payment Sync"

    # Set transaction ID in context
    set_template_var "TRANSACTION_ID" "$txn_id"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "psync")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/payment-sync-$$.json"
    generate_request "payment-sync" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.PaymentService" "Get" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Payment sync failed"
        return 1
    fi

    # Validate response
    validate_response "payment-sync" "$response" "$CONNECTOR_NAME"

    log_success "Payment sync successful"
    return 0
}

# Call Capture
call_capture() {
    local txn_id="${1:-$(get_template_var "TRANSACTION_ID")}"

    if [[ -z "$txn_id" ]]; then
        fatal_error "Transaction ID required for capture"
    fi

    log_section "Capture"

    # Set transaction ID in context
    set_template_var "TRANSACTION_ID" "$txn_id"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "capture")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/capture-$$.json"
    generate_request "capture" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.PaymentService" "Capture" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Capture failed"
        return 1
    fi

    # Validate response
    validate_response "capture" "$response" "$CONNECTOR_NAME"

    log_success "Capture successful"
    return 0
}

# Call Refund
call_refund() {
    local txn_id="${1:-$(get_template_var "TRANSACTION_ID")}"

    if [[ -z "$txn_id" ]]; then
        fatal_error "Transaction ID required for refund"
    fi

    log_section "Refund"

    # Set transaction ID in context
    set_template_var "TRANSACTION_ID" "$txn_id"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "refund")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/refund-$$.json"
    generate_request "refund" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.PaymentService" "Refund" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Refund failed"
        return 1
    fi

    # Validate response (with PR #240 checks)
    validate_response "refund" "$response" "$CONNECTOR_NAME"

    # Extract refund ID
    local refund_id
    refund_id=$(extract_refund_id "$response")

    if [[ -z "$refund_id" ]]; then
        log_warning "Failed to extract refund ID from response"
        return 0
    fi

    log_success "Refund successful - Refund ID: $refund_id"

    # Store in template context
    set_template_var "REFUND_ID" "$refund_id"

    echo "$refund_id"
    return 0
}

# Call Refund Sync
call_refund_sync() {
    local txn_id="${1:-$(get_template_var "TRANSACTION_ID")}"
    local refund_id="${2:-$(get_template_var "REFUND_ID")}"

    if [[ -z "$txn_id" ]]; then
        fatal_error "Transaction ID required for refund sync"
    fi

    if [[ -z "$refund_id" ]]; then
        fatal_error "Refund ID required for refund sync"
    fi

    log_section "Refund Sync"

    # Set IDs in context
    set_template_var "TRANSACTION_ID" "$txn_id"
    set_template_var "REFUND_ID" "$refund_id"

    # Generate reference ID
    local ref_id=$(generate_ref_id "$CONNECTOR_NAME" "rsync")
    set_template_var "REQUEST_REF_ID" "$ref_id"

    # Generate request
    local request_file="/tmp/refund-sync-$$.json"
    generate_request "refund-sync" "$request_file"

    # Make call
    local response
    response=$(grpc_call "ucs.v2.RefundService" "Get" "$request_file" "$ref_id")
    local exit_code=$?

    # Clean up
    rm -f "$request_file"

    if [[ $exit_code -ne 0 ]]; then
        log_error "Refund sync failed"
        return 1
    fi

    # Validate response (with PR #240 checks for action arrays)
    validate_response "refund-sync" "$response" "$CONNECTOR_NAME"

    log_success "Refund sync successful"
    return 0
}
