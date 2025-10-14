# Pattern Extraction Prompt Template

> **Purpose:** This template is used by the Pattern Extractor Agent (Agent 1) to extract universal code quality patterns from GitHub PR review comments.

---

## Agent Instructions

You are tasked with extracting universal, connector-agnostic code quality patterns from PR review comments for the UCS connector quality feedback database.

### INPUT DATA

- **PR URL:** `{{PR_URL}}`
- **PR Owner:** `{{PR_OWNER}}`
- **PR Repo:** `{{PR_REPO}}`
- **PR Number:** `{{PR_NUMBER}}`
- **Date:** `{{DATE}}`

### YOUR TASK

Extract all code quality patterns from the PR review comments and generalize them to universal rules applicable to ALL UCS connectors.

---

## STEP 1: Fetch PR Comments

Fetch ALL review comments from the PR including diff_hunks:

```bash
gh api repos/{{PR_OWNER}}/{{PR_REPO}}/pulls/{{PR_NUMBER}}/comments --paginate > /tmp/pr{{PR_NUMBER}}_comments.json
```

Count total comments:

```bash
jq 'length' /tmp/pr{{PR_NUMBER}}_comments.json
```

---

## STEP 2: Parse Comments

For each comment, extract:
- **Comment body** - The feedback text
- **File path and line number** - Location of the issue
- **Reviewer username** - Who provided the feedback
- **diff_hunk** - Code context showing WRONG (- lines) vs CORRECT (+ lines)

Parse into readable format:

```bash
jq -r '.[] | "\n=== COMMENT ===\nFile: \(.path)\nLine: \(.line // \"N/A\")\nReviewer: \(.user.login)\nDate: \(.created_at)\nComment: \(.body)\n--- DIFF HUNK ---\n\(.diff_hunk // \"N/A\")\n"' /tmp/pr{{PR_NUMBER}}_comments.json > /tmp/pr{{PR_NUMBER}}_parsed.txt
```

---

## STEP 3: Extract Patterns

For each comment, identify:

1. **The WRONG pattern** - What was done incorrectly
2. **The CORRECT pattern** - What should be done instead
3. **Code examples** from diff_hunk (if available)
4. **The underlying universal principle** - Why this matters for ALL connectors

---

## STEP 4: Generalize to Universal Patterns

**CRITICAL:** Every pattern MUST apply to ALL connectors, not just `{{PR_REPO}}`.

**Generalization Rules:**
- Replace connector-specific names:
  - `{{PR_REPO}}` → `{{ConnectorName}}`
  - `{{pr_repo}}` → `{{connector_name}}`
  - Any specific connector name → `{{ConnectorName}}`
- Mark as `connector: general` (NOT connector-specific)
- Mark as `applicability: ALL_CONNECTORS`
- Extract UNIVERSAL principle applicable to all UCS connectors

**Example Generalization:**

```yaml
# BEFORE (connector-specific):
wrong_code: |
  impl Stripe {
      fn authorize() { ... }
  }

# AFTER (universal):
wrong_code: |
  impl {{ConnectorName}} {
      fn authorize() { ... }
  }
```

---

## STEP 5: Categorize Each Pattern

Assign category based on content:

- **UCS_PATTERN_VIOLATION** - Wrong UCS types/traits (RouterData vs RouterDataV2, ConnectorIntegration vs ConnectorIntegrationV2, hyperswitch_* vs domain_types)
- **RUST_BEST_PRACTICE** - Rust idioms (.clone() usage, error handling, ? operator, etc.)
- **CONNECTOR_PATTERN** - Connector implementation patterns (request types, transformers, status mapping, authentication)
- **CODE_QUALITY** - Code duplication, naming, structure, hardcoding, DRY violations
- **DOCUMENTATION** - Missing or incorrect docs
- **PERFORMANCE** - Inefficiencies, unnecessary allocations
- **SECURITY** - Security issues, unsafe code, memory manipulation

---

## STEP 6: Assign Severity

Based on impact:

- **CRITICAL** - Must fix (UCS pattern violations, security issues, breaks functionality, data integrity issues)
- **WARNING** - Should fix (code quality, best practices, technical debt)
- **SUGGESTION** - Nice to have (minor improvements, optimizations)

---

## STEP 7: Create Structured Output

Output each pattern in this YAML structure:

```yaml
---
PATTERN_ID: PATTERN-001
category: [CATEGORY]
severity: CRITICAL|WARNING|SUGGESTION
title: [Short universal title]

wrong_pattern: |
  [Description of wrong pattern in universal terms]

correct_pattern: |
  [Description of correct pattern in universal terms]

code_example_wrong: |
  [Code from diff_hunk showing - lines, generalized with {{ConnectorName}}]

code_example_correct: |
  [Code from diff_hunk showing + lines, generalized with {{ConnectorName}}]

universal_principle: |
  [Why this matters for ALL connectors - the underlying reason]

reviewer: [username]
source_pr: "{{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}"
source_connector: "{{PR_REPO}}"
applies_to: "ALL_CONNECTORS"
---
```

---

## STEP 8: Save Output

Write all patterns to:

```
/tmp/pr{{PR_NUMBER}}_extracted_patterns.yaml
```

---

## OUTPUT FORMAT EXAMPLE

```yaml
---
PATTERN_ID: PATTERN-001
category: UCS_PATTERN_VIOLATION
severity: CRITICAL
title: Use amount conversion framework instead of manual conversion

wrong_pattern: |
  Manually converting amounts without using the UCS amount conversion framework

correct_pattern: |
  Declaring amount converters in the amount_converters field of create_all_prerequisites macro

code_example_wrong: |
  macros::create_all_prerequisites!(
      ...
      amount_converters: [],  // Empty - wrong!

code_example_correct: |
  macros::create_all_prerequisites!(
      ...
      amount_converters: [
          (flow: Authorize, converter: AuthorizeAmountConverter),
          (flow: Capture, converter: CaptureAmountConverter),
      ],

universal_principle: |
  UCS provides a standardized amount conversion framework that handles currency conversions, minor unit calculations, and amount validation consistently. Always use this framework rather than implementing manual amount conversions to ensure correctness and consistency across all connectors.

reviewer: {{REVIEWER_USERNAME}}
source_pr: "{{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}"
source_connector: "{{PR_REPO}}"
applies_to: "ALL_CONNECTORS"
---
```

---

## IMPORTANT RULES

1. **Universality:** Every pattern MUST apply to ALL connectors, not just `{{PR_REPO}}`
2. **Specificity:** Include exact code examples from diff_hunks (generalized)
3. **Traceability:** Always include reviewer, source PR, source connector
4. **Generalization:** Use placeholders like `{{ConnectorName}}`, `{{FlowName}}`, `{{RequestType}}`
5. **Completeness:** Process ALL comments, don't skip any
6. **Deduplication:** If multiple comments describe same pattern, create one pattern entry

---

## FINAL DELIVERABLE

**File:** `/tmp/pr{{PR_NUMBER}}_extracted_patterns.yaml`

**Summary:** "Extracted [N] universal patterns from [M] PR comments"

**Contents:** All extracted patterns in YAML format, ready for Agent 2 to transform into rich feedback entries.
