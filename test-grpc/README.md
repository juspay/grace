# Modular gRPC Connector Testing Framework

A modular, configuration-driven testing framework for payment connector gRPC APIs.

## Features

- **Modular Architecture** - Separate libraries for logging, config, templates, validation, and API calls
- **Configuration-Driven** - JSON configs with environment variable overrides
- **Template-Based Requests** - Reusable JSON templates with variable substitution
- **Validation Framework** - Prevents PR #240 issues with comprehensive response validation
- **Multiple Test Sets** - Pre-defined test flows for common scenarios
- **Interactive Mode** - Run individual operations manually

## Quick Start

```bash
cd test-grpc

# Run test set 1 (Authorize + Payment Sync)
./test-connector.sh bambora --set 1

# Run with environment variable overrides
BAMBORA_API_KEY="your_key" ./test-connector.sh bambora --set 2

# Interactive mode
./test-connector.sh bambora --interactive
```

## Directory Structure

```
test-grpc/
├── test-connector.sh              # Main entry point
├── lib/                           # Modular libraries
│   ├── logger.sh                 # Color logging
│   ├── config-loader.sh          # Config + env var handling
│   ├── template-engine.sh        # Template substitution
│   ├── validator.sh              # Response validation
│   ├── grpc-client.sh            # grpcurl wrappers
│   └── utils.sh                  # Common utilities
├── configs/
│   ├── connectors/               # Per-connector configs
│   │   └── bambora.json
│   └── server.json               # Server defaults
├── templates/                     # Request templates
│   ├── authorize-auto.json.template
│   ├── authorize-manual.json.template
│   ├── capture.json.template
│   ├── refund.json.template
│   ├── payment-sync.json.template
│   └── refund-sync.json.template
├── validation/rules/              # Validation rules
│   ├── authorize.json
│   ├── capture.json
│   ├── refund.json              # PR #240 checks
│   ├── payment-sync.json
│   └── refund-sync.json
├── test-sets/                     # Test set definitions
│   ├── set1-auth-psync.json
│   ├── set2-full-flow.json
│   └── set3-auth-capture.json
└── output/                        # Test execution logs
    ├── logs/
    └── results/
```

## Test Sets

### Set 1: Authorize + Payment Sync
Basic authorization with automatic capture and payment sync.

```bash
./test-connector.sh bambora --set 1
```

**Operations:**
1. Authorize (automatic capture)
2. Payment Sync

### Set 2: Full Refund Flow
Complete flow including refund and refund sync.

```bash
./test-connector.sh bambora --set 2
```

**Operations:**
1. Authorize (automatic capture)
2. Payment Sync
3. Refund
4. Refund Sync

### Set 3: Manual Capture Flow
Authorization with manual capture.

```bash
./test-connector.sh bambora --set 3
```

**Operations:**
1. Authorize (manual capture)
2. Capture

## Configuration

### Connector Configuration

Create a JSON config file in `configs/connectors/{connector}.json`:

```json
{
  "connector_name": "bambora",
  "credentials": {
    "auth_type": "body-key",
    "api_key": "your_api_key",
    "key1": "your_key1",
    "merchant_id": "your_merchant_id"
  },
  "server": {
    "address": "localhost:8000",
    "use_tls": false
  },
  "test_data": {
    "default_amount": 5000,
    "default_currency": "USD",
    "test_cards": {
      "mastercard_success": {
        "number": "5100000010001004",
        "cvc": "123",
        "exp_month": "12",
        "exp_year": "2030",
        "network": "MASTERCARD"
      }
    },
    "billing_address": {
      "first_name": "John",
      "last_name": "Doe",
      "line1": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "country": "US",
      "email": "john.doe@example.com",
      "phone": "1234567890",
      "phone_country_code": "1"
    }
  }
}
```

#### Authentication Types

The `auth_type` field in credentials determines how the connector authenticates:

**Available auth types:**
- `body-key` - API key sent in request body
- `header-key` - API key sent in headers only
- `signature-key` - Signature-based authentication
- `multi-key` - Multiple keys required

**Examples:**

```json
// Body Key Authentication (e.g., Bambora)
{
  "credentials": {
    "auth_type": "body-key",
    "api_key": "your_api_key",
    "key1": "your_key1",
    "merchant_id": "merchant_123"
  }
}

// Header Key Authentication
{
  "credentials": {
    "auth_type": "header-key",
    "api_key": "your_api_key",
    "merchant_id": "merchant_123"
  }
}

// Signature Key Authentication
{
  "credentials": {
    "auth_type": "signature-key",
    "api_key": "your_api_key",
    "secret_key": "your_secret_key",
    "merchant_id": "merchant_123"
  }
}

// Multi-Key Authentication
{
  "credentials": {
    "auth_type": "multi-key",
    "api_key": "your_api_key",
    "key1": "key1_value",
    "key2": "key2_value",
    "merchant_id": "merchant_123"
  }
}
```

The `auth_type` is sent as the `x-auth` header in gRPC requests.

### Environment Variable Overrides

Environment variables override config file values with priority: `ENV_VAR > config_file > default`

**Naming convention:** `{CONNECTOR_UPPER}_{KEY_UPPER}`

**Examples:**
```bash
# Override credentials
export BAMBORA_AUTH_TYPE="header-key"
export BAMBORA_API_KEY="production_key"
export BAMBORA_KEY1="production_key1"
export BAMBORA_MERCHANT_ID="prod_merchant_123"

# Override server
export BAMBORA_SERVER_ADDRESS="production.bambora.com:443"

# Override test data
export BAMBORA_DEFAULT_AMOUNT="10000"
export BAMBORA_DEFAULT_CURRENCY="EUR"

# Run with overrides
./test-connector.sh bambora --set 1
```

## Adding a New Connector

1. **Create connector config:**
```bash
cp configs/connectors/bambora.json configs/connectors/newconnector.json
# Edit the file with your connector's details
```

2. **Add connector-specific validation rules (optional):**

Edit `validation/rules/refund.json` to add connector-specific checks:

```json
{
  "connector_specific": {
    "newconnector": {
      "required_fields": [
        "connectorMetadata.custom_field"
      ],
      "critical_checks": [
        "Your connector-specific validation"
      ]
    }
  }
}
```

3. **Test the connector:**
```bash
./test-connector.sh newconnector --set 1
```

## Validation Framework

The framework includes comprehensive validation to prevent issues like those in PR #240:

### PR #240 Issue #1: Refund Status Logic
Don't assume all actions with `status: "success"` are successful refunds.

**Check:** Validates action type is "REFUND" before checking status.

### PR #240 Issue #3: Action Array Handling
RSync returns charge with actions array - must validate correct refund action.

**Check:** Ensures proper action selection by refund_id.

### Validation Rules Location
`validation/rules/{operation}.json`

## Interactive Mode

Run individual operations manually:

```bash
./test-connector.sh bambora --interactive
```

**Available operations:**
1. Authorize (Automatic Capture)
2. Authorize (Manual Capture)
3. Payment Sync
4. Capture
5. Refund
6. Refund Sync

Transaction IDs are automatically tracked between operations.

## Advanced Usage

### Debug Mode
```bash
DEBUG=true ./test-connector.sh bambora --set 1
```

### Custom Test Amounts
```bash
BAMBORA_DEFAULT_AMOUNT=10000 ./test-connector.sh bambora --set 1
```

### Multiple Connectors
```bash
for connector in bambora silverflow; do
    ./test-connector.sh "$connector" --set 1
done
```

## Logs

Detailed execution logs are saved to:
```
output/logs/test_{timestamp}.log
```

Logs include:
- Request headers and bodies
- Response JSON
- Validation results
- Error messages

## Requirements

- `bash` 4.0+ (for associative array support)
- `jq` (JSON processor)
- `grpcurl` (gRPC client)

**Install dependencies:**
```bash
# macOS
brew install bash jq grpcurl

# Linux
apt-get install jq
# grpcurl: https://github.com/fullstorydev/grpcurl#installation
```

**Important for macOS users:**
macOS ships with Bash 3.2 (from 2007) which doesn't support associative arrays. You need Bash 4.0+:

```bash
# Check your bash version
bash --version

# If it shows 3.2.x, install modern bash:
brew install bash

# Or if you're using Nix (like in this case):
# The scripts use #!/usr/bin/env bash which will find the first bash in your PATH
```

## Troubleshooting

### Missing required configuration
```
Error: Missing required configuration: API_KEY
```
**Solution:** Set the environment variable or add to config file:
```bash
export BAMBORA_API_KEY="your_key"
```

### Template file not found
```
Error: Template not found: templates/authorize-auto.json.template
```
**Solution:** Ensure you're running from the `test-grpc` directory:
```bash
cd test-grpc
./test-connector.sh bambora --set 1
```

### Bash version error (declare: -A: invalid option)
```
declare: -A: invalid option
declare: usage: declare [-afFirtx] [-p] [name[=value] ...]
```
**Solution:** You're using an old Bash version (3.2). Install Bash 4.0+:
```bash
# Check version
bash --version

# macOS - Install via Homebrew
brew install bash

# Then ensure scripts use the new bash (already configured with #!/usr/bin/env bash)
# Make sure your PATH includes the homebrew bash before /bin/bash
which bash  # Should show /usr/local/bin/bash or /opt/homebrew/bin/bash

# Or use full path
/usr/local/bin/bash /Users/yashasvi.kapil/grace-main/grace/test-grpc/test-connector.sh bambora --set 1
```

### Environment variable naming
**Issue:** Variables not being picked up

**Common mistake:** Using underscores incorrectly
```bash
# WRONG
export BAMBORA_KEY_1="..."  # Won't work

# CORRECT
export BAMBORA_KEY1="..."   # No underscore between KEY and 1
```

**Correct naming pattern:** `{CONNECTOR_UPPER}_{CONFIG_KEY_UPPER}`
- `BAMBORA_API_KEY` (not `BAMBORA_APIKEY`)
- `BAMBORA_KEY1` (not `BAMBORA_KEY_1`)
- `BAMBORA_MERCHANT_ID` (not `BAMBORA_MERCHANTID`)

### grpcurl connection failed
```
Error: grpcurl call failed with exit code: 1
```
**Solution:** Check server is running and address is correct:
```bash
# Check server
grpcurl -plaintext localhost:8000 list

# Or override server address
export BAMBORA_SERVER_ADDRESS="your-server:8000"
```

## Architecture

The framework follows the modular architecture pattern from `add-connector.sh`:

1. **Configuration Section** - Readonly constants for all paths
2. **Library Modules** - Separated concerns (logging, config, templates, etc.)
3. **Template Engine** - Simple `{{VAR}}` bash substitution
4. **Validation Framework** - JSON-based rules with jq expressions
5. **Test Sets** - Declarative JSON definitions

## Contributing

To add new features:

1. **New operation** - Add template in `templates/`, validation rules in `validation/rules/`, and function in `lib/grpc-client.sh`
2. **New validation check** - Update `validation/rules/{operation}.json`
3. **New test set** - Create JSON in `test-sets/`

## Migration from Legacy Script

The old monolithic script is available as `test-connector.legacy.sh`.

**Key differences:**
- Configuration is now in JSON files (was embedded in script)
- Request templates are separate files (was embedded in script)
- Validation rules are declarative (was embedded in script)
- Environment variables override configs (new feature)

## License

Same as parent project.
