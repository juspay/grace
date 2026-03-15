#!/bin/bash

# =============================================================================
# Hyperswitch Connector Generator v2.0
# =============================================================================
# A robust, maintainable script for generating connector boilerplate code
#
# Usage: ./add_connector.sh <connector_name> <base_url> [options]
#
# Features:
# - Modular design for easy maintenance
# - Comprehensive error handling and validation
# - Self-documenting configuration
# - Future-proof architecture
# =============================================================================

set -euo pipefail  # Strict error handling

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================
# All configurable values are centralized here for easy maintenance

# Script metadata
readonly SCRIPT_VERSION="2.1.0"
readonly SCRIPT_NAME="Hyperswitch Connector Generator"

# Paths configuration
# Use the script's location to derive paths reliably, regardless of the
# directory the user invokes the script from. BASH_SOURCE is preferred;
# $0 is used as a fallback (e.g., when sourced).
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# ROOT_DIR is the Hyperswitch repo root (parent of the grace/ directory).
readonly ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly TEMPLATE_DIR="$SCRIPT_DIR/template-generation"
readonly BACKEND_DIR="$ROOT_DIR/backend"
readonly CONFIG_DIR="$ROOT_DIR/config"

# File paths
readonly CONNECTOR_TYPES_FILE="$BACKEND_DIR/interfaces/src/connector_types.rs"
readonly DOMAIN_TYPES_FILE="$BACKEND_DIR/domain_types/src/connector_types.rs"
readonly DOMAIN_TYPES_TYPES_FILE="$BACKEND_DIR/domain_types/src/types.rs"
readonly INTEGRATION_TYPES_FILE="$BACKEND_DIR/connector-integration/src/types.rs"
readonly CONNECTORS_MODULE_FILE="$BACKEND_DIR/connector-integration/src/connectors.rs"
readonly PROTO_FILE="$BACKEND_DIR/grpc-api-types/proto/payment.proto"
readonly ROUTER_DATA_FILE="$BACKEND_DIR/domain_types/src/router_data.rs"
readonly CONFIG_FILE="$CONFIG_DIR/development.toml"
readonly SANDBOX_CONFIG_FILE="$CONFIG_DIR/sandbox.toml"
readonly PRODUCTION_CONFIG_FILE="$CONFIG_DIR/production.toml"

# Template files
readonly CONNECTOR_TEMPLATE="$TEMPLATE_DIR/connector.rs.template"
readonly TRANSFORMERS_TEMPLATE="$TEMPLATE_DIR/transformers.rs.template"
readonly MACRO_TEMPLATE="$TEMPLATE_DIR/connector_macros.rs.template"

# =============================================================================
# DYNAMIC FLOW DETECTION
# =============================================================================
# This script automatically detects all available flows from connector_types.rs
# When new flows are added to the ConnectorServiceTrait, they will be automatically
# included in new connector templates without any manual configuration needed.

# Global array to store detected flows
AVAILABLE_FLOWS=()

# =============================================================================
# FLOW DETECTION FUNCTIONS
# =============================================================================

detect_flows_from_connector_service_trait() {
    log_step "Auto-detecting flows from ConnectorServiceTrait"

    local connector_types_file="$CONNECTOR_TYPES_FILE"
    if [[ ! -f "$connector_types_file" ]]; then
        fatal_error "Cannot find connector_types.rs at: $connector_types_file"
    fi

    # Extract all trait names from ConnectorServiceTrait definition
    # This looks for lines like "+ PaymentAuthorizeV2<T>" or "+ PaymentSyncV2"
    local detected_flows
    detected_flows=$(grep -A 50 "pub trait ConnectorServiceTrait" "$connector_types_file" | \
                    grep -E "^[[:space:]]*\+[[:space:]]*[A-Z][A-Za-z0-9]*" | \
                    sed -E 's/^[[:space:]]*\+[[:space:]]*([A-Z][A-Za-z0-9]*).*/\1/' | \
                    grep -v "ConnectorCommon" | \
                    sort -u) || true

    if [[ -z "$detected_flows" ]]; then
        fatal_error "No flows detected from ConnectorServiceTrait"
    fi

    # Convert to array
    while IFS= read -r flow; do
        if [[ -n "$flow" ]]; then
            AVAILABLE_FLOWS+=("$flow")
        fi
    done <<< "$detected_flows"

    log_success "Detected ${#AVAILABLE_FLOWS[@]} flows from ConnectorServiceTrait"
    log_debug "Detected flows: ${AVAILABLE_FLOWS[*]}"
}

# Function to get basic description for any flow
get_flow_description() {
    case "$1" in
        *"Authorize"*) echo "Process payment authorization" ;;
        *"Sync"*) echo "Synchronize status" ;;
        *"Void"*) echo "Void/cancel operations" ;;
        *"Capture"*) echo "Capture authorized payments" ;;
        *"Refund"*) echo "Process refunds" ;;
        *"Mandate"*) echo "Setup recurring payment mandates" ;;
        *"Repeat"*) echo "Process recurring payments" ;;
        *"Order"*) echo "Create payment orders" ;;
        *"Token"*) echo "Handle tokenization" ;;
        *"Dispute"*) echo "Handle payment disputes" ;;
        *"Evidence"*) echo "Submit dispute evidence" ;;
        *"Webhook"*) echo "Handle incoming webhooks" ;;
        *"Validation"*) echo "Basic validation functionality" ;;
        *"Access"*) echo "Handle access tokens" ;;
        *"Session"*) echo "Handle session tokens" ;;
        *"Authenticate"*) echo "Handle authentication" ;;
        *) echo "Payment processing flow" ;;
    esac
}

# =============================================================================
# FLOW METADATA EXTRACTION FUNCTIONS
# =============================================================================
# These functions parse connector_types.rs to extract metadata about each flow
# This metadata is used to generate trait implementations dynamically

# Global indexed arrays to store flow metadata (Bash 3.x compatible)
FLOW_NAMES=()                # All flow trait names
FLOW_GENERICS=()             # "true" or "false" for each flow
FLOW_INTEGRATION_PARAMS=()   # ConnectorIntegrationV2 params for each flow

# Helper function to find index of a flow in FLOW_NAMES array
get_flow_index() {
    local flow_name="$1"
    local i
    for i in "${!FLOW_NAMES[@]}"; do
        if [[ "${FLOW_NAMES[$i]}" == "$flow_name" ]]; then
            echo "$i"
            return 0
        fi
    done
    echo "-1"
}

# Extract metadata for a specific flow trait from connector_types.rs
extract_flow_metadata() {
    local flow_trait="$1"
    local connector_types_file="$CONNECTOR_TYPES_FILE"
    
    log_debug "Extracting metadata for flow: $flow_trait"
    
    # Add flow to the names array
    FLOW_NAMES+=("$flow_trait")
    local flow_idx=$((${#FLOW_NAMES[@]} - 1))
    
    # Check if trait has generics by looking for <T in trait definition
    if grep -A 1 "pub trait $flow_trait" "$connector_types_file" | grep -q "<T"; then
        FLOW_GENERICS[$flow_idx]="true"
        log_debug "  └─ Has generics: true"
    else
        FLOW_GENERICS[$flow_idx]="false"
        log_debug "  └─ Has generics: false"
    fi
    
    # Extract ConnectorIntegrationV2 type parameters
    # First check if this trait even has ConnectorIntegrationV2 to avoid grep hanging
    local trait_def
    trait_def=$(sed -n "/pub trait $flow_trait/,/^}/p" "$connector_types_file")
    
    if ! echo "$trait_def" | grep -q "ConnectorIntegrationV2"; then
        FLOW_INTEGRATION_PARAMS[$flow_idx]=""
        log_debug "  └─ No ConnectorIntegrationV2 found (webhook/validation/redirect trait)"
        return 0
    fi
    
    
    # Extract the ConnectorIntegrationV2 type parameters
    # Join all lines first to handle multi-line definitions, then extract content
    # between ConnectorIntegrationV2< and > (followed by whitespace/brace)
    local integration_types
    integration_types=$(echo "$trait_def" | \
                       tr '\n' ' ' | \
                       sed 's/.*ConnectorIntegrationV2<//;s/>[[:space:]]*{.*//' | \
                       sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/[[:space:]][[:space:]]*/ /g')
    
    if [[ -n "$integration_types" ]]; then
        FLOW_INTEGRATION_PARAMS[$flow_idx]="$integration_types"
        log_debug "  └─ Integration types: $integration_types"
    else
        FLOW_INTEGRATION_PARAMS[$flow_idx]=""
        log_debug "  └─ No integration types extracted"
    fi
}

# Extract metadata for all detected flows
extract_all_flow_metadata() {
    log_step "Extracting flow metadata from connector_types.rs"
    
    # Clear arrays first
    FLOW_NAMES=()
    FLOW_GENERICS=()
    FLOW_INTEGRATION_PARAMS=()
    
    local flow
    for flow in "${AVAILABLE_FLOWS[@]}"; do
        extract_flow_metadata "$flow"
    done
    
    log_success "Extracted metadata for ${#FLOW_NAMES[@]} flows"
}

# Generate trait implementation code for a specific flow
generate_trait_impl() {
    local flow_trait="$1"
    local flow_idx=$(get_flow_index "$flow_trait")
    
    if [[ $flow_idx -lt 0 ]]; then
        log_debug "Flow $flow_trait not found in metadata"
        return
    fi
    
    local has_generics="${FLOW_GENERICS[$flow_idx]}"
    
    if [[ "$has_generics" == "true" ]]; then
        cat <<EOF
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    connector_types::${flow_trait}<T> for ${NAME_PASCAL}<T>
{
}

EOF
    else
        cat <<EOF
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    connector_types::${flow_trait} for ${NAME_PASCAL}<T>
{
}

EOF
    fi
}

# Generate ConnectorIntegrationV2 implementation for a specific flow
generate_connector_integration_impl() {
    local flow_trait="$1"
    local flow_idx=$(get_flow_index "$flow_trait")
    
    if [[ $flow_idx -lt 0 ]]; then
        log_debug "Flow $flow_trait not found in metadata"
        return
    fi
    
    local integration_types="${FLOW_INTEGRATION_PARAMS[$flow_idx]}"
    
    # Trim whitespace and check if empty or malformed
    integration_types=$(echo "$integration_types" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Skip if no integration types or malformed (e.g., IncomingWebhook, ValidationTrait)
    if [[ -z "$integration_types" ]] || [[ "$integration_types" == "{" ]] || [[  "$integration_types" == "}" ]]; then
        log_debug "Skipping ConnectorIntegrationV2 for $flow_trait (no integration types)"
        return
    fi
    
    # Parse the integration types
    local flow_type data_types
    flow_type=$(echo "$integration_types" | cut -d',' -f1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    data_types=$(echo "$integration_types" | cut -d',' -f2- | sed 's/^[[:space:]]*//')
    
    # Additional validation - skip if flow_type is empty or invalid
    if [[ -z "$flow_type" ]] || [[ "$flow_type" == "{" ]] || [[ "$flow_type" == "}"  ]]; then
        log_debug "Skipping ConnectorIntegrationV2 for $flow_trait (invalid flow type)"
        return
    fi

    # Skip core flows - they get macro-based implementations via create_all_prerequisites!
    # and macro_connector_implementation! instead of empty impls
    case "$flow_type" in
        "connector_flow::Authorize"|"connector_flow::PSync"|"connector_flow::Capture"|"connector_flow::Void"|"connector_flow::Refund"|"connector_flow::RSync")
            log_debug "Skipping ConnectorIntegrationV2 for $flow_trait (core flow, handled by macros)"
            return
            ;;
    esac
    
    cat <<EOF
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    ConnectorIntegrationV2<${flow_type}, ${data_types}>
    for ${NAME_PASCAL}<T>
{
}

EOF
}

# Generate SourceVerification implementation for flows that need it

# =============================================================================
# CONNECTOR SPECIFIC CONFIG REGISTRATION
# =============================================================================
# Registers the new connector in ConnectorSpecificConfig (router_data.rs)
# and field-probe (main.rs). Defaults to single api_key (HeaderKey) pattern.
# For connectors requiring different auth, manually adjust after generation.

readonly ROUTER_DATA_FILE="$BACKEND_DIR/domain_types/src/router_data.rs"
readonly FIELD_PROBE_FILE="$BACKEND_DIR/field-probe/src/main.rs"

register_connector_specific_config() {
    log_step "Registering ConnectorSpecificConfig for $NAME_PASCAL"

    # Check if already registered
    if grep -q "ConnectorSpecificConfig::${NAME_PASCAL}" "$ROUTER_DATA_FILE" 2>/dev/null; then
        log_warning "ConnectorSpecificConfig::${NAME_PASCAL} already registered, skipping"
        return 0
    fi

    # 1. Add enum variant after "pub enum ConnectorSpecificConfig {"
    log_debug "Adding ConnectorSpecificConfig enum variant"
    awk -v name="$NAME_PASCAL" '
        /pub enum ConnectorSpecificConfig \{/ {
            print
            print "    " name " {"
            print "        api_key: Secret<String>,"
            print "        base_url: Option<String>,"
            print "    },"
            next
        }
        { print }
    ' "$ROUTER_DATA_FILE" > "${ROUTER_DATA_FILE}.tmp" && mv "${ROUTER_DATA_FILE}.tmp" "$ROUTER_DATA_FILE"

    # 2. Add to extract_base_url! macro (insert after first "Stripe { api_key }," inside extract_base_url!)
    log_debug "Adding to extract_base_url! macro"
    # Use awk to insert only in the extract_base_url! context (first occurrence of Stripe { api_key })
    awk -v name="$NAME_PASCAL" '
        /extract_base_url!\(/ { in_extract=1 }
        in_extract && /Stripe \{ api_key \},/ {
            print
            print "            " name " { api_key },"
            in_extract=0
            next
        }
        { print }
    ' "$ROUTER_DATA_FILE" > "${ROUTER_DATA_FILE}.tmp" && mv "${ROUTER_DATA_FILE}.tmp" "$ROUTER_DATA_FILE"

    # 3. Add to connector_key! invocation (insert after first "Stripe { api_key }," inside connector_key!)
    log_debug "Adding to connector_key! macro"
    awk -v name="$NAME_PASCAL" '
        /connector_key!\(/ { in_connkey=1 }
        in_connkey && /Stripe \{ api_key \},/ {
            print
            print "                " name " { api_key },"
            in_connkey=0
            next
        }
        { print }
    ' "$ROUTER_DATA_FILE" > "${ROUTER_DATA_FILE}.tmp" && mv "${ROUTER_DATA_FILE}.tmp" "$ROUTER_DATA_FILE"

    # 4. Add ConnectorAuthType ForeignTryFrom match arm (insert before Stripe entry)
    log_debug "Adding ForeignTryFrom match arm"
    awk -v name="$NAME_PASCAL" '
        /ConnectorEnum::Stripe => match auth \{/ && !done_foreign {
            print "            ConnectorEnum::" name " => match auth {"
            print "                ConnectorAuthType::HeaderKey { api_key } => Ok(Self::" name " {"
            print "                    api_key: api_key.clone(),"
            print "                    base_url: None,"
            print "                }),"
            print "                _ => Err(err().into()),"
            print "            },"
            done_foreign=1
        }
        { print }
    ' "$ROUTER_DATA_FILE" > "${ROUTER_DATA_FILE}.tmp" && mv "${ROUTER_DATA_FILE}.tmp" "$ROUTER_DATA_FILE"

    # 5. Add to dummy_auth() in field-probe
    if [[ -f "$FIELD_PROBE_FILE" ]]; then
        log_debug "Adding to dummy_auth() in field-probe"
        awk -v name="$NAME_PASCAL" '
            /ConnectorEnum::Stripe => ConnectorSpecificConfig::Stripe \{/ && !done_dummy {
                print "        ConnectorEnum::" name " => ConnectorSpecificConfig::" name " {"
                print "            api_key: k(),"
                print "            base_url: None,"
                print "        },"
                done_dummy=1
            }
            { print }
        ' "$FIELD_PROBE_FILE" > "${FIELD_PROBE_FILE}.tmp" && mv "${FIELD_PROBE_FILE}.tmp" "$FIELD_PROBE_FILE"

        # 6. Add to all_connectors() if it exists
        if grep -q "fn all_connectors" "$FIELD_PROBE_FILE" 2>/dev/null; then
            log_debug "Adding to all_connectors()"
            awk -v name="$NAME_PASCAL" '
                /ConnectorEnum::Stripe,/ && !done_all {
                    print
                    print "        ConnectorEnum::" name ","
                    done_all=1
                    next
                }
                { print }
            ' "$FIELD_PROBE_FILE" > "${FIELD_PROBE_FILE}.tmp" && mv "${FIELD_PROBE_FILE}.tmp" "$FIELD_PROBE_FILE"
        fi
    fi

    log_success "Registered ConnectorSpecificConfig for $NAME_PASCAL (default: HeaderKey/api_key)"
    log_info "If this connector uses different auth (BodyKey, SignatureKey, etc.),"
    log_info "manually update the ConnectorSpecificConfig variant and ForeignTryFrom match arm."
}

# =============================================================================

readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_RESET='\033[0m'

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# User inputs
CONNECTOR_NAME=""
BASE_URL=""
FORCE_MODE=false
YES_MODE=false

# Auto-detected flows (populated by detect_flows_from_connector_service_trait)
SELECTED_FLOWS=()

# Generated values
NAME_SNAKE=""
NAME_PASCAL=""
NAME_UPPER=""
ENUM_ORDINAL=""
BACKUP_DIR=""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Logging functions with consistent formatting
log_info() {
    echo -e "${COLOR_BLUE}ℹ️  INFO: $1${COLOR_RESET}"
}

log_success() {
    echo -e "${COLOR_GREEN}✅ SUCCESS: $1${COLOR_RESET}"
}

log_warning() {
    echo -e "${COLOR_YELLOW}⚠️  WARNING: $1${COLOR_RESET}"
}

log_error() {
    echo -e "${COLOR_RED}❌ ERROR: $1${COLOR_RESET}"
}

log_step() {
    echo -e "${COLOR_PURPLE}🔧 STEP: $1${COLOR_RESET}"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${COLOR_CYAN}🐛 DEBUG: $1${COLOR_RESET}"
    fi
}

# Error handling with context
fatal_error() {
    log_error "$1"
    log_error "Script execution terminated."
    exit 1
}

# Validation helpers
validate_file_exists() {
    local file="$1"
    local description="$2"

    if [[ ! -f "$file" ]]; then
        fatal_error "$description not found at: $file"
    fi
    log_debug "Validated file exists: $file"
}

validate_directory_exists() {
    local dir="$1"
    local description="$2"

    if [[ ! -d "$dir" ]]; then
        fatal_error "$description not found at: $dir"
    fi
    log_debug "Validated directory exists: $dir"
}

# String manipulation utilities
to_snake_case() {
    echo "$1" | sed 's/\([A-Z]\)/_\1/g' | sed 's/^_//' | tr '[:upper:]' '[:lower:]'
}

to_pascal_case() {
    # Convert snake_case to PascalCase
    echo "$1" | awk -F'_' '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))} 1' OFS=''
}

to_upper_case() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
}

# Portable sed -i wrapper (macOS sed requires '' after -i, GNU does not)
sed_i() {
    if sed --version 2>/dev/null | grep -q "GNU"; then
        sed -i "$@"
    else
        sed -i '' "$@"
    fi
}

# =============================================================================
# HELP AND USAGE FUNCTIONS
# =============================================================================

show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
}

show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION

USAGE:
    $0 <connector_name> <base_url> [OPTIONS]

ARGUMENTS:
    connector_name    Name of the connector (snake_case, e.g., 'my_connector')
    base_url         Base URL for the connector API

OPTIONS:
    --list-flows     Show auto-detected flows from codebase
    --force          Ignore git status and force creation
    -y, --yes        Skip confirmation prompts
    --debug          Enable debug logging
    -h, --help       Show this help message
    -v, --version    Show version information

EXAMPLES:
    # Full scaffold -- create connector with all flows
    $0 stripe https://api.stripe.com/v1

    # Full scaffold with auto-confirmation
    $0 example https://api.example.com --force -y

    # List auto-detected flows
    $0 --list-flows

WORKFLOW:
    1. Auto-detects flows from connector_types.rs
    2. Validates environment and inputs
    3. Generates connector boilerplate with all flows
    4. Updates integration files
    5. Validates compilation
    6. Provides next steps guidance

For more information, visit: https://github.com/juspay/hyperswitch
EOF
}

show_available_flows() {
    echo "Auto-Detected Flows from ConnectorServiceTrait:"
    echo "==============================================="
    echo

    # Auto-detect flows first
    detect_flows_from_connector_service_trait

    local flow
    for flow in "${AVAILABLE_FLOWS[@]}"; do
        local description=$(get_flow_description "$flow")
        printf "  %-25s %s\n" "$flow" "$description"
    done

    echo
    echo "NOTE: All flows are automatically included when creating a connector."
    echo "No manual selection is required - the script is future-proof!"
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

parse_arguments() {
    log_debug "Parsing arguments: $*"

    # Handle special cases first
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi

    if [[ $# -eq 1 ]]; then
        case "$1" in
            --list-flows)
                show_available_flows
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            *)
                log_error "Missing required arguments."
                show_help
                exit 1
                ;;
        esac
    fi

    # First positional argument is always the connector name
    CONNECTOR_NAME="$1"
    shift

    # Scan remaining args for flags and positional args
    local remaining_positional=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                FORCE_MODE=true
                shift
                ;;
            -y|--yes)
                YES_MODE=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --list-flows)
                show_available_flows
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            -*)
                fatal_error "Unknown option: $1"
                ;;
            *)
                remaining_positional+=("$1")
                shift
                ;;
        esac
    done

    # BASE_URL is required
    if [[ ${#remaining_positional[@]} -lt 1 ]]; then
        log_error "Missing required argument: base_url"
        show_help
        exit 1
    fi
    BASE_URL="${remaining_positional[0]}"

    log_debug "Arguments parsed successfully"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

validate_environment() {
    log_step "Validating environment"

    # Check if we're in the correct directory
    validate_directory_exists "$TEMPLATE_DIR" "Template directory"
    validate_directory_exists "$BACKEND_DIR" "Backend directory"

    # Check required template files
    validate_file_exists "$CONNECTOR_TEMPLATE" "Connector template"
    validate_file_exists "$TRANSFORMERS_TEMPLATE" "Transformers template"
    validate_file_exists "$MACRO_TEMPLATE" "Macro template"

    # Check target files that will be modified
    validate_file_exists "$CONNECTOR_TYPES_FILE" "Connector types file"
    validate_file_exists "$DOMAIN_TYPES_FILE" "Domain types file"
    validate_file_exists "$INTEGRATION_TYPES_FILE" "Integration types file"
    validate_file_exists "$CONNECTORS_MODULE_FILE" "Connectors module file"
    validate_file_exists "$PROTO_FILE" "Protocol buffer file"

    # Check git status unless forced
    if [[ "$FORCE_MODE" == "false" ]] && command -v git >/dev/null 2>&1; then
        if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
            fatal_error "Git working directory is not clean. Use --force to proceed anyway."
        fi
    fi

    log_success "Environment validation passed"
}

validate_inputs() {
    log_step "Validating inputs"

    # Validate connector name
    if [[ ! "$CONNECTOR_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
        fatal_error "Connector name must start with a letter and contain only lowercase letters, numbers, and underscores"
    fi

    # Validate base URL
    if [[ ! "$BASE_URL" =~ ^https?://.+ ]]; then
        fatal_error "Base URL must be a valid HTTP/HTTPS URL"
    fi

    # Reject URLs containing characters that could cause sed injection or
    # shell expansion issues. Only allow URL-safe characters.
    if [[ "$BASE_URL" =~ [^a-zA-Z0-9/:._~%?#@!\$\&\'*+,\;=\[\]-] ]]; then
        fatal_error "Base URL contains invalid characters. Only standard URL characters are allowed."
    fi

    # Generate name variants
    NAME_SNAKE="$CONNECTOR_NAME"
    NAME_PASCAL=$(to_pascal_case "$CONNECTOR_NAME")
    NAME_UPPER=$(to_upper_case "$CONNECTOR_NAME")

    # Auto-detect flows from codebase
    detect_flows_from_connector_service_trait

    # Always use all detected flows (no manual selection)
    SELECTED_FLOWS=("${AVAILABLE_FLOWS[@]}")

    log_success "Input validation passed"
    log_info "Configuration: $NAME_SNAKE → $NAME_PASCAL"
    log_info "Base URL: $BASE_URL"
    log_info "Auto-detected ${#SELECTED_FLOWS[@]} flows: ${SELECTED_FLOWS[*]}"
}

check_naming_conflicts() {
    log_step "Checking for naming conflicts"

    # Check if connector files already exist
    local connector_file="$BACKEND_DIR/connector-integration/src/connectors/$NAME_SNAKE.rs"
    local connector_dir="$BACKEND_DIR/connector-integration/src/connectors/$NAME_SNAKE"

    if [[ -f "$connector_file" ]] || [[ -d "$connector_dir" ]]; then
        if [[ "$FORCE_MODE" == "false" ]]; then
            fatal_error "Connector '$NAME_SNAKE' already exists. Use --force to override."
        else
            log_warning "Connector files exist but will be overwritten due to --force mode"
        fi
    fi

    # Check protobuf enum (skip if --force mode)
    if [[ "$FORCE_MODE" == "false" ]] && grep -q "$NAME_UPPER =" "$PROTO_FILE" 2>/dev/null; then
        fatal_error "Connector '$NAME_UPPER' already exists in protobuf enum"
    elif grep -q "$NAME_UPPER =" "$PROTO_FILE" 2>/dev/null; then
        log_warning "Connector '$NAME_UPPER' already in protobuf enum, will skip protobuf update"
    fi

    # Check domain types (skip if --force mode)
    if [[ "$FORCE_MODE" == "false" ]] && grep -q "$NAME_PASCAL" "$DOMAIN_TYPES_FILE" 2>/dev/null; then
        fatal_error "Connector '$NAME_PASCAL' already exists in domain types"
    elif grep -q "$NAME_PASCAL" "$DOMAIN_TYPES_FILE" 2>/dev/null; then
        log_warning "Connector '$NAME_PASCAL' already in domain types, will skip domain types update"
    fi

    log_success "Conflict check completed"
}

# =============================================================================
# CORE GENERATION FUNCTIONS
# =============================================================================

get_next_enum_ordinal() {
    log_step "Determining next enum ordinal"

    if [[ -f "$PROTO_FILE" ]]; then
        # Extract the highest ordinal from Connector enum
        local max_ordinal
        max_ordinal=$(sed -n '/^enum Connector {/,/^}/p' "$PROTO_FILE" | \
                     grep -o '= [0-9]\+;' | \
                     grep -o '[0-9]\+' | \
                     sort -n | \
                     tail -1) || true

        if [[ -n "$max_ordinal" ]]; then
            ENUM_ORDINAL=$((max_ordinal + 1))
        else
            ENUM_ORDINAL=100
        fi
    else
        ENUM_ORDINAL=100
    fi

    log_debug "Next enum ordinal: $ENUM_ORDINAL"
}

create_backup() {
    log_step "Creating backup"

    BACKUP_DIR="$ROOT_DIR/.connector_backup_$(date +%s)_$$"
    mkdir -p "$BACKUP_DIR"

    local files_to_backup=(
        "$PROTO_FILE"
        "$DOMAIN_TYPES_FILE"
        "$DOMAIN_TYPES_TYPES_FILE"
        "$CONNECTORS_MODULE_FILE"
        "$INTEGRATION_TYPES_FILE"
        "$ROUTER_DATA_FILE"
        "$CONFIG_FILE"
        "$SANDBOX_CONFIG_FILE"
        "$PRODUCTION_CONFIG_FILE"
        "$ROUTER_DATA_FILE"
        "$FIELD_PROBE_FILE"
    )

    local file
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$file" ]]; then
            # Create unique backup names for files with same basename
            if [[ "$file" == "$DOMAIN_TYPES_TYPES_FILE" ]]; then
                cp "$file" "$BACKUP_DIR/domain_types_types.rs"
                log_debug "Backed up: domain_types/types.rs"
            elif [[ "$file" == "$INTEGRATION_TYPES_FILE" ]]; then
                cp "$file" "$BACKUP_DIR/integration_types.rs"
                log_debug "Backed up: connector-integration/types.rs"
            elif [[ "$file" == "$ROUTER_DATA_FILE" ]]; then
                cp "$file" "$BACKUP_DIR/router_data.rs"
                log_debug "Backed up: domain_types/router_data.rs"
            else
                cp "$file" "$BACKUP_DIR/$(basename "$file")"
                log_debug "Backed up: $(basename "$file")"
            fi
        fi
    done

    log_success "Backup created at: $BACKUP_DIR"
}

substitute_template_variables() {
    local input_file="$1"
    local output_file="$2"

    log_debug "Substituting variables in template: $(basename "$input_file")"

    sed -e "s/{{CONNECTOR_NAME_PASCAL}}/$NAME_PASCAL/g" \
        -e "s/{{CONNECTOR_NAME_SNAKE}}/$NAME_SNAKE/g" \
        -e "s/{{CONNECTOR_NAME_UPPER}}/$NAME_UPPER/g" \
        -e "s|{{BASE_URL}}|$BASE_URL|g" \
        "$input_file" > "$output_file"
}

create_connector_files() {
    log_step "Creating connector files"

    local connectors_dir="$BACKEND_DIR/connector-integration/src/connectors"
    local connector_subdir="$connectors_dir/$NAME_SNAKE"

    # Create main connector file from template
    substitute_template_variables "$CONNECTOR_TEMPLATE" "$connectors_dir/$NAME_SNAKE.rs"

    # Create connector subdirectory and transformers file
    mkdir -p "$connector_subdir"
    substitute_template_variables "$TRANSFORMERS_TEMPLATE" "$connector_subdir/transformers.rs"
    
    # Generate and append dynamic implementations
    generate_dynamic_implementations "$connectors_dir/$NAME_SNAKE.rs"

    log_success "Created connector files with dynamic implementations"
}

# Generate dynamic implementation code for all flows and append to connector file
generate_dynamic_implementations() {
    local connector_file="$1"
    
    log_step "Generating dynamic implementations for all flows"
    
    # Create a temporary file for the dynamic implementations
    local temp_file="${connector_file}.dynamic"
    
    # Add header comment
    cat > "$temp_file" <<'EOF'

// =============================================================================
// DYNAMICALLY GENERATED IMPLEMENTATIONS
// =============================================================================
// The following implementations were auto-generated by add_connector.sh
// based on the flows detected in ConnectorServiceTrait.
// 
// To customize a flow implementation:
// 1. Move the empty impl block above (before this comment section)
// 2. Add your custom logic inside the impl block
// 3. The script will not regenerate moved implementations
// =============================================================================

// ===== CONNECTOR SERVICE TRAIT IMPLEMENTATIONS =====
// Main service trait - aggregates all other traits
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    connector_types::ConnectorServiceTrait<T> for {{CONNECTOR_NAME_PASCAL}}<T>
{
}

// ===== FLOW TRAIT IMPLEMENTATIONS =====
EOF
    
    # Substitute connector name in the header
    sed "s/{{CONNECTOR_NAME_PASCAL}}/$NAME_PASCAL/g" "$temp_file" > "${temp_file}.out" && mv "${temp_file}.out" "$temp_file"
    
    # Generate trait implementations for each flow
    local flow
    for flow in "${AVAILABLE_FLOWS[@]}"; do
        # Skip special traits that don't need standard implementation
        # ConnectorCommon: implemented in the template
        # ValidationTrait: implemented in the template  
        if [[ "$flow" == "ConnectorCommon" ]] || [[ "$flow" == "ValidationTrait" ]]; then
            continue
        fi
        
        generate_trait_impl "$flow" >> "$temp_file"
    done
    
    # Add section for ConnectorIntegrationV2 implementations
    cat >> "$temp_file" <<EOF

// ===== CONNECTOR INTEGRATION V2 IMPLEMENTATIONS =====
EOF
    
    # Generate ConnectorIntegrationV2 implementations
    for flow in "${AVAILABLE_FLOWS[@]}"; do
        if [[ "$flow" == "ConnectorCommon" ]] || [[ "$flow" == "IncomingWebhook" ]] || [[ "$flow" == "ValidationTrait" ]] || [[ "$flow" == "VerifyRedirectResponse" ]]; then
            continue
        fi
        
        generate_connector_integration_impl "$flow" >> "$temp_file"
    done
    
    # SourceVerification is a simple non-generic trait required by VerifyRedirectResponse
    # Add a single implementation for all connectors
    cat >> "$temp_file" <<EOF



// ===== SOURCE VERIFICATION IMPLEMENTATION =====
// Simple non-generic trait for webhook signature verification
impl<T: PaymentMethodDataTypes + Debug + Sync + Send + 'static + Serialize>
    interfaces::verification::SourceVerification for ${NAME_PASCAL}<T>
{
}

EOF
    
    # Append dynamic implementations to the connector file
    cat "$temp_file" >> "$connector_file"
    rm -f "$temp_file"
    
    # Append macro-based flow implementations from template
    log_step "Appending macro-based flow implementations"
    local macro_temp="${connector_file}.macros"
    substitute_template_variables "$MACRO_TEMPLATE" "$macro_temp"
    cat "$macro_temp" >> "$connector_file"
    rm -f "$macro_temp"
    
    log_success "Generated dynamic implementations with macro-based flows for ${#AVAILABLE_FLOWS[@]} flows"
}


# =============================================================================
# FILE UPDATE FUNCTIONS
# =============================================================================

update_protobuf() {
    log_step "Updating protobuf definitions"

    # Check if already exists
    if grep -q "$NAME_UPPER =" "$PROTO_FILE" 2>/dev/null; then
        log_warning "Skipping protobuf update - $NAME_UPPER already exists"
        return 0
    fi

    # Add new connector to enum before closing brace
    local tmp_file="${PROTO_FILE}.tmp"
    awk -v name="$NAME_UPPER" -v ordinal="$ENUM_ORDINAL" '
    /enum Connector \{/ { in_enum=1 }
    in_enum && /\}/ {
        printf "  %s = %s;\n", name, ordinal
        in_enum=0
    }
    { print }
    ' "$PROTO_FILE" > "$tmp_file" && mv "$tmp_file" "$PROTO_FILE"

    log_success "Updated protobuf with $NAME_UPPER = $ENUM_ORDINAL"
}

update_domain_types() {
    log_step "Updating domain types"

    # Check if already exists in ConnectorEnum
    if grep -q "^[[:space:]]*$NAME_PASCAL," "$DOMAIN_TYPES_FILE" 2>/dev/null; then
        log_warning "Skipping domain types update - $NAME_PASCAL already exists"
        return 0
    fi

    # Add to ConnectorEnum
    local tmp_file="${DOMAIN_TYPES_FILE}.tmp"
    awk -v name="$NAME_PASCAL" '
    /pub enum ConnectorEnum \{/ { in_enum=1 }
    in_enum && /\}/ {
        printf "    %s,\n", name
        in_enum=0
    }
    { print }
    ' "$DOMAIN_TYPES_FILE" > "$tmp_file" && mv "$tmp_file" "$DOMAIN_TYPES_FILE"

    # Add to gRPC mapping - find the line with "Unspecified =>" and add before it
    tmp_file="${DOMAIN_TYPES_FILE}.tmp2"
    awk -v name="$NAME_PASCAL" '
    /grpc_api_types::payments::Connector::Unspecified =>/ {
        printf "            grpc_api_types::payments::Connector::%s => Ok(Self::%s),\n", name, name
    }
    { print }
    ' "$DOMAIN_TYPES_FILE" > "$tmp_file" && mv "$tmp_file" "$DOMAIN_TYPES_FILE"

    rm -f "${DOMAIN_TYPES_FILE}.bak"

    log_success "Updated domain types with $NAME_PASCAL"
}

update_domain_types_file() {
    log_step "Updating domain types types.rs file"

    # Idempotency check
    if grep -q "pub ${NAME_SNAKE}: ConnectorParams," "$DOMAIN_TYPES_TYPES_FILE" 2>/dev/null; then
        log_warning "$NAME_SNAKE already in Connectors struct, skipping"
        return 0
    fi

    # Add connector field to Connectors struct
    # Insert before the closing brace of the struct
    local tmp_file="${DOMAIN_TYPES_TYPES_FILE}.tmp"
    awk -v name="$NAME_SNAKE" '
    /^pub struct Connectors \{/ { in_struct=1 }
    in_struct && /^\}/ {
        printf "    pub %s: ConnectorParams,\n", name
        in_struct=0
    }
    { print }
    ' "$DOMAIN_TYPES_TYPES_FILE" > "$tmp_file" && mv "$tmp_file" "$DOMAIN_TYPES_TYPES_FILE"

    log_success "Added $NAME_SNAKE to Connectors struct in types.rs"
}

update_router_data() {
    log_step "Updating router_data.rs (ConnectorSpecificAuth + match arm)"

    # Check if already exists
    if grep -q "ConnectorEnum::$NAME_PASCAL =>" "$ROUTER_DATA_FILE" 2>/dev/null; then
        log_warning "Skipping router_data update - $NAME_PASCAL already exists"
        return 0
    fi

    # 1. Add ConnectorSpecificAuth enum variant (default: HeaderKey with api_key)
    #    Insert before the closing brace of the enum
    sed -i.bak "/^pub enum ConnectorSpecificAuth {/,/^}/ s/^}/    $NAME_PASCAL {\n        api_key: Secret<String>,\n    },\n}/" "$ROUTER_DATA_FILE"
    rm -f "$ROUTER_DATA_FILE.bak"

    # 2. Add match arm in the ConnectorEnum match for ConnectorAuthType conversion
    #    Insert before the closing brace of the match statement in
    #    ForeignTryFrom<(&ConnectorAuthType, &connector_types::ConnectorEnum)>
    #    We find the last match arm (Revolv3) and add after it
    sed -i.bak "/ConnectorEnum::Revolv3 => match auth {/,/},/ {
        /},/ a\\
\\            ConnectorEnum::$NAME_PASCAL => match auth {\\
                ConnectorAuthType::HeaderKey { api_key } => Ok(Self::$NAME_PASCAL {\\
                    api_key: api_key.clone(),\\
                }),\\
                _ => Err(err().into()),\\
            },
    }" "$ROUTER_DATA_FILE"
    rm -f "$ROUTER_DATA_FILE.bak"

    log_success "Updated router_data.rs with $NAME_PASCAL auth variant and match arm"
}

update_protobuf_auth() {
    log_step "Updating protobuf auth definitions"

    # Check if auth message already exists
    if grep -q "${NAME_PASCAL}Auth" "$PROTO_FILE" 2>/dev/null; then
        log_warning "Skipping protobuf auth update - ${NAME_PASCAL}Auth already exists"
        return 0
    fi

    # 1. Add auth message before the ConnectorAuth message
    sed -i.bak "/^message ConnectorAuth {/i\\
message ${NAME_PASCAL}Auth {\\
  SecretString api_key = 1;\\
}\\
" "$PROTO_FILE"
    rm -f "$PROTO_FILE.bak"

    # 2. Get the next oneof field number by finding the highest existing one
    local max_field_num
    max_field_num=$(grep -E "Auth [a-z_]+ = [0-9]+;" "$PROTO_FILE" | \
                    sed -E 's/.*= ([0-9]+);/\1/' | \
                    sort -n | tail -1)
    local next_field_num=$((max_field_num + 1))

    # 3. Add oneof entry before the closing brace of ConnectorAuth
    #    Insert after the last entry in the oneof
    sed -i.bak "/^  oneof auth_type {/,/^  }/ s|^  }|    // $NAME_UPPER = $ENUM_ORDINAL\n    ${NAME_PASCAL}Auth $(echo "$NAME_SNAKE" | tr '[:upper:]' '[:lower:]') = $next_field_num;\n  }|" "$PROTO_FILE"
    rm -f "$PROTO_FILE.bak"

    log_success "Updated protobuf with ${NAME_PASCAL}Auth message and oneof entry"
}

update_router_data_grpc_auth() {
    log_step "Updating router_data.rs gRPC AuthType mapping"

    # Check if already exists
    if grep -q "AuthType::$NAME_PASCAL(" "$ROUTER_DATA_FILE" 2>/dev/null; then
        log_warning "Skipping gRPC auth mapping - $NAME_PASCAL already exists"
        return 0
    fi

    # Find the last AuthType match arm and add after it
    # We insert before the closing brace of the match statement in
    # ForeignTryFrom<grpc_api_types::payments::ConnectorAuth>
    local last_auth_type
    last_auth_type=$(grep -E "AuthType::[A-Z][A-Za-z0-9]*\(" "$ROUTER_DATA_FILE" | tail -1 | sed -E 's/.*AuthType::([A-Za-z0-9]+)\(.*/\1/')

    # Compute the lowercase variable binding name used in the existing code
    local last_auth_lower
    last_auth_lower=$(echo "$last_auth_type" | tr '[:upper:]' '[:lower:]')

    # Use the lowercase name for the new variable binding
    local name_lower
    name_lower=$(echo "$NAME_SNAKE" | tr '[:upper:]' '[:lower:]')

    sed -i.bak "/AuthType::${last_auth_type}(${last_auth_lower})/,/}),/ {
        /}),/ a\\
\\            AuthType::$NAME_PASCAL($name_lower) => Ok(Self::$NAME_PASCAL {\\
                api_key: $name_lower.api_key.ok_or_else(err)?,\\
            }),
    }" "$ROUTER_DATA_FILE"
    rm -f "$ROUTER_DATA_FILE.bak"

    log_success "Updated router_data.rs with gRPC AuthType::$NAME_PASCAL mapping"
}

update_connectors_module() {
    log_step "Updating connectors module"

    # Idempotency check: skip if already declared
    if grep -q "pub mod $NAME_SNAKE;" "$CONNECTORS_MODULE_FILE" 2>/dev/null; then
        log_warning "Module '$NAME_SNAKE' already declared in connectors.rs, skipping"
        return 0
    fi

    # Add module declaration and use statement
    cat >> "$CONNECTORS_MODULE_FILE" << EOF

pub mod $NAME_SNAKE;
pub use self::${NAME_SNAKE}::${NAME_PASCAL};
EOF

    log_success "Updated connectors module"
}

update_integration_types() {
    log_step "Updating integration types"

    # Idempotency check
    if grep -q "ConnectorEnum::${NAME_PASCAL} =>" "$INTEGRATION_TYPES_FILE" 2>/dev/null; then
        log_warning "Integration type mapping for $NAME_PASCAL already exists, skipping"
        return 0
    fi

    # Add enum mapping to the convert_connector match statement
    # Insert after the last existing ConnectorEnum:: mapping
    local tmp_file="${INTEGRATION_TYPES_FILE}.tmp"
    local last_line
    last_line=$(grep -n "ConnectorEnum::" "$INTEGRATION_TYPES_FILE" | tail -1 | cut -d: -f1)
    if [[ -n "$last_line" ]]; then
        awk -v name="$NAME_PASCAL" -v after="$last_line" '
        NR == after {
            print
            printf "            ConnectorEnum::%s => Box::new(connectors::%s::new()),\n", name, name
            next
        }
        { print }
        ' "$INTEGRATION_TYPES_FILE" > "$tmp_file" && mv "$tmp_file" "$INTEGRATION_TYPES_FILE"
    fi

    rm -f "$INTEGRATION_TYPES_FILE.bak"

    log_success "Updated integration types with $NAME_PASCAL mapping"
}

update_config_file() {
    local config_file="$1"
    local config_name="$2"

    if [[ -f "$config_file" ]]; then
        # Idempotency check: skip if already configured
        if grep -q "^${NAME_SNAKE}\.base_url" "$config_file" 2>/dev/null; then
            log_warning "$NAME_SNAKE already configured in $config_name, skipping"
            return 0
        fi

        # Check if [connectors] section exists
        if grep -q "^\[connectors\]" "$config_file"; then
            # Insert after [connectors] section header using awk
            local tmp_file="${config_file}.tmp"
            awk -v name="$NAME_SNAKE" -v url="$BASE_URL" '
            /^\[connectors\]/ {
                print
                printf "%s.base_url = \"%s\"\n", name, url
                next
            }
            { print }
            ' "$config_file" > "$tmp_file" && mv "$tmp_file" "$config_file"
            log_success "Updated $config_name in [connectors] section"
        else
            # Create [connectors] section at the end
            echo "" >> "$config_file"
            echo "[connectors]" >> "$config_file"
            echo "# $NAME_PASCAL connector configuration" >> "$config_file"
            echo "$NAME_SNAKE.base_url = \"$BASE_URL\"" >> "$config_file"
            log_success "Created [connectors] section in $config_name and added configuration"
        fi
    else
        log_warning "$config_name not found, skipping config update"
    fi
}

update_config() {
    log_step "Updating configuration files"

    # Update all environment config files
    update_config_file "$CONFIG_FILE" "development.toml"
    update_config_file "$SANDBOX_CONFIG_FILE" "sandbox.toml"
    update_config_file "$PRODUCTION_CONFIG_FILE" "production.toml"

    log_success "All configuration files updated"
}

# =============================================================================
# VALIDATION AND CLEANUP
# =============================================================================

format_code() {
    log_step "Formatting code"

    if command -v cargo >/dev/null 2>&1; then
        if cargo +nightly fmt --all >/dev/null 2>&1; then
            log_success "Code formatted with nightly rustfmt"
        elif cargo fmt --all >/dev/null 2>&1; then
            log_success "Code formatted with stable rustfmt"
        else
            log_warning "Code formatting failed"
        fi
    else
        log_warning "Cargo not found, skipping code formatting"
    fi
}

validate_compilation() {
    log_step "Validating compilation"

    if command -v cargo >/dev/null 2>&1; then
        log_info "Running cargo check..."

        if (cd "$BACKEND_DIR" && cargo check 2>&1); then
            log_success "Compilation validation passed"
            return 0
        else
            log_error "Compilation validation failed"
            return 1
        fi
    else
        log_warning "Cargo not found, skipping compilation validation"
        return 0
    fi
}

cleanup_backup() {
    if [[ -n "$BACKUP_DIR" ]] && [[ -d "$BACKUP_DIR" ]]; then
        rm -rf "$BACKUP_DIR"
        log_debug "Cleaned up backup directory"
    fi
}

emergency_rollback() {
    log_step "Performing emergency rollback"

    if [[ -n "$BACKUP_DIR" ]] && [[ -d "$BACKUP_DIR" ]]; then
        # Remove created files
        rm -f "$BACKEND_DIR/connector-integration/src/connectors/$NAME_SNAKE.rs"
        rm -rf "$BACKEND_DIR/connector-integration/src/connectors/$NAME_SNAKE"

        # Restore backed up files
        local backup_file
        for backup_file in "$BACKUP_DIR"/*; do
            if [[ -f "$backup_file" ]]; then
                local filename
                filename=$(basename "$backup_file")
                case "$filename" in
                    "payment.proto")
                        cp "$backup_file" "$PROTO_FILE"
                        ;;
                    "connector_types.rs")
                        cp "$backup_file" "$DOMAIN_TYPES_FILE"
                        ;;
                    "domain_types_types.rs")
                        cp "$backup_file" "$DOMAIN_TYPES_TYPES_FILE"
                        ;;
                    "integration_types.rs")
                        cp "$backup_file" "$INTEGRATION_TYPES_FILE"
                        ;;
                    "router_data.rs")
                        cp "$backup_file" "$ROUTER_DATA_FILE"
                        ;;
                    "connectors.rs")
                        cp "$backup_file" "$CONNECTORS_MODULE_FILE"
                        ;;
                    "development.toml")
                        cp "$backup_file" "$CONFIG_FILE"
                        ;;
                    "sandbox.toml")
                        cp "$backup_file" "$SANDBOX_CONFIG_FILE"
                        ;;
                    "production.toml")
                        cp "$backup_file" "$PRODUCTION_CONFIG_FILE"
                        ;;
                    "router_data.rs")
                        cp "$backup_file" "$ROUTER_DATA_FILE"
                        ;;
                    "main.rs")
                        cp "$backup_file" "$FIELD_PROBE_FILE"
                        ;;
                esac
            fi
        done

        rm -rf "$BACKUP_DIR"
        log_success "Emergency rollback completed"
    else
        log_warning "No backup found for rollback"
    fi
}

# =============================================================================
# USER INTERACTION
# =============================================================================

show_implementation_plan() {
    if [[ "$YES_MODE" == "true" ]]; then
        return 0
    fi

    echo
    log_step "Implementation Plan"
    echo "====================="
    echo
    echo "📁 Files to create:"
    echo "   ├── backend/connector-integration/src/connectors/$NAME_SNAKE.rs"
    echo "   └── backend/connector-integration/src/connectors/$NAME_SNAKE/transformers.rs"
    echo
    echo "📝 Files to modify:"
    echo "   ├── backend/grpc-api-types/proto/payment.proto"
    echo "   ├── backend/domain_types/src/connector_types.rs"
    echo "   ├── backend/domain_types/src/router_data.rs"
    echo "   ├── backend/connector-integration/src/connectors.rs"
    echo "   ├── backend/connector-integration/src/types.rs"
    echo "   └── config/development.toml"
    echo
    echo "🎯 Configuration:"
    echo "   ├── Connector: $NAME_PASCAL"
    echo "   ├── Enum ordinal: $ENUM_ORDINAL"
    echo "   ├── Base URL: $BASE_URL"
    echo "   └── Flows: ${SELECTED_FLOWS[*]}"
    echo

    read -p "❓ Proceed with implementation? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Implementation cancelled by user"
        exit 1
    fi
}

show_next_steps() {
    echo
    log_success "Connector '$NAME_SNAKE' successfully created!"
    echo
    log_step "Next Steps"
    echo "============"
    echo
    echo "1️⃣  Implement Core Logic:"
    echo "   📁 Edit: backend/connector-integration/src/connectors/$NAME_SNAKE/transformers.rs"
    echo "      • Update request/response structures for your API"
    echo "      • Implement proper field mappings"
    echo "      • Handle authentication requirements"
    echo
    echo "2️⃣  Customize Connector:"
    echo "   📁 Edit: backend/connector-integration/src/connectors/$NAME_SNAKE.rs"
    echo "      • Update URL patterns and endpoints"
    echo "      • Implement error handling"
    echo "      • Add connector-specific logic"
    echo
    echo "3️⃣  Validation Commands:"
    echo "   📋 Check compilation: cargo check --package connector-integration"
    echo "   📋 Run tests: cargo test --package connector-integration"
    echo "   📋 Build: cargo build --package connector-integration"
    echo
    log_success "Connector '$NAME_PASCAL' is ready for implementation!"
}

# =============================================================================
# MAIN EXECUTION FLOW
# =============================================================================

main() {
    # Print header
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
    echo "======================================="
    echo

    # Core execution flow (no ERR trap yet — backup doesn't exist)
    parse_arguments "$@"

    # Full scaffold mode
    validate_environment
    validate_inputs
    check_naming_conflicts
    get_next_enum_ordinal

    # Extract flow metadata for dynamic generation
    extract_all_flow_metadata

    # Show implementation plan and get confirmation
    show_implementation_plan

    # Create backup for safety
    create_backup

    # NOW set up the ERR trap — backup exists so rollback is safe
    trap 'emergency_rollback; exit 1' ERR

    # Execute main operations
    create_connector_files
    update_protobuf
    update_domain_types
    update_domain_types_file
    update_connectors_module
    update_integration_types
    update_config
    register_connector_specific_config

    # Validate and finalize
    format_code
    if ! validate_compilation; then
        log_warning "Compilation check failed. ConnectorSpecificConfig registration may need manual fixes."
        log_warning "See integrate_connector.md Step 3.5 for manual registration instructions."
        log_warning "Files have NOT been rolled back. Review and fix manually."
        log_warning "Backup preserved at: $BACKUP_DIR"
    else
        # Only clean up backup on successful compilation
        cleanup_backup
    fi
    show_next_steps
}

# Execute main function with all arguments
main "$@"