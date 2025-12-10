#!/bin/bash
# Header Builder - Build gRPC headers based on authentication type
# Constructs appropriate headers for grpcurl commands

set -euo pipefail

# Build gRPC headers based on auth type
# Args: auth_type connector_name output_array_name
# Populates the specified array with header arguments
build_grpc_headers() {
    local auth_type="$1"
    local connector="$2"
    local -n headers_ref=$3  # Reference to output array

    log_debug "Building headers for auth type: $auth_type"

    # Always include connector header
    headers_ref+=("-H" "x-connector: $connector")

    # Always include x-auth header (maps to auth_type)
    headers_ref+=("-H" "x-auth: ${auth_type}")

    # Add merchant ID if available
    if [[ -n "${MERCHANT_ID:-}" ]]; then
        headers_ref+=("-H" "x-merchant-id: $MERCHANT_ID")
    fi

    # Build headers based on auth type
    case "$auth_type" in
        header-key)
            # Only API key in headers
            headers_ref+=("-H" "x-api-key: $API_KEY")
            log_debug "Added headers: x-api-key"
            ;;

        body-key)
            # API key + KEY1
            headers_ref+=("-H" "x-api-key: $API_KEY")
            headers_ref+=("-H" "x-key1: $KEY1")
            log_debug "Added headers: x-api-key, x-key1"
            ;;

        signature-key)
            # API key + signature + KEY1
            headers_ref+=("-H" "x-api-key: $API_KEY")
            headers_ref+=("-H" "x-api-signature: $API_SIGNATURE")
            headers_ref+=("-H" "x-key1: $KEY1")
            log_debug "Added headers: x-api-key, x-api-signature, x-key1"
            ;;

        multiauth-key)
            # API key + signature + KEY1 + optional KEY2, KEY3, etc.
            headers_ref+=("-H" "x-api-key: $API_KEY")
            headers_ref+=("-H" "x-api-signature: $API_SIGNATURE")
            headers_ref+=("-H" "x-key1: $KEY1")

            # Add optional additional keys
            for i in {2..9}; do
                local key_var="KEY${i}"
                if [[ -n "${!key_var:-}" ]]; then
                    headers_ref+=("-H" "x-key${i}: ${!key_var}")
                    log_debug "Added header: x-key${i}"
                fi
            done
            log_debug "Added headers: x-api-key, x-api-signature, x-key1 (+ optional keys)"
            ;;

        *)
            log_error "Unknown auth type: $auth_type"
            return 1
            ;;
    esac

    log_debug "Headers built successfully (${#headers_ref[@]} total)"
    return 0
}

# Add reference ID header
# Args: reference_id output_array_name
add_reference_id_header() {
    local ref_id="$1"
    local -n headers_ref=$2

    headers_ref+=("-H" "x-reference-id: $ref_id")
    log_debug "Added reference ID header: $ref_id"
}

# Generate signature for signature-based auth (placeholder for future enhancement)
# Args: payload secret
# Returns: signature string
generate_signature() {
    local payload="$1"
    local secret="$2"

    # HMAC-SHA256 signature
    echo -n "$payload" | openssl dgst -sha256 -hmac "$secret" | awk '{print $2}'
}
