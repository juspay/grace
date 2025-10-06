# Tech Spec Validation YAML Sections

**IMPORTANT: Add these YAML sections to the generated tech spec for validation testing.**

These sections enable tech spec credibility validation by providing all information needed to generate curl test scripts.

---

## 🔧 API Configuration

Add this section after the connector overview:

```yaml
api_config:
  # Base URLs for different environments
  production_url: "https://api.{{connector}}.com"
  sandbox_url: "https://sandbox.{{connector}}.com"
  test_url: "https://api-test.{{connector}}.com"  # Used for validation testing

  # API versioning
  api_version: "v1"
  version_in_path: true  # true if version appears in URL path like /v1/payments
  version_header: null   # or header name if version sent in header like "API-Version"

  # Rate limiting (for test script delays)
  rate_limit:
    requests_per_second: 10
    test_delay_ms: 200  # Delay between test scripts to avoid rate limiting
```

---

## 🔐 Authentication Configuration

```yaml
auth:
  # Authentication type
  type: "bearer_token"
  # Options: bearer_token, basic_auth, api_key_header, custom_headers, oauth2

  # Header configuration (will be used in curl scripts)
  headers:
    - name: "Authorization"
      format: "Bearer {api_key}"  # {api_key} will be replaced with user's credential
      required: true
      static: false  # false means value comes from credentials

    - name: "X-API-Version"
      format: "2023-10-16"
      required: false
      static: true  # true means this is a fixed value, not from credentials

  # Credential requirements (describes what user needs to provide)
  credentials_required:
    api_key:
      description: "API secret key for authentication (e.g., sk_test_xxxxx)"
      example_format: "sk_test_xxxxxxxxxxxxx"
      required: true
      env_var: "{{CONNECTOR}}_SECRET_KEY"

    api_secret:
      description: "Additional secret for request signing (if needed)"
      example_format: "secret_xxxxxxxxxxxxx"
      required: false
      env_var: "{{CONNECTOR}}_API_SECRET"

    key1:
      description: "Merchant ID or additional identifier (if needed)"
      example_format: "merchant_12345"
      required: false
      env_var: "{{CONNECTOR}}_MERCHANT_ID"
```

---

## 📡 Flow API Specifications

### Authorize Flow

```yaml
authorize:
  # Endpoint configuration
  method: "POST"
  path: "/v1/payments"
  full_url: "{base_url}/v1/payments"

  # Request configuration
  request:
    content_type: "application/json"
    encoding: "json"  # Options: json, form_url_encoded, xml

    # Complete request body structure with test values
    body_structure:
      amount:
        type: "integer"
        required: true
        description: "Amount in smallest currency unit (cents)"
        test_value: 1000

      currency:
        type: "string"
        required: true
        description: "Three-letter ISO currency code"
        test_value: "USD"

      payment_method:
        type: "object"
        required: true
        description: "Payment method details"
        test_value:
          type: "card"
          card:
            number: "4242424242424242"
            exp_month: 12
            exp_year: 2025
            cvc: "123"

      capture:
        type: "boolean"
        required: false
        description: "Whether to capture immediately"
        test_value: false

      description:
        type: "string"
        required: false
        test_value: "GRACE-UCS tech spec validation test"

    # CRITICAL: Complete example request body for curl testing
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
        },
        "capture": false,
        "description": "GRACE-UCS validation test"
      }

  # Response configuration
  response:
    success_status_codes: [200, 201]
    content_type: "application/json"

    # Field mappings (where to find ID and status in response)
    id_field: "id"  # Field name containing payment ID
    status_field: "status"  # Field name containing payment status

    # Required fields that must be present
    required_fields:
      - "id"
      - "status"
      - "amount"
      - "currency"
      - "created"

    # Status mappings (connector status → UCS AttemptStatus)
    status_mappings:
      "pending": "Pending"
      "requires_payment_method": "Pending"
      "requires_confirmation": "Pending"
      "requires_action": "AuthenticationPending"
      "processing": "Processing"
      "requires_capture": "Authorized"
      "canceled": "Voided"
      "succeeded": "Charged"
      "failed": "Failure"

    # Example successful response (for documentation)
    example_response: |
      {
        "id": "pay_3abc123",
        "object": "payment",
        "amount": 1000,
        "currency": "USD",
        "status": "requires_capture",
        "created": 1234567890
      }
```

### Capture Flow

```yaml
capture:
  method: "POST"
  path: "/v1/payments/{payment_id}/capture"

  # URL parameters (will be replaced from state.json)
  url_params:
    - payment_id: "Payment ID from authorize response"

  request:
    content_type: "application/json"

    # Simple request body
    test_example: |
      {
        "amount": 1000
      }

  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    required_fields: ["id", "status", "amount"]

    status_mappings:
      "captured": "Charged"
      "succeeded": "Charged"
      "failed": "Failure"
```

### Void Flow

```yaml
void:
  method: "POST"
  path: "/v1/payments/{payment_id}/cancel"  # or /void depending on API

  url_params:
    - payment_id: "Payment ID from authorize response"

  request:
    content_type: "application/json"
    test_example: "{}"  # Empty body or minimal

  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    required_fields: ["id", "status"]

    status_mappings:
      "canceled": "Voided"
      "voided": "Voided"
      "failed": "Failure"
```

### Refund Flow

```yaml
refund:
  method: "POST"
  path: "/v1/payments/{payment_id}/refund"

  url_params:
    - payment_id: "Payment ID from captured payment"

  request:
    content_type: "application/json"
    test_example: |
      {
        "amount": 1000,
        "reason": "requested_by_customer"
      }

  response:
    success_status_codes: [200, 201]
    id_field: "refund_id"  # or "id" depending on API
    status_field: "status"
    required_fields: ["refund_id", "status", "amount"]

    status_mappings:
      "succeeded": "Success"
      "pending": "Pending"
      "failed": "Failure"
```

### Payment Sync (PSync) Flow

```yaml
psync:
  method: "GET"
  path: "/v1/payments/{payment_id}"

  url_params:
    - payment_id: "Payment ID to query"

  request:
    content_type: null  # GET request, no body
    test_example: null

  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    required_fields: ["id", "status"]

    # Complete status mappings (must include ALL possible statuses)
    status_mappings:
      "pending": "Pending"
      "requires_payment_method": "Pending"
      "requires_confirmation": "Pending"
      "requires_action": "AuthenticationPending"
      "processing": "Processing"
      "requires_capture": "Authorized"
      "canceled": "Voided"
      "succeeded": "Charged"
      "captured": "Charged"
      "failed": "Failure"
```

### Refund Sync (RSync) Flow

```yaml
rsync:
  method: "GET"
  path: "/v1/refunds/{refund_id}"

  url_params:
    - refund_id: "Refund ID to query"

  request:
    content_type: null
    test_example: null

  response:
    success_status_codes: [200]
    id_field: "id"
    status_field: "status"
    required_fields: ["id", "status", "amount"]

    status_mappings:
      "succeeded": "Success"
      "pending": "Pending"
      "failed": "Failure"
      "canceled": "Failure"
```

---

## 📝 Tech Spec Validation Notes

After generating this tech spec with complete YAML sections, it will be validated by:

1. **Making actual API calls** using the `test_example` request bodies
2. **Verifying endpoints** are correct (checking for 404 errors)
3. **Validating auth format** works (checking for 401 errors)
4. **Confirming response structures** match `required_fields`
5. **Ensuring status mappings** are complete for all actual status values
6. **Testing flow dependencies** (authorize → capture → void/refund)

All sections marked with `test_value` and `test_example` will be used in validation curl scripts. This ensures the tech spec is accurate before any implementation begins!

---

## Implementation Checklist

When creating tech spec, ensure:

- [ ] `api_config.test_url` is correct sandbox/test environment
- [ ] `auth.headers` has correct format with `{api_key}` placeholders
- [ ] `auth.credentials_required` describes what user needs
- [ ] Each flow has complete `test_example` request body
- [ ] Each flow has correct `method` and `path`
- [ ] Each flow has `id_field` and `status_field` mappings
- [ ] Each flow has comprehensive `status_mappings`
- [ ] `test_example` uses test card numbers (4242... for testing)
- [ ] All 6 core flows documented (authorize, capture, void, refund, psync, rsync)

**A complete tech spec = successful validation = accurate implementation!**
