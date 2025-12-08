#!/usr/bin/env bash

# Modular gRPC Testing Script for Payment Connectors
# Architecture pattern from: add-connector.sh

set -euo pipefail

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LIB_DIR="$SCRIPT_DIR/lib"
readonly CONFIG_DIR="$SCRIPT_DIR/configs"
readonly TEMPLATE_DIR="$SCRIPT_DIR/templates"
readonly VALIDATION_DIR="$SCRIPT_DIR/validation"
readonly TEST_SETS_DIR="$SCRIPT_DIR/test-sets"
readonly OUTPUT_DIR="$SCRIPT_DIR/output"

# =============================================================================
# LOAD LIBRARY MODULES
# =============================================================================

# Source all library modules
source "$LIB_DIR/logger.sh"
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/config-loader.sh"
source "$LIB_DIR/template-engine.sh"
source "$LIB_DIR/validator.sh"
source "$LIB_DIR/grpc-client.sh"

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

CONNECTOR_NAME=""
SELECTED_SET=""
INTERACTIVE_MODE=false

# =============================================================================
# FUNCTIONS
# =============================================================================

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 <connector> [options]

Arguments:
  connector              Connector name (e.g., bambora, silverflow)

Options:
  --set <number>         Test set to run (1, 2, or 3)
  --interactive          Interactive mode (custom operations)
  --debug                Enable debug output
  --help                 Show this help message

Test Sets:
  1  Authorize (automatic capture) + Payment Sync
  2  Authorize + Payment Sync + Refund + Refund Sync
  3  Authorize (manual capture) + Capture

Environment Variables:
  {CONNECTOR}_API_KEY       Override API key
  {CONNECTOR}_MERCHANT_ID   Override merchant ID
  {CONNECTOR}_KEY1          Override key1
  DEBUG=true               Enable debug output

Examples:
  $0 bambora --set 1
  BAMBORA_API_KEY="prod_key" $0 bambora --set 2
  $0 bambora --interactive

EOF
}

# Parse command line arguments
parse_arguments() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi

    CONNECTOR_NAME="$1"
    shift

    while [[ $# -gt 0 ]]; do
        case $1 in
            --set)
                SELECTED_SET="$2"
                shift 2
                ;;
            --interactive)
                INTERACTIVE_MODE=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Initialize the script
initialize() {
    log_section "gRPC Payment Connector Testing"
    echo "Version: $SCRIPT_VERSION"
    echo "Connector: $CONNECTOR_NAME"
    echo ""

    # Initialize logger
    init_logger

    # Validate environment
    validate_environment

    # Load connector configuration
    load_connector_config "$CONNECTOR_NAME"

    # Load server configuration
    load_server_config "local"

    # Export config variables
    export_config_vars

    # Validate required config
    validate_required_config

    # Initialize template context
    init_template_context

    if [[ "${DEBUG:-false}" == "true" ]]; then
        print_config
    fi
}

# Show test set menu
show_test_set_menu() {
    if [[ -n "$SELECTED_SET" ]]; then
        return 0
    fi

    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        return 0
    fi

    log_section "Select Test Set"

    echo "1) Set 1: Authorize (automatic capture) + Payment Sync"
    echo "2) Set 2: Authorize + Payment Sync + Refund + Refund Sync"
    echo "3) Set 3: Authorize (manual capture) + Capture"
    echo "4) Interactive mode (custom operations)"
    echo ""

    read -p "Enter your choice [1-4]: " SELECTED_SET
    echo ""

    if [[ "$SELECTED_SET" == "4" ]]; then
        INTERACTIVE_MODE=true
    fi
}

# Execute test set 1
execute_set1() {
    log_section "Executing Set 1: Authorize + Payment Sync"

    # Step 1: Authorize (automatic capture)
    local txn_id
    txn_id=$(call_authorize_auto)

    if [[ -z "$txn_id" ]]; then
        log_error "Set 1 failed: No transaction ID from authorize"
        return 1
    fi

    # Wait before next operation
    sleep 2

    # Step 2: Payment Sync
    call_payment_sync "$txn_id"

    log_success "Set 1 completed successfully"
}

# Execute test set 2
execute_set2() {
    log_section "Executing Set 2: Full Refund Flow"

    # Step 1: Authorize (automatic capture)
    local txn_id
    txn_id=$(call_authorize_auto)

    if [[ -z "$txn_id" ]]; then
        log_error "Set 2 failed: No transaction ID from authorize"
        return 1
    fi

    # Wait before next operation
    sleep 2

    # Step 2: Payment Sync
    call_payment_sync "$txn_id" || log_warning "Payment sync failed but continuing"

    # Wait before next operation
    sleep 2

    # Step 3: Refund
    local refund_id
    refund_id=$(call_refund "$txn_id")

    # Wait before next operation
    sleep 2

    # Step 4: Refund Sync (if refund ID available)
    if [[ -n "$refund_id" ]]; then
        call_refund_sync "$txn_id" "$refund_id" || log_warning "Refund sync failed"
    else
        log_warning "Skipping refund sync - no refund ID"
    fi

    log_success "Set 2 completed successfully"
}

# Execute test set 3
execute_set3() {
    log_section "Executing Set 3: Manual Capture Flow"

    # Step 1: Authorize (manual capture)
    local txn_id
    txn_id=$(call_authorize_manual)

    if [[ -z "$txn_id" ]]; then
        log_error "Set 3 failed: No transaction ID from authorize"
        return 1
    fi

    # Wait before next operation
    sleep 2

    # Step 2: Capture
    call_capture "$txn_id"

    log_success "Set 3 completed successfully"
}

# Interactive mode
run_interactive_mode() {
    log_section "Interactive Mode"

    local txn_id=""
    local refund_id=""

    while true; do
        echo ""
        echo "================================================"
        echo "Available Operations:"
        echo "================================================"
        echo "1) Authorize (Automatic Capture)"
        echo "2) Authorize (Manual Capture)"
        echo "3) Payment Sync"
        echo "4) Capture"
        echo "5) Refund"
        echo "6) Refund Sync"
        echo "0) Exit"
        echo ""

        read -p "Select operation: " op

        case $op in
            1)
                txn_id=$(call_authorize_auto)
                ;;
            2)
                txn_id=$(call_authorize_manual)
                ;;
            3)
                if [[ -z "$txn_id" ]]; then
                    read -p "Enter transaction ID: " txn_id
                fi
                call_payment_sync "$txn_id"
                ;;
            4)
                if [[ -z "$txn_id" ]]; then
                    read -p "Enter transaction ID: " txn_id
                fi
                call_capture "$txn_id"
                ;;
            5)
                if [[ -z "$txn_id" ]]; then
                    read -p "Enter transaction ID: " txn_id
                fi
                refund_id=$(call_refund "$txn_id")
                ;;
            6)
                if [[ -z "$txn_id" ]]; then
                    read -p "Enter transaction ID: " txn_id
                fi
                if [[ -z "$refund_id" ]]; then
                    read -p "Enter refund ID: " refund_id
                fi
                call_refund_sync "$txn_id" "$refund_id"
                ;;
            0)
                break
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
    done
}

# Execute the selected test set
execute_test_set() {
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        run_interactive_mode
        return 0
    fi

    case $SELECTED_SET in
        1)
            execute_set1
            ;;
        2)
            execute_set2
            ;;
        3)
            execute_set3
            ;;
        *)
            log_error "Invalid test set: $SELECTED_SET"
            exit 1
            ;;
    esac
}

# Generate final report
generate_report() {
    log_section "Test Execution Complete"

    echo "Connector: $CONNECTOR_NAME"
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        echo "Mode: Interactive"
    else
        echo "Test Set: $SELECTED_SET"
    fi
    echo ""

    if [[ -n "$LOG_FILE" ]]; then
        echo "Detailed logs saved to: $LOG_FILE"
    fi

    echo ""
    log_success "All operations completed"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    parse_arguments "$@"
    initialize
    show_test_set_menu
    execute_test_set
    generate_report
}

# Run main function
main "$@"
