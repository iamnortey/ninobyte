# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant
technical and governance decisions for the ninobyte project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision
made along with its context and consequences. ADRs provide:

- **Immutable history** of why decisions were made
- **Context** for future developers
- **Accountability** through evidence receipts

## Naming Convention

ADR files follow the pattern:

```
ADR-YYYYMMDD-HHMMSS-<slug>.md
```

Where:
- `YYYYMMDD-HHMMSS` is the UTC timestamp when the decision was recorded
- `<slug>` is a kebab-case summary of the decision title

Example: `ADR-20251223-120000-use-canonical-json-for-receipts.md`

## ADR Statuses

| Status | Meaning |
|--------|---------|
| `proposed` | Decision is under discussion |
| `accepted` | Decision has been approved and is in effect |
| `superseded` | Decision has been replaced by a newer ADR |
| `rejected` | Decision was considered but not adopted |

## Evidence Receipts

Every ADR must include an **Evidence Receipt** linking to an immutable
decision receipt under `ops/evidence/decisions/`. This provides:

- Cryptographic integrity (SHA256 checksum)
- Deterministic canonical JSON format
- Git commit anchoring

Receipt path format:
```
ops/evidence/decisions/decision_YYYYMMDD_HHMMSS_<shortsha>.canonical.json
```

## Creating an ADR

Use the CLI tool to create ADRs with proper receipts:

```bash
python3 scripts/ops/log_decision.py add \
    --title "Use canonical JSON for receipts" \
    --status accepted \
    --context "We need deterministic hashing for evidence integrity" \
    --decision "Adopt canonical JSON serialization" \
    --consequences "All receipts use sorted keys and compact format" \
    --verify
```

## Listing ADRs

```bash
python3 scripts/ops/log_decision.py list
```

## Validating ADRs

The CI pipeline validates:
1. Every ADR has exactly one evidence receipt reference
2. Referenced receipts exist on disk
3. No orphan receipts (all receipts are referenced)

Run locally:
```bash
python3 scripts/ci/validate_adr_links.py
```

## Files

| File | Purpose |
|------|---------|
| `README.md` | This documentation |
| `TEMPLATE.md` | Template for manual ADR creation |
| `ADR-*.md` | Individual decision records |
