# PostmanToCypress Module

Convert Postman collections into executable, deterministic test structures using AI-powered analysis.

## Overview

The PostmanToCypress module analyzes Postman collection JSON files and automatically:

1. **Parses** API endpoints with full metadata extraction
2. **Categorizes** APIs using Claude subagents (authorize, capture, psync, other)
3. **Generates** deterministic test structures inspired by Cypress patterns
4. **Collects** required credentials dynamically
5. **Executes** tests headlessly or interactively

## Features

- 🤖 **AI-Powered Categorization**: Claude analyzes APIs to identify payment flow patterns
- 🔄 **Deterministic Execution**: Sequential test flows with proper dependencies
- 🔑 **Dynamic Credentials**: Automatically detects and collects required authentication
- 🎯 **Test Generation**: Creates Python test structures with assertions
- 🚀 **Headless Execution**: Fully automated testing without user interaction
- 📊 **Comprehensive Reporting**: Detailed execution summaries and results

## Installation

The module is included with GRACE. Ensure you have the dependencies:

```bash
cd grace
uv sync
```

## Usage

### Basic Usage

```bash
# Convert a Postman collection
grace postman-to-cypress collection.json

# Specify output directory
grace postman-to-cypress collection.json --output ./my_tests

# Run in headless mode
grace postman-to-cypress collection.json --headless

# Enable verbose output
grace postman-to-cypress collection.json --verbose
```

### Advanced Usage

```bash
# Full workflow with custom output and headless execution
grace postman-to-cypress payment_api.json \\
  --output ./payment_tests \\
  --headless \\
  --verbose
```

## Workflow Steps

### 1. Collection Parsing

Extracts API endpoints from Postman JSON:

```json
{
  "info": {
    "name": "Payment API",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "Create Payment",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/payments",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\\"amount\\": 1000, \\"currency\\": \\"USD\\"}"
        }
      }
    }
  ]
}
```

### 2. AI Categorization

Claude analyzes each endpoint:

- **authorize**: Payment creation, authorization, intent APIs
- **capture**: Payment capture, confirmation, settlement APIs  
- **psync**: Payment status, sync, retrieval APIs
- **other**: Customer management, webhooks, refunds, etc.

### 3. Test Generation

Creates Python test files with:

- Sequential execution order
- Proper assertions based on API type
- Variable passing between tests
- Error handling and timeouts

Example generated test:

```python
class Test001CreatePayment:
    def execute(self) -> Dict[str, Any]:
        # Setup
        method = "POST"
        url = "https://api.example.com/payments"
        headers = get_credentials().get("headers", {})
        body = {
            "amount": 1000,
            "currency": "USD"
        }
        
        # Execute request
        response = requests.request(method, url, headers=headers, json=body)
        
        # Assertions
        assertion_results = []
        
        # Check status code
        passed = response.status_code in [200, 201, 202]
        assertion_results.append({
            'description': 'Check POST request succeeds',
            'passed': passed
        })
        
        # Store payment ID for future tests
        if passed and 'id' in response.json():
            store_variable('payment_id', response.json()['id'])
        
        return {
            "success": all(a["passed"] for a in assertion_results),
            "assertions": assertion_results,
            "response_data": response.json()
        }
```

### 4. Credential Collection

Dynamic authentication setup:

- **Bearer Token**: `Enter your API key/Bearer token:`
- **Basic Auth**: `Enter username:` / `Enter password:`
- **API Key**: `Enter api_key:`
- **OAuth2**: `Enter access_token:` or `Client ID/Secret`

### 5. Test Execution

Runs generated tests with:

- Sequential execution based on dependencies
- Response validation and assertions
- Variable storage between tests
- Comprehensive error reporting

## Generated Files

```
generated_tests/
├── test_000_create_payment.py       # Individual test files
├── test_001_capture_payment.py
├── test_002_get_payment_status.py
├── test_runner.py                   # Main test runner
├── test_config.py                   # Configuration and credentials
└── credentials.json                 # Stored credentials (secure)
```

## Examples

### Example 1: Payment API

```bash
# Convert payment processor collection
grace postman-to-cypress stripe_collection.json --output ./stripe_tests

# Output:
# ✅ Postman to Cypress conversion completed successfully!
# 📊 Conversion Summary:
#   • Collection: Stripe Payment API
#   • API Endpoints: 5
#   • Generated Tests: 5
#   • Output Directory: ./stripe_tests
# 📋 Next Steps:
#   • Review generated tests in: ./stripe_tests
#   • Run tests: cd ./stripe_tests && python test_runner.py
```

### Example 2: Headless Execution

```bash
# Set credentials via environment
export BEARER_TOKEN="sk_test_..."

# Run headless conversion and execution
grace postman-to-cypress paypal_collection.json --headless --verbose

# Output:
# 🚀 Starting Postman to Cypress conversion...
# 🤖 Starting AI categorization of 8 endpoints...
# 🏗️ Generating test structures for 8 endpoints...
# 🔑 Found existing credentials, using those...
# 🚀 Test Execution Results:
#   • Total Tests: 8
#   • Passed: 7
#   • Failed: 1
#   • Success Rate: 87.5%
```

### Example 3: Interactive Mode

```bash
grace postman-to-cypress adyen_collection.json

# Interactive prompts:
# 🔐 Credential Collection for Adyen Payment API
# 📝 API key authentication using X-API-Key
# Enter X-API-Key (input hidden): ****
# 
# Do you want to execute the generated tests? (y/n): y
# 🎯 Starting test execution for Adyen Payment API
# ▶️  Running test 1/4: Create Payment Intent
# ✅ Test passed in 245ms
```

## Configuration

### Environment Variables

```bash
# Authentication
export API_KEY="your_api_key"
export BEARER_TOKEN="your_bearer_token"
export USERNAME="your_username"
export PASSWORD="your_password"

# Workflow settings
export CREDENTIALS_FILE="./custom_creds.json"
```

### Custom Credentials File

```json
{
  "headers": {
    "Authorization": "Bearer sk_test_...",
    "Content-Type": "application/json",
    "X-API-Key": "ak_test_..."
  },
  "api_key": "your_api_key",
  "client_id": "your_client_id"
}
```

## API Categorization Patterns

The AI categorization follows these patterns:

### Authorize APIs
- Payment creation (`POST /payments`)
- Payment intents (`POST /payment_intents`)
- Authorization (`POST /authorize`)
- Charges (`POST /charges`)

### Capture APIs  
- Payment capture (`POST /payments/{id}/capture`)
- Confirmation (`POST /payments/{id}/confirm`)
- Settlement (`POST /settle`)

### Psync APIs
- Payment retrieval (`GET /payments/{id}`)
- Status check (`GET /payments/{id}/status`)
- Transaction sync (`GET /transactions/{id}`)

### Other APIs
- Customer management (`POST /customers`)
- Webhooks (`POST /webhooks`)
- Refunds (`POST /refunds`)

## Error Handling

Common issues and solutions:

### Collection File Not Found
```bash
❌ Conversion failed: Collection file not found: missing.json
```
**Solution**: Verify the file path exists

### Invalid JSON Format
```bash
❌ Conversion failed: Collection file must be a JSON file
```
**Solution**: Ensure file has `.json` extension and valid JSON content

### Missing Credentials
```bash
❌ Bearer token required but not found in environment variables
```
**Solution**: Set environment variables or run in interactive mode

### AI Categorization Failure
```bash
⚠️ Failed to categorize endpoint 'Custom API': API service unavailable
```
**Solution**: Check AI service configuration, will fallback to pattern-based categorization

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Grace
        run: |
          cd grace
          uv sync
      - name: Run API Tests
        env:
          BEARER_TOKEN: ${{ secrets.API_KEY }}
        run: |
          cd grace
          grace postman-to-cypress api_collection.json --headless --verbose
```

### Docker Example

```dockerfile
FROM python:3.9

COPY grace/ /app/grace/
WORKDIR /app/grace

RUN uv sync

ENV BEARER_TOKEN=""
ENV HEADLESS=true

CMD ["grace", "postman-to-cypress", "collection.json", "--headless"]
```

## Best Practices

1. **Collection Organization**: Group related APIs in folders within Postman
2. **Variable Usage**: Use Postman variables for dynamic values (`{{base_url}}`, `{{token}}`)
3. **Authentication**: Include auth configuration in collection or environment
4. **Documentation**: Add descriptions to requests for better AI categorization
5. **Testing**: Validate generated tests with sample data before production use

## Limitations

- Currently supports JSON-based APIs only
- OAuth flows require manual token provision
- File uploads not yet supported
- Limited to HTTP/HTTPS protocols
- AI categorization requires internet connection

## Troubleshooting

### Enable Debug Mode

```bash
grace postman-to-cypress collection.json --verbose
```

### Check Generated Files

```bash
# Review test structure
cat generated_tests/test_runner.py

# Check configuration
cat generated_tests/test_config.py

# Validate credentials
cat generated_tests/credentials.json
```

### Manual Test Execution

```bash
cd generated_tests
python test_config.py  # Setup credentials
python test_runner.py  # Run tests
```

## Contributing

To extend the PostmanToCypress module:

1. **Add new auth types**: Extend `collect_credentials.py`
2. **Improve categorization**: Update prompts in `categorize_apis.py`
3. **Custom assertions**: Modify `generate_tests.py`
4. **New output formats**: Extend test generation templates

## Support

For issues and questions:

1. Check the verbose output for detailed error messages
2. Review generated test files for debugging
3. Validate Postman collection structure
4. Ensure proper authentication configuration