# Release Gate Policy

**Version:** 1.0.0
**Effective:** 2025-12-26
**Purpose:** Codify merge and release gates as a single source of truth

---

## Overview

All code changes must pass through defined gates before merge. This policy establishes mandatory and recommended gates for different change types.

---

## Gate Definitions

### Gate 1: Automated CI

**Type:** Mandatory (all changes)

| Check | Tool | Failure Action |
|-------|------|----------------|
| Artifact Validation | `validate_artifacts.py` | Block merge |
| Repository Structure | CI workflow | Block merge |
| Security Scan | CI workflow | Block merge |
| Unit Tests | pytest | Block merge |
| Contract Gates | CI workflow | Block merge |

### Gate 2: /audit

**Type:** Mandatory (code changes)

Run `/audit` command before PR creation.

| Check | Scope |
|-------|-------|
| Security vulnerabilities | OWASP Top 10 |
| Code quality | Complexity, duplication |
| Best practices | Language-specific patterns |

**Evidence Location:** PR description or linked artifact

### Gate 3: /compliance

**Type:** Mandatory (all changes)

Run `/compliance` command before PR creation.

| Check | Scope |
|-------|-------|
| Secrets detection | API keys, tokens, passwords |
| PII exposure | Personal data in code/logs |
| Logging safety | No sensitive data logged |
| Rate limiting | Public endpoints protected |
| License compatibility | No GPL contamination |

**Evidence Location:** PR description or linked artifact

### Gate 4: /red-team

**Type:** Recommended (feature changes)

Run `/red-team` command for significant features.

| Analysis | Output |
|----------|--------|
| Abuse cases | How could this be exploited? |
| Failure modes | What happens when dependencies fail? |
| Adversarial tests | Edge cases and attack vectors |

**Evidence Location:** PR description or ops/evidence/

---

## Change Type Matrix

| Change Type | CI | /audit | /compliance | /red-team |
|-------------|-------|--------|-------------|-----------|
| Documentation | Required | Optional | Required | Optional |
| Bug Fix | Required | Required | Required | Optional |
| Feature | Required | Required | Required | Recommended |
| Security Fix | Required | Required | Required | Required |
| Infrastructure | Required | Required | Required | Required |
| Dependency Update | Required | Required | Required | Optional |

---

## Evidence Artifacts

### Required Evidence Location

All gate evidence must be stored in one of:

1. **PR Description** - Inline summary of gate results
2. **ops/evidence/** - Full audit artifacts (for significant changes)
3. **ops/claude-setup/*/ARTIFACTS/** - Session-specific evidence

### Evidence Format

```markdown
## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| /audit | PASS | No issues found |
| /compliance | PASS | No secrets, no PII |
| /red-team | LOW risk | [link to analysis] |
```

---

## Approval Requirements

### Destructive Operations

Changes involving destructive operations require Safety Harness approval:

1. Submit `/change-plan` with exact commands
2. Receive `APPROVE:<id>` token
3. Execute only after approval
4. Log to audit trail

**Destructive operations include:**
- `git push`, `git push -f`
- `rm`, `rm -rf`, file deletion
- Database migrations
- Infrastructure changes
- Permission modifications

### Code Owners

If CODEOWNERS file exists, relevant owners must approve changes to their areas.

---

## Gate Bypass (Emergency Only)

In emergency situations, gates may be bypassed with:

1. **Justification document** explaining why bypass is necessary
2. **Post-merge audit** within 24 hours
3. **Issue creation** to address any skipped gates

Bypass must be documented in:
```
ops/evidence/bypasses/YYYY-MM-DD-<description>.md
```

---

## Enforcement

This policy is enforced by:

1. **CI Pipeline** - Automated checks block merge
2. **CLAUDE.md Director Rulebook** - Claude Code governance
3. **PR Templates** - Require gate evidence
4. **Code Review** - Reviewers verify gate completion

---

## Related Documents

| Document | Purpose |
|----------|---------|
| RELEASE_CHECKLIST.md | Full release process checklist |
| SAFETY_HARNESS.md | Destructive operation policy |
| CANONICAL_COMMAND_MAP.md | Command reference |
| ADR-0001 | Claude Operating System decision |

