# Feedback Population Prompt Template

> **Purpose:** This template is used by the Feedback Populator Agent (Agent 2) to transform extracted patterns into rich feedback entries and update the feedback database.

---

## Agent Instructions

You are tasked with creating rich feedback entries from extracted patterns and updating the UCS connector quality feedback database.

### INPUT DATA

- **Extracted Patterns:** `/tmp/pr{{PR_NUMBER}}_extracted_patterns.yaml`
- **Feedback Database:** `/Users/tushar.shukla/Downloads/Work/UCS/connector-service/grace/modules/Codegen/guides/feedback.md`
- **PR Number:** `{{PR_NUMBER}}`
- **Date:** `{{DATE}}`

### YOUR TASK

Transform the extracted patterns into comprehensive feedback entries following the exact template in feedback.md, then update the database with proper FB-ID assignment and statistics.

---

## STEP 1: Read Input Files

Read both files:

1. **Extracted patterns:** `/tmp/pr{{PR_NUMBER}}_extracted_patterns.yaml`
2. **Current feedback database:** `guides/feedback.md`

Count patterns to process:

```bash
grep -c "^PATTERN_ID:" /tmp/pr{{PR_NUMBER}}_extracted_patterns.yaml
```

---

## STEP 2: Scan Existing FB-IDs

Extract all existing FB-IDs from feedback.md to avoid conflicts:

```bash
grep -oE "FB-[0-9]{3}" guides/feedback.md | sort -u > /tmp/existing_fb_ids.txt
```

Count existing entries:

```bash
wc -l /tmp/existing_fb_ids.txt
```

---

## STEP 2.5: Duplicate Detection (Smart Pattern Matching)

**Purpose:** Prevent duplicate entries when processing same PR multiple times or when similar patterns exist across different PRs.

### Duplicate Detection Algorithm

For each pattern from extracted_patterns.yaml, check if a similar pattern already exists in feedback.md:

```python
# Pseudocode for duplicate detection

def detect_duplicate(new_pattern, existing_patterns):
    """
    Compare new pattern against all existing patterns.
    Returns (is_duplicate: bool, existing_fb_id: str, similarity_score: int)
    """

    best_match = None
    best_score = 0

    for existing_pattern in existing_patterns:
        score = 0

        # 1. Category Match (30 points)
        if new_pattern.category == existing_pattern.category:
            score += 30

        # 2. Title Similarity (30 points)
        title_similarity = calculate_text_similarity(
            new_pattern.title,
            existing_pattern.title
        )
        if title_similarity >= 0.7:  # 70% similar
            score += 30
        elif title_similarity >= 0.5:  # 50% similar
            score += 15

        # 3. Wrong Code Similarity (20 points)
        wrong_code_similarity = calculate_code_similarity(
            new_pattern.code_example_wrong,
            existing_pattern.code_example_wrong
        )
        if wrong_code_similarity >= 0.6:  # 60% similar
            score += 20
        elif wrong_code_similarity >= 0.4:  # 40% similar
            score += 10

        # 4. Correct Code Similarity (20 points)
        correct_code_similarity = calculate_code_similarity(
            new_pattern.code_example_correct,
            existing_pattern.code_example_correct
        )
        if correct_code_similarity >= 0.6:  # 60% similar
            score += 20
        elif correct_code_similarity >= 0.4:  # 40% similar
            score += 10

        # Track best match
        if score > best_score:
            best_score = score
            best_match = existing_pattern

    # Threshold: 70+ points = duplicate
    is_duplicate = best_score >= 70

    return is_duplicate, best_match.fb_id if best_match else None, best_score


def calculate_text_similarity(text1, text2):
    """
    Calculate text similarity (0.0 to 1.0)
    Can use: word overlap, Levenshtein distance, etc.
    """
    # Normalize: lowercase, remove punctuation
    words1 = set(normalize(text1).split())
    words2 = set(normalize(text2).split())

    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def calculate_code_similarity(code1, code2):
    """
    Calculate code similarity (0.0 to 1.0)
    Focus on structure, not whitespace/comments
    """
    # Normalize: remove comments, whitespace, {{ConnectorName}} placeholders
    normalized1 = normalize_code(code1)
    normalized2 = normalize_code(code2)

    # Token-based comparison
    tokens1 = set(tokenize(normalized1))
    tokens2 = set(tokenize(normalized2))

    # Jaccard similarity
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0
```

### Extraction Process

**Extract existing patterns from feedback.md:**

```bash
# Find all FB-XXX entries with their content
grep -A 150 "^### FB-" guides/feedback.md > /tmp/existing_patterns_raw.txt
```

For each existing pattern, extract:
- `FB-ID` (from heading: `### FB-XXX: Title`)
- `category` (from metadata YAML)
- `title` (from heading)
- `code_example_wrong` (from "Code Example - WRONG" section)
- `code_example_correct` (from "Code Example - CORRECT" section)
- `frequency` (current value from metadata)
- `source_pr` (current value from metadata)

### Decision Logic

For each new pattern:

1. **Run duplicate detection** against all existing patterns
2. **If duplicate detected (score >= 70):**
   ```
   - Find existing entry in feedback.md by FB-ID
   - Increment frequency: frequency = frequency + 1
   - Update source_pr to include new PR (make it a list if needed):
     - If source_pr is single value: "owner/repo#123"
     - Convert to: "owner/repo#123, owner2/repo2#456"
   - Add/update date_last_observed metadata field: {{DATE}}
     (This field may not exist in older entries, add it if missing)
   - Optionally add reviewer to reviewers list if tracking multiple reviewers
   - Skip FB-ID assignment
   - Skip creating new entry
   - Add to UPDATED_PATTERNS list for reporting
   ```

3. **If NOT duplicate (score < 70):**
   ```
   - Proceed with normal flow
   - Assign new FB-ID (STEP 3)
   - Create new entry (STEP 4)
   - Add to CREATED_PATTERNS list for reporting
   ```

### Tracking Lists

Maintain two lists throughout processing:

```python
CREATED_PATTERNS = []   # New patterns that got new FB-IDs
UPDATED_PATTERNS = []   # Existing patterns that were updated
```

Example:
```python
# New pattern (no duplicate)
CREATED_PATTERNS.append({
    'fb_id': 'FB-123',
    'title': 'New Pattern',
    'category': 'CODE_QUALITY'
})

# Duplicate pattern
UPDATED_PATTERNS.append({
    'fb_id': 'FB-100',  # Existing ID
    'title': 'Existing Pattern',
    'old_frequency': 1,
    'new_frequency': 2,
    'added_pr': 'owner/repo#456'
})
```

### Practical Implementation Tips

**Simplified Text Similarity:**
```bash
# Using grep/awk for basic similarity check
# Count common words between two strings

common_words=$(comm -12 \
    <(echo "$text1" | tr ' ' '\n' | sort -u) \
    <(echo "$text2" | tr ' ' '\n' | sort -u) \
    | wc -l)

total_words=$(echo "$text1 $text2" | tr ' ' '\n' | sort -u | wc -l)
similarity=$(echo "scale=2; $common_words / $total_words" | bc)
```

**Simplified Code Similarity:**
```bash
# Normalize code (remove whitespace, comments)
normalize_code() {
    sed 's/\/\/.*$//' |      # Remove // comments
    sed 's/{{.*}}/PLACEHOLDER/g' |  # Normalize placeholders
    tr -d ' \t\n' |          # Remove whitespace
    tr '[:upper:]' '[:lower:]'  # Lowercase
}

# Compare
code1_normalized=$(echo "$code1" | normalize_code)
code2_normalized=$(echo "$code2" | normalize_code)

if [ "$code1_normalized" == "$code2_normalized" ]; then
    similarity=1.0
else
    # Use diff or other comparison
    similarity=$(compare_strings "$code1_normalized" "$code2_normalized")
fi
```

### Output

At end of STEP 2.5:

```markdown
Duplicate Detection Results:
- Total patterns to process: [N]
- New patterns (will create): [M]
- Duplicate patterns (will update): [K]

Duplicates found:
- FB-100: Similar to PATTERN-005 (similarity: 85%)
- FB-102: Similar to PATTERN-012 (similarity: 78%)
```

---

## STEP 3: FB-ID Assignment Logic

**NOTE:** Only apply this step to NEW patterns (not duplicates identified in STEP 2.5).

For each NEW pattern (not marked as duplicate), assign FB-ID based on category and severity:

### FB-ID Ranges (from feedback.md lines 583-594):

| Range | Purpose | Section |
|-------|---------|---------|
| FB-001 to FB-099 | Critical UCS Pattern Violations | Section 1 |
| FB-100 to FB-199 | UCS-Specific Guidelines | Section 2 |
| FB-200 to FB-299 | Flow-Specific Best Practices | Section 3 |
| FB-300 to FB-399 | Payment Method Patterns | Section 4 |
| FB-400 to FB-499 | Common Anti-Patterns | Section 5 |
| FB-500 to FB-599 | Success Patterns | Section 6 |
| FB-600 to FB-699 | Rust Best Practices | Section 5 (subsection) |
| FB-700 to FB-799 | Performance Patterns | Section 5 (subsection) |
| FB-800 to FB-899 | Security Guidelines | Section 8 |
| FB-900 to FB-999 | Testing Patterns | Future use |

### Assignment Algorithm:

```python
# Pseudocode for FB-ID assignment

def assign_fb_id(pattern, existing_ids):
    category = pattern.category
    severity = pattern.severity

    # Determine range based on category + severity
    if category == "UCS_PATTERN_VIOLATION" and severity == "CRITICAL":
        range_start, range_end = 1, 99
        section = 1
    elif category == "UCS_PATTERN_VIOLATION" or (category == "CONNECTOR_PATTERN" and "ucs" in pattern.tags):
        range_start, range_end = 100, 199
        section = 2
    elif "flow-specific" in pattern.tags:
        range_start, range_end = 200, 299
        section = 3
    elif "payment-method" in pattern.tags:
        range_start, range_end = 300, 399
        section = 4
    elif category == "CODE_QUALITY":
        range_start, range_end = 400, 499
        section = 5
    elif category == "CONNECTOR_PATTERN":
        range_start, range_end = 400, 499  # Also Section 5
        section = 5
    elif category == "RUST_BEST_PRACTICE":
        range_start, range_end = 400, 499  # Subsection of 5
        section = 5
    elif category == "SECURITY":
        range_start, range_end = 800, 899
        section = 8
    elif category == "PERFORMANCE":
        range_start, range_end = 700, 799
        section = 5  # Subsection
    elif category == "TESTING_GAP":
        range_start, range_end = 900, 999
        section = 9  # Future
    else:
        range_start, range_end = 400, 499  # Default to common anti-patterns
        section = 5

    # Find next available ID in range
    for fb_id_num in range(range_start, range_end + 1):
        fb_id = f"FB-{fb_id_num:03d}"
        if fb_id not in existing_ids:
            return fb_id, section

    # If range full, error
    raise Exception(f"FB-ID range {range_start}-{range_end} is full!")

# Usage:
fb_id, target_section = assign_fb_id(pattern, existing_fb_ids)
```

---

## STEP 4: Create Rich Feedback Entries

**NOTE:** Only apply this step to NEW patterns. For DUPLICATE patterns, update existing entries instead (increment frequency, add source_pr).

For each NEW pattern (not marked as duplicate), create a complete feedback entry following the template from feedback.md (lines 518-581).

### Feedback Entry Template:

```markdown
### FB-[ID]: [Brief Descriptive Title]

**Metadata:**
```yaml
id: FB-XXX
category: [CATEGORY_NAME]
severity: CRITICAL | WARNING | SUGGESTION
connector: general
flow: All
applicability: ALL_CONNECTORS
date_added: {{DATE}}
status: Active
frequency: 1
impact: High | Medium | Low
tags: [tag1, tag2, tag3]
source_pr: {{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}
source_connector: {{PR_REPO}}
reviewer: [reviewer_username]
```

**Issue Description:**
[Universal description - what is wrong or what pattern to follow]

**Context / When This Applies:**
[When this issue typically occurs]

**Code Example - WRONG:**
```rust
// Generalized wrong example with {{ConnectorName}} placeholders
[wrong code from extracted pattern]
```

**Code Example - CORRECT:**
```rust
// Generalized correct example with {{ConnectorName}} placeholders
[correct code from extracted pattern]
```

**Why This Matters:**
[Universal principle from extracted pattern - why important for ALL connectors]

**How to Fix:**
1. [Step-by-step fix instructions]
2. [Specific actions to take]
3. [Reasoning]

**Auto-Fix Rule:**
```
IF [condition pattern]
THEN [suggested fix]
```

**Related Patterns:**
- See: FB-XXX (if related to other entries)
- Reference: guides/patterns/pattern_[flow].md

**Lessons Learned:**
[Key takeaways]

**Prevention:**
[How to avoid in future]

---
```

### Impact Level Guidelines:

- **High:** Breaks functionality, security issue, data integrity, UCS architecture violation
- **Medium:** Technical debt, maintainability, performance concern
- **Low:** Code style, minor optimization, documentation

---

## STEP 5: Insert Entries into Correct Sections

Based on `target_section` from FB-ID assignment, insert into appropriate section:

- **Section 1:** Critical Patterns (Must Follow) - FB-001 to FB-099
- **Section 2:** UCS-Specific Guidelines - FB-100 to FB-199
- **Section 3:** Flow-Specific Best Practices - FB-200 to FB-299
- **Section 4:** Payment Method Patterns - FB-300 to FB-399
- **Section 5:** Common Anti-Patterns - FB-400 to FB-499 (includes subsections for Rust, Performance)
- **Section 6:** Success Patterns - FB-500 to FB-599
- **Section 7:** Historical Feedback Archive
- **Section 8:** Security Guidelines - FB-800 to FB-899

**Insertion Strategy:**

1. Locate section header (e.g., `# 2. UCS-SPECIFIC GUIDELINES`)
2. If section is empty (has placeholder text), replace placeholder
3. If section has entries, append after last entry
4. Maintain markdown formatting
5. Keep quality review template at top intact

---

## STEP 6: Update Statistics

Update the **APPENDIX: METRICS & TRACKING** section (near end of feedback.md):

### Statistics to Update:

1. **Total Feedback Entries:**
   - Count all FB-XXX entries in file

2. **By Category:**
   - Count entries for each category
   - List FB-IDs for each category

3. **By Severity:**
   - Count CRITICAL, WARNING, SUGGESTION, INFO
   - List FB-IDs for each severity

4. **By Section:**
   - Count entries in each section
   - List FB-ID ranges

5. **Source Information:**
   - Update "Last PR processed"
   - Update "Last update" date
   - Increment "Total PRs processed" if tracked

### Example Statistics Update:

```markdown
## Feedback Statistics

**Total Feedback Entries:** [NEW_COUNT]

**By Category:**
- UCS_PATTERN_VIOLATION: [COUNT] (FB-XXX, FB-YYY, ...)
- RUST_BEST_PRACTICE: [COUNT] (FB-ZZZ, ...)
- CODE_QUALITY: [COUNT]
- CONNECTOR_PATTERN: [COUNT]
- SECURITY: [COUNT]
- TESTING_GAP: [COUNT]
- DOCUMENTATION: [COUNT]
- PERFORMANCE: [COUNT]
- SUCCESS_PATTERN: [COUNT]

**By Severity:**
- CRITICAL: [COUNT]
- WARNING: [COUNT]
- SUGGESTION: [COUNT]
- INFO: [COUNT]

**By Section:**
- Section 1 (Critical Patterns): [COUNT]
- Section 2 (UCS-Specific Guidelines): [COUNT]
- Section 3 (Flow-Specific Best Practices): [COUNT]
- Section 4 (Payment Method Patterns): [COUNT]
- Section 5 (Common Anti-Patterns): [COUNT]
- Section 6 (Success Patterns): [COUNT]
- Section 7 (Historical Archive): [COUNT]
- Section 8 (Security Guidelines): [COUNT]

**Source Information:**
- Last PR processed: {{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}
- Last update: {{DATE}}
- Source Connector: {{PR_REPO}}
- Reviewer: [reviewer_username]
```

---

## STEP 7: Update Version History

Add entry to version history section:

```markdown
## Version History

**v1.X.0** - {{DATE}}
- Added [N] feedback entries from {{PR_REPO}} connector review
- Populated Section [X]: [Section Name] (FB-XXX to FB-YYY)
- Updated statistics and metrics
- Source: {{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}, reviewer: [username]

[... previous versions ...]
```

---

## STEP 8: Write Updated feedback.md

Write the complete updated file back to:

```
/Users/tushar.shukla/Downloads/Work/UCS/connector-service/grace/modules/Codegen/guides/feedback.md
```

---

## STEP 9: Generate Summary Report

Create a comprehensive report at:

```
/tmp/pr{{PR_NUMBER}}_feedback_population_report.md
```

**Report Contents:**

```markdown
# PR #{{PR_NUMBER}} Feedback Population Report

**Date:** {{DATE}}
**Source PR:** {{PR_URL}}
**Source Connector:** {{PR_REPO}}
**Reviewer:** [username]
**Total Patterns Extracted:** [N]
**New Entries Created:** [M]
**Existing Entries Updated:** [K]

## Summary

- ✅ Created [M] new feedback entries
- ✅ Updated [K] existing feedback entries (duplicates detected)
- ✅ FB-IDs assigned: FB-XXX to FB-YYY (new entries)
- ✅ FB-IDs updated: FB-AAA, FB-BBB, ... (existing entries)
- ✅ Sections affected: [list]
- ✅ Statistics updated

## New Entries Created (FB-IDs Assigned)

### Section 2: UCS-Specific Guidelines
- FB-XXX: [Title] ✨ NEW

### Section 5: Common Anti-Patterns
- FB-AAA: [Title] ✨ NEW

[... etc ...]

## Existing Entries Updated (Duplicates)

### FB-100: [Existing Pattern Title]
- **Action:** Incremented frequency (1 → 2)
- **Updated:** Added source PR {{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}
- **Similarity:** 85% (matched PATTERN-005 from extracted patterns)
- **Reason:** Same category, similar title and code examples

### FB-205: [Another Existing Pattern]
- **Action:** Incremented frequency (3 → 4)
- **Updated:** Added source PR {{PR_OWNER}}/{{PR_REPO}}#{{PR_NUMBER}}
- **Similarity:** 78%
- **Reason:** Similar issue pattern detected

[... etc ...]

## Statistics

**By Category:**
| Category | Count |
|----------|-------|
| UCS_PATTERN_VIOLATION | [N] |
| CODE_QUALITY | [N] |
| ... | ... |

**By Severity:**
| Severity | Count |
|----------|-------|
| CRITICAL | [N] |
| WARNING | [N] |

## Files Updated

- ✅ guides/feedback.md (size: [OLD] → [NEW] lines)
- ✅ Statistics updated
- ✅ Version history updated

## Impact

**Quality Score Impact (if all patterns violated):**
- CRITICAL issues: [N] × -20 = -[X] points
- WARNING issues: [M] × -5 = -[Y] points
- Total: [SCORE]/100

**Status:** ✅ COMPLETE
```

---

## OUTPUT REQUIREMENTS

1. **Updated feedback.md:**
   - All new entries inserted in correct sections
   - Statistics updated accurately
   - Version history updated
   - No formatting errors

2. **Summary Report:**
   - File: `/tmp/pr{{PR_NUMBER}}_feedback_population_report.md`
   - Complete breakdown of what was added
   - Statistics and metrics

3. **Validation:**
   - All FB-IDs unique (no conflicts)
   - All entries have complete metadata
   - All code examples generalized ({{ConnectorName}})
   - All patterns marked: connector: general, applicability: ALL_CONNECTORS

---

## ERROR HANDLING

**If FB-ID range is full:**
- Error with clear message
- Suggest expanding range or using alternate range

**If pattern duplicate detected:**
- Increment frequency count instead of creating new entry
- Add source PR to list
- Note in report

**If metadata incomplete:**
- Error with specific missing fields
- Do not proceed with incomplete entries

---

## FINAL DELIVERABLE

**Summary Message:**

```
✅ Feedback Population Complete

📊 Processing Results:
- Total patterns extracted: [N]
- New entries created: [M]
- Existing entries updated: [K] (duplicates detected)

✨ New FB-IDs assigned: [list of new IDs]
🔄 Updated FB-IDs: [list of updated IDs]

📂 Sections affected: [list]
📈 Statistics: ✅ Updated

📄 Detailed Report: /tmp/pr{{PR_NUMBER}}_feedback_population_report.md
📊 Database: guides/feedback.md ([OLD_SIZE] → [NEW_SIZE] lines)

💡 Duplicate Detection:
- [K] duplicate patterns detected and merged with existing entries
- Frequency counts updated for patterns observed multiple times
- Source PRs tracked for traceability
```
