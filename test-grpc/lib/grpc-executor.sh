#!/bin/bash
# gRPC Executor - Execute grpcurl commands with error handling
# Provides wrapper functions for making gRPC calls

# Source guard - prevent multiple sourcing
[[ -n "${GRPC_EXECUTOR_SH_LOADED:-}" ]] && return 0
readonly GRPC_EXECUTOR_SH_LOADED=1

set -euo pipefail

# Check if grpcurl is installed
check_grpcurl() {
    if ! command -v grpcurl &> /dev/null; then
        log_error "grpcurl is not installed"
        log_info "Install with: brew install grpcurl (macOS) or go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest"
        return 1
    fi

    log_debug "grpcurl found: $(command -v grpcurl)"
    return 0
}

# Execute a grpcurl command
# Args: service method payload base_url headers_array
# Returns: JSON response on stdout
execute_grpc_call() {
    local service="$1"
    local method="$2"
    local payload="$3"
    local base_url="$4"
    shift 4
    local headers_array=("$@")

    local full_method="${service}/${method}"

    log_debug "Executing gRPC call: $full_method"
    log_debug "Base URL: $base_url"
    log_debug "Payload: $(echo "$payload" | jq -c '.' 2>/dev/null || echo "$payload")"

    # Build grpcurl command
    local grpcurl_cmd=(
        "grpcurl"
        "-plaintext"
        "-d" "$payload"
    )

    # Add all headers
    for header in "${headers_array[@]}"; do
        grpcurl_cmd+=("$header")
    done

    # Add base URL and method
    grpcurl_cmd+=("$base_url" "$full_method")

    # Execute command
    log_debug "Running grpcurl with ${#grpcurl_cmd[@]} arguments"
    log_debug "Headers array has ${#headers_array[@]} elements"
    if [[ "${DEBUG:-false}" == "true" ]]; then
        local i=0
        for arg in "${grpcurl_cmd[@]}"; do
            log_debug "  arg[$i]: $arg"
            i=$((i + 1))
        done
    fi

    local response
    local exit_code

    # Capture output and exit code
    set +e
    response=$(${grpcurl_cmd[@]} 2>&1)
    exit_code=$?
    set -e

    if [[ $exit_code -ne 0 ]]; then
        log_error "grpcurl failed with exit code $exit_code"
        log_error "Response: $response"
        return 1
    fi

    # Check if response is valid JSON
    if ! echo "$response" | jq empty 2>/dev/null; then
        log_error "Response is not valid JSON"
        log_error "Response: $response"
        return 1
    fi

    log_debug "gRPC call successful"

    # Output response to stdout
    echo "$response"
    return 0
}

# Execute grpcurl and save response to file
# Args: service method payload base_url output_file headers_array
execute_grpc_call_and_save() {
    local service="$1"
    local method="$2"
    local payload="$3"
    local base_url="$4"
    local output_file="$5"
    shift 5
    local headers_array=("$@")

    log_debug "Executing gRPC call with output to: $output_file"

    local response
    response=$(execute_grpc_call "$service" "$method" "$payload" "$base_url" "${headers_array[@]}")

    if [[ $? -ne 0 ]]; then
        log_error "Failed to execute gRPC call"
        return 1
    fi

    # Pretty print and save to file
    echo "$response" | jq '.' > "$output_file"
    log_debug "Response saved to: $output_file"

    # Return response on stdout
    echo "$response"
    return 0
}
