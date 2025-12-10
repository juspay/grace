#!/bin/bash
# Template Engine - Substitute placeholders in template files
# Provides template processing with {{VARIABLE}} substitution

set -euo pipefail

# Global associative array for template variables
declare -gA TEMPLATE_VARS

# Initialize template variables with common defaults
init_template_vars() {
    log_debug "Initializing template variables"

    # Clear existing variables
    TEMPLATE_VARS=()

    # Add common defaults
    TEMPLATE_VARS[CURRENCY]="${CURRENCY:-USD}"
    TEMPLATE_VARS[TIMESTAMP]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    log_debug "Template variables initialized"
}

# Add a variable to the template substitution map
# Args: key value
add_template_var() {
    local key="$1"
    local value="$2"

    TEMPLATE_VARS[$key]="$value"
    log_debug "Added template variable: $key = $value"
}

# Add multiple variables from connector config
load_template_vars_from_config() {
    local connector="${1:-$CONNECTOR_NAME}"

    log_debug "Loading template variables from config"

    # Load test card details
    local card_number=$(get_config_value "test_card.card_number" "$connector" 2>/dev/null || echo "4111111111111111")
    local card_cvc=$(get_config_value "test_card.card_cvc" "$connector" 2>/dev/null || echo "123")
    local card_exp_month=$(get_config_value "test_card.card_exp_month" "$connector" 2>/dev/null || echo "12")
    local card_exp_year=$(get_config_value "test_card.card_exp_year" "$connector" 2>/dev/null || echo "2030")
    local card_network=$(get_config_value "test_card.card_network" "$connector" 2>/dev/null || echo "VISA")

    add_template_var "CARD_NUMBER" "$card_number"
    add_template_var "CARD_CVC" "$card_cvc"
    add_template_var "CARD_EXP_MONTH" "$card_exp_month"
    add_template_var "CARD_EXP_YEAR" "$card_exp_year"
    add_template_var "CARD_NETWORK" "$card_network"

    # Load billing address
    local first_name=$(get_config_value "billing_address.first_name" "$connector" 2>/dev/null || echo "John")
    local last_name=$(get_config_value "billing_address.last_name" "$connector" 2>/dev/null || echo "Doe")
    local line1=$(get_config_value "billing_address.line1" "$connector" 2>/dev/null || echo "123 Main St")
    local city=$(get_config_value "billing_address.city" "$connector" 2>/dev/null || echo "New York")
    local state=$(get_config_value "billing_address.state" "$connector" 2>/dev/null || echo "NY")
    local zip_code=$(get_config_value "billing_address.zip_code" "$connector" 2>/dev/null || echo "10001")
    local country=$(get_config_value "billing_address.country_alpha2_code" "$connector" 2>/dev/null || echo "US")
    local email=$(get_config_value "billing_address.email" "$connector" 2>/dev/null || echo "test@example.com")
    local phone=$(get_config_value "billing_address.phone_number" "$connector" 2>/dev/null || echo "1234567890")
    local phone_code=$(get_config_value "billing_address.phone_country_code" "$connector" 2>/dev/null || echo "1")

    add_template_var "FIRST_NAME" "$first_name"
    add_template_var "LAST_NAME" "$last_name"
    add_template_var "ADDRESS_LINE1" "$line1"
    add_template_var "CITY" "$city"
    add_template_var "STATE" "$state"
    add_template_var "ZIP_CODE" "$zip_code"
    add_template_var "COUNTRY" "$country"
    add_template_var "EMAIL" "$email"
    add_template_var "PHONE_NUMBER" "$phone"
    add_template_var "PHONE_COUNTRY_CODE" "$phone_code"

    # Load URLs
    local return_url=$(get_config_value "return_url" "$connector" 2>/dev/null || echo "https://example.com/return")
    local webhook_url=$(get_config_value "webhook_url" "$connector" 2>/dev/null || echo "https://example.com/webhook")

    add_template_var "RETURN_URL" "$return_url"
    add_template_var "WEBHOOK_URL" "$webhook_url"

    # Add merchant ID
    if [[ -n "${MERCHANT_ID:-}" ]]; then
        add_template_var "MERCHANT_ID" "$MERCHANT_ID"
    fi

    log_debug "Template variables loaded from config"
}

# Process template file and substitute variables
# Args: template_file
# Returns: processed content on stdout
process_template() {
    local template_file="$1"

    if [[ ! -f "$template_file" ]]; then
        log_error "Template file not found: $template_file"
        return 1
    fi

    log_debug "Processing template: $template_file"

    local content=$(cat "$template_file")

    # Substitute each variable
    for key in "${!TEMPLATE_VARS[@]}"; do
        local value="${TEMPLATE_VARS[$key]}"
        # Escape special characters in value for sed
        local escaped_value=$(printf '%s\n' "$value" | sed 's/[&/\]/\\&/g')
        content=$(echo "$content" | sed "s|{{${key}}}|${escaped_value}|g")
    done

    # Check for unsubstituted placeholders
    if echo "$content" | grep -q '{{'; then
        log_warning "Template contains unsubstituted placeholders"
        local unsubstituted=$(echo "$content" | grep -o '{{[^}]*}}' | sort -u)
        log_debug "Unsubstituted placeholders: $unsubstituted"
    fi

    # Validate resulting JSON
    if ! echo "$content" | jq empty 2>/dev/null; then
        log_error "Processed template is not valid JSON"
        log_debug "Content: $content"
        return 1
    fi

    log_debug "Template processed successfully"

    echo "$content"
    return 0
}

# Process template and save to file
# Args: template_file output_file
process_template_to_file() {
    local template_file="$1"
    local output_file="$2"

    log_debug "Processing template to file: $output_file"

    local content
    content=$(process_template "$template_file")

    if [[ $? -ne 0 ]]; then
        log_error "Failed to process template"
        return 1
    fi

    echo "$content" > "$output_file"
    log_debug "Processed template saved to: $output_file"

    return 0
}
