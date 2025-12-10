#!/bin/bash
# Utility Functions - Common utilities for test automation
# Provides helper functions for directory management, summaries, and prerequisites

# Source guard - prevent multiple sourcing
[[ -n "${UTILS_SH_LOADED:-}" ]] && return 0
readonly UTILS_SH_LOADED=1

set -euo pipefail

# Create output directory with timestamp
# Args: connector_name
# Returns: output directory path
create_output_directory() {
    local connector="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_dir="${ROOT_DIR}/output/${connector}/${timestamp}"

    mkdir -p "$output_dir"
    log_debug "Created output directory: $output_dir"

    # Set log file for this run
    export LOG_FILE="${output_dir}/test.log"
    log_debug "Log file: $LOG_FILE"

    echo "$output_dir"
}

# Generate flow summary JSON
# Args: output_dir flow_name status
generate_flow_summary() {
    local output_dir="$1"
    local flow_name="$2"
    local status="$3"  # SUCCESS or FAILURE

    local summary_file="${output_dir}/summary.json"

    log_debug "Generating flow summary: $summary_file"

    # Start JSON structure
    cat > "$summary_file" << EOF
{
  "flow": "$flow_name",
  "status": "$status",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "results": {
EOF

    # Add each operation result
    local first=true
    for result_file in "$output_dir"/*.json; do
        if [[ -f "$result_file" && "$(basename "$result_file")" != "summary.json" ]]; then
            if [[ "$first" == "false" ]]; then
                echo "," >> "$summary_file"
            fi
            first=false

            local operation=$(basename "$result_file" .json)
            echo -n "    \"$operation\": " >> "$summary_file"
            cat "$result_file" >> "$summary_file"
        fi
    done

    # Close JSON structure
    cat >> "$summary_file" << EOF

  }
}
EOF

    log_success "Flow summary generated: $summary_file"
}

# Check for required prerequisites (grpcurl, jq)
# Returns: 0 if all prerequisites met, 1 otherwise
check_prerequisites() {
    local missing=()

    if ! command -v grpcurl &> /dev/null; then
        missing+=("grpcurl")
    fi

    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Install missing tools:"
        for tool in "${missing[@]}"; do
            case "$tool" in
                grpcurl)
                    log_info "  • grpcurl: brew install grpcurl (macOS) or go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest"
                    ;;
                jq)
                    log_info "  • jq: brew install jq (macOS) or apt-get install jq (Linux)"
                    ;;
            esac
        done
        return 1
    fi

    log_debug "All prerequisites met: grpcurl, jq"
    return 0
}

# Get uppercase version of connector name for env vars
# Args: connector_name
# Returns: UPPERCASE_NAME
to_upper() {
    echo "$1" | tr '[:lower:]' '[:upper:]' | tr '-' '_'
}

# Get timestamp for reference IDs
# Returns: timestamp string
get_timestamp() {
    date +%s
}

# Generate reference ID
# Args: connector operation
# Returns: ref_{connector}_{operation}_{timestamp}
generate_reference_id() {
    local connector="$1"
    local operation="$2"
    echo "ref_${connector}_${operation}_$(get_timestamp)"
}

# Wait for user confirmation in interactive mode
# Args: message
wait_for_user() {
    local message="$1"
    echo ""
    log_info "$message"
    read -p "Press Enter to continue, or Ctrl+C to abort..."
    echo ""
}

# Pretty print JSON
# Args: json_string
pretty_json() {
    local json="$1"
    echo "$json" | jq '.' 2>/dev/null || echo "$json"
}

# Check if running in CI environment
is_ci() {
    [[ -n "${CI:-}" ]] || [[ -n "${GITHUB_ACTIONS:-}" ]] || [[ -n "${GITLAB_CI:-}" ]]
}
