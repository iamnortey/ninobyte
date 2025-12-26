# Vibe Pilot Runbook

**Version:** 1.0.0
**Created:** 2025-12-26
**Owner:** DevSecOps

---

## Purpose

This runbook documents the "Vibe Pilot" process for validating enterprise delivery loops on this repository. It ensures changes follow the Plan > Expert Review > Code > Audit > Release workflow.

---

## Prerequisites

### Environment
- Claude Code v2.0.53+
- Git configured with signing (optional)
- Access to governance commands in `~/.claude/commands/`

### Mode
- **Enterprise Mode** must be active
- Run `/enterprise` to activate
- Verify with `/status`

### Safety Harness
Destructive operations require explicit approval:
1. `/change-plan` generates approval token
2. User types `APPROVE:<id>` to execute

---

## Procedure

### 1. Pre-flight
```bash
# Verify repo
git rev-parse --show-toplevel
git status --porcelain=v1

# Check for dirty state (document but proceed)
```

### 2. Create Pilot Branch
```bash
git checkout -b chore/vibe-pilot-YYYY-MM-DD
```

### 3. Plan First
- Choose a small, low-risk change
- Avoid: auth, infra, migrations, production config
- Allowed: docs, tests, minor refactors

Create implementation plan with:
- Scope
- Files affected
- Tests
- Rollback strategy
- Security notes

### 4. Implement Change
- Keep patch minimal
- Follow existing code style
- Add tests if touching code

### 5. Quality Gates

Run all three governance checks:

```
/audit      → Security + code quality review
/red-team   → Breakage plan generation
/compliance → Pre-commit compliance check
```

All gates must pass before proceeding.

### 6. Local Commit
```bash
git add <files>
git commit -m "chore: <description>"
```

**Do NOT push without approval.**

### 7. PR Preparation

Generate PR draft with:
- Summary
- Test plan
- Audit result
- Compliance result
- Red-team notes
- Rollback instructions

### 8. Approval for Remote Operations

The following require `/change-plan` + `APPROVE:<id>`:
- `git push`
- `gh pr create`
- Branch deletion
- Any destructive action

---

## Quality Gate Details

### /audit
Checks for:
- Hardcoded secrets
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure dependencies
- OWASP Top 10 issues

### /red-team
Generates:
- Abuse cases
- Failure modes
- Adversarial tests

### /compliance
Verifies:
- No secrets in code
- No PII in logs
- License compatibility
- Rate limiting (if applicable)

---

## Evidence Outputs

All runs should produce:
```
ops/claude-setup/next-run/YYYY-MM-DD/
├── RUN_REPORT.md
├── RUN_STATE.json
├── RUN_COMMAND_LOG.md
└── ARTIFACTS/
    ├── PLAN.md
    ├── AUDIT.md
    ├── RED_TEAM.md
    ├── COMPLIANCE.md
    └── PR_DRAFT.md
```

---

## Rollback

If issues are discovered:
1. Do not push
2. Reset branch: `git checkout main`
3. Delete branch: `git branch -D chore/vibe-pilot-YYYY-MM-DD`
4. Document in run report

---

## References

- [SAFETY_HARNESS.md](../../docs/governance/SAFETY_HARNESS.md)
- [CLAUDE.md](~/CLAUDE.md) - Director Rulebook
- [CANONICAL_COMMAND_MAP.md](../../docs/governance/CANONICAL_COMMAND_MAP.md)
