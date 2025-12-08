#!/usr/bin/env bash

# Template Engine module - Variable substitution in templates
# Pattern from: add-connector.sh template substitution

# Template context (associative array for variable storage)
declare -A TEMPLATE_CONTEXT

# Initialize template context with config values
init_template_context() {
    # Basic info
    TEMPLATE_CONTEXT["CONNECTOR"]="$CONNECTOR_NAME"
    TEMPLATE_CONTEXT["AMOUNT"]="$DEFAULT_AMOUNT"
    TEMPLATE_CONTEXT["CURRENCY"]="$DEFAULT_CURRENCY"

    # Card details
    TEMPLATE_CONTEXT["CARD_NUMBER"]="$CARD_NUMBER"
    TEMPLATE_CONTEXT["CARD_CVC"]="$CARD_CVC"
    TEMPLATE_CONTEXT["CARD_EXP_MONTH"]="$CARD_EXP_MONTH"
    TEMPLATE_CONTEXT["CARD_EXP_YEAR"]="$CARD_EXP_YEAR"
    TEMPLATE_CONTEXT["CARD_NETWORK"]="$CARD_NETWORK"

    # Billing address
    TEMPLATE_CONTEXT["FIRST_NAME"]="$FIRST_NAME"
    TEMPLATE_CONTEXT["LAST_NAME"]="$LAST_NAME"
    TEMPLATE_CONTEXT["ADDRESS_LINE1"]="$ADDRESS_LINE1"
    TEMPLATE_CONTEXT["CITY"]="$CITY"
    TEMPLATE_CONTEXT["STATE"]="$STATE"
    TEMPLATE_CONTEXT["ZIP_CODE"]="$ZIP_CODE"
    TEMPLATE_CONTEXT["COUNTRY_CODE"]="$COUNTRY_CODE"
    TEMPLATE_CONTEXT["EMAIL"]="$EMAIL"
    TEMPLATE_CONTEXT["PHONE"]="$PHONE"
    TEMPLATE_CONTEXT["PHONE_COUNTRY_CODE"]="$PHONE_COUNTRY_CODE"

    # URLs
    TEMPLATE_CONTEXT["RETURN_URL"]="$RETURN_URL"
    TEMPLATE_CONTEXT["WEBHOOK_URL"]="$WEBHOOK_URL"

    log_debug "Template context initialized with ${#TEMPLATE_CONTEXT[@]} variables"
}

# Set a template variable
set_template_var() {
    local var_name="$1"
    local var_value="$2"

    TEMPLATE_CONTEXT["$var_name"]="$var_value"
    log_debug "Set template variable: $var_name=$var_value"
}

# Get a template variable
get_template_var() {
    local var_name="$1"
    echo "${TEMPLATE_CONTEXT[$var_name]:-}"
}

# Load template file
load_template() {
    local template_file="$1"

    validate_file_exists "$template_file" "Template file"

    cat "$template_file"
}

# Extract template variables from content
get_template_vars() {
    local content="$1"
    echo "$content" | grep -o '{{[A-Z_]*}}' | sort -u | sed 's/[{}]//g'
}

# Validate that all required variables are defined
validate_template_vars() {
    local template_content="$1"
    local missing_vars=()

    # Extract all {{VAR}} placeholders
    local vars
    vars=$(get_template_vars "$template_content")

    while IFS= read -r var; do
        if [[ -z "${TEMPLATE_CONTEXT[$var]:-}" ]]; then
            missing_vars+=("$var")
        fi
    done <<< "$vars"

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_warning "Missing template variables: ${missing_vars[*]}"
        return 1
    fi

    return 0
}

# Substitute all {{VAR}} placeholders with context values
substitute_template() {
    local template_file="$1"
    local output_file="$2"

    log_debug "Substituting template: $template_file -> $output_file"

    # Load template content
    local content
    content=$(load_template "$template_file")

    # Validate variables (optional, won't fail if missing)
    validate_template_vars "$content" || log_debug "Some variables may be undefined"

    # Perform substitution for all context variables
    for var_name in "${!TEMPLATE_CONTEXT[@]}"; do
        local var_value="${TEMPLATE_CONTEXT[$var_name]}"
        # Escape special characters for sed
        var_value=$(echo "$var_value" | sed 's/[\/&]/\\&/g')
        content="${content//\{\{$var_name\}\}/$var_value}"
    done

    # Write to output file
    echo "$content" > "$output_file"

    log_debug "Template substitution complete: $output_file"
}

# Substitute template and return content (not write to file)
substitute_template_to_string() {
    local template_file="$1"

    # Create temp file
    local temp_file="/tmp/template_$$_$(date +%s).json"

    # Substitute
    substitute_template "$template_file" "$temp_file"

    # Read and return content
    local content
    content=$(cat "$temp_file")

    # Clean up
    rm -f "$temp_file"

    echo "$content"
}

# Generate request from template
generate_request() {
    local operation="$1"
    local output_file="$2"

    # Determine template file
    local template_file="${TEMPLATE_DIR}/${operation}.json.template"

    if [[ ! -f "$template_file" ]]; then
        fatal_error "Template not found: $template_file"
    fi

    # Generate reference ID if not set
    if [[ -z "${TEMPLATE_CONTEXT[REQUEST_REF_ID]:-}" ]]; then
        TEMPLATE_CONTEXT["REQUEST_REF_ID"]=$(generate_ref_id "$CONNECTOR_NAME" "$operation")
    fi

    # Generate order ID if not set
    if [[ -z "${TEMPLATE_CONTEXT[ORDER_ID]:-}" ]]; then
        TEMPLATE_CONTEXT["ORDER_ID"]="order_${CONNECTOR_NAME}_$(date +%s)"
    fi

    # Generate description if not set
    if [[ -z "${TEMPLATE_CONTEXT[DESCRIPTION]:-}" ]]; then
        TEMPLATE_CONTEXT["DESCRIPTION"]="Test $operation for $CONNECTOR_NAME"
    fi

    # Substitute template
    substitute_template "$template_file" "$output_file"

    log_success "Generated request: $operation"
}

# Print template context (for debugging)
print_template_context() {
    log_section "Template Context"

    for var_name in $(echo "${!TEMPLATE_CONTEXT[@]}" | tr ' ' '\n' | sort); do
        local var_value="${TEMPLATE_CONTEXT[$var_name]}"
        # Truncate long values
        if [[ ${#var_value} -gt 50 ]]; then
            var_value="${var_value:0:47}..."
        fi
        printf "  %-30s = %s\n" "$var_name" "$var_value"
    done

    echo ""
}
