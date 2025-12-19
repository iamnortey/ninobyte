# Test Harness

Instructions for running verification tests on skills and plugins.

**Version**: 0.1.1

---

## Overview

The test harness verifies that skills produce outputs matching expected formats and enforce security policy. Verification includes structural compliance, security policy enforcement, and content quality.

---

## Running Tests Manually

### Via Claude Code Plugin (Recommended)

1. **Install the plugin**:
   ```bash
   /plugin marketplace add ./
   /plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
   ```

2. **Run fixture**:
   - Open `skills/senior-developer-brain/tests/fixtures/fixture_001.md`
   - Copy the **Input** section
   - Paste into Claude Code
   - Capture the output

3. **Compare to golden**:
   - Open `skills/senior-developer-brain/tests/goldens/golden_001_expected.md`
   - Use the **Verification Checklist** to compare

### Via Claude Projects (Web Interface)

1. **Load skill**:
   - Create a new Claude Project
   - Upload `skills/senior-developer-brain/SKILL.md`
   - Upload files from `patterns/` directory

2. **Run fixture**:
   - Open fixture file
   - Copy the **Input** section
   - Paste into the Claude Project conversation

3. **Compare to golden**:
   - Use the Verification Checklist from the golden file

---

## Verification Criteria (v0.1.1)

### Structure Checks
- [ ] All required sections present (Summary, Components, Strengths, Concerns, Security Assessment, Risks, Recommendations, Questions)
- [ ] Section headers match SKILL.md specification
- [ ] Tables have required columns
- [ ] Security Assessment section present (NEW in v0.1.1)

### Security Policy Enforcement (MANDATORY)
- [ ] JWT in localStorage flagged as **CRITICAL** (not HIGH/MEDIUM)
- [ ] Single points of failure flagged as **CRITICAL**
- [ ] Recommendations include established patterns (httpOnly cookies, etc.)
- [ ] No approval of insecure defaults
- [ ] Security Assessment covers: Authentication, Authorization, Encryption, Secrets Management

### Content Checks
- [ ] Key findings are identified
- [ ] Severity ratings are appropriate (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Recommendations are actionable with priority labels
- [ ] No hallucinated claims

### Format Checks
- [ ] Markdown renders correctly
- [ ] Tables are properly formatted
- [ ] Priorities use consistent labels

---

## Pass/Fail Criteria

### PASS
- All structural sections present
- Security policy violations flagged at correct severity
- Recommendations provide secure alternatives
- No approval of insecure patterns

### FAIL
- Missing required sections (especially Security Assessment)
- Security issues rated below CRITICAL when policy requires CRITICAL
- Approval of insecure patterns (e.g., "JWT in localStorage is acceptable")
- Missing recommendations for flagged issues

---

## Test Run Log Template

```markdown
## Test Run: [DATE]

### Environment
- Platform: Claude Code / Claude Projects
- Plugin Version: [version]
- Skill Version: [version]
- Tester: [name]

### Results

| Fixture | Golden | Pass/Fail | Notes |
|---------|--------|-----------|-------|
| fixture_001.md | golden_001_expected.md | PASS/FAIL | [notes] |

### Security Policy Verification
- [ ] JWT localStorage flagged CRITICAL
- [ ] Single EC2 flagged CRITICAL
- [ ] Security Assessment section present
- [ ] Secure alternatives recommended

### Issues Found
- [Issue description]

### Sign-off
- [ ] All structural checks pass
- [ ] Security policy enforced correctly
- [ ] Output format matches v0.1.1 specification
```

---

## Current Test Inventory

### Senior Developer's Brain (v0.1.1)

| Fixture | Golden | Mode | Security Focus |
|---------|--------|------|----------------|
| fixture_001.md | golden_001_expected.md | Architecture Review | JWT localStorage, SPOFs |

---

## Adding New Tests

### Fixture Requirements

1. Create in `skills/<skill-name>/tests/fixtures/`
2. Use naming: `fixture_NNN.md`
3. Include:
   - Fixture ID
   - Mode being tested
   - Purpose
   - Input (exact text to paste)
   - Expected Behavior (what output must include)
   - **Security Policy Verification** (what security checks apply)
   - Verification Criteria (checklist)

### Golden Requirements

1. Create in `skills/<skill-name>/tests/goldens/`
2. Use naming: `golden_NNN_expected.md`
3. Include:
   - Golden ID and version
   - Corresponding fixture reference
   - Expected Output Structure (template)
   - **Security Policy Enforcement** checklist (MANDATORY)
   - Verification Checklist (detailed)
   - Notes on acceptable variance

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Output doesn't match format | Ensure SKILL.md is loaded; check version is 0.1.1 |
| Missing Security Assessment | Skill may be outdated; use canonical skill from `skills/` |
| Wrong severity ratings | Verify skill has Security Policy section |
| Plugin not found | Run `/plugin marketplace add ./` first |
