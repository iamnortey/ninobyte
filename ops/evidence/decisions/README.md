# Decision Evidence Receipts

This directory contains immutable evidence receipts for Architecture Decision Records (ADRs).

## File Structure

Each decision generates three files:

```
decision_YYYYMMDD_HHMMSS_<shortsha>.json           # Human-readable (pretty-printed)
decision_YYYYMMDD_HHMMSS_<shortsha>.canonical.json # Canonical format (for hashing)
decision_YYYYMMDD_HHMMSS_<shortsha>.canonical.json.sha256  # SHA256 checksum
```

## Receipt ID Format

```
decision_YYYYMMDD_HHMMSS_<shortsha>
```

Where:
- `YYYYMMDD_HHMMSS` is the UTC timestamp
- `<shortsha>` is the first 7 characters of the git HEAD SHA

## Canonical JSON Format

Canonical JSON ensures deterministic SHA256 hashes:

- **Sorted keys**: Fields appear in alphabetical order
- **Compact format**: No extraneous whitespace (`separators=(",", ":")`)
- **Consistent encoding**: Unicode preserved (`ensure_ascii=False`)
- **Trailing newline**: Single `\n` at EOF

## Generate a Receipt

```bash
# Create ADR with receipt
python3 scripts/ops/log_decision.py add \
    --title "Decision title" \
    --status accepted \
    --context "Why this decision" \
    --decision "What we decided" \
    --consequences "What happens as a result" \
    --verify

# Preview without writing
python3 scripts/ops/log_decision.py add \
    --title "Decision title" \
    --status proposed \
    --context "..." \
    --decision "..." \
    --consequences "..." \
    --dry-run
```

## Verify Integrity

```bash
# Compute SHA256 of canonical file
shasum -a 256 ops/evidence/decisions/decision_*.canonical.json

# Compare with stored checksum
cat ops/evidence/decisions/decision_*.canonical.json.sha256
```

Both should match exactly.

## Cross-Link Policy

Every decision receipt MUST be referenced by exactly one ADR in `docs/adr/`.
Orphan receipts (not referenced by any ADR) cause CI failure.

Validate with:
```bash
python3 scripts/ci/validate_adr_links.py
```

## Schema

```json
{
  "schema_version": "1",
  "receipt_id": "decision_YYYYMMDD_HHMMSS_<shortsha>",
  "created_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "title": "Decision title",
  "status": "proposed|accepted|superseded|rejected",
  "context": "Why this decision was needed",
  "decision": "What was decided",
  "consequences": "What happens as a result",
  "tags": ["tag1", "tag2"],
  "source": "Optional source reference",
  "notes": "Optional additional notes",
  "actor": "scripts/ops/log_decision.py",
  "repo_head": "full git commit SHA",
  "adr_path": "docs/adr/ADR-YYYYMMDD-HHMMSS-<slug>.md"
}
```
