# Tech Spec Credibility Validation

## Purpose

Validate the accuracy and credibility of generated tech specs by testing them against real connector APIs **before implementation**. This ensures the tech spec is a trustworthy blueprint for code generation.

## Core Principle

**EVERYTHING for the curl test comes from the tech spec, EXCEPT credentials.**

### From Tech Spec (AI extracts automatically):
- ✅ Base URL (test/sandbox environment)
- ✅ Endpoint paths for all flows
- ✅ HTTP methods (POST/GET/PUT/DELETE)
- ✅ Authentication header formats
- ✅ Content-Type headers
- ✅ Complete request body structures
- ✅ Request body example values
- ✅ Response field names
- ✅ Expected HTTP status codes
- ✅ Status mappings to UCS types

**Extraction works with:**
- ✅ **YAML sections** (preferred - structured, easy to parse)
- ✅ **Prose/Markdown** (fallback - AI extracts from natural language)

### From User (only 3 values):
- ✅ `api_key` - Primary API credential
- ✅ `api_secret` - Secondary credential (if needed)
- ✅ `key1` - Additional identifier (if needed)

## How It Works

### 1. Tech Spec Generation
AI analyzes connector documentation and generates a comprehensive tech spec with:
- Complete API endpoint configurations
- Request/response structures with test examples
- Authentication formats
- Status mappings

The tech spec must be **self-contained** - it should have ALL information needed to make API calls.

### 2. Credential Collection
After tech spec generation, AI asks user for minimal credentials:

```
🔐 Tech Spec Credibility Validation

Connector: Stripe
Test URL (from tech spec): https://api.stripe.com

Please provide test credentials:
{
  "api_key": "sk_test_xxxxxxxxxxxxx",
  "api_secret": "",  // Not needed for Stripe
  "key1": ""         // Not needed for Stripe
}

Note: Use test/sandbox credentials only. Never production credentials!
```

### 3. Curl Generation from Tech Spec

AI extracts everything from tech spec (YAML or prose) and generates curl commands:

#### **Option A: From YAML Sections** (Preferred - Easy Parsing)

From tech spec YAML:
```yaml
authorize:
  method: "POST"
  path: "/v1/payment_intents"
  request:
    content_type: "application/x-www-form-urlencoded"
    test_example: "amount=1000&currency=usd&payment_method_types[]=card&capture_method=manual"
  response:
    success_status_codes: [200, 201]
    id_field: "id"
    status_field: "status"
```

AI extracts directly:
- method = "POST"
- path = "/v1/payment_intents"
- content_type = "application/x-www-form-urlencoded"
- request_body = "amount=1000&currency=usd..."

#### **Option B: From Prose/Markdown** (Fallback - NLP Extraction)

From tech spec prose:
```markdown
## Authorize Payment

To authorize a payment, send a POST request to `/v1/payment_intents` with the
following form-encoded parameters:

Required fields:
- amount (integer): Amount in cents
- currency (string): ISO code like "usd"
- payment_method_types (array): e.g., ["card"]
- capture_method (string): "manual" or "automatic"

Example: amount=1000&currency=usd&payment_method_types[]=card

The API returns JSON with 'id' and 'status' fields.
Success status codes: 200, 201
```

AI extracts via natural language understanding:
- method = "POST" (from "send a POST request")
- path = "/v1/payment_intents" (from "to `/v1/payment_intents`")
- content_type = "application/x-www-form-urlencoded" (from "form-encoded")
- request_body = "amount=1000&currency=usd&payment_method_types[]=card" (from example)
- id_field = "id" (from "'id' and 'status' fields")
- status_field = "status"
- success_codes = [200, 201] (from "Success status codes")

**Extraction Patterns:**
- "POST to X" or "POST request to X" → method=POST, path=X
- "JSON payload" / "send JSON" → content_type=application/json
- "form-encoded" / "form data" → content_type=application/x-www-form-urlencoded
- "Example:" followed by code block → test_example
- "returns" / "response contains" / "includes" → response field names

AI generates curl:
```bash
curl -X POST "https://api.stripe.com/v1/payment_intents" \
  -H "Authorization: Bearer sk_test_xxxxx" \  # Format from tech spec + user credential
  -H "Content-Type: application/x-www-form-urlencoded" \  # From tech spec
  -d "amount=1000&currency=usd&payment_method_types[]=card&capture_method=manual" \  # From tech spec
  -o responses/authorize_response.json \
  -w "\nHTTP_CODE:%{http_code}\n" \
  -s
```

**User only provided:** API key value
**Everything else:** Extracted from tech spec

### 4. Test Execution
6 curl scripts execute in sequence against the **real connector API**:

1. **01_authorize.sh** → Creates payment, saves `payment_id` to state.json
2. **02_capture.sh** → Captures payment using `payment_id` from state
3. **03_void.sh** → Voids a fresh authorization
4. **04_refund.sh** → Refunds captured payment, saves `refund_id`
5. **05_psync.sh** → Retrieves payment status
6. **06_rsync.sh** → Retrieves refund status using `refund_id`

### 5. Response Validation
For each test, AI validates actual API response against tech spec expectations:

✅ **HTTP Status Match:**
- Tech spec says: `success_status_codes: [200, 201]`
- Actual response: `200 OK` ✅

✅ **Response Structure Match:**
- Tech spec expects: `required_fields: [id, status, amount]`
- Actual response has: ✅ `id`, ✅ `status`, ✅ `amount`

✅ **Field Names Match:**
- Tech spec says: `id_field: "id"`
- Actual response has: `"id": "pi_3abc123"` ✅

✅ **Status Mapping Exists:**
- Tech spec has: `"requires_capture": "Authorized"`
- Actual response: `"status": "requires_capture"` ✅

❌ **Mismatch Example:**
- Tech spec endpoint: `/v1/payments/{id}/void`
- Actual API returns: `404 Not Found`
- Analysis: **Endpoint path wrong in tech spec**

### 6. Credibility Report Generation
AI creates detailed validation report:

```markdown
# Tech Spec Credibility Report
**Connector:** Stripe
**Validation Date:** 2025-01-15
**Attempt:** 1/3

## Summary
- ✅ Passed: 5/6 flows
- ❌ Failed: 1/6 flow
- **Overall:** NEEDS FIXES

## Test Results

### ✅ Authorize Flow - PASSED
- HTTP Status: 200 OK ✅
- ID Field: Found at `id` = "pi_3abc123" ✅
- Status Field: Found at `status` = "requires_capture" ✅
- Required Fields: All present ✅
- Status Mapping: "requires_capture" → "Authorized" ✅

### ❌ Void Flow - FAILED
- HTTP Status: 404 Not Found ❌
- Error: "Unrecognized request URL"
- **Issue:** Endpoint path incorrect in tech spec
- **Tech spec says:** `/v1/payment_intents/{id}/void`
- **Should be:** `/v1/payment_intents/{id}/cancel`

## Issues Identified

### Critical (Must Fix)
1. **Void endpoint path incorrect**
   - Location: Tech spec section 3.2.3
   - Current: `/v1/payment_intents/{id}/void`
   - Correct: `/v1/payment_intents/{id}/cancel`
   - Auto-fixable: ✅ YES

## Recommendations
- Auto-fix available for all issues
- Estimated fix time: 30 seconds
- Re-test required after fixes

## Tech Spec Credibility Score
Before fixes: 83% (5/6 flows work)
After fixes: Estimated 100%
```

### 7. Feedback Loop with Auto-Fix

#### **Special Case: Authentication Errors (401/403)**

If validation fails with authentication errors, AI handles differently:

```
⚠️  Authentication Failed (HTTP 401)

Error from API: "Invalid API key provided"

This could be:
1. Invalid credentials (wrong API key/secret)
2. Incorrect auth header format in tech spec

Please verify your credentials are correct:
- Are you using TEST/SANDBOX credentials?
- Is the API key active and valid?
- Does the API key have required permissions?

Options:
[R] Retry with new credentials
[F] Fix auth format in tech spec (if credentials are definitely correct)
[C] Cancel validation

Your choice (R/F/C):
```

**If [R] Retry with new credentials:**
1. AI asks for corrected credentials
2. Updates credentials.json
3. Re-runs failed test with new credentials
4. If still fails, offers [F] or [C] options

**If [F] Fix auth format:**
1. AI analyzes error messages
2. Updates auth header format in tech spec
3. Regenerates curl scripts
4. Re-runs tests

**If [C] Cancel:**
1. Validation stops
2. User can fix credentials manually

#### **Other Validation Failures**

For non-authentication errors, AI offers options:

```
⚠️  Tech Spec Validation Failed (Attempt 1/3)

Issues found:
- Void endpoint path incorrect (404 error)

Choose action:
[A] Auto-fix - I'll update tech spec and re-validate (Recommended)
[M] Manual - You fix tech spec, I'll re-validate
[P] Proceed - Continue despite issues (NOT recommended)
[C] Cancel - Stop for manual review

Your choice (A/M/P/C):
```

**If [A] Auto-fix:**
1. AI updates tech spec with corrections
2. Regenerates curl scripts from updated tech spec
3. Re-runs all 6 tests
4. Shows updated validation results
5. Maximum 3 attempts (excluding credential retries)

**If [M] Manual:**
1. User updates tech spec manually
2. AI regenerates curl scripts
3. AI re-runs tests

**If [P] Proceed:**
1. AI documents known issues in implementation plan
2. Flags connector as "HIGH RISK - Unvalidated tech spec"
3. Continues to implementation (not recommended)

**If [C] Cancel:**
1. Workflow stops
2. User can review detailed report

### 8. Success Criteria
Tech spec considered **credible and validated** when:
- ✅ All 6 flows return success HTTP codes (200-299)
- ✅ All required response fields present in actual responses
- ✅ All actual status values have mappings in tech spec
- ✅ Authentication works correctly
- ✅ No structural mismatches between tech spec and reality

**Only proceed to implementation when tech spec is validated!**

## Directory Structure

Per-connector validation creates:

```
testing/tech-spec-validation/{{connector_name}}/
├── credentials.json              # User-provided credentials (gitignored)
├── test_scripts/                 # Generated curl scripts (gitignored)
│   ├── 01_authorize.sh
│   ├── 02_capture.sh
│   ├── 03_void.sh
│   ├── 04_refund.sh
│   ├── 05_psync.sh
│   └── 06_rsync.sh
├── responses/                    # Actual API responses (gitignored)
│   ├── authorize_response.json
│   ├── capture_response.json
│   └── ...
├── state.json                    # Shared state between tests (gitignored)
└── credibility_report.md         # Validation results (kept for reference)
```

## State Management

**state.json** tracks IDs between dependent tests:

```json
{
  "authorize": {
    "payment_id": "pi_3abc123",
    "status": "requires_capture",
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "capture": {
    "payment_id": "pi_3abc123",
    "status": "succeeded",
    "timestamp": "2025-01-15T10:30:15Z"
  },
  "refund": {
    "refund_id": "re_3def456",
    "payment_id": "pi_3abc123",
    "status": "succeeded",
    "timestamp": "2025-01-15T10:30:30Z"
  }
}
```

Subsequent tests read from this file to get necessary IDs.

## Security Considerations

- ✅ All credential files are gitignored automatically
- ✅ Never commit API keys, secrets, or tokens
- ✅ Use only test/sandbox credentials, never production
- ✅ API responses may contain sensitive data - also gitignored
- ✅ Option to clear credentials after validation

## Benefits

### 1. Early Error Detection
Catch tech spec errors **before** writing any implementation code.

### 2. Time Savings
Don't waste time implementing based on incorrect assumptions.

### 3. High Confidence
Know the tech spec accurately reflects the real API.

### 4. Minimal Effort
User provides only 3 credential values - everything else is automated.

### 5. Auto-Correction
AI can automatically fix most common tech spec issues.

### 6. Validated Blueprint
Implementation can trust the validated tech spec completely.

### 7. Credential Verification
Special handling for authentication errors - AI asks user to verify/update credentials before assuming tech spec is wrong, preventing false auto-fixes.

## Example Workflow

```bash
# 1. Generate tech spec
integrate Stripe using grace-ucs/.graceucs

# 2. AI asks for credentials
🔐 Provide test credentials: {...}

# 3. AI generates and runs tests
🧪 Running tech spec validation...
✅ Authorize: PASS
✅ Capture: PASS
❌ Void: FAIL (endpoint incorrect)
✅ Refund: PASS
✅ PSync: PASS
✅ RSync: PASS

# 4. AI offers auto-fix
[A] Auto-fix tech spec and re-validate?

# 5. After auto-fix
✅ All 6 flows validated!
Tech spec credibility: CONFIRMED
Proceeding to implementation...
```

## Related Documentation

- [`curl_generator.md`](./curl_generator.md) - How to generate curl scripts from tech spec
- [`validation_rules.md`](./validation_rules.md) - Detailed validation criteria
- [`credentials_template.json`](./credentials_template.json) - Credential format template
- [`../../connector_integration/template/tech_spec.md`](../../connector_integration/template/tech_spec.md) - Tech spec template with YAML sections

---

**Remember:** A validated tech spec = trustworthy implementation blueprint. Always validate before implementing!
