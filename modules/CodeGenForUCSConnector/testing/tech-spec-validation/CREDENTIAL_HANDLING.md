# Credential Handling in Tech Spec Validation

## Overview

When validating tech specs, authentication errors (401/403) require special handling because they could indicate either:
1. **Invalid credentials** (most common - wrong API key/secret)
2. **Incorrect auth format in tech spec** (less common - wrong header structure)

## Critical Rule

**❌ NEVER auto-fix auth format immediately on 401/403 errors**

**✅ ALWAYS ask user to verify credentials first**

---

## Workflow for 401/403 Errors

### Step 1: Detect Authentication Error

```bash
HTTP_CODE=401
Error: "Invalid API key provided"
```

### Step 2: Ask User to Verify Credentials

```
⚠️  Authentication Failed (HTTP 401/403)

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

### Step 3: Handle User Response

#### **If [R] - Retry with New Credentials**

1. **Ask for new credentials:**
   ```
   Please provide updated test credentials:
   {
     "api_key": "your_corrected_test_key",
     "api_secret": "your_corrected_secret_if_needed",
     "key1": "additional_key_if_needed"
   }
   ```

2. **Update credentials.json**
3. **Re-run the SAME test** (don't start from scratch)
4. **If still fails with 401/403:**
   - Offer [F] or [C] options again
   - User may have made another mistake or format is genuinely wrong

5. **If succeeds:**
   - Continue with remaining tests
   - Note in report: "Credentials were corrected during validation"

#### **If [F] - Fix Auth Format**

User has confirmed credentials are correct, so it MUST be a tech spec issue.

1. **Analyze API error message** for hints about expected format
2. **Update tech spec auth section:**
   ```yaml
   auth:
     headers:
       - name: "Authorization"
         format: "Bearer {api_key}"  # Update based on error
   ```
3. **Regenerate curl scripts** from updated tech spec
4. **Re-run all tests**
5. **Document in report:** "Auth format corrected based on API error response"

#### **If [C] - Cancel**

1. **Stop validation**
2. **Save partial results** to credibility_report.md
3. **User can fix manually:**
   - Either update credentials in credentials.json
   - Or update auth format in tech spec
4. **When ready, user can restart validation**

---

## Why This Matters

### ❌ Without Credential Verification (Bad):

```
401 error → AI auto-fixes tech spec → Wrong fix applied → More validation failures
```

User had wrong credentials, but AI assumed tech spec was wrong and broke it.

### ✅ With Credential Verification (Good):

```
401 error → Ask user → User provides correct creds → Tests pass → Success
```

Problem solved without touching tech spec.

---

## Examples

### Example 1: Wrong API Key

```bash
# Initial attempt
curl -H "Authorization: Bearer sk_test_wrong123"
# → 401 Unauthorized

# AI asks user to verify
# User realizes mistake, provides: sk_test_correct456

# Retry with correct key
curl -H "Authorization: Bearer sk_test_correct456"
# → 200 OK ✅

# Tech spec was correct all along!
```

### Example 2: Wrong Auth Format

```bash
# Initial attempt with correct credentials
curl -H "Authorization: Bearer sk_test_correct456"
# → 401 Unauthorized
# Error: "Expected 'Basic' authentication"

# User confirms credentials are correct
# Choose [F] to fix format

# AI updates tech spec:
# Before: format: "Bearer {api_key}"
# After:  format: "Basic {api_key}"

# Retry
curl -H "Authorization: Basic sk_test_correct456"
# → 200 OK ✅
```

### Example 3: API Key Needs Base64 Encoding

```bash
# Initial attempt
curl -H "Authorization: Basic sk_test_123"
# → 401 Unauthorized
# Error: "API key must be base64 encoded"

# User confirms credentials correct, chooses [F]

# AI updates tech spec with encoding note:
auth:
  headers:
    - name: "Authorization"
      format: "Basic {base64(api_key)}"

# Regenerate scripts with base64 encoding
curl -H "Authorization: Basic $(echo -n sk_test_123 | base64)"
# → 200 OK ✅
```

---

## Auto-Fix Decision Tree

```
401/403 Error Received
    ↓
Ask User to Verify Credentials
    ↓
    ├─ [R] Retry with New Credentials
    │   ↓
    │   Update credentials.json
    │   ↓
    │   Re-run same test
    │   ↓
    │   ├─ Success → Continue
    │   └─ Still 401/403 → Offer [F] or [C]
    │
    ├─ [F] Fix Auth Format (credentials confirmed correct)
    │   ↓
    │   Update tech spec auth section
    │   ↓
    │   Regenerate curl scripts
    │   ↓
    │   Re-run all tests
    │
    └─ [C] Cancel
        ↓
        Stop validation
        Save partial report
```

---

## Implementation Notes

### In `.graceucs`:
- Lines 328-355: Special handling for 401/403 errors
- Lines 414-416: Don't auto-fix auth without credential verification

### In `validation_rules.md`:
- Lines 25-26: Updated table with "Special Handling" column
- Lines 61-97: Complete example of credential verification workflow

### In `README.md`:
- Lines 224-264: "Special Case: Authentication Errors (401/403)" section
- Line 394: Added benefit #7 about credential verification

---

## Summary

**Authentication errors get special treatment:**
1. ✅ Ask user to verify credentials first
2. ✅ Allow credential retry without penalty
3. ✅ Only fix tech spec if user confirms credentials are correct
4. ✅ Prevent false auto-fixes that break correct tech specs

This approach ensures we don't "fix" a correct tech spec when the real problem is just wrong credentials.
