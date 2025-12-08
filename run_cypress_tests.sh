#!/bin/bash

################################################################################
# Cypress Test Runner Script
#
# Description: Automates running Cypress tests for payment connectors with
#              flow-based test selection
#
# Mandatory Tests: 00000-CoreFlows, 00001-AccountCreate, 00002-CustomerCreate,
#                  00003-ConnectorCreate (always run)
#
# Optional Flows:
#   - 3ds_auto    -> Test 00004 (3DS Auto-Capture)
#   - 3ds_manual  -> Test 00006 (3DS Manual-Capture)
#   - void        -> Test 00007 (Void/Cancel Payment)
#   - refund      -> Test 00009 (Refund Payment)
#
# Usage: Press Enter when prompted to run ALL tests (mandatory + all flows)
#        Or enter specific flows: 3ds_auto,void,refund
#
# Features: Interactive prompts, flow selection, failure tracking, JSON reports
#
# JSON Report Format:
# {
#   "connector": "stripe",
#   "port": 8080,
#   "timestamp": "2025-12-08T10:30:45Z",
#   "selected_flows": "3ds_auto,void,refund",
#   "tests_run": "00000,00001,00002,00003,00004,00007,00009",
#   "total_tests_run": 7,
#   "failures": [
#     {
#       "test_number": "00001",
#       "test_file": "cypress/e2e/spec/Payment/00001-AccountCreate.cy.js",
#       "test_name": "should create account successfully",
#       "test_case": "Account Create > should create account successfully",
#       "error_message": "AssertionError: expected 500 to equal 200",
#       "failure_reason": "AssertionError",
#       "duration_ms": 1234
#     }
#   ],
#   "summary": {
#     "total_failures": 3,
#     "3ds_failures_excluded": 1,
#     "non_3ds_failures": 2
#   }
# }
################################################################################

set -e  # Exit on error (disabled for test execution)

# Color codes for better UX
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Variables
PORT=""
CONNECTOR=""
CREDS_PATH=""
SELECTED_FLOWS=""
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
CYPRESS_DIR=""
REPORT_DIR="${SCRIPT_DIR}/cypress-fails"
REPORT_FILE=""

# Flow to test number mapping function
# Compatible with bash 3.x and 4.x
get_test_number() {
    local flow=$1
    case "$flow" in
        "3ds_auto")
            echo "00004"
            ;;
        "3ds_manual")
            echo "00006"
            ;;
        "void")
            echo "00007"
            ;;
        "refund")
            echo "00009"
            ;;
        *)
            echo ""
            ;;
    esac
}

################################################################################
# Utility Functions
################################################################################

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

################################################################################
# Input Validation Functions
################################################################################

validate_port() {
    local port=$1
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    if [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        return 1
    fi
    return 0
}

validate_file_path() {
    local file_path=$1
    if [ ! -f "$file_path" ]; then
        print_error "File not found: $file_path"
        return 1
    fi
    if [ ! -r "$file_path" ]; then
        print_error "File is not readable: $file_path"
        return 1
    fi
    return 0
}

################################################################################
# Interactive Prompts
################################################################################

prompt_hyperswitch_status() {
    print_header "Hyperswitch Status Check"
    while true; do
        read -p "Is Hyperswitch already running? (y/n): " answer
        case $answer in
            [Yy]* )
                print_success "Proceeding with test execution"
                return 0
                ;;
            [Nn]* )
                print_info "Please start Hyperswitch before running this script"
                print_info "Example: cd ../hyperswitch && cargo run"
                exit 0
                ;;
            * )
                print_error "Please answer 'y' or 'n'"
                ;;
        esac
    done
}

prompt_port() {
    print_header "Port Configuration"
    while true; do
        read -p "Enter the port number Hyperswitch is running on (e.g., 8080): " PORT
        if validate_port "$PORT"; then
            print_success "Port set to: $PORT"
            return 0
        else
            print_error "Invalid port number. Please enter a valid port (1-65535)"
        fi
    done
}

prompt_connector() {
    print_header "Connector Selection"
    print_info "Examples: stripe, adyen, braintree, checkout, paypal, etc."
    while true; do
        read -p "Enter the connector name to test: " CONNECTOR
        if [ -n "$CONNECTOR" ]; then
            print_success "Connector set to: $CONNECTOR"
            return 0
        else
            print_error "Connector name cannot be empty"
        fi
    done
}

prompt_creds_path() {
    print_header "Credentials File Location"
    while true; do
        read -p "Enter the full path to creds.json file: " CREDS_PATH
        # Expand ~ to home directory
        CREDS_PATH="${CREDS_PATH/#\~/$HOME}"
        if validate_file_path "$CREDS_PATH"; then
            print_success "Credentials file validated: $CREDS_PATH"
            return 0
        else
            print_error "Please provide a valid file path"
            read -p "Try again? (y/n): " retry
            case $retry in
                [Nn]* ) exit 1 ;;
            esac
        fi
    done
}

prompt_flow_selection() {
    print_header "Flow Selection"
    print_info "Mandatory tests: 00000-CoreFlows, 00001-AccountCreate, 00002-CustomerCreate, 00003-ConnectorCreate"
    print_info ""
    print_info "Available optional flows:"
    print_info "  - 3ds_auto    (Test 00004: 3DS Auto-Capture)"
    print_info "  - 3ds_manual  (Test 00006: 3DS Manual-Capture)"
    print_info "  - void        (Test 00007: Void/Cancel Payment)"
    print_info "  - refund      (Test 00009: Refund Payment)"
    print_info ""
    print_info "Enter flows separated by commas (e.g., 3ds_auto,void,refund)"
    print_info "Or press Enter to run ALL tests (mandatory + all optional flows)"

    while true; do
        read -p "Select flows to run: " SELECTED_FLOWS

        # If empty, run all tests (mandatory + all optional flows)
        if [ -z "$SELECTED_FLOWS" ]; then
            SELECTED_FLOWS="3ds_auto,3ds_manual,void,refund"
            print_success "Running ALL tests (mandatory + all optional flows)"
            print_info "Tests to run:"
            print_info "  - Mandatory: 00000, 00001, 00002, 00003"
            print_info "  - 3ds_auto: 00004"
            print_info "  - 3ds_manual: 00006"
            print_info "  - void: 00007"
            print_info "  - refund: 00009"
            return 0
        fi

        # Validate flow names
        local valid=true
        local validated_flows=""

        # Convert to lowercase and remove spaces
        SELECTED_FLOWS=$(echo "$SELECTED_FLOWS" | tr '[:upper:]' '[:lower:]' | tr -d ' ')

        # Split by comma and validate each flow
        IFS=',' read -ra FLOWS <<< "$SELECTED_FLOWS"
        for flow in "${FLOWS[@]}"; do
            local test_num=$(get_test_number "$flow")
            if [[ -n "$test_num" ]]; then
                validated_flows="${validated_flows}${flow},"
            else
                print_error "Invalid flow name: $flow"
                valid=false
                break
            fi
        done

        if [ "$valid" = true ]; then
            # Remove trailing comma
            validated_flows="${validated_flows%,}"
            SELECTED_FLOWS="$validated_flows"

            print_success "Selected flows: $SELECTED_FLOWS"

            # Show which tests will run
            print_info "Tests to run:"
            print_info "  - Mandatory: 00000, 00001, 00002, 00003"
            IFS=',' read -ra FLOWS <<< "$SELECTED_FLOWS"
            for flow in "${FLOWS[@]}"; do
                local test_num=$(get_test_number "$flow")
                print_info "  - ${flow}: ${test_num}"
            done

            return 0
        else
            print_error "Please enter valid flow names separated by commas"
            print_info "Valid options: 3ds_auto, 3ds_manual, void, refund"
        fi
    done
}

################################################################################
# Setup Functions
################################################################################

setup_directories() {
    print_header "Setting Up Directories"

    # Create cypress-fails directory if it doesn't exist
    if [ ! -d "$REPORT_DIR" ]; then
        mkdir -p "$REPORT_DIR"
        print_success "Created report directory: $REPORT_DIR"
    else
        print_info "Report directory already exists: $REPORT_DIR"
    fi

    # Validate cypress-tests directory
    CYPRESS_DIR="${SCRIPT_DIR}/../../hyperswitch/cypress-tests"
    if [ ! -d "$CYPRESS_DIR" ]; then
        print_error "Cypress tests directory not found: $CYPRESS_DIR"
        print_error "Expected location: ../hyperswitch/cypress-tests"
        exit 1
    fi
    print_success "Cypress tests directory found: $CYPRESS_DIR"

    # Set report file path
    REPORT_FILE="${REPORT_DIR}/${CONNECTOR}_failures_${TIMESTAMP}.json"
}

setup_environment() {
    print_header "Configuring Environment Variables"

    export CYPRESS_UCS_ENABLED=true
    export CYPRESS_UCS_MODE=direct_bridge
    export CYPRESS_METHOD_FLOW="card_Authorize,card_Void,card_Capture,card_PSync,Execute,RSync"
    export CYPRESS_ADMINAPIKEY='test_admin'
    export CYPRESS_BASEURL="http://localhost:${PORT}"
    export CYPRESS_CONNECTOR_AUTH_FILE_PATH="${CREDS_PATH}"
    export CYPRESS_CONNECTOR="${CONNECTOR}"

    print_success "CYPRESS_UCS_ENABLED=true"
    print_success "CYPRESS_UCS_MODE=direct_bridge"
    print_success "CYPRESS_METHOD_FLOW=card_Authorize,card_Void,card_Capture,card_PSync,Execute,RSync"
    print_success "CYPRESS_ADMINAPIKEY=test_admin"
    print_success "CYPRESS_BASEURL=http://localhost:${PORT}"
    print_success "CYPRESS_CONNECTOR_AUTH_FILE_PATH=${CREDS_PATH}"
    print_success "CYPRESS_CONNECTOR=${CONNECTOR}"
}

################################################################################
# Test Execution Functions
################################################################################

run_tests() {
    print_header "Running Cypress Tests"

    cd "$CYPRESS_DIR" || exit 1
    print_info "Working directory: $(pwd)"

    # Build test spec pattern based on selected flows
    local test_numbers="00000,00001,00002,00003"  # Mandatory tests

    # Add optional flow tests
    if [ -n "$SELECTED_FLOWS" ]; then
        IFS=',' read -ra FLOWS <<< "$SELECTED_FLOWS"
        for flow in "${FLOWS[@]}"; do
            local test_num=$(get_test_number "$flow")
            if [[ -n "$test_num" ]]; then
                test_numbers="${test_numbers},${test_num}"
            fi
        done
    fi

    # Create the spec pattern
    local spec_pattern=$(echo "$test_numbers" | sed 's/,/,/g')
    local cypress_spec="cypress/e2e/spec/Payment/{${spec_pattern}}*.cy.js"

    print_info "Test pattern: {${spec_pattern}}"
    print_info "Running selected tests..."

    # Create temporary files for output
    local output_file=$(mktemp)
    local json_output=$(mktemp)

    # Initialize JSON report structure
    cat > "$json_output" <<EOF
{
  "connector": "$CONNECTOR",
  "port": $PORT,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "selected_flows": "$SELECTED_FLOWS",
  "tests_run": "${test_numbers}",
  "total_tests_run": 0,
  "failures": [],
  "summary": {
    "total_failures": 0,
    "3ds_failures_excluded": 0,
    "non_3ds_failures": 0
  }
}
EOF

    # Run tests (allow failures)
    set +e
    npm run cypress:ci -- --spec "$cypress_spec" 2>&1 | tee -a "$output_file"
    local test_exit_code=$?
    set -e

    if [ $test_exit_code -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_info "Some tests failed - check the report for details"
    fi

    print_success "Test execution complete"

    # Parse test results
    parse_test_results "$output_file" "$json_output"

    # Save final report
    cp "$json_output" "$REPORT_FILE"

    # Save raw console output for reference
    local raw_output_file="${REPORT_DIR}/${CONNECTOR}_console_output_${TIMESTAMP}.txt"
    cp "$output_file" "$raw_output_file"
    print_info "Raw console output saved to: $raw_output_file"

    # Add raw output path to JSON report
    if command -v jq &> /dev/null; then
        local temp_json=$(mktemp)
        jq --arg raw_output "$raw_output_file" \
           '.raw_console_output = $raw_output' \
           "$REPORT_FILE" > "$temp_json" && mv "$temp_json" "$REPORT_FILE"
    fi

    # Cleanup temporary files
    rm -f "$output_file" "$json_output"

    # Return to original directory
    cd "$SCRIPT_DIR" || exit 1
}

################################################################################
# Result Parsing Functions
################################################################################

is_3ds_test() {
    local test_name=$1
    # Check if test name contains 3DS-related keywords
    if echo "$test_name" | grep -iE "(3ds|three.?ds|threeds)" > /dev/null; then
        return 0  # Is a 3DS test
    fi
    return 1  # Not a 3DS test
}

parse_test_results() {
    local output_file=$1
    local json_output=$2

    print_header "Parsing Test Results"

    # Try to parse Cypress JSON reporter output if available (most accurate)
    local cypress_report="${CYPRESS_DIR}/cypress/reports/${CONNECTOR}/json/${CONNECTOR}_report.json"
    if [ -f "$cypress_report" ]; then
        print_info "Found Cypress JSON report, parsing detailed results..."
        parse_cypress_json_report "$cypress_report" "$json_output"
    else
        print_info "Cypress JSON report not found, parsing console output..."
        parse_console_output "$output_file" "$json_output"
    fi

    print_success "Parsing complete"
}

parse_console_output() {
    local output_file=$1
    local json_output=$2

    print_info "Parsing Cypress console output for failures..."
    print_info "Note: For detailed error messages, check the console output"
    print_info "      Or configure Cypress JSON reporter for better reporting"

    # Extract basic statistics from Cypress output
    local total_tests=$(grep -oE "[0-9]+ passing" "$output_file" | head -1 | grep -oE "[0-9]+" || echo "0")
    local failing_count=$(grep -oE "[0-9]+ failing" "$output_file" | head -1 | grep -oE "[0-9]+" || echo "0")

    # Try to find the "Failing:" section and extract failures
    local failures_array="[]"
    local in_failures_section=false
    local current_suite=""
    local current_test=""
    local current_error_type=""
    local current_error_msg=""
    local collecting_error=false
    local line_count=0
    local threeDS_failures=0
    local non_3ds_failures=0

    # Function to save a failure entry
    save_failure() {
        local full_test="${current_suite} > ${current_test}"

        # Check if 3DS test
        if is_3ds_test "$full_test"; then
            threeDS_failures=$((threeDS_failures + 1))
            return
        fi

        non_3ds_failures=$((non_3ds_failures + 1))

        if command -v jq &> /dev/null; then
            local temp_json=$(mktemp)
            echo "$failures_array" | jq --arg suite "$current_suite" \
                                         --arg test "$current_test" \
                                         --arg full "$full_test" \
                                         --arg err_type "$current_error_type" \
                                         --arg err_msg "$current_error_msg" \
                                         '. += [{
                                           test_number: "unknown",
                                           test_name: $test,
                                           test_suite: $suite,
                                           test_case: $full,
                                           error_message: $err_msg,
                                           failure_reason: $err_type
                                         }]' > "$temp_json" 2>/dev/null
            failures_array=$(cat "$temp_json")
            rm -f "$temp_json"
            print_error "Test failed: $full_test"
        fi
    }

    while IFS= read -r line; do
        # Detect start of failures section
        if echo "$line" | grep -q "^  Failing:$\|^  ([0-9]+ of [0-9]+ failed)"; then
            in_failures_section=true
            continue
        fi

        # Skip if not in failures section
        if [ "$in_failures_section" = false ]; then
            continue
        fi

        # Detect end of failures section (usually a blank line followed by screenshots/videos section)
        if echo "$line" | grep -qE "^  \(Screenshots\)|^  \(Videos\)|^  \(Run Finished\)|^$"; then
            # Save last failure if exists
            if [ -n "$current_test" ] && [ -n "$current_error_msg" ]; then
                save_failure
            fi
            break
        fi

        # Match numbered failure line: "  1) Suite Name"
        if echo "$line" | grep -qE "^  [0-9]+\) "; then
            # Save previous failure if exists
            if [ -n "$current_test" ] && [ -n "$current_error_msg" ]; then
                save_failure
            fi

            # Extract suite name (line with number)
            current_suite=$(echo "$line" | sed -E 's/^  [0-9]+\) //')
            current_test=""
            current_error_type=""
            current_error_msg=""
            collecting_error=false
            continue
        fi

        # Match indented test name: "     test-name:"
        if echo "$line" | grep -qE "^     [a-zA-Z0-9_-]+:$"; then
            current_test=$(echo "$line" | sed -E 's/^     //' | sed 's/:$//')
            collecting_error=true
            continue
        fi

        # Match error type: "     ErrorType: message"
        if [ "$collecting_error" = true ] && echo "$line" | grep -qE "^     (AssertionError|CypressError|Error|TypeError|ReferenceError|TimeoutError)"; then
            current_error_type=$(echo "$line" | sed -E 's/^     ([^:]+):.*/\1/')
            current_error_msg=$(echo "$line" | sed -E 's/^     [^:]+: //')
            continue
        fi

        # Continue collecting multiline error message
        if [ "$collecting_error" = true ] && [ -n "$current_error_msg" ] && echo "$line" | grep -qE "^     [^at]"; then
            local extra_msg=$(echo "$line" | sed -E 's/^     //')
            current_error_msg="${current_error_msg} ${extra_msg}"
        fi

    done < "$output_file"

    # Update JSON report with failures
    if command -v jq &> /dev/null; then
        local temp_json=$(mktemp)
        cat "$json_output" | jq --arg total "$total_tests" \
                                 --arg failures "$failing_count" \
                                 --arg threeDS "$threeDS_failures" \
                                 --arg non3ds "$non_3ds_failures" \
                                 --argjson fail_array "$failures_array" \
                                 '.total_tests_run = ($total | tonumber) |
                                  .failures = $fail_array |
                                  .summary.total_failures = ($failures | tonumber) |
                                  .summary."3ds_failures_excluded" = ($threeDS | tonumber) |
                                  .summary.non_3ds_failures = ($non3ds | tonumber)' \
                                 > "$temp_json" 2>/dev/null && mv "$temp_json" "$json_output" || true
    fi

    print_info "Extracted $non_3ds_failures non-3DS failures (excluded $threeDS_failures 3DS failures)"
}

parse_cypress_json_report() {
    local cypress_report=$1
    local json_output=$2

    # Check if jq is available for JSON parsing
    if ! command -v jq &> /dev/null; then
        print_info "jq not found, skipping detailed JSON parsing"
        return
    fi

    # Parse Cypress JSON report and extract failures
    # Filter out 3DS tests and extract detailed error information
    local temp_json=$(mktemp)

    jq --arg connector "$CONNECTOR" \
       --arg port "$PORT" \
       --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
       '{
         connector: $connector,
         port: ($port | tonumber),
         timestamp: $timestamp,
         total_tests_run: (.stats.tests // 0),
         failures: [
           .results[]? as $result |
           $result.suites[]?.tests[]? |
           select(.fail == true) |
           select(.title | test("3ds|3DS|ThreeDS|three.ds"; "i") | not) |
           {
             test_number: (($result.file // "") | capture("(?<num>[0-9]{5})") | .num // "unknown"),
             test_file: ($result.file // "unknown"),
             test_name: .title,
             test_case: .fullTitle,
             error_message: (.err.message // (.err.estack // "Unknown error")),
             failure_reason: (.err.name // "Test failure"),
             duration_ms: (.duration // 0)
           }
         ],
         summary: {
           total_failures: ([.results[]?.suites[]?.tests[]? | select(.fail == true)] | length),
           "3ds_failures_excluded": ([.results[]?.suites[]?.tests[]? | select(.fail == true) | select(.title | test("3ds|3DS|ThreeDS|three.ds"; "i"))] | length),
           non_3ds_failures: ([.results[]?.suites[]?.tests[]? | select(.fail == true) | select(.title | test("3ds|3DS|ThreeDS|three.ds"; "i") | not)] | length)
         }
       }' "$cypress_report" > "$temp_json" 2>/dev/null && mv "$temp_json" "$json_output" || true
}

################################################################################
# Main Summary
################################################################################

print_summary() {
    print_header "Test Execution Complete!"

    echo -e "${BLUE}Connector:${NC} $CONNECTOR"
    echo -e "${BLUE}Port:${NC} $PORT"

    # Show selected flows
    if [ -n "$SELECTED_FLOWS" ]; then
        echo -e "${BLUE}Selected Flows:${NC} $SELECTED_FLOWS"
    else
        echo -e "${BLUE}Selected Flows:${NC} None (mandatory tests only)"
    fi

    # Parse summary from JSON if jq is available
    if command -v jq &> /dev/null && [ -f "$REPORT_FILE" ]; then
        local tests_run=$(jq -r '.tests_run' "$REPORT_FILE" 2>/dev/null || echo "00000,00001,00002,00003")
        local total_tests=$(jq -r '.total_tests_run' "$REPORT_FILE" 2>/dev/null || echo "0")
        local total_failures=$(jq -r '.summary.total_failures' "$REPORT_FILE" 2>/dev/null || echo "0")
        local threeDS_excluded=$(jq -r '.summary."3ds_failures_excluded"' "$REPORT_FILE" 2>/dev/null || echo "0")
        local non_3ds_failures=$(jq -r '.summary.non_3ds_failures' "$REPORT_FILE" 2>/dev/null || echo "0")

        echo -e "${BLUE}Tests Run:${NC} $tests_run"
        echo -e "${BLUE}Total Tests:${NC} $total_tests"
        echo -e "${BLUE}Total Failures:${NC} $total_failures"
        echo -e "${BLUE}3DS Failures Excluded:${NC} $threeDS_excluded"
        echo -e "${BLUE}Non-3DS Failures Reported:${NC} $non_3ds_failures"
    fi

    echo -e "${BLUE}Report saved to:${NC} $REPORT_FILE"

    print_info "View the detailed JSON report at: $REPORT_FILE"
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "Cypress Test Runner for Connectors"

    # Interactive prompts
    prompt_hyperswitch_status
    prompt_port
    prompt_connector
    prompt_creds_path
    prompt_flow_selection

    # Setup
    setup_directories
    setup_environment

    # Run tests
    run_tests

    # Show summary
    print_summary

    print_success "\nAll done! Happy testing! 🚀"
}

# Run main function
main
