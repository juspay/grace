---
description: Populate feedback.md from GitHub PR review comments automatically
---

You are automating UCS feedback database population from a GitHub Pull Request.

## INPUT

**PR URL:** {arg1}

Example:
```
/populate-feedback https://github.com/juspay/connector-service/pull/216
```

## YOUR MISSION

Extract code quality patterns from the provided PR's review comments and populate the UCS feedback database (`guides/feedback.md`) with rich, reusable feedback entries.

---

## PROCESS OVERVIEW

This is a **2-agent sequential workflow**:

1. **Agent 1 (Pattern Extractor):** Fetch PR comments → Extract universal patterns → Output YAML
2. **Agent 2 (Feedback Populator):** Read patterns → Assign FB-IDs → Create rich entries → Update database

---

## STEP 1: Parse PR URL

Extract PR information from the URL:

**URL Format:** `https://github.com/{owner}/{repo}/pull/{number}`

**Extract:**
- `PR_OWNER`: Repository owner (e.g., "juspay")
- `PR_REPO`: Repository name (e.g., "connector-service")
- `PR_NUMBER`: Pull request number (e.g., "216")
- `PR_URL`: Full URL (keep as provided)
- `DATE`: Current date in YYYY-MM-DD format

**Validation:**
- URL must be a GitHub PR URL
- Must match pattern: `https://github.com/*/*/pull/*`
- PR number must be numeric

If URL is invalid, error and ask user for correct format.

---

## STEP 2: Launch Pattern Extractor Agent

**Agent Type:** general-purpose

**Task Description:** "Extract universal patterns from PR #{number}"

**Prompt Construction:**

1. Read the template from: `modules/Codegen/guides/quality/templates/extract_patterns_prompt.md`
2. Replace template variables:
   - `{{PR_URL}}` → {arg1}
   - `{{PR_OWNER}}` → {extracted owner}
   - `{{PR_REPO}}` → {extracted repo}
   - `{{PR_NUMBER}}` → {extracted number}
   - `{{DATE}}` → {current date}
3. Pass the customized prompt to the agent

**Agent Responsibilities:**
- Fetch PR comments via `gh api`
- Parse diff_hunks for code context
- Extract patterns with WRONG vs CORRECT code
- Generalize connector-specific → universal (`{{ConnectorName}}`)
- Categorize by type (UCS_PATTERN_VIOLATION, CODE_QUALITY, etc.)
- Assign severity (CRITICAL, WARNING, SUGGESTION)
- Output to: `/tmp/pr{number}_extracted_patterns.yaml`

**Expected Output File:**
```
/tmp/pr{number}_extracted_patterns.yaml
```

**Wait for Agent 1 to complete before proceeding.**

---

## STEP 3: Validate Agent 1 Output

Check that the output file exists and is not empty:

```bash
test -f /tmp/pr{number}_extracted_patterns.yaml && echo "✅ Patterns extracted" || echo "❌ Extraction failed"
```

If extraction failed:
- Check if PR has review comments
- Verify gh CLI is authenticated
- Display error and stop

If successful:
- Count patterns: `grep -c "^PATTERN_ID:" /tmp/pr{number}_extracted_patterns.yaml`
- Display: "✅ Extracted [N] patterns from PR #{number}"

---

## STEP 4: Launch Feedback Populator Agent

**Agent Type:** general-purpose

**Task Description:** "Create rich feedback entries from PR #{number} patterns"

**Prompt Construction:**

1. Read the template from: `modules/Codegen/guides/quality/templates/populate_feedback_prompt.md`
2. Replace template variables:
   - `{{PR_NUMBER}}` → {extracted number}
   - `{{PR_OWNER}}` → {extracted owner}
   - `{{PR_REPO}}` → {extracted repo}
   - `{{PR_URL}}` → {arg1}
   - `{{DATE}}` → {current date}
3. Pass the customized prompt to the agent

**Agent Responsibilities:**
- Read extracted patterns from `/tmp/pr{number}_extracted_patterns.yaml`
- Read current `guides/feedback.md`
- Scan for existing FB-IDs to avoid conflicts
- Assign FB-IDs based on category/severity (using appropriate ranges)
- Create rich feedback entries (10 sections each):
  - Metadata (14 fields)
  - Issue Description
  - Context / When This Applies
  - Code Example - WRONG
  - Code Example - CORRECT
  - Why This Matters
  - How to Fix
  - Auto-Fix Rule
  - Related Patterns
  - Lessons Learned
  - Prevention
- Insert entries into correct sections
- Update statistics (counts by category/severity)
- Update version history
- Write updated `guides/feedback.md`
- Generate summary report: `/tmp/pr{number}_feedback_population_report.md`

**Expected Output Files:**
```
guides/feedback.md (updated)
/tmp/pr{number}_feedback_population_report.md
```

**Wait for Agent 2 to complete.**

---

## STEP 5: Generate Final Summary

After both agents complete, display a comprehensive summary:

```markdown
## ✅ Feedback Population Complete

**Source PR:** {PR_URL}
**Connector:** {PR_REPO}
**Date:** {DATE}

### Results

- ✅ Fetched [M] comments from PR #{number}
- ✅ Extracted [N] universal patterns
- ✅ Created [N] feedback entries
- ✅ Assigned FB-IDs: [list of FB-IDs]
- ✅ Updated feedback.md ([OLD_SIZE] → [NEW_SIZE] lines)
- ✅ Updated statistics

### Sections Updated

- Section [X]: [Name] ([count] entries)
- Section [Y]: [Name] ([count] entries)

### By Severity

- CRITICAL: [count] entries
- WARNING: [count] entries
- SUGGESTION: [count] entries

### Files

- 📊 Database: `guides/feedback.md`
- 📄 Report: `/tmp/pr{number}_feedback_population_report.md`
- 🔍 Extracted Patterns: `/tmp/pr{number}_extracted_patterns.yaml`

### Next Steps

1. Review the report: `/tmp/pr{number}_feedback_population_report.md`
2. Verify feedback.md updates: `guides/feedback.md`
3. Quality Guardian can now use these patterns for reviews

---

**Status:** ✅ SUCCESS
**Processing Time:** [duration]
```

---

## ERROR HANDLING

### Common Errors & Solutions:

**Error: GitHub CLI not authenticated**
```
Solution: Run `gh auth login` and authenticate
```

**Error: PR has no review comments**
```
Solution: This PR has no review comments to extract patterns from.
The feedback population system requires PR review comments.
```

**Error: FB-ID range full**
```
Solution: A category's FB-ID range is exhausted. This is rare.
Contact system administrator to expand the range.
```

**Error: Invalid PR URL**
```
Solution: Provide a valid GitHub PR URL in format:
https://github.com/{owner}/{repo}/pull/{number}
```

**Error: Pattern extraction failed**
```
Solution: Check that:
- gh CLI is authenticated (`gh auth status`)
- PR number exists and is accessible
- You have network connectivity to GitHub
```

**Error: Feedback.md update failed**
```
Solution: Check file permissions on guides/feedback.md
Ensure no other process is editing the file.
```

---

## IMPORTANT NOTES

### Sequential Execution

**CRITICAL:** Agent 2 MUST wait for Agent 1 to complete.

Do NOT run agents in parallel. The workflow is:
```
Agent 1 (Extract) → Complete → Agent 2 (Populate) → Complete → Summary
```

### Template Variables

Both agent prompts use template variables. You MUST replace all variables before passing to agents:

- `{{PR_URL}}`
- `{{PR_OWNER}}`
- `{{PR_REPO}}`
- `{{PR_NUMBER}}`
- `{{DATE}}`

### Output Files

Expected files after completion:
```
/tmp/pr{number}_extracted_patterns.yaml  (from Agent 1)
/tmp/pr{number}_feedback_population_report.md  (from Agent 2)
guides/feedback.md  (updated by Agent 2)
```

### Universality Guarantee

All feedback entries created will be:
- ✅ Universal (apply to ALL connectors)
- ✅ Generalized (use {{ConnectorName}} placeholders)
- ✅ Traceable (include source PR, reviewer, date)
- ✅ Complete (all 10 sections + metadata)
- ✅ Validated (FB-ID uniqueness checked)

---

## TEMPLATE FILE LOCATIONS

**Agent 1 Template:**
```
modules/Codegen/guides/quality/templates/extract_patterns_prompt.md
```

**Agent 2 Template:**
```
modules/Codegen/guides/quality/templates/populate_feedback_prompt.md
```

**Target Database:**
```
modules/Codegen/guides/feedback.md
```

**Documentation:**
```
modules/Codegen/guides/quality/POPULATE_FEEDBACK.md
```

---

## USAGE EXAMPLES

### Example 1: Populate from PR #216
```
/populate-feedback https://github.com/juspay/connector-service/pull/216
```

### Example 2: Populate from PR #220
```
/populate-feedback https://github.com/juspay/connector-service/pull/220
```

### Example 3: Any GitHub PR
```
/populate-feedback https://github.com/{owner}/{repo}/pull/{number}
```

---

## TROUBLESHOOTING

If anything goes wrong:

1. **Check Agent 1 output:** Does `/tmp/pr{number}_extracted_patterns.yaml` exist?
2. **Check pattern count:** How many patterns were extracted?
3. **Check Agent 2 output:** Was `guides/feedback.md` updated?
4. **Check report:** Review `/tmp/pr{number}_feedback_population_report.md` for details
5. **Check logs:** Look for error messages in agent outputs

**For detailed troubleshooting, see:**
```
modules/Codegen/guides/quality/POPULATE_FEEDBACK.md
```

---

**Ready to automate feedback population!** 🚀

Execute the 2-agent workflow as described above.
