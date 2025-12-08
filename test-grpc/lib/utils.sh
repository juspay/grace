#!/usr/bin/env bash

# Utils module - Common utility functions
# Pattern from: add-connector.sh validation and utility functions

# File validation
validate_file_exists() {
    local file="$1"
    local description="${2:-File}"

    if [[ ! -f "$file" ]]; then
        fatal_error "$description not found: $file"
    fi
}

# Directory validation
validate_directory_exists() {
    local dir="$1"
    local description="${2:-Directory}"

    if [[ ! -d "$dir" ]]; then
        fatal_error "$description not found: $dir"
    fi
}

# String case conversion
to_upper_case() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
}

to_lower_case() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

# JSON helpers with jq
jq_get() {
    local json="$1"
    local path="$2"
    local default="${3:-}"

    local result
    result=$(echo "$json" | jq -r "$path // empty" 2>/dev/null)

    if [[ -z "$result" ]]; then
        echo "$default"
    else
        echo "$result"
    fi
}

jq_exists() {
    local json="$1"
    local path="$2"

    echo "$json" | jq -e "$path" &>/dev/null
    return $?
}

jq_array_length() {
    local json="$1"
    local path="$2"

    echo "$json" | jq -r "${path} | length" 2>/dev/null || echo "0"
}

# Reference ID generation
generate_ref_id() {
    local connector="$1"
    local operation="$2"
    local timestamp=$(date +%s)

    echo "${connector}_${operation}_${timestamp}"
}

# ISO8601 timestamp
timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Random string generator
random_string() {
    local length="${1:-16}"
    LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c "$length"
}

# Email validation
is_valid_email() {
    local email="$1"
    [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

# URL validation
is_valid_url() {
    local url="$1"
    [[ "$url" =~ ^https?:// ]]
}

# Extract transaction ID from response JSON
extract_transaction_id() {
    local response="$1"
    jq_get "$response" ".transactionId.id"
}

# Extract refund ID from response JSON
extract_refund_id() {
    local response="$1"
    local refund_id

    # Try multiple possible paths for refund ID
    refund_id=$(jq_get "$response" ".refundId")
    if [[ -z "$refund_id" ]]; then
        refund_id=$(jq_get "$response" ".refund_id")
    fi
    if [[ -z "$refund_id" ]]; then
        refund_id=$(jq_get "$response" ".connectorRefundId")
    fi

    echo "$refund_id"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Validate environment requirements
validate_environment() {
    log_step "Validating environment requirements"

    local missing_commands=()

    if ! command_exists jq; then
        missing_commands+=("jq")
    fi

    if ! command_exists grpcurl; then
        missing_commands+=("grpcurl")
    fi

    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        echo ""
        echo "Installation instructions:"
        echo "  jq:"
        echo "    macOS: brew install jq"
        echo "    Linux: apt-get install jq or yum install jq"
        echo ""
        echo "  grpcurl:"
        echo "    macOS: brew install grpcurl"
        echo "    Linux: https://github.com/fullstorydev/grpcurl#installation"
        exit 1
    fi

    log_success "Environment validation passed"
}

# Pretty print table
print_table() {
    local -a headers=("$@")
    printf "%-20s %-20s %-20s\n" "${headers[@]}"
    printf "%-20s %-20s %-20s\n" "--------------------" "--------------------" "--------------------"
}

# Trim whitespace
trim() {
    local var="$1"
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo "$var"
}

# Sleep with countdown
sleep_with_countdown() {
    local seconds=$1
    local message="${2:-Waiting}"

    for ((i=seconds; i>0; i--)); do
        printf "\r${message}: %d seconds remaining..." "$i"
        sleep 1
    done
    printf "\r${message}: Done!                    \n"
}
