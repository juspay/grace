#!/usr/bin/env bash

# Config Loader module - Load and merge connector configs with env vars
# Priority: ENV_VAR > config_file > default

# Global config variables
declare -A CONFIG
CONNECTOR_NAME=""
CONNECTOR_CONFIG_FILE=""

# Load connector configuration
load_connector_config() {
    local connector="$1"

    CONNECTOR_NAME="$connector"
    CONNECTOR_CONFIG_FILE="${CONFIG_DIR}/connectors/${connector}.json"

    log_step "Loading configuration for connector: $connector"

    # Check if config file exists
    if [[ ! -f "$CONNECTOR_CONFIG_FILE" ]]; then
        log_warning "Config file not found: $CONNECTOR_CONFIG_FILE"
        log_info "Will use environment variables and defaults"
        return 0
    fi

    # Validate JSON
    if ! jq empty "$CONNECTOR_CONFIG_FILE" 2>/dev/null; then
        fatal_error "Invalid JSON in config file: $CONNECTOR_CONFIG_FILE"
    fi

    # Load config into associative array
    load_config_to_array

    log_success "Configuration loaded successfully"
    log_debug "Config file: $CONNECTOR_CONFIG_FILE"
}

# Load server configuration
load_server_config() {
    local server_config="${CONFIG_DIR}/server.json"
    local env="${1:-local}"

    if [[ -f "$server_config" ]]; then
        local address=$(jq -r ".environments.${env}.address // .default_address" "$server_config")
        local use_tls=$(jq -r ".environments.${env}.tls // .default_tls" "$server_config")

        CONFIG["server_address"]="$address"
        CONFIG["server_tls"]="$use_tls"
    else
        log_debug "Server config not found, using defaults"
        CONFIG["server_address"]="localhost:8000"
        CONFIG["server_tls"]="false"
    fi
}

# Load config values into associative array
load_config_to_array() {
    local config_json
    config_json=$(cat "$CONNECTOR_CONFIG_FILE")

    # Load credentials
    CONFIG["auth_type"]=$(jq_get "$config_json" ".credentials.auth_type" "body-key")
    CONFIG["api_key"]=$(jq_get "$config_json" ".credentials.api_key")
    CONFIG["key1"]=$(jq_get "$config_json" ".credentials.key1")
    CONFIG["merchant_id"]=$(jq_get "$config_json" ".credentials.merchant_id")

    # Load server settings
    CONFIG["server_address"]=$(jq_get "$config_json" ".server.address" "localhost:8000")
    CONFIG["server_tls"]=$(jq_get "$config_json" ".server.use_tls" "false")

    # Load test data
    CONFIG["default_amount"]=$(jq_get "$config_json" ".test_data.default_amount" "5000")
    CONFIG["default_currency"]=$(jq_get "$config_json" ".test_data.default_currency" "USD")

    # Load card details (mastercard_success)
    CONFIG["card_number"]=$(jq_get "$config_json" ".test_data.test_cards.mastercard_success.number")
    CONFIG["card_cvc"]=$(jq_get "$config_json" ".test_data.test_cards.mastercard_success.cvc")
    CONFIG["card_exp_month"]=$(jq_get "$config_json" ".test_data.test_cards.mastercard_success.exp_month")
    CONFIG["card_exp_year"]=$(jq_get "$config_json" ".test_data.test_cards.mastercard_success.exp_year")
    CONFIG["card_network"]=$(jq_get "$config_json" ".test_data.test_cards.mastercard_success.network")

    # Load billing address
    CONFIG["first_name"]=$(jq_get "$config_json" ".test_data.billing_address.first_name" "John")
    CONFIG["last_name"]=$(jq_get "$config_json" ".test_data.billing_address.last_name" "Doe")
    CONFIG["address_line1"]=$(jq_get "$config_json" ".test_data.billing_address.line1" "123 Main Street")
    CONFIG["city"]=$(jq_get "$config_json" ".test_data.billing_address.city" "New York")
    CONFIG["state"]=$(jq_get "$config_json" ".test_data.billing_address.state" "NY")
    CONFIG["zip_code"]=$(jq_get "$config_json" ".test_data.billing_address.zip_code" "10001")
    CONFIG["country"]=$(jq_get "$config_json" ".test_data.billing_address.country" "US")
    CONFIG["email"]=$(jq_get "$config_json" ".test_data.billing_address.email" "john.doe@example.com")
    CONFIG["phone"]=$(jq_get "$config_json" ".test_data.billing_address.phone" "1234567890")
    CONFIG["phone_country_code"]=$(jq_get "$config_json" ".test_data.billing_address.phone_country_code" "1")

    # Load URLs
    CONFIG["return_url"]=$(jq_get "$config_json" ".test_data.urls.return_url" "https://example.com/return")
    CONFIG["webhook_url"]=$(jq_get "$config_json" ".test_data.urls.webhook_url" "https://example.com/webhook")
}

# Get config value with environment variable override
# Priority: ENV_VAR > config_file > default
get_config_value() {
    local key="$1"
    local default="${2:-}"
    local connector_upper=$(to_upper_case "$CONNECTOR_NAME")
    local key_upper=$(to_upper_case "$key")
    local env_var_name="${connector_upper}_${key_upper}"

    # Check if environment variable exists
    if [[ -n "${!env_var_name:-}" ]]; then
        log_debug "Using env var $env_var_name for $key"
        echo "${!env_var_name}"
    elif [[ -n "${CONFIG[$key]:-}" ]]; then
        log_debug "Using config file value for $key"
        echo "${CONFIG[$key]}"
    else
        log_debug "Using default value for $key"
        echo "$default"
    fi
}

# Export config values as shell variables
export_config_vars() {
    # Export with env var override support
    AUTH_TYPE=$(get_config_value "auth_type" "body-key")
    API_KEY=$(get_config_value "api_key")
    KEY1=$(get_config_value "key1")
    MERCHANT_ID=$(get_config_value "merchant_id")
    SERVER_ADDRESS=$(get_config_value "server_address" "localhost:8000")
    SERVER_TLS=$(get_config_value "server_tls" "false")

    # Test data
    DEFAULT_AMOUNT=$(get_config_value "default_amount" "5000")
    DEFAULT_CURRENCY=$(get_config_value "default_currency" "USD")

    # Card data
    CARD_NUMBER=$(get_config_value "card_number" "5100000010001004")
    CARD_CVC=$(get_config_value "card_cvc" "123")
    CARD_EXP_MONTH=$(get_config_value "card_exp_month" "12")
    CARD_EXP_YEAR=$(get_config_value "card_exp_year" "2030")
    CARD_NETWORK=$(get_config_value "card_network" "MASTERCARD")

    # Billing address
    FIRST_NAME=$(get_config_value "first_name" "John")
    LAST_NAME=$(get_config_value "last_name" "Doe")
    ADDRESS_LINE1=$(get_config_value "address_line1" "123 Main Street")
    CITY=$(get_config_value "city" "New York")
    STATE=$(get_config_value "state" "NY")
    ZIP_CODE=$(get_config_value "zip_code" "10001")
    COUNTRY_CODE=$(get_config_value "country" "US")
    EMAIL=$(get_config_value "email" "john.doe@example.com")
    PHONE=$(get_config_value "phone" "1234567890")
    PHONE_COUNTRY_CODE=$(get_config_value "phone_country_code" "1")

    # URLs
    RETURN_URL=$(get_config_value "return_url" "https://example.com/return")
    WEBHOOK_URL=$(get_config_value "webhook_url" "https://example.com/webhook")

    log_debug "Configuration variables exported"
}

# Validate required config values
validate_required_config() {
    local missing=()

    if [[ -z "$API_KEY" ]]; then
        missing+=("API_KEY")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required configuration: ${missing[*]}"
        echo ""
        echo "Set via environment variables or config file:"
        for var in "${missing[@]}"; do
            echo "  ${CONNECTOR_NAME^^}_${var}=value"
        done
        exit 1
    fi
}

# Print loaded configuration (for debugging)
print_config() {
    log_section "Loaded Configuration"

    echo "Connector: $CONNECTOR_NAME"
    echo "API Key: ${API_KEY:0:10}... (truncated)"
    echo "Merchant ID: $MERCHANT_ID"
    echo "Server: $SERVER_ADDRESS"
    echo "Currency: $DEFAULT_CURRENCY"
    echo "Amount: $DEFAULT_AMOUNT"
    echo ""
}
