# Curl Script Generator Guide

## Purpose

This guide explains how AI generates curl test scripts by extracting information from the tech spec and combining it with user-provided credentials.

## Core Principle

**100% of curl structure comes from tech spec. User only provides credential values.**

---

## Input Sources

### From Tech Spec

Tech specs can provide information in **two formats**:

#### **Option A: YAML Sections** (Preferred - Structured and Easy to Parse)

```yaml
api_config:
  test_url: "https://api.stripe.com"

auth:
  headers:
    - name: "Authorization"
      format: "Bearer {api_key}"

authorize:
  method: "POST"
  path: "/v1/payment_intents"
  request:
    content_type: "application/x-www-form-urlencoded"
    test_example: "amount=1000&currency=usd..."
  response:
    success_status_codes: [200, 201]
    id_field: "id"
    status_field: "status"
```

**Extraction from YAML:**
- Direct parsing of structured data
- Field access: `api_config.test_url`, `authorize.method`, etc.
- Easy to validate completeness
- Minimal risk of extraction errors

#### **Option B: Prose/Markdown** (Fallback - Natural Language Understanding)

When tech spec lacks YAML structure, AI must extract information from natural language prose:

```markdown
## API Configuration

Stripe's test API is available at `https://api.stripe.com`. All requests must include authentication.

## Authentication

Pass your API key in the Authorization header using Bearer token format:
```
Authorization: Bearer sk_test_xxxxxxxxxxxxx
```

## Authorize Payment

To authorize a payment, send a POST request to `/v1/payment_intents` with form-encoded data:

**Required Parameters:**
- `amount` (integer): Payment amount in cents
- `currency` (string): ISO currency code like "usd"
- `payment_method_types[]` (array): Payment methods, e.g., "card"
- `capture_method` (string): Use "manual" for separate capture

**Example Request:**
```
amount=1000&currency=usd&payment_method_types[]=card&capture_method=manual
```

The API returns a JSON response with status code 200 or 201. The response contains:
- `id` - The payment intent ID
- `status` - Current status (e.g., "requires_capture")
- `amount` - Confirmed amount
```

**Extraction from Prose via NLP:**

AI analyzes natural language to extract structured information:

| **Element** | **Extraction Pattern** | **Example** | **Result** |
|-------------|----------------------|-------------|------------|
| **Base URL** | "API is at", "endpoint is", "base URL", "test environment at" | "Stripe's test API is available at `https://api.stripe.com`" | `test_url = "https://api.stripe.com"` |
| **HTTP Method** | "send a POST", "POST request to", "make a GET call", "PUT to" | "send a POST request to `/v1/payment_intents`" | `method = "POST"` |
| **Endpoint Path** | "request to /path", "endpoint: /path", "POST /path" | "to `/v1/payment_intents`" | `path = "/v1/payment_intents"` |
| **Content Type** | "JSON payload", "form-encoded", "XML document", "send JSON" | "with form-encoded data" | `content_type = "application/x-www-form-urlencoded"` |
| **Auth Format** | "Authorization: format", "Bearer token", "API key in header" | "Authorization: Bearer sk_test_xxx" | `auth_format = "Bearer {api_key}"` |
| **Request Body** | "Example:", "Sample request:", code blocks after "Request:" | Code block with example | `test_example = "amount=1000&..."` |
| **Response Fields** | "returns", "response contains", "includes field", "has property" | "response contains: `id`, `status`" | `id_field = "id"`, `status_field = "status"` |
| **Success Codes** | "status code 200", "returns 201", "success: 200-299" | "status code 200 or 201" | `success_codes = [200, 201]` |

**Common Prose Patterns:**

```markdown
Pattern: "POST to /endpoint"
→ Extract: method=POST, path=/endpoint

Pattern: "JSON payload" / "send JSON" / "JSON body"
→ Extract: content_type=application/json

Pattern: "form-encoded" / "URL-encoded" / "form data"
→ Extract: content_type=application/x-www-form-urlencoded

Pattern: "XML document" / "XML body"
→ Extract: content_type=application/xml

Pattern: "Example:" / "Sample request:" [code block]
→ Extract: test_example=[content of code block]

Pattern: "Authorization: Bearer TOKEN"
→ Extract: auth_format="Bearer {api_key}"

Pattern: "X-API-Key: YOUR_KEY"
→ Extract: auth_format="{api_key}", header_name="X-API-Key"

Pattern: "response includes 'id' field"
→ Extract: id_field="id"

Pattern: "status code 200" / "returns 201" / "HTTP 200 OK"
→ Extract: success_status_codes=[200] or [201]
```

**AI Extraction Algorithm:**

1. **Scan for flow sections**: Look for headings like "Authorize", "Capture", "Refund"
2. **Within each section**, search for:
   - HTTP method keywords (POST, GET, PUT, DELETE, PATCH)
   - Endpoint paths (text in backticks starting with `/`)
   - Content type indicators (JSON, form-encoded, XML)
   - Example request bodies (code blocks, "Example:", "Sample:")
   - Authentication descriptions (header formats)
   - Response field mentions (field names in backticks or quotes)
   - Success status codes (200, 201, etc.)
3. **Extract and structure** all found information into internal YAML-like structure
4. **Validate completeness**: Ensure all required fields extracted for curl generation
5. **Flag missing info**: If critical fields missing, ask user or mark as validation blocker

### From User (credentials.json)
```json
{
  "api_key": "sk_test_xxxxx",
  "api_secret": "",
  "key1": ""
}
```

---

## Generation Process

### Step 1: Extract Base Configuration

#### **From YAML (Structured Parsing)**

```bash
#!/bin/bash
# Extract from tech spec YAML sections using grep/awk

# Base URL
BASE_URL=$(grep -A5 "api_config:" tech_spec.md | grep "test_url:" | cut -d'"' -f2)
# Result: "https://api.stripe.com"

# For specific flow (e.g., authorize)
METHOD=$(grep -A20 "authorize:" tech_spec.md | grep "method:" | cut -d'"' -f2)
# Result: "POST"

PATH=$(grep -A20 "authorize:" tech_spec.md | grep "path:" | cut -d'"' -f2)
# Result: "/v1/payment_intents"

CONTENT_TYPE=$(grep -A20 "authorize:" tech_spec.md | grep "content_type:" | cut -d'"' -f2)
# Result: "application/x-www-form-urlencoded"
```

#### **From Prose (NLP Extraction)**

When tech spec is pure Markdown without YAML, AI reads and extracts:

```markdown
**Tech Spec Prose (example):**

## API Configuration
Stripe's test API is available at https://api.stripe.com

## Authorize Payment
To authorize a payment, send a POST request to /v1/payment_intents with
form-encoded parameters: amount=1000&currency=usd&payment_method_types[]=card

The API returns JSON with status 200 or 201 containing 'id' and 'status' fields.
```

**AI Extraction Process:**

```python
# Pseudocode for AI extraction from prose

def extract_from_prose(tech_spec_markdown):
    extracted = {}

    # 1. Extract Base URL
    # Look for: "API at", "endpoint", "base URL"
    base_url_patterns = [
        r"API (?:is )?(?:available )?at ([https?://][^\s]+)",
        r"base URL:?\s*([https?://][^\s]+)",
        r"test environment:?\s*([https?://][^\s]+)"
    ]
    extracted['test_url'] = find_first_match(tech_spec, base_url_patterns)
    # Result: "https://api.stripe.com"

    # 2. Extract HTTP Method
    # Look for: "POST to", "send POST", "GET request"
    method_patterns = [
        r"(POST|GET|PUT|DELETE|PATCH) (?:request )?to",
        r"send (?:a )?(POST|GET|PUT|DELETE|PATCH)",
        r"make (?:a )?(POST|GET|PUT|DELETE|PATCH)"
    ]
    extracted['method'] = find_first_match(section, method_patterns)
    # Result: "POST"

    # 3. Extract Endpoint Path
    # Look for: paths in backticks after method, "/v1/..." patterns
    path_patterns = [
        r"`(/[^`]+)`",  # Path in backticks
        r"(?:to|endpoint:?)\s+(/v\d+/[\w/{}]+)",  # Explicit path mention
    ]
    extracted['path'] = find_first_match(section, path_patterns)
    # Result: "/v1/payment_intents"

    # 4. Extract Content Type
    # Look for: "JSON", "form-encoded", "XML"
    content_type_mapping = {
        r"(?:send |with )?JSON": "application/json",
        r"form-encoded|URL-encoded|form data": "application/x-www-form-urlencoded",
        r"XML": "application/xml"
    }
    extracted['content_type'] = map_first_match(section, content_type_mapping)
    # Result: "application/x-www-form-urlencoded"

    # 5. Extract Request Body Example
    # Look for: code blocks after "Example:", "Sample:", "Parameters:"
    # Or inline code with request structure
    code_blocks = extract_code_blocks(section)
    for block in code_blocks:
        if looks_like_request_body(block):
            extracted['test_example'] = block.strip()
            break
    # Result: "amount=1000&currency=usd&payment_method_types[]=card"

    # 6. Extract Response Field Names
    # Look for: "returns 'field'", "response contains field", "`field` in response"
    field_patterns = [
        r"returns.*?['\"`](\w+)['\"`]",
        r"response (?:contains|includes|has).*?['\"`](\w+)['\"`]",
        r"['\"`](\w+)['\"`].*?(?:field|property|attribute)"
    ]
    extracted['id_field'] = find_field_match(section, ['id', 'payment_id', 'transaction_id'])
    extracted['status_field'] = find_field_match(section, ['status', 'state'])
    # Result: id_field="id", status_field="status"

    # 7. Extract Success Status Codes
    # Look for: "status 200", "returns 201", "HTTP 200 OK"
    status_patterns = [
        r"(?:status|HTTP)\s+(\d{3})",
        r"returns\s+(\d{3})",
        r"(\d{3})\s+(?:OK|Created|Success)"
    ]
    extracted['success_status_codes'] = find_all_matches(section, status_patterns)
    # Result: [200, 201]

    return extracted

# Example execution:
authorize_section = extract_section(tech_spec, "Authorize")
config = extract_from_prose(authorize_section)

# config = {
#     'test_url': 'https://api.stripe.com',
#     'method': 'POST',
#     'path': '/v1/payment_intents',
#     'content_type': 'application/x-www-form-urlencoded',
#     'test_example': 'amount=1000&currency=usd&payment_method_types[]=card',
#     'id_field': 'id',
#     'status_field': 'status',
#     'success_status_codes': [200, 201]
# }
```

**Result:** AI constructs internal structured representation from prose, then proceeds with standard curl generation.

```bash
# After AI extraction, same variables available as with YAML:
BASE_URL="https://api.stripe.com"
METHOD="POST"
PATH="/v1/payment_intents"
CONTENT_TYPE="application/x-www-form-urlencoded"
REQUEST_BODY="amount=1000&currency=usd&payment_method_types[]=card"
```

### Step 2: Build Authentication Headers

```bash
# Extract auth header format from tech spec
AUTH_FORMAT=$(grep -A10 "auth:" tech_spec.md | grep "format:" | cut -d'"' -f2)
# Result: "Bearer {api_key}"

# Load user credential
API_KEY=$(jq -r '.api_key' credentials.json)
# Result: "sk_test_xxxxx"

# Replace placeholder with actual credential
AUTH_HEADER="${AUTH_FORMAT/\{api_key\}/$API_KEY}"
# Result: "Bearer sk_test_xxxxx"
```

### Step 3: Extract Request Body

```bash
# Extract test example from tech spec
# The test_example contains the complete request body to use
REQUEST_BODY=$(sed -n '/test_example: |/,/^[^ ]/p' tech_spec.md | sed '1d;$d' | tr -d '\n')
# Result: "amount=1000&currency=usd&payment_method_types[]=card..."
```

### Step 4: Generate Complete Curl Command

```bash
#!/bin/bash
# Auto-generated curl test script
# Flow: Authorize
# Generated from tech spec

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDS_FILE="$SCRIPT_DIR/../credentials.json"
RESPONSE_FILE="$SCRIPT_DIR/../responses/authorize_response.json"
STATE_FILE="$SCRIPT_DIR/../state.json"

# === CONFIGURATION FROM TECH SPEC ===
BASE_URL="https://api.stripe.com"
ENDPOINT="/v1/payment_intents"
METHOD="POST"
CONTENT_TYPE="application/x-www-form-urlencoded"

# === LOAD USER CREDENTIALS ===
if [ ! -f "$CREDS_FILE" ]; then
  echo "❌ Credentials file not found: $CREDS_FILE"
  exit 1
fi

API_KEY=$(jq -r '.api_key' "$CREDS_FILE")
API_SECRET=$(jq -r '.api_secret // empty' "$CREDS_FILE")
KEY1=$(jq -r '.key1 // empty' "$CREDS_FILE")

# === BUILD AUTH HEADER (format from tech spec) ===
AUTH_HEADER="Authorization: Bearer $API_KEY"

# === REQUEST BODY FROM TECH SPEC ===
REQUEST_BODY='amount=1000&currency=usd&payment_method_types[]=card&capture_method=manual&description=GRACE-UCS+validation'

echo "🧪 Testing Authorize Flow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Connector: Stripe"
echo "Endpoint: $METHOD $BASE_URL$ENDPOINT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# === EXECUTE CURL ===
HTTP_CODE=$(curl -X "$METHOD" "$BASE_URL$ENDPOINT" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: $CONTENT_TYPE" \
  -d "$REQUEST_BODY" \
  -o "$RESPONSE_FILE" \
  -w "%{http_code}" \
  -s)

echo "HTTP Status: $HTTP_CODE"
echo ""

# === VALIDATE RESPONSE (expectations from tech spec) ===
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  echo "✅ HTTP Status: SUCCESS"

  # Tech spec says: id_field = "id"
  PAYMENT_ID=$(jq -r '.id // empty' "$RESPONSE_FILE")

  # Tech spec says: status_field = "status"
  STATUS=$(jq -r '.status // empty' "$RESPONSE_FILE")

  if [ -n "$PAYMENT_ID" ]; then
    echo "✅ Payment ID received: $PAYMENT_ID"

    # Save state for subsequent tests
    jq -n \
      --arg payment_id "$PAYMENT_ID" \
      --arg status "$STATUS" \
      '{authorize: {payment_id: $payment_id, status: $status, timestamp: now|todate}}' \
      > "$STATE_FILE"

    echo "✅ State saved for next tests"
  else
    echo "❌ No payment ID found in response"
    echo "Expected field: id"
    jq '.' "$RESPONSE_FILE"
    exit 1
  fi

  if [ -n "$STATUS" ]; then
    echo "✅ Payment Status: $STATUS"
  fi

else
  echo "❌ HTTP Status: FAILED ($HTTP_CODE)"
  echo ""
  echo "Error Response:"
  jq '.' "$RESPONSE_FILE" 2>/dev/null || cat "$RESPONSE_FILE"
  exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Authorize Flow: PASSED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

---

## Handling Different Request Formats

### JSON Request Body

**Tech Spec:**
```yaml
authorize:
  request:
    content_type: "application/json"
    test_example: |
      {
        "amount": 1000,
        "currency": "USD",
        "payment_method": {
          "type": "card",
          "card": {
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
          }
        }
      }
```

**Generated Curl:**
```bash
REQUEST_BODY='{
  "amount": 1000,
  "currency": "USD",
  "payment_method": {
    "type": "card",
    "card": {
      "number": "4242424242424242",
      "exp_month": 12,
      "exp_year": 2025,
      "cvc": "123"
    }
  }
}'

curl -X POST "$BASE_URL$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY"
```

### Form URL Encoded

**Tech Spec:**
```yaml
authorize:
  request:
    content_type: "application/x-www-form-urlencoded"
    test_example: "amount=1000&currency=usd&card[number]=4242424242424242&card[exp_month]=12"
```

**Generated Curl:**
```bash
REQUEST_BODY='amount=1000&currency=usd&card[number]=4242424242424242&card[exp_month]=12'

curl -X POST "$BASE_URL$ENDPOINT" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "$REQUEST_BODY"
```

### XML Request Body

**Tech Spec:**
```yaml
authorize:
  request:
    content_type: "application/xml"
    test_example: |
      <?xml version="1.0"?>
      <payment>
        <amount>1000</amount>
        <currency>USD</currency>
      </payment>
```

**Generated Curl:**
```bash
REQUEST_BODY='<?xml version="1.0"?>
<payment>
  <amount>1000</amount>
  <currency>USD</currency>
</payment>'

curl -X POST "$BASE_URL$ENDPOINT" \
  -H "Content-Type: application/xml" \
  -d "$REQUEST_BODY"
```

### GET Request (No Body)

**Tech Spec:**
```yaml
psync:
  method: "GET"
  path: "/v1/payments/{payment_id}"
  request:
    content_type: null
    test_example: null
```

**Generated Curl:**
```bash
# No request body for GET
curl -X GET "$BASE_URL$ENDPOINT" \
  -H "$AUTH_HEADER"
```

---

## Handling URL Parameters

### Dynamic Path Parameters

**Tech Spec:**
```yaml
capture:
  path: "/v1/payments/{payment_id}/capture"
  url_params:
    - payment_id: "From authorize response"
```

**Generated Script:**
```bash
# Read payment_id from state file (saved by authorize test)
PAYMENT_ID=$(jq -r '.authorize.payment_id' "$STATE_FILE")

if [ -z "$PAYMENT_ID" ]; then
  echo "❌ No payment_id found. Run authorize test first."
  exit 1
fi

# Replace {payment_id} in endpoint path
ENDPOINT="/v1/payments/${PAYMENT_ID}/capture"

# Then execute curl
curl -X POST "$BASE_URL$ENDPOINT" ...
```

### Query Parameters

**Tech Spec:**
```yaml
psync:
  path: "/v1/payments/{payment_id}"
  query_params:
    expand: "customer"
```

**Generated Script:**
```bash
ENDPOINT="/v1/payments/${PAYMENT_ID}?expand=customer"

curl -X GET "$BASE_URL$ENDPOINT" ...
```

---

## Handling Multiple Authentication Headers

**Tech Spec:**
```yaml
auth:
  headers:
    - name: "Authorization"
      format: "Bearer {api_key}"
      required: true

    - name: "X-API-Secret"
      format: "{api_secret}"
      required: true

    - name: "X-Merchant-ID"
      format: "{key1}"
      required: false
```

**Generated Curl:**
```bash
# Build all headers from tech spec
AUTH_HEADER_1="Authorization: Bearer $API_KEY"
AUTH_HEADER_2="X-API-Secret: $API_SECRET"

# Optional header (only if key1 provided)
if [ -n "$KEY1" ]; then
  AUTH_HEADER_3="X-Merchant-ID: $KEY1"
  curl -X POST "$BASE_URL$ENDPOINT" \
    -H "$AUTH_HEADER_1" \
    -H "$AUTH_HEADER_2" \
    -H "$AUTH_HEADER_3" \
    -H "Content-Type: $CONTENT_TYPE" \
    -d "$REQUEST_BODY"
else
  curl -X POST "$BASE_URL$ENDPOINT" \
    -H "$AUTH_HEADER_1" \
    -H "$AUTH_HEADER_2" \
    -H "Content-Type: $CONTENT_TYPE" \
    -d "$REQUEST_BODY"
fi
```

---

## Test Script Template

**Generic template for any flow:**

```bash
#!/bin/bash
# Auto-generated from tech spec
# Flow: {{FLOW_NAME}}
# Generated: {{TIMESTAMP}}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDS_FILE="$SCRIPT_DIR/../credentials.json"
RESPONSE_FILE="$SCRIPT_DIR/../responses/{{flow_name}}_response.json"
STATE_FILE="$SCRIPT_DIR/../state.json"

# === FROM TECH SPEC ===
BASE_URL="{{api_config.test_url}}"
ENDPOINT="{{flow.path}}"  # May need {id} replacement
METHOD="{{flow.method}}"
CONTENT_TYPE="{{flow.request.content_type}}"

# === LOAD CREDENTIALS ===
API_KEY=$(jq -r '.api_key' "$CREDS_FILE")
API_SECRET=$(jq -r '.api_secret // empty' "$CREDS_FILE")
KEY1=$(jq -r '.key1 // empty' "$CREDS_FILE")

# === BUILD AUTH (format from tech spec) ===
{{#each auth.headers}}
{{#if required}}
HEADER_{{@index}}="{{name}}: {{format}}"  # Replace {placeholders} with credentials
{{/if}}
{{/each}}

# === HANDLE PATH PARAMETERS (if needed) ===
{{#if flow.url_params}}
# Read required IDs from state
{{#each flow.url_params}}
{{PARAM_NAME}}=$(jq -r '.{{source}}.{{field}}' "$STATE_FILE")
ENDPOINT="${ENDPOINT/\{{{PARAM_NAME}}\}/${{PARAM_NAME}}}"
{{/each}}
{{/if}}

# === REQUEST BODY FROM TECH SPEC ===
{{#if flow.request.test_example}}
REQUEST_BODY='{{flow.request.test_example}}'
{{/if}}

# === EXECUTE CURL ===
echo "🧪 Testing {{FLOW_NAME}} Flow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HTTP_CODE=$(curl -X "$METHOD" "$BASE_URL$ENDPOINT" \
  {{#each auth.headers}}
  -H "$HEADER_{{@index}}" \
  {{/each}}
  -H "Content-Type: $CONTENT_TYPE" \
  {{#if flow.request.test_example}}
  -d "$REQUEST_BODY" \
  {{/if}}
  -o "$RESPONSE_FILE" \
  -w "%{http_code}" \
  -s)

# === VALIDATE (expectations from tech spec) ===
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  echo "✅ HTTP Status: SUCCESS ($HTTP_CODE)"

  # Extract ID field (from tech spec)
  {{#if flow.response.id_field}}
  ID=$(jq -r '.{{flow.response.id_field}} // empty' "$RESPONSE_FILE")
  if [ -n "$ID" ]; then
    echo "✅ ID received: $ID"
    # Save to state for dependent tests
    jq --arg id "$ID" '.{{flow_name}}.{{flow.response.id_field}} = $id' "$STATE_FILE" > tmp && mv tmp "$STATE_FILE"
  fi
  {{/if}}

  # Extract status field (from tech spec)
  {{#if flow.response.status_field}}
  STATUS=$(jq -r '.{{flow.response.status_field}} // empty' "$RESPONSE_FILE")
  echo "✅ Status: $STATUS"
  {{/if}}

else
  echo "❌ HTTP Status: FAILED ($HTTP_CODE)"
  jq '.' "$RESPONSE_FILE" 2>/dev/null || cat "$RESPONSE_FILE"
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ {{FLOW_NAME}} Flow: PASSED"
```

---

## Master Test Runner

**Script to run all 6 tests in sequence:**

```bash
#!/bin/bash
# Master test runner for tech spec validation
# Runs all 6 flow tests in sequence

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════╗"
echo "║  Tech Spec Credibility Validation     ║"
echo "║  Connector: {{CONNECTOR_NAME}}         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Test sequence with descriptions
TESTS=(
  "01_authorize.sh:Authorize Flow:Creates payment authorization"
  "02_capture.sh:Capture Flow:Captures authorized payment"
  "03_void.sh:Void Flow:Cancels authorization"
  "04_refund.sh:Refund Flow:Refunds captured payment"
  "05_psync.sh:Payment Sync Flow:Retrieves payment status"
  "06_rsync.sh:Refund Sync Flow:Retrieves refund status"
)

PASSED=0
FAILED=0
FAILED_TESTS=()

for test in "${TESTS[@]}"; do
  IFS=':' read -r script name description <<< "$test"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📋 $name"
  echo "   $description"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if bash "$SCRIPT_DIR/$script"; then
    ((PASSED++))
    echo "✅ $name: PASSED"
  else
    ((FAILED++))
    FAILED_TESTS+=("$name")
    echo "❌ $name: FAILED"
  fi
  echo ""

  # Rate limiting delay (from tech spec)
  sleep 0.2
done

echo "╔════════════════════════════════════════╗"
echo "║  Validation Results Summary            ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "✅ Passed: $PASSED/6"
echo "❌ Failed: $FAILED/6"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "🎉 All tests passed!"
  echo "✅ Tech spec is credible and validated."
  exit 0
else
  echo "⚠️  Some tests failed:"
  for test in "${FAILED_TESTS[@]}"; do
    echo "  - $test"
  done
  echo ""
  echo "📄 Review credibility_report.md for details"
  exit 1
fi
```

---

## Key Takeaways

1. **Everything from tech spec** - URLs, endpoints, headers, body structure, validation rules
2. **User provides only credentials** - api_key, api_secret, key1 values
3. **AI assembles and executes** - Combines tech spec + credentials → curl scripts
4. **State management** - Tests share state via state.json for dependent operations
5. **Validation built-in** - Each script validates response against tech spec expectations
6. **Dual-mode extraction**:
   - **YAML (preferred)**: Direct structured parsing, minimal errors
   - **Prose (fallback)**: NLP extraction from natural language, requires careful pattern matching

## Extraction Mode Selection

When generating curl scripts, AI determines extraction mode:

```python
def select_extraction_mode(tech_spec_content):
    # Check for YAML sections
    yaml_indicators = [
        'api_config:',
        'authorize:',
        'test_url:',
        'method:',
        'test_example:'
    ]

    if any(indicator in tech_spec_content for indicator in yaml_indicators):
        return "YAML_MODE"  # Preferred - structured parsing
    else:
        return "PROSE_MODE"  # Fallback - NLP extraction

# Both modes produce same internal structure for curl generation
```

This dual-mode approach ensures tech spec completeness and accuracy validation works regardless of tech spec format!
