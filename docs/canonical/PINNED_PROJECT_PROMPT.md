# Pinned Project Prompt

**Execution contract for AI agents working in this repository.**

---

## Core Rules

1. **No Hallucinations**: Never invent APIs, schemas, or platform claims. If uncertain, mark as `[UNVERIFIED]` and create a validation task.

2. **Official Source Validation**: Before finalizing platform-dependent details, validate against official Anthropic sources. Log evidence in `VALIDATION_LOG.md`.

3. **Fallback Protocol**: If validation is impossible, proceed with best-known method but FLAG everything platform-dependent as `[UNVERIFIED]` in docs and code comments.

4. **Conflict Resolution**: When internal docs conflict with official sources about platform behavior, official sources win. Flag and document the discrepancy.

5. **Security First**: Never commit secrets. Never log sensitive content. Apply least privilege.

6. **Evidence Discipline**: Cite repo paths, reference internal docs, mark assumptions clearly.

7. **Output Format**: All significant outputs must follow the format in `PROJECT_INSTRUCTIONS.md`.

---

## Quick Reference

- **Validation Log**: `docs/canonical/VALIDATION_LOG.md`
- **Project Instructions**: `docs/canonical/PROJECT_INSTRUCTIONS.md`
- **Threat Model**: `docs/architecture/THREAT_MODEL.md`
- **Security Policy**: `SECURITY.md`

---

## Before You Start

1. Have you read `PROJECT_INSTRUCTIONS.md`?
2. Have you checked `VALIDATION_LOG.md` for existing validations?
3. Is your task platform-dependent? If yes, validate or mark `[UNVERIFIED]`.
