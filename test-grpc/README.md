# gRPC Test Automation

Generic test automation system for payment connector gRPC APIs. Supports automated testing of authorization, capture, refund, void, and sync operations with multiple authentication types.

## Features

- **4 Pre-defined Test Flows**: auth+psync, auth+capture, auth+refund+rsync, auth+void
- **4 Authentication Types**: header-key, body-key, signature-key, multiauth-key
- **Hybrid Configuration**: JSON config files with environment variable overrides
- **Template-based Requests**: Reusable templates with placeholder substitution
- **Interactive Mode**: Pause between operations for manual verification
- **JSON Output**: Detailed results saved for each test run
- **Generic & Extensible**: Easily add new connectors with minimal configuration

## Prerequisites

Install required tools:

```bash
# macOS
brew install grpcurl jq

# Linux
# grpcurl: go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
# jq: apt-get install jq (Debian/Ubuntu) or yum install jq (RHEL/CentOS)
```

## Quick Start

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your connector credentials
   ```

2. **Run a test flow**:
   ```bash
   # Make the script executable
   chmod +x test-grpc.sh

   # Run auth + capture flow
   ./test-grpc.sh bambora auth-capture

   # Run with interactive mode
   ./test-grpc.sh bambora auth-refund-rsync --interactive

   # Enable debug logging
   ./test-grpc.sh bambora auth-void --debug
   ```

3. **View results**:
   ```bash
   # Results are saved to output/<connector>/<timestamp>/
   ls -la output/bambora/
   cat output/bambora/20251209_120000/summary.json
   ```

## Available Flows

| Flow | Operations | Description |
|------|-----------|-------------|
| `auth-psync` | Authorize + Payment Sync | Auto-capture payment and verify status |
| `auth-capture` | Authorize (manual) + Capture | Manual authorization then capture |
| `auth-refund-rsync` | Authorize (auto) + Refund + Refund Sync | Payment, refund, and verify refund |
| `auth-void` | Authorize (manual) + Void | Authorization then cancellation |

## Configuration

### Connector Configuration

Create a JSON config file in `configs/<connector>.json`:

```json
{
  "connector_name": "bambora",
  "base_url": "localhost:8000",
  "auth_type": "body-key",
  "merchant_id": "test_merchant_bambora",
  "proto_service": "ucs.v2.PaymentService",
  "default_amounts": {
    "auth": 5000,
    "capture": 5000,
    "refund": 2500
  },
  "test_card": {
    "card_number": "5100000010001004",
    "card_cvc": "123",
    "card_exp_month": "12",
    "card_exp_year": "2030",
    "card_network": "MASTERCARD"
  },
  "billing_address": {
    "first_name": "John",
    "last_name": "Doe",
    "line1": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "country_alpha2_code": "US",
    "email": "john.doe@example.com",
    "phone_number": "1234567890",
    "phone_country_code": "1"
  },
  "default_currency": "USD"
}
```

### Environment Variables

Set sensitive credentials in `.env`:

```bash
# Connector credentials (UPPERCASE)
BAMBORA_API_KEY=your_api_key_here
BAMBORA_KEY1=your_merchant_key_here

# For signature-based auth
CONNECTOR_API_SIGNATURE=your_signature_here

# Optional: Enable debug logging
DEBUG=false
```

### Authentication Types

Different auth types require different environment variables:

| Auth Type | Required Variables |
|-----------|-------------------|
| `header-key` | `{CONNECTOR}_API_KEY` |
| `body-key` | `{CONNECTOR}_API_KEY`, `{CONNECTOR}_KEY1` |
| `signature-key` | `{CONNECTOR}_API_KEY`, `{CONNECTOR}_API_SIGNATURE`, `{CONNECTOR}_KEY1` |
| `multiauth-key` | `{CONNECTOR}_API_KEY`, `{CONNECTOR}_API_SIGNATURE`, `{CONNECTOR}_KEY1`, `{CONNECTOR}_KEY2`, ... |

## Output Format

Results are saved to `output/<connector>/<timestamp>/`:

```
output/bambora/20251209_120000/
├── auth.json         # Authorization response
├── capture.json      # Capture response
├── summary.json      # Flow summary with all results
└── test.log          # Detailed execution log
```

### Summary JSON Format

```json
{
  "flow": "auth-capture",
  "status": "SUCCESS",
  "timestamp": "2025-12-09T12:00:00Z",
  "results": {
    "auth": {
      "transactionId": { "id": "10006485" },
      "status": "AUTHORIZED"
    },
    "capture": {
      "transactionId": { "id": "10006485" },
      "status": "CHARGED"
    }
  }
}
```

## Adding a New Connector

1. **Create connector config**:
   ```bash
   cp configs/template.json configs/myconnector.json
   # Edit configs/myconnector.json with your connector details
   ```

2. **Set environment variables**:
   ```bash
   # Add to .env
   MYCONNECTOR_API_KEY=your_key
   MYCONNECTOR_KEY1=your_merchant_key  # if using body-key auth
   ```

3. **Run tests**:
   ```bash
   ./test-grpc.sh myconnector auth-capture
   ```

## Directory Structure

```
test-grpc/
├── lib/                  # Reusable libraries
│   ├── logger.sh        # Color-coded logging
│   ├── config-loader.sh # Config + env var loading
│   ├── grpc-executor.sh # gRPC call execution
│   ├── response-parser.sh # JSON response parsing
│   ├── template-engine.sh # Template substitution
│   ├── header-builder.sh # Auth header generation
│   └── utils.sh         # Common utilities
├── configs/             # Connector configurations
├── templates/           # Request templates
├── operations/          # Individual operation scripts
├── flows/              # Test flow orchestration
├── output/             # Test results
├── test-grpc.sh        # Main entry point
└── README.md           # This file
```

## Usage Examples

### Basic Usage

```bash
# Run auth + capture flow
./test-grpc.sh bambora auth-capture
```

### Interactive Mode

```bash
# Pause between operations
./test-grpc.sh bambora auth-refund-rsync --interactive
```

### Debug Mode

```bash
# Enable detailed debug logging
./test-grpc.sh bambora auth-void --debug
```

### Running Individual Operations

```bash
# You can also run individual operations directly
./operations/auth.sh bambora ./output/test1 MANUAL 5000
```

## Troubleshooting

### grpcurl not found

```bash
# macOS
brew install grpcurl

# Go
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
```

### jq not found

```bash
# macOS
brew install jq

# Linux
apt-get install jq  # Debian/Ubuntu
yum install jq      # RHEL/CentOS
```

### Missing environment variables

```bash
# Check your .env file has the required variables
cat .env

# Example for bambora (body-key auth)
BAMBORA_API_KEY=your_api_key
BAMBORA_KEY1=your_merchant_key
```

### Connector config not found

```bash
# List available connectors
ls -1 configs/*.json

# Create new connector config from template
cp configs/template.json configs/yourconnector.json
```

### Invalid response / gRPC errors

- Check that the gRPC server is running at the configured `base_url`
- Verify credentials in `.env` are correct
- Enable debug mode to see detailed request/response: `--debug`
- Check the operation log in `output/<connector>/<timestamp>/test.log`

## Advanced Usage

### Customizing Amounts

Edit the connector config `default_amounts`:

```json
{
  "default_amounts": {
    "auth": 10000,
    "capture": 10000,
    "refund": 5000
  }
}
```

### Custom Test Card

Update the connector config `test_card`:

```json
{
  "test_card": {
    "card_number": "4111111111111111",
    "card_cvc": "123",
    "card_exp_month": "12",
    "card_exp_year": "2030",
    "card_network": "VISA"
  }
}
```

### Creating Custom Flows

Create a new flow script in `flows/`:

```bash
#!/bin/bash
# flows/custom-flow.sh

source "$ROOT_DIR/lib/logger.sh"
source "$ROOT_DIR/lib/utils.sh"
source "$ROOT_DIR/operations/auth.sh"
source "$ROOT_DIR/operations/capture.sh"

execute_flow_custom() {
    local connector="$1"
    local output_dir=$(create_output_directory "$connector")

    # Your custom flow logic here
    tx_id=$(execute_auth "$connector" "$output_dir" "MANUAL")
    execute_capture "$connector" "$output_dir" "$tx_id"

    generate_flow_summary "$output_dir" "custom-flow" "SUCCESS"
}
```

## Contributing

When adding new features:

1. Follow existing patterns in library modules
2. Add comprehensive error handling
3. Use color-coded logging for user feedback
4. Update this README with new features
5. Test with multiple connectors and auth types

## License

Internal use only
