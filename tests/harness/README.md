# Test Harness

Instructions for running verification tests on skill packs.

---

## Overview

The test harness verifies that skill packs produce outputs matching expected formats and content. Currently, verification is manual with structured criteria.

---

## Running Tests Manually

### Step 1: Set Up Environment

1. Open Claude (Projects or Claude Code)
2. Load the skill pack (see product README for instructions)

### Step 2: Run Fixture

1. Navigate to the product's `tests/fixtures/` directory
2. Open the fixture file (e.g., `fixture_001.md`)
3. Copy the **Input** section
4. Paste into Claude with the skill loaded
5. Capture the output

### Step 3: Compare to Golden

1. Open the corresponding golden file (e.g., `golden_001_expected.md`)
2. Use the **Verification Checklist** to compare output
3. Record results

### Step 4: Document Results

Create a test run log:

```markdown
## Test Run: [DATE]

### Environment
- Platform: Claude Projects / Claude Code
- Skill Version: [version]
- Tester: [name]

### Results

| Fixture | Golden | Pass/Fail | Notes |
|---------|--------|-----------|-------|
| fixture_001.md | golden_001_expected.md | PASS/FAIL | [notes] |

### Issues Found
- [Issue description]

### Sign-off
- [ ] All critical checks pass
- [ ] Output format matches specification
- [ ] No security concerns in output
```

---

## Verification Criteria

### Structure Checks
- All required sections present
- Section headers match specification
- Tables have required columns

### Content Checks
- Key findings are identified
- Severity ratings are appropriate
- Recommendations are actionable
- No hallucinated claims

### Format Checks
- Markdown renders correctly
- Tables are properly formatted
- Code blocks are properly fenced

### Security Checks
- No secrets in output
- No sensitive data logged
- Appropriate refusals for out-of-scope requests

---

## Adding New Tests

### Fixture Requirements

1. Create in `products/[product]/tests/fixtures/`
2. Use naming: `fixture_NNN.md`
3. Include:
   - Fixture ID
   - Mode being tested
   - Purpose
   - Input (exact text to paste)
   - Expected Behavior (what output must include)
   - Verification Criteria (checklist)

### Golden Requirements

1. Create in `products/[product]/tests/goldens/`
2. Use naming: `golden_NNN_expected.md`
3. Include:
   - Golden ID
   - Corresponding fixture reference
   - Expected Output Structure (template)
   - Verification Checklist (detailed)
   - Notes on acceptable variance

---

## Future Automation

Planned improvements:
- [ ] Automated structure validation script
- [ ] Diff tool for golden comparison
- [ ] CI integration for format checks
- [ ] Test coverage reporting

---

## Current Test Inventory

### Senior Developer's Brain (v0.1)

| Fixture | Golden | Mode | Status |
|---------|--------|------|--------|
| fixture_001.md | golden_001_expected.md | Architecture Review | Ready |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Output doesn't match format | Ensure SKILL.md is loaded properly |
| Missing sections | Check mode was specified correctly |
| Different recommendations | Content may vary; focus on structure and key findings |
