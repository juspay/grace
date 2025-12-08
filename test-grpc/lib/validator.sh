#!/usr/bin/env bash

# Validator module - Response validation engine
# Addresses PR #240 critical issues

# Validation context
declare -A VALIDATION_ERRORS
declare -A VALIDATION_WARNINGS
VALIDATION_RULES_FILE=""

# Load validation rules for operation
load_validation_rules() {
    local operation="$1"

    VALIDATION_RULES_FILE="${VALIDATION_DIR}/rules/${operation}.json"

    if [[ ! -f "$VALIDATION_RULES_FILE" ]]; then
        log_warning "Validation rules not found: $VALIDATION_RULES_FILE"
        return 1
    fi

    log_debug "Loaded validation rules: $operation"
    return 0
}

# Check required fields in response
check_required_fields() {
    local response_json="$1"
    local rules_json="$2"

    log_debug "Checking required fields"

    # Get required fields from rules
    local required_fields
    required_fields=$(echo "$rules_json" | jq -r '.required_fields[]? // empty')

    if [[ -z "$required_fields" ]]; then
        log_debug "No required fields defined"
        return 0
    fi

    while IFS= read -r field; do
        if [[ -z "$field" ]]; then
            continue
        fi

        # Check if field exists and is not empty
        local value
        value=$(echo "$response_json" | jq -r ".$field // empty")

        if [[ -z "$value" ]]; then
            VALIDATION_ERRORS["required_field_$field"]="Required field missing or empty: $field"
        else
            log_debug "  ✓ $field: present"
        fi
    done <<< "$required_fields"
}

# Check field validations
check_field_validations() {
    local response_json="$1"
    local rules_json="$2"

    log_debug "Checking field validations"

    # Get field validations array
    local validations
    validations=$(echo "$rules_json" | jq -c '.field_validations[]? // empty')

    if [[ -z "$validations" ]]; then
        log_debug "No field validations defined"
        return 0
    fi

    while IFS= read -r validation; do
        if [[ -z "$validation" ]]; then
            continue
        fi

        local field=$(echo "$validation" | jq -r '.field')
        local rules=$(echo "$validation" | jq -r '.rules[]? // empty')
        local error_msg=$(echo "$validation" | jq -r '.error_message // "Validation failed"')
        local allowed_values=$(echo "$validation" | jq -r '.allowed_values[]? // empty')

        # Get field value
        local value
        value=$(echo "$response_json" | jq -r ".$field // empty")

        # Check not_empty rule
        if echo "$rules" | grep -q "not_empty"; then
            if [[ -z "$value" ]]; then
                VALIDATION_ERRORS["field_$field"]="$error_msg"
                continue
            fi
        fi

        # Check allowed values
        if [[ -n "$allowed_values" ]]; then
            local valid=false
            while IFS= read -r allowed_value; do
                if [[ "$value" == "$allowed_value" ]]; then
                    valid=true
                    break
                fi
            done <<< "$allowed_values"

            if [[ "$valid" == "false" ]]; then
                VALIDATION_ERRORS["field_value_$field"]="$error_msg (got: $value)"
            fi
        fi

    done <<< "$validations"
}

# Validate connector-specific rules
validate_connector_specific() {
    local response_json="$1"
    local rules_json="$2"
    local connector="$3"

    log_debug "Checking connector-specific rules for: $connector"

    # Check if connector-specific rules exist
    if ! echo "$rules_json" | jq -e ".connector_specific.${connector}" &>/dev/null; then
        log_debug "No connector-specific rules for $connector"
        return 0
    fi

    local connector_rules
    connector_rules=$(echo "$rules_json" | jq ".connector_specific.${connector}")

    # Check connector-specific required fields
    local required_fields
    required_fields=$(echo "$connector_rules" | jq -r '.required_fields[]? // empty')

    while IFS= read -r field; do
        if [[ -z "$field" ]]; then
            continue
        fi

        local value
        value=$(echo "$response_json" | jq -r ".$field // empty")

        if [[ -z "$value" ]]; then
            VALIDATION_ERRORS["connector_required_$field"]="Connector-specific required field missing: $field"
        fi
    done <<< "$required_fields"

    # Check critical validations (PR #240 issues)
    check_critical_validations "$response_json" "$connector_rules" "$connector"
}

# Check critical validations (PR #240 specific checks)
check_critical_validations() {
    local response_json="$1"
    local connector_rules="$2"
    local connector="$3"

    log_debug "Running critical validations (PR #240 checks)"

    # Check if critical_checks array exists
    if ! echo "$connector_rules" | jq -e '.critical_checks' &>/dev/null; then
        log_debug "No critical checks defined"
        return 0
    fi

    # For refund operations, check action array handling
    if echo "$connector_rules" | jq -e '.critical_checks[]? | select(. == "Refund action type verification")' &>/dev/null; then
        check_refund_action_type "$response_json"
    fi

    # Check if actions array exists and validate
    if echo "$response_json" | jq -e '.actions' &>/dev/null; then
        log_debug "Actions array detected - validating PR #240 Issue #3"
        validate_actions_array "$response_json"
    fi
}

# PR #240 Issue #1: Refund status logic
# Don't assume all actions with status: "success" are successful
check_refund_action_type() {
    local response_json="$1"

    log_debug "PR #240 Check: Refund action type verification"

    # Check if actions array exists
    if ! echo "$response_json" | jq -e '.actions' &>/dev/null; then
        log_debug "No actions array found"
        return 0
    fi

    # Find REFUND action
    local refund_action
    refund_action=$(echo "$response_json" | jq '.actions[] | select(.action_type == "REFUND")' 2>/dev/null)

    if [[ -z "$refund_action" ]]; then
        VALIDATION_WARNINGS["refund_action_type"]="PR #240 Issue #1: No REFUND action found in actions array"
    else
        log_success "PR #240 Check passed: REFUND action type verified"
    fi
}

# PR #240 Issue #3: Action array handling
# Validate which refund action is being checked
validate_actions_array() {
    local response_json="$1"

    log_debug "PR #240 Check: Action array handling"

    local actions_count
    actions_count=$(echo "$response_json" | jq '.actions | length' 2>/dev/null || echo "0")

    if [[ "$actions_count" -eq 0 ]]; then
        VALIDATION_WARNINGS["actions_array"]="PR #240 Issue #3: Actions array is empty"
    else
        log_debug "Actions array contains $actions_count action(s)"
    fi
}

# Main validation function
validate_response() {
    local operation="$1"
    local response_json="$2"
    local connector="$3"

    log_step "Validating $operation response"

    # Clear previous validation results
    VALIDATION_ERRORS=()
    VALIDATION_WARNINGS=()

    # Load validation rules
    if ! load_validation_rules "$operation"; then
        log_warning "Skipping validation - no rules file"
        return 0
    fi

    # Load rules
    local rules_json
    rules_json=$(cat "$VALIDATION_RULES_FILE")

    # Run validation checks
    check_required_fields "$response_json" "$rules_json"
    check_field_validations "$response_json" "$rules_json"
    validate_connector_specific "$response_json" "$rules_json" "$connector"

    # Report results
    report_validation_results
}

# Report validation results
report_validation_results() {
    local has_errors=false
    local has_warnings=false

    # Report errors
    if [[ ${#VALIDATION_ERRORS[@]} -gt 0 ]]; then
        has_errors=true
        log_error "Validation failed with ${#VALIDATION_ERRORS[@]} error(s):"
        for key in "${!VALIDATION_ERRORS[@]}"; do
            log_error "  - ${VALIDATION_ERRORS[$key]}"
        done
    fi

    # Report warnings
    if [[ ${#VALIDATION_WARNINGS[@]} -gt 0 ]]; then
        has_warnings=true
        log_warning "Validation warnings (${#VALIDATION_WARNINGS[@]}):"
        for key in "${!VALIDATION_WARNINGS[@]}"; do
            log_warning "  - ${VALIDATION_WARNINGS[$key]}"
        done
    fi

    # Final result
    if [[ "$has_errors" == "true" ]]; then
        return 1
    elif [[ "$has_warnings" == "true" ]]; then
        log_success "Validation passed with warnings"
        return 0
    else
        log_success "Validation passed - all checks successful"
        return 0
    fi
}

# Validate gRPC status code
validate_grpc_status() {
    local response_json="$1"
    local expected_status="${2:-OK}"

    local status
    status=$(echo "$response_json" | jq -r '.status // "UNKNOWN"')

    if [[ "$status" != "$expected_status" ]]; then
        log_warning "gRPC status: $status (expected: $expected_status)"
        return 1
    fi

    log_debug "gRPC status validated: $status"
    return 0
}
