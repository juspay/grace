#!/bin/bash
# Response Parser - Parse JSON responses and extract values
# Uses jq to parse gRPC JSON responses

set -euo pipefail

# Check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        log_info "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
        return 1
    fi

    log_debug "jq found: $(command -v jq)"
    return 0
}

# Check if response is valid JSON
# Args: response
# Returns: 0 if valid, 1 otherwise
is_valid_json() {
    local response="$1"

    if echo "$response" | jq empty 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Extract transaction ID from payment response
# Args: response
# Returns: transaction ID or empty string
extract_transaction_id() {
    local response="$1"

    log_debug "Extracting transaction ID from response"

    # Try multiple possible paths for transaction ID
    local tx_id=$(echo "$response" | jq -r '
        .transactionId.id //
        .transactionId //
        .transaction_id.id //
        .transaction_id //
        .id //
        empty
    ' 2>/dev/null)

    if [[ -z "$tx_id" || "$tx_id" == "null" ]]; then
        log_warning "Failed to extract transaction ID from response"
        log_debug "Response: $(echo "$response" | jq -c '.' 2>/dev/null || echo "$response")"
        echo ""
        return 1
    fi

    log_debug "Extracted transaction ID: $tx_id"
    echo "$tx_id"
    return 0
}

# Extract refund ID from refund response
# Args: response
# Returns: refund ID or empty string
extract_refund_id() {
    local response="$1"

    log_debug "Extracting refund ID from response"

    # Try multiple possible paths for refund ID
    local refund_id=$(echo "$response" | jq -r '
        .refundId //
        .refund_id //
        .id //
        empty
    ' 2>/dev/null)

    if [[ -z "$refund_id" || "$refund_id" == "null" ]]; then
        log_warning "Failed to extract refund ID from response"
        log_debug "Response: $(echo "$response" | jq -c '.' 2>/dev/null || echo "$response")"
        echo ""
        return 1
    fi

    log_debug "Extracted refund ID: $refund_id"
    echo "$refund_id"
    return 0
}

# Extract status from response
# Args: response
# Returns: status string or empty string
extract_status() {
    local response="$1"

    log_debug "Extracting status from response"

    local status=$(echo "$response" | jq -r '.status // empty' 2>/dev/null)

    if [[ -z "$status" || "$status" == "null" ]]; then
        log_warning "Failed to extract status from response"
        echo ""
        return 1
    fi

    log_debug "Extracted status: $status"
    echo "$status"
    return 0
}

# Extract response reference ID
# Args: response
# Returns: response reference ID or empty string
extract_response_ref_id() {
    local response="$1"

    log_debug "Extracting response reference ID"

    local ref_id=$(echo "$response" | jq -r '
        .responseRefId.id //
        .responseRefId //
        .response_ref_id //
        empty
    ' 2>/dev/null)

    if [[ -z "$ref_id" || "$ref_id" == "null" ]]; then
        log_debug "No response reference ID found"
        echo ""
        return 1
    fi

    log_debug "Extracted response reference ID: $ref_id"
    echo "$ref_id"
    return 0
}

# Extract amount from response
# Args: response
# Returns: amount or empty string
extract_amount() {
    local response="$1"

    local amount=$(echo "$response" | jq -r '.amount // .minor_amount // empty' 2>/dev/null)

    if [[ -z "$amount" || "$amount" == "null" ]]; then
        log_debug "No amount found in response"
        echo ""
        return 1
    fi

    echo "$amount"
    return 0
}

# Extract currency from response
# Args: response
# Returns: currency code or empty string
extract_currency() {
    local response="$1"

    local currency=$(echo "$response" | jq -r '.currency // empty' 2>/dev/null)

    if [[ -z "$currency" || "$currency" == "null" ]]; then
        log_debug "No currency found in response"
        echo ""
        return 1
    fi

    echo "$currency"
    return 0
}

# Check if status matches expected value
# Args: response expected_status
# Returns: 0 if matches, 1 otherwise
validate_status() {
    local response="$1"
    local expected_status="$2"

    local actual_status=$(extract_status "$response")

    if [[ "$actual_status" == "$expected_status" ]]; then
        log_success "Status validation passed: $actual_status"
        return 0
    else
        log_error "Status validation failed: expected '$expected_status', got '$actual_status'"
        return 1
    fi
}

# Extract all relevant fields from response for summary
# Args: response
# Returns: JSON object with extracted fields
extract_summary_fields() {
    local response="$1"

    local tx_id=$(extract_transaction_id "$response" 2>/dev/null || echo "")
    local refund_id=$(extract_refund_id "$response" 2>/dev/null || echo "")
    local status=$(extract_status "$response" 2>/dev/null || echo "")
    local amount=$(extract_amount "$response" 2>/dev/null || echo "")
    local currency=$(extract_currency "$response" 2>/dev/null || echo "")

    jq -n \
        --arg tx_id "$tx_id" \
        --arg refund_id "$refund_id" \
        --arg status "$status" \
        --arg amount "$amount" \
        --arg currency "$currency" \
        '{
            transaction_id: (if $tx_id != "" then $tx_id else null end),
            refund_id: (if $refund_id != "" then $refund_id else null end),
            status: (if $status != "" then $status else null end),
            amount: (if $amount != "" then $amount else null end),
            currency: (if $currency != "" then $currency else null end)
        }'
}
