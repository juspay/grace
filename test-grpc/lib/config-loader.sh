#!/bin/bash
# Config Loader - Hybrid JSON + Environment Variable Configuration
# Loads connector configuration from JSON with env var overrides for sensitive data

# Source guard - prevent multiple sourcing
[[ -n "${CONFIG_LOADER_SH_LOADED:-}" ]] && return 0
readonly CONFIG_LOADER_SH_LOADED=1

set -euo pipefail

# Global variables to store loaded config
CONNECTOR_NAME=""
BASE_URL=""
AUTH_TYPE=""
MERCHANT_ID=""
PROTO_SERVICE=""
CONFIG_FILE=""

# Load .env file if it exists
load_env_file() {
    local env_file="${ROOT_DIR}/.env"

    if [[ -f "$env_file" ]]; then
        log_debug "Loading environment from: $env_file"
        set -a
        source "$env_file"
        set +a
        log_debug "Environment loaded successfully"
    else
        log_debug "No .env file found at: $env_file"
    fi
}

# Load connector configuration from JSON file
# Overrides sensitive values with environment variables
# Args: connector_name
load_connector_config() {
    local connector="$1"

    # Set config file path
    CONFIG_FILE="${ROOT_DIR}/configs/${connector}.json"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Connector config not found: $CONFIG_FILE"
        log_info "Available connectors:"
        if [[ -d "${ROOT_DIR}/configs" ]]; then
            ls -1 "${ROOT_DIR}/configs"/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json$//' | sed 's/^/  - /' || log_info "  (none)"
        fi
        return 1
    fi

    log_debug "Loading config from: $CONFIG_FILE"

    # Load basic config values
    CONNECTOR_NAME=$(jq -r '.connector_name' "$CONFIG_FILE")
    BASE_URL=$(jq -r '.base_url' "$CONFIG_FILE")
    AUTH_TYPE=$(jq -r '.auth_type' "$CONFIG_FILE")
    MERCHANT_ID=$(jq -r '.merchant_id' "$CONFIG_FILE")
    PROTO_SERVICE=$(jq -r '.proto_service' "$CONFIG_FILE")

    # Validate required fields
    if [[ -z "$CONNECTOR_NAME" || "$CONNECTOR_NAME" == "null" ]]; then
        log_error "Missing required field in config: connector_name"
        return 1
    fi

    if [[ -z "$BASE_URL" || "$BASE_URL" == "null" ]]; then
        log_error "Missing required field in config: base_url"
        return 1
    fi

    if [[ -z "$AUTH_TYPE" || "$AUTH_TYPE" == "null" ]]; then
        log_error "Missing required field in config: auth_type"
        return 1
    fi

    # Load .env file for sensitive credentials
    load_env_file

    # Load credentials from environment variables (UPPERCASE connector name)
    local connector_upper=$(to_upper "$connector")

    # Get API key from env var
    local api_key_var="${connector_upper}_API_KEY"
    export API_KEY="${!api_key_var:-}"

    if [[ -z "$API_KEY" ]]; then
        log_error "Missing required environment variable: $api_key_var"
        log_info "Set this in your .env file or export it directly"
        return 1
    fi

    log_debug "Loaded API_KEY from $api_key_var"

    # Load additional keys based on auth type
    case "$AUTH_TYPE" in
        header-key)
            log_debug "Auth type: header-key (API_KEY only)"
            ;;
        body-key)
            local key1_var="${connector_upper}_KEY1"
            export KEY1="${!key1_var:-}"
            if [[ -z "$KEY1" ]]; then
                log_error "Missing required environment variable for body-key auth: $key1_var"
                return 1
            fi
            log_debug "Loaded KEY1 from $key1_var"
            ;;
        signature-key)
            local key1_var="${connector_upper}_KEY1"
            local sig_var="${connector_upper}_API_SIGNATURE"
            export KEY1="${!key1_var:-}"
            export API_SIGNATURE="${!sig_var:-}"
            if [[ -z "$KEY1" ]] || [[ -z "$API_SIGNATURE" ]]; then
                log_error "Missing required environment variables for signature-key auth: $key1_var, $sig_var"
                return 1
            fi
            log_debug "Loaded KEY1 and API_SIGNATURE"
            ;;
        multiauth-key)
            local key1_var="${connector_upper}_KEY1"
            local sig_var="${connector_upper}_API_SIGNATURE"
            export KEY1="${!key1_var:-}"
            export API_SIGNATURE="${!sig_var:-}"

            if [[ -z "$KEY1" ]] || [[ -z "$API_SIGNATURE" ]]; then
                log_error "Missing required environment variables for multiauth-key auth: $key1_var, $sig_var"
                return 1
            fi

            # Load optional KEY2, KEY3, etc.
            for i in {2..9}; do
                local key_var="${connector_upper}_KEY${i}"
                if [[ -n "${!key_var:-}" ]]; then
                    export "KEY${i}"="${!key_var}"
                    log_debug "Loaded KEY${i} from $key_var"
                fi
            done
            ;;
        *)
            log_error "Unknown auth_type: $AUTH_TYPE"
            log_info "Supported types: header-key, body-key, signature-key, multiauth-key"
            return 1
            ;;
    esac

    log_success "Configuration loaded for connector: $CONNECTOR_NAME (auth: $AUTH_TYPE)"
    return 0
}

# Get config value from JSON using jq path
# Args: json_path connector_name
# Returns: value or empty string
get_config_value() {
    local path="$1"
    local connector="${2:-$CONNECTOR_NAME}"
    local config_file="${ROOT_DIR}/configs/${connector}.json"

    if [[ ! -f "$config_file" ]]; then
        log_error "Config file not found: $config_file"
        return 1
    fi

    local value=$(jq -r ".$path // empty" "$config_file" 2>/dev/null)

    if [[ -z "$value" || "$value" == "null" ]]; then
        log_debug "No value found for config path: $path"
        echo ""
        return 1
    fi

    echo "$value"
}

# Get default amount for an operation
# Args: operation_type connector_name
get_default_amount() {
    local operation="$1"
    local connector="${2:-$CONNECTOR_NAME}"

    local amount=$(get_config_value "default_amounts.${operation}" "$connector")

    if [[ -z "$amount" ]]; then
        # Fallback defaults
        case "$operation" in
            auth|capture)
                echo "5000"
                ;;
            refund)
                echo "2500"
                ;;
            *)
                echo "1000"
                ;;
        esac
    else
        echo "$amount"
    fi
}

# Validate that all required environment variables are set
validate_config() {
    local connector="${1:-$CONNECTOR_NAME}"
    local connector_upper=$(to_upper "$connector")

    # Check API key
    local api_key_var="${connector_upper}_API_KEY"
    if [[ -z "${!api_key_var:-}" ]]; then
        log_error "Missing required environment variable: $api_key_var"
        return 1
    fi

    log_success "Configuration validation passed"
    return 0
}
