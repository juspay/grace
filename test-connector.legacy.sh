#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Function to extract transaction ID from response
extract_transaction_id() {
    local response="$1"
    echo "$response" | jq -r '.transactionId.id // empty'
}

# Function to extract refund ID from response
extract_refund_id() {
    local response="$1"
    echo "$response" | jq -r '.refundId // .refund_id // empty'
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    print_error "jq is required but not installed. Please install it first."
    echo "  macOS: brew install jq"
    echo "  Linux: apt-get install jq or yum install jq"
    exit 1
fi

# Check if grpcurl is installed
if ! command -v grpcurl &> /dev/null; then
    print_error "grpcurl is required but not installed. Please install it first."
    echo "  macOS: brew install grpcurl"
    echo "  Linux: https://github.com/fullstorydev/grpcurl#installation"
    exit 1
fi

echo "================================================"
echo "   gRPC Payment Connector Testing Script"
echo "================================================"
echo ""

# Collect connector credentials
read -p "Enter connector name: " CONNECTOR
read -p "Enter API key (x-api-key): " API_KEY
read -p "Enter key1 (x-key1): " KEY1
read -p "Enter merchant ID: " MERCHANT_ID
read -p "Enter server address [localhost:8000]: " SERVER
SERVER=${SERVER:-localhost:8000}

# Generate base reference ID
BASE_REF="test_${CONNECTOR}_$(date +%s)"

echo ""
echo "================================================"
echo "Select test set to run:"
echo "================================================"
echo "1) Set 1: Authorize (automatic capture) + Payment Sync"
echo "2) Set 2: Authorize + Payment Sync + Refund + Refund Sync"
echo "3) Set 3: Authorize (manual capture) + Capture"
echo "4) Custom - Run individual operations"
echo ""
read -p "Enter your choice [1-4]: " CHOICE

# Function to run authorize (automatic capture)
run_authorize_auto() {
    local ref_id="${1:-${BASE_REF}_auth_auto}"
    print_info "Running Authorize (Automatic Capture)..."

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "amount": 5000,
          "minor_amount": 5000,
          "currency": "USD",
          "capture_method": "AUTOMATIC",
          "auth_type": "NO_THREE_DS",
          "payment_method": {
            "card": {
              "card_number": {"value": "5100000010001004"},
              "card_cvc": {"value": "123"},
              "card_exp_month": {"value": "12"},
              "card_exp_year": {"value": "2030"},
              "card_network": "MASTERCARD"
            }
          },
          "address": {
            "billing_address": {
              "first_name": {"value": "John"},
              "last_name": {"value": "Doe"},
              "line1": {"value": "123 Main Street"},
              "city": {"value": "New York"},
              "state": {"value": "NY"},
              "zip_code": {"value": "10001"},
              "country_alpha2_code": "US",
              "email": {"value": "john.doe@example.com"},
              "phone_number": {"value": "1234567890"},
              "phone_country_code": "1"
            }
          },
          "return_url": "https://example.com/return",
          "webhook_url": "https://example.com/webhook",
          "order_category": "pay",
          "enrolled_for_3ds": false,
          "request_incremental_authorization": false,
          "metadata": {
            "order_id": "order_'"${CONNECTOR}"'_123",
            "customer_email": "john.doe@example.com",
            "description": "Test payment for '"${CONNECTOR}"'"
          }
        }' \
        ${SERVER} ucs.v2.PaymentService/Authorize 2>&1)

    if [ $? -eq 0 ]; then
        local txn_id=$(extract_transaction_id "$response")
        if [ -n "$txn_id" ]; then
            print_success "Authorize successful. Transaction ID: $txn_id"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            echo "$txn_id"
            return 0
        else
            print_error "Authorize failed - no transaction ID in response"
            echo "$response"
            return 1
        fi
    else
        print_error "Authorize failed"
        echo "$response"
        return 1
    fi
}

# Function to run authorize (manual capture)
run_authorize_manual() {
    local ref_id="${1:-${BASE_REF}_auth_manual}"
    print_info "Running Authorize (Manual Capture)..."

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "amount": 5000,
          "minor_amount": 5000,
          "currency": "USD",
          "capture_method": "MANUAL",
          "auth_type": "NO_THREE_DS",
          "payment_method": {
            "card": {
              "card_number": {"value": "5100000010001004"},
              "card_cvc": {"value": "123"},
              "card_exp_month": {"value": "12"},
              "card_exp_year": {"value": "2030"},
              "card_network": "MASTERCARD"
            }
          },
          "address": {
            "billing_address": {
              "first_name": {"value": "John"},
              "last_name": {"value": "Doe"},
              "line1": {"value": "123 Main Street"},
              "city": {"value": "New York"},
              "state": {"value": "NY"},
              "zip_code": {"value": "10001"},
              "country_alpha2_code": "US",
              "email": {"value": "john.doe@example.com"},
              "phone_number": {"value": "1234567890"},
              "phone_country_code": "1"
            }
          },
          "return_url": "https://example.com/return",
          "webhook_url": "https://example.com/webhook",
          "order_category": "pay",
          "enrolled_for_3ds": false,
          "request_incremental_authorization": false,
          "metadata": {
            "order_id": "order_'"${CONNECTOR}"'_123",
            "customer_email": "john.doe@example.com",
            "description": "Test payment for '"${CONNECTOR}"'"
          }
        }' \
        ${SERVER} ucs.v2.PaymentService/Authorize 2>&1)

    if [ $? -eq 0 ]; then
        local txn_id=$(extract_transaction_id "$response")
        if [ -n "$txn_id" ]; then
            print_success "Authorize (Manual) successful. Transaction ID: $txn_id"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            echo "$txn_id"
            return 0
        else
            print_error "Authorize failed - no transaction ID in response"
            echo "$response"
            return 1
        fi
    else
        print_error "Authorize failed"
        echo "$response"
        return 1
    fi
}

# Function to run payment sync
run_payment_sync() {
    local txn_id="$1"
    local ref_id="${2:-${BASE_REF}_psync}"

    if [ -z "$txn_id" ]; then
        print_error "Transaction ID required for payment sync"
        return 1
    fi

    print_info "Running Payment Sync for transaction: $txn_id"

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "transaction_id": {"id": "'"${txn_id}"'"},
          "amount": 5000,
          "currency": "USD"
        }' \
        ${SERVER} ucs.v2.PaymentService/Get 2>&1)

    if [ $? -eq 0 ]; then
        print_success "Payment Sync successful"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 0
    else
        print_error "Payment Sync failed"
        echo "$response"
        return 1
    fi
}

# Function to run capture
run_capture() {
    local txn_id="$1"
    local ref_id="${2:-${BASE_REF}_capture}"

    if [ -z "$txn_id" ]; then
        print_error "Transaction ID required for capture"
        return 1
    fi

    print_info "Running Capture for transaction: $txn_id"

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "transaction_id": {"id": "'"${txn_id}"'"},
          "amount_to_capture": 5000,
          "currency": "USD"
        }' \
        ${SERVER} ucs.v2.PaymentService/Capture 2>&1)

    if [ $? -eq 0 ]; then
        print_success "Capture successful"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 0
    else
        print_error "Capture failed"
        echo "$response"
        return 1
    fi
}

# Function to run refund
run_refund() {
    local txn_id="$1"
    local ref_id="${2:-${BASE_REF}_refund}"

    if [ -z "$txn_id" ]; then
        print_error "Transaction ID required for refund"
        return 1
    fi

    print_info "Running Refund for transaction: $txn_id"

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "transaction_id": {"id": "'"${txn_id}"'"},
          "refund_amount": 5000,
          "minor_refund_amount": 5000,
          "currency": "USD",
          "reason": "customer_return"
        }' \
        ${SERVER} ucs.v2.PaymentService/Refund 2>&1)

    if [ $? -eq 0 ]; then
        local refund_id=$(extract_refund_id "$response")
        if [ -n "$refund_id" ]; then
            print_success "Refund successful. Refund ID: $refund_id"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            echo "$refund_id"
            return 0
        else
            print_success "Refund successful (no refund ID in response)"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
            return 0
        fi
    else
        print_error "Refund failed"
        echo "$response"
        return 1
    fi
}

# Function to run refund sync
run_refund_sync() {
    local txn_id="$1"
    local refund_id="$2"
    local ref_id="${3:-${BASE_REF}_rsync}"

    if [ -z "$txn_id" ]; then
        print_error "Transaction ID required for refund sync"
        return 1
    fi

    if [ -z "$refund_id" ]; then
        print_error "Refund ID required for refund sync"
        return 1
    fi

    print_info "Running Refund Sync for transaction: $txn_id, refund: $refund_id"

    local response=$(grpcurl -plaintext \
        -H "x-connector: ${CONNECTOR}" \
        -H "x-auth: body-key" \
        -H "x-api-key: ${API_KEY}" \
        -H "x-key1: ${KEY1}" \
        -H "x-merchant-id: ${MERCHANT_ID}" \
        -H "x-reference-id: ${ref_id}" \
        -d '{
          "request_ref_id": {"id": "'"${ref_id}"'"},
          "transaction_id": {"id": "'"${txn_id}"'"},
          "refund_id": "'"${refund_id}"'"
        }' \
        ${SERVER} ucs.v2.RefundService/Get 2>&1)

    if [ $? -eq 0 ]; then
        print_success "Refund Sync successful"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 0
    else
        print_error "Refund Sync failed"
        echo "$response"
        return 1
    fi
}

# Execute based on choice
echo ""
echo "================================================"
echo "Starting test execution..."
echo "================================================"
echo ""

case $CHOICE in
    1)
        # Set 1: Authorize (automatic) + Payment Sync
        txn_id=$(run_authorize_auto)
        if [ $? -eq 0 ] && [ -n "$txn_id" ]; then
            echo ""
            sleep 2
            run_payment_sync "$txn_id"
        fi
        ;;

    2)
        # Set 2: Authorize + Payment Sync + Refund + Refund Sync
        txn_id=$(run_authorize_auto)
        if [ $? -eq 0 ] && [ -n "$txn_id" ]; then
            echo ""
            sleep 2
            run_payment_sync "$txn_id"

            echo ""
            sleep 2
            refund_id=$(run_refund "$txn_id")

            if [ $? -eq 0 ] && [ -n "$refund_id" ]; then
                echo ""
                sleep 2
                run_refund_sync "$txn_id" "$refund_id"
            fi
        fi
        ;;

    3)
        # Set 3: Authorize (manual) + Capture
        txn_id=$(run_authorize_manual)
        if [ $? -eq 0 ] && [ -n "$txn_id" ]; then
            echo ""
            sleep 2
            run_capture "$txn_id"
        fi
        ;;

    4)
        # Custom - Run individual operations
        while true; do
            echo ""
            echo "================================================"
            echo "Custom Operations Menu"
            echo "================================================"
            echo "1) Authorize (Automatic Capture)"
            echo "2) Authorize (Manual Capture)"
            echo "3) Payment Sync"
            echo "4) Capture"
            echo "5) Refund"
            echo "6) Refund Sync"
            echo "0) Exit"
            echo ""
            read -p "Select operation: " OP

            case $OP in
                1)
                    txn_id=$(run_authorize_auto)
                    ;;
                2)
                    txn_id=$(run_authorize_manual)
                    ;;
                3)
                    read -p "Enter transaction ID: " input_txn_id
                    run_payment_sync "$input_txn_id"
                    ;;
                4)
                    read -p "Enter transaction ID: " input_txn_id
                    run_capture "$input_txn_id"
                    ;;
                5)
                    read -p "Enter transaction ID: " input_txn_id
                    refund_id=$(run_refund "$input_txn_id")
                    ;;
                6)
                    read -p "Enter transaction ID: " input_txn_id
                    read -p "Enter refund ID: " input_refund_id
                    run_refund_sync "$input_txn_id" "$input_refund_id"
                    ;;
                0)
                    break
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
        done
        ;;

    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo "Test execution completed"
echo "================================================"
