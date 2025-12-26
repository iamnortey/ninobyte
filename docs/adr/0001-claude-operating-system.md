# ADR-0001: Claude Operating System - Safety Harness and Enterprise Loop

## Status

**Status**: accepted

## Context

As Claude Code adoption increased for development workflows at Ninobyte, we observed:

1. **Uncontrolled destructive operations** - Push, delete, and infrastructure commands executed without explicit approval
2. **Inconsistent quality gates** - Some PRs skipped audit/compliance/red-team reviews
3. **No audit trail** - Difficult to trace what operations Claude performed and when
4. **Mode ambiguity** - No clear distinction between "fast iteration" and "enterprise rigor" modes

We needed a governance framework that:
- Maintains developer velocity for low-risk operations
- Enforces approval gates for destructive operations
- Provides clear audit trails
- Supports both rapid prototyping and enterprise-grade delivery

## Decision

We adopt the **Claude Operating System** framework consisting of:

### 1. Safety Harness Policy

A compensating control system that requires explicit `APPROVE:<id>` tokens before executing destructive operations:

- File deletion (`rm`, `rm -rf`)
- File movement outside repo (`mv`)
- Permission changes (`chmod`, `chown`)
- Git push operations
- Infrastructure changes (Terraform, Kubernetes)
- Database migrations

### 2. Enterprise Mode (Default)

The default operating mode follows the enterprise delivery loop:

```
/enterprise → plan → implement → /audit → /compliance → /red-team → PR
```

All PRs must pass:
- `/audit` - Security and code quality review
- `/compliance` - Secrets, PII, licensing checks
- `/red-team` - Adversarial breakage analysis

### 3. Rapid Vibe Mode (Opt-in)

For prototyping, developers can enable Rapid Vibe Mode with:
- Reduced ceremony
- Required `TODO: VIBE_CODED - NEEDS AUDIT` stamps
- Mandatory audit pass before merge

### 4. Governance Commands

| Command | Purpose |
|---------|---------|
| `/enterprise` | Enable Safety Harness |
| `/vibe` | Enable Rapid Vibe Mode |
| `/change-plan` | Propose destructive operation |
| `/approve APPROVE:<id>` | Approve change plan |
| `/status` | Show current mode |

### 5. Audit Trail

All operations logged to:
- `ops/claude-setup/*/COMMAND_LOG.md`
- `ops/claude-setup/*/runtime/approvals.jsonl`

## Consequences

### Positive

- Destructive operations cannot execute without explicit human approval
- Clear audit trail for compliance and post-incident analysis
- Quality gates ensure consistent review standards
- Mode switching allows velocity when appropriate
- Documentation and runbooks formalize best practices

### Negative

- Additional ceremony for approved operations
- Learning curve for new team members
- Overhead for very simple changes

### Neutral

- Governance files add to repo size
- Slash commands require Claude Code familiarity

## Alternatives Considered

| Alternative | Pros | Cons | Why Not Chosen |
|-------------|------|------|----------------|
| No governance | Maximum velocity | High risk of accidents | Unacceptable for production repos |
| Pre-commit hooks only | Simpler | No destructive op protection | Insufficient coverage |
| Full manual review | Maximum control | Slow, no AI assistance | Negates Claude Code benefits |

## Evidence

This ADR documents the governance framework implemented across:

- `~/CLAUDE.md` - Director Rulebook
- `ops/claude-setup/followups/2025-12-26/governance/SAFETY_HARNESS.md`
- `ops/claude-setup/followups/2025-12-26/governance/CANONICAL_COMMAND_MAP.md`
- `ops/runbooks/VIBE_PILOT_RUNBOOK.md`

## Links

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Safety Harness Policy](../../../ops/claude-setup/followups/2025-12-26/governance/SAFETY_HARNESS.md)
- [PR #83 - Vibe Pilot Runbook](https://github.com/iamnortey/ninobyte/pull/83)

