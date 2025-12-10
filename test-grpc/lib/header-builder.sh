#!/bin/bash
# Header Builder - Build gRPC headers based on authentication type
# Constructs appropriate headers for grpcurl commands

# Source guard - prevent multiple sourcing
[[ -n "${HEADER_BUILDER_SH_LOADED:-}" ]] && return 0
readonly HEADER_BUILDER_SH_LOADED=1

set -euo pipefail

# Build gRPC headers based on auth type
# Args: auth_type connector_name
# Outputs: headers to stdout (one per line, format: "-H|header: value")
build_grpc_headers() {
    local auth_type="$1"
    local connector="$2"

    log_debug "Building headers for auth type: $auth_type"

    # Always include connector header
    echo "-H"
    echo "x-connector: $connector"

    # Always include x-auth header (maps to auth_type)
    echo "-H"
    echo "x-auth: ${auth_type}"

    # Add merchant ID if available
    if [[ -n "${MERCHANT_ID:-}" ]]; then
        echo "-H"
        echo "x-merchant-id: $MERCHANT_ID"
    fi

    # Build headers based on auth type
    case "$auth_type" in
        header-key)
            # Only API key in headers
            echo "-H"
            echo "x-api-key: $API_KEY"
            log_debug "Added headers: x-api-key"
            ;;

        body-key)
            # API key + KEY1
            echo "-H"
            echo "x-api-key: $API_KEY"
            echo "-H"
            echo "x-key1: $KEY1"
            log_debug "Added headers: x-api-key, x-key1"
            ;;

        signature-key)
            # API key + signature + KEY1
            echo "-H"
            echo "x-api-key: $API_KEY"
            echo "-H"
            echo "x-api-signature: $API_SIGNATURE"
            echo "-H"
            echo "x-key1: $KEY1"
            log_debug "Added headers: x-api-key, x-api-signature, x-key1"
            ;;

        multiauth-key)
            # API key + signature + KEY1 + optional KEY2, KEY3, etc.
            echo "-H"
            echo "x-api-key: $API_KEY"
            echo "-H"
            echo "x-api-signature: $API_SIGNATURE"
            echo "-H"
            echo "x-key1: $KEY1"

            # Add optional additional keys
            for i in {2..9}; do
                local key_var="KEY${i}"
                if [[ -n "${!key_var:-}" ]]; then
                    echo "-H"
                    echo "x-key${i}: ${!key_var}"
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

    log_debug "Headers built successfully"
    return 0
}

# Add reference ID header
# Args: reference_id
# Outputs: header to stdout
add_reference_id_header() {
    local ref_id="$1"

    echo "-H"
    echo "x-reference-id: $ref_id"
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
