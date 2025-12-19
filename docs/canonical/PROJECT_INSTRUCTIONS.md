# Project Instructions

**Repo Root**: `/Users/isaacnortey/Developer/ninobyte`
**Version**: 0.1
**Last Updated**: 2025-12-19

---

## Mission

Build the #2 most trusted, implementation-grade education and tooling resource around Anthropic/Claude agent ecosystems (Skills, MCP, Claude Code plugins) by shipping verified, secure, reproducible assets.

## Non-Goals

- We do NOT compete on volume or breadth—quality and trust win
- We do NOT fabricate capabilities, APIs, or roadmap claims
- We do NOT ship unverified platform-dependent code as production-ready

---

## Governance — Enforcement Files

| File | Purpose |
|------|---------|
| `PINNED_PROJECT_PROMPT.md` | Execution contract for AI agents working in this repo |
| `VALIDATION_LOG.md` | Evidence trail for all official source validations |
| `CHANGELOG.md` | Version history and breaking changes |
| `COMPATIBILITY_MATRIX.md` | Platform version compatibility tracking |

---

## Sources of Truth Hierarchy

### Tier A: Internal Canon (Strategy & Design Intent)
- `docs/canonical/PROJECT_INSTRUCTIONS.md` (this file)
- `docs/canonical/PINNED_PROJECT_PROMPT.md`
- Product-level `SKILL.md` and `README.md` files

### Tier B: Official Sources (Platform Behavior & Feasibility)
- https://github.com/anthropics
- https://platform.claude.com/docs/en/home
- https://www.anthropic.com/engineering
- https://www.anthropic.com/research
- https://www.anthropic.com/learn
- https://claude.com/resources/use-cases
- https://anthropic.skilljar.com/

### Tier C: Community & Inference
- Community examples, blog posts, third-party tutorials
- Inference from observed behavior
- **Always mark as lower confidence**

---

## Always-Current Policy

### Freshness Rule

Any claim about Anthropic/Claude platform behavior is TEMPORARY until validated against Tier B sources within the last 30 days.

### Mandatory Validation Logging

Every platform-dependent decision MUST be logged in `VALIDATION_LOG.md` with:
- Entry ID: `VL-YYYYMMDD-###`
- Retrieval date
- Source URL(s)
- For GitHub: repo + commit/tag/release/issue reference
- What was confirmed or changed
- Impact on implementation

### Conflict Resolution Tie-Breaker

When Internal Canon (Tier A) conflicts with Official Sources (Tier B) about platform capabilities or syntax:

1. **Official Sources ALWAYS supersede** for technical feasibility
2. Flag the discrepancy in the relevant product's risks section
3. Add an entry in `VALIDATION_LOG.md`
4. Propose updates to internal docs to align with reality

---

## Required Response Format

All significant work outputs must include:

1. **Executive Summary** — What was done
2. **Decisions Made** — Trade-offs and rationale
3. **Official Validation Notes** — What was validated vs marked `[UNVERIFIED]`
4. **Repo Map** — Affected files/directories
5. **What Was Created/Updated** — File-by-file summary
6. **Acceptance Criteria** — How to verify completeness
7. **Risks + Mitigations** — Including Canon vs Official conflicts
8. **Next Actions** — Prioritized follow-ups

---

## Security Posture

- No secrets committed; strong `.gitignore`
- `SECURITY.md` at repo root
- Threat model at `docs/architecture/THREAT_MODEL.md`
- Never log sensitive content
- Treat tool calls, plugins, and MCP servers as attack surfaces

---

## Development Workflow

1. Read `PINNED_PROJECT_PROMPT.md` before any work
2. Check `VALIDATION_LOG.md` for relevant validations
3. If platform-dependent:
   - Validate against Tier B sources
   - Log in `VALIDATION_LOG.md`
   - If validation impossible, mark `[UNVERIFIED]`
4. Follow product-specific `SKILL.md` or `README.md`
5. Run tests/verification before completion
6. Follow `ops/release/RELEASE_CHECKLIST.md` for releases
