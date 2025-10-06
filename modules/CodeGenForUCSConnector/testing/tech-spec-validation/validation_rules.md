# Tech Spec Credibility Validation Rules

## Purpose

Define comprehensive validation criteria for determining tech spec credibility by comparing actual API responses with tech spec expectations.

---

## Validation Levels

### Level 1: HTTP Response Validation

**Validates basic API connectivity and request acceptance.**

#### ✅ Pass Criteria
- HTTP status code in `flow.response.success_status_codes` (typically 200, 201)
- Response body is parseable (valid JSON/XML as per `content_type`)
- No network errors or timeouts

#### ❌ Fail Indicators & Root Causes

| HTTP Code | Issue | Tech Spec Problem | Auto-Fixable | Special Handling |
|-----------|-------|-------------------|--------------|------------------|
| 400 Bad Request | Request body malformed | Wrong request format or missing required fields | ⚠️ Partial | - |
| 401 Unauthorized | Authentication failed | Wrong auth header format OR invalid credentials | ⚠️ Conditional | **Ask user to verify credentials first** |
| 403 Forbidden | Access denied | Missing permissions OR invalid credentials | ⚠️ Conditional | **Ask user to verify credentials first** |
| 404 Not Found | Endpoint doesn't exist | Wrong endpoint path in tech spec | ✅ Yes | - |
| 405 Method Not Allowed | Wrong HTTP method | Tech spec has wrong method (GET vs POST) | ✅ Yes | - |
| 422 Unprocessable Entity | Validation failed | Missing required field or wrong data type | ✅ Yes | - |
| 429 Too Many Requests | Rate limit exceeded | Too many test requests | ❌ No | Add delay and retry |
| 500 Internal Server Error | API error | Malformed request or API issue | ⚠️ Maybe | - |
| 503 Service Unavailable | API maintenance | Temporary unavailability | ❌ No | Retry later |

**Example Validation:**
```bash
# Expected (from tech spec)
success_status_codes: [200, 201]

# Actual
HTTP_CODE=200

# Result: ✅ PASS
```

**Example Failure (Endpoint Error):**
```bash
# Expected
success_status_codes: [200]

# Actual
HTTP_CODE=404
Error: "No such resource: /v1/payments/void"

# Analysis
Issue: Endpoint path incorrect
Tech spec says: /v1/payments/{id}/void
Should be: /v1/payments/{id}/cancel
Auto-fix: ✅ YES
```

**Example Failure (Authentication Error - SPECIAL HANDLING):**
```bash
# Actual
HTTP_CODE=401
Error: "Invalid API key provided"

# ⚠️ CRITICAL: DO NOT AUTO-FIX IMMEDIATELY
# This could be:
# 1. Wrong credentials (most common)
# 2. Wrong auth header format

# Required Action:
Ask user:
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

# If user chooses [R]: Request new credentials and retry same test
# If user chooses [F]: Only then auto-fix auth format in tech spec
# If user chooses [C]: Stop validation
```

---

### Level 2: Response Structure Validation

**Validates that response contains expected fields.**

#### ✅ Pass Criteria
- Response contains `flow.response.id_field`
- Response contains `flow.response.status_field`
- Response contains all fields in `flow.response.required_fields`
- Fields are accessible (not nested incorrectly)

#### ❌ Fail Indicators

**Missing ID Field:**
```yaml
# Tech spec says
id_field: "transaction_id"

# Actual response
{
  "id": "pay_123",  # ❌ Field is named "id" not "transaction_id"
  "status": "authorized"
}

# Issue: Tech spec has wrong id_field name
# Fix: Change id_field to "id"
# Auto-fixable: ✅ YES
```

**Missing Status Field:**
```yaml
# Tech spec says
status_field: "state"

# Actual response
{
  "id": "pay_123",
  "status": "authorized"  # ❌ Field is "status" not "state"
}

# Issue: Tech spec has wrong status_field name
# Fix: Change status_field to "status"
# Auto-fixable: ✅ YES
```

**Missing Required Fields:**
```yaml
# Tech spec says
required_fields: ["id", "status", "amount", "currency", "customer"]

# Actual response
{
  "id": "pay_123",
  "status": "authorized",
  "amount": 1000,
  "currency": "USD"
  # ❌ Missing "customer" field
}

# Issue: Tech spec expects field that API doesn't return
# Fix: Remove "customer" from required_fields OR API doesn't support it
# Auto-fixable: ✅ YES (remove from required)
```

---

### Level 3: Status Mapping Validation

**Validates that actual status values have mappings in tech spec.**

#### ✅ Pass Criteria
- Response status value exists as a key in `flow.response.status_mappings`
- Mapped value is a valid UCS `AttemptStatus`

#### ❌ Fail Indicators

**Unmapped Status:**
```yaml
# Tech spec status mappings
status_mappings:
  "authorized": "Authorized"
  "captured": "Charged"
  "failed": "Failure"

# Actual response
{
  "status": "processing"  # ❌ Not in status_mappings
}

# Issue: Missing status mapping
# Fix: Add "processing": "Processing" to mappings
# Auto-fixable: ✅ YES
```

**Invalid Mapping:**
```yaml
# Tech spec
status_mappings:
  "completed": "Success"  # ❌ "Success" is not a valid AttemptStatus

# Valid UCS AttemptStatus values:
# Authorized, Charged, Pending, Failure, Voided, Processing,
# AuthenticationPending, PartialCharged, etc.

# Fix: Change to valid status like "Charged"
# Auto-fixable: ⚠️ Requires context
```

---

### Level 4: Flow Dependency Validation

**Validates that dependent flows can chain correctly.**

#### ✅ Pass Criteria
- Authorize flow returns usable `payment_id` for Capture/Void flows
- Capture flow succeeds so Refund can be tested
- Refund flow returns `refund_id` for RSync flow

#### ❌ Fail Indicators

**Missing Dependency:**
```bash
# Capture flow tries to read payment_id from state
PAYMENT_ID=$(jq -r '.authorize.payment_id' state.json)

# But state.json doesn't have it
# Result: PAYMENT_ID is empty

# Issue: Authorize flow didn't save payment_id properly
# Fix: Check id_field mapping in authorize flow
# Auto-fixable: ⚠️ Requires checking previous flow
```

**Wrong State Structure:**
```json
// State from authorize (wrong structure)
{
  "payment": "pay_123"  // ❌ Should be nested properly
}

// Should be
{
  "authorize": {
    "payment_id": "pay_123",
    "status": "authorized"
  }
}

// Fix: Correct state saving logic
// Auto-fixable: ✅ YES
```

---

## Issue Classification

### Critical Issues (Must Fix Before Implementation)

1. **Wrong Endpoint Path** (404 errors)
   - **Symptom:** 404 Not Found
   - **Impact:** Flow completely non-functional
   - **Auto-fix:** ✅ YES (extract correct path from error message)
   - **Priority:** P0

2. **Wrong Authentication Format** (401 errors)
   - **Symptom:** 401 Unauthorized
   - **Impact:** All flows fail
   - **Auto-fix:** ❌ NO (requires API doc review or user input)
   - **Priority:** P0

3. **Wrong HTTP Method** (405 errors)
   - **Symptom:** 405 Method Not Allowed
   - **Impact:** Flow non-functional
   - **Auto-fix:** ✅ YES (try alternative method)
   - **Priority:** P0

4. **Missing Required Fields** (422 errors)
   - **Symptom:** 422 Unprocessable Entity
   - **Impact:** Request rejected by API
   - **Auto-fix:** ✅ YES (add field from error message)
   - **Priority:** P0

### High Priority Issues (Should Fix)

5. **Wrong Field Names**
   - **Symptom:** Can't extract ID or status from response
   - **Impact:** Dependent flows fail
   - **Auto-fix:** ✅ YES (inspect actual response structure)
   - **Priority:** P1

6. **Incomplete Status Mappings**
   - **Symptom:** Unknown status in response
   - **Impact:** Status not mapped to UCS types
   - **Auto-fix:** ✅ YES (add missing mappings)
   - **Priority:** P1

7. **Wrong Request Format** (400 errors)
   - **Symptom:** 400 Bad Request
   - **Impact:** Request rejected
   - **Auto-fix:** ⚠️ PARTIAL (depends on error details)
   - **Priority:** P1

### Medium Priority Issues (Good to Fix)

8. **Extra Required Fields**
   - **Symptom:** Tech spec expects fields API doesn't return
   - **Impact:** Validation fails but flow works
   - **Auto-fix:** ✅ YES (remove from required_fields)
   - **Priority:** P2

9. **Wrong Success Status Codes**
   - **Symptom:** API returns 201, tech spec expects 200
   - **Impact:** False negative in validation
   - **Auto-fix:** ✅ YES (add to accepted codes)
   - **Priority:** P2

### Low Priority Issues (Nice to Fix)

10. **Response Has Extra Fields**
    - **Symptom:** Response contains more than expected
    - **Impact:** None (extra fields ignored)
    - **Auto-fix:** ℹ️ N/A (not an issue)
    - **Priority:** P3

11. **Different Field Order**
    - **Symptom:** Fields in different order than tech spec
    - **Impact:** None (JSON order doesn't matter)
    - **Auto-fix:** ℹ️ N/A (not an issue)
    - **Priority:** P3

---

## Auto-Fix Capability Matrix

| Issue Type | Detectable | Auto-Fixable | Strategy |
|------------|-----------|--------------|----------|
| Wrong endpoint path | ✅ Yes (404) | ✅ Yes | Extract from error message |
| Wrong HTTP method | ✅ Yes (405) | ✅ Yes | Try POST/GET/PUT alternatives |
| Wrong field names | ✅ Yes | ✅ Yes | Inspect actual response keys |
| Missing status mapping | ✅ Yes | ✅ Yes | Add mapping for new status |
| Missing required field in request | ✅ Yes (422) | ✅ Yes | Parse error message for field |
| Extra required field in response | ✅ Yes | ✅ Yes | Remove from required list |
| Wrong auth format | ✅ Yes (401) | ❌ No | Need API docs or user input |
| Wrong content-type | ✅ Yes (400/415) | ⚠️ Maybe | Try JSON vs form-encoded |
| Invalid credentials | ✅ Yes (401/403) | ❌ No | User must provide valid creds |
| API rate limiting | ✅ Yes (429) | ✅ Yes | Add delay between requests |

---

## Validation Report Format

### Structure

```markdown
# Tech Spec Credibility Report
**Connector:** {{connector_name}}
**Validation Date:** {{date}}
**Attempt:** {{attempt_number}}/3

## Executive Summary
- **Passed:** {{pass_count}}/6 flows
- **Failed:** {{fail_count}}/6 flows
- **Overall Status:** {{PASS|NEEDS_FIXES|CRITICAL_ISSUES}}
- **Tech Spec Credibility:** {{percentage}}%

## Detailed Test Results

### ✅ Authorize Flow - PASSED
**Endpoint:** POST /v1/payment_intents
**HTTP Status:** 200 OK ✅
**Validations:**
- ✅ ID Field: Found at `id` = "pi_3abc123"
- ✅ Status Field: Found at `status` = "requires_capture"
- ✅ Required Fields: All present [id, status, amount, currency]
- ✅ Status Mapping: "requires_capture" → "Authorized"

**Response Sample:**
```json
{
  "id": "pi_3abc123",
  "status": "requires_capture",
  "amount": 1000,
  "currency": "usd"
}
```

### ❌ Void Flow - FAILED
**Endpoint:** POST /v1/payment_intents/{id}/void
**HTTP Status:** 404 Not Found ❌
**Error Message:** "Unrecognized request URL (POST: /v1/payment_intents/pi_123/void)"

**Issue Analysis:**
- **Problem:** Endpoint path incorrect in tech spec
- **Tech spec says:** `/v1/payment_intents/{id}/void`
- **API expects:** `/v1/payment_intents/{id}/cancel`
- **Severity:** CRITICAL
- **Auto-fixable:** ✅ YES

**Recommended Fix:**
```yaml
# In tech spec, change:
void:
  path: "/v1/payment_intents/{payment_id}/cancel"  # was: /void
```

### ⚠️ PSync Flow - PARTIAL PASS
**Endpoint:** GET /v1/payment_intents/{id}
**HTTP Status:** 200 OK ✅
**Validations:**
- ✅ ID Field: Found
- ✅ Status Field: Found
- ✅ Required Fields: All present
- ⚠️ Status Mapping: Partial (3 missing mappings)

**Missing Status Mappings:**
- `"requires_payment_method"` - Not mapped in tech spec
- `"requires_confirmation"` - Not mapped in tech spec
- `"requires_action"` - Not mapped in tech spec

**Recommended Fix:**
```yaml
# Add to tech spec status_mappings:
status_mappings:
  "requires_payment_method": "Pending"
  "requires_confirmation": "Pending"
  "requires_action": "AuthenticationPending"
```

## Issues Summary

### Critical (Must Fix) - {{count}}
1. **Void endpoint path incorrect** (Line 245 in tech spec)
   - Current: `/v1/payment_intents/{id}/void`
   - Correct: `/v1/payment_intents/{id}/cancel`
   - Auto-fix: ✅ Available

### High Priority (Should Fix) - {{count}}
2. **Incomplete status mappings in PSync** (Line 387 in tech spec)
   - Missing 3 status mappings
   - Auto-fix: ✅ Available

### Medium Priority (Good to Fix) - {{count}}
None identified

### Low Priority (Optional) - {{count}}
None identified

## Auto-Fix Summary

**Auto-fixable issues:** 2/2 (100%)
**Estimated fix time:** 30 seconds
**Re-test required:** Yes

## Recommendations

### Option A: Auto-Fix (Recommended)
AI will automatically:
1. Update void endpoint path in tech spec
2. Add 3 missing status mappings in psync
3. Regenerate curl test scripts
4. Re-run all 6 validation tests
5. Generate updated credibility report

**Estimated time:** 1 minute

### Option B: Manual Fix
You update tech spec manually, then AI re-validates.

### Option C: Proceed Despite Issues
NOT RECOMMENDED - Implementing with unvalidated tech spec may cause:
- Wrong endpoint implementations
- Incomplete status handling
- Failed tests during development

## Tech Spec Credibility Score

**Before Fixes:** 83% credible
- 5/6 flows work correctly
- 1 critical issue (void endpoint)
- 1 high priority issue (status mappings)

**After Auto-Fix:** 100% credible (projected)
- All 6 flows expected to pass
- All known issues resolved

## Next Steps

Choose action:
- [A] Auto-fix and re-validate
- [M] Manual fix, then re-validate
- [P] Proceed to implementation (not recommended)
- [C] Cancel for manual review
```

---

## State Management Validation

**state.json** structure must be validated:

```json
{
  "authorize": {
    "payment_id": "pi_123",
    "status": "requires_capture",
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "capture": {
    "payment_id": "pi_123",
    "status": "succeeded",
    "timestamp": "2025-01-15T10:30:15Z"
  },
  "void": {
    "payment_id": "pi_456",
    "status": "canceled",
    "timestamp": "2025-01-15T10:30:20Z"
  },
  "refund": {
    "refund_id": "re_789",
    "payment_id": "pi_123",
    "status": "succeeded",
    "timestamp": "2025-01-15T10:30:30Z"
  }
}
```

**Validation checks:**
- ✅ authorize.payment_id exists (needed by capture)
- ✅ void.payment_id exists (separate from capture)
- ✅ refund.refund_id exists (needed by rsync)
- ✅ Timestamps are sequential
- ✅ All statuses are valid

---

## Success Criteria Summary

Tech spec is considered **CREDIBLE and VALIDATED** when:

| Criterion | Requirement |
|-----------|-------------|
| HTTP Success | All 6 flows return 2xx status codes |
| Response Structure | All flows have correct id_field and status_field |
| Required Fields | All required_fields present in responses |
| Status Mappings | All actual status values have mappings |
| Flow Dependencies | All dependent flows can chain correctly |
| No Critical Issues | Zero P0 issues remaining |
| Auto-Fix Applied | All auto-fixable issues resolved |

**Only proceed to implementation when ALL criteria met!**

---

## Edge Cases

### Rate Limiting (429 Too Many Requests)
```bash
# Add delay between tests
sleep 0.5  # 500ms delay

# Or from tech spec
DELAY=$(yq '.api_config.rate_limit.test_delay_ms' tech_spec.md)
sleep $(echo "scale=2; $DELAY/1000" | bc)
```

### Idempotency Issues
```bash
# Some APIs require unique identifiers
TIMESTAMP=$(date +%s)
REQUEST_BODY=$(echo "$REQUEST_BODY" | sed "s/test-payment/test-payment-$TIMESTAMP/")
```

### Webhook Verification
```bash
# Cannot test webhooks via curl
# Mark as SKIP with note
echo "⏭️  Webhook flow: SKIPPED (requires webhook endpoint)"
```

This comprehensive validation ensures tech spec accuracy before any code is written!
