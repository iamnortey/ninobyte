# Validation Evidence

This directory stores immutable evidence receipts for validation log entries.

## File Types

| Pattern | Description |
|---------|-------------|
| `validation_<timestamp>_<sha>.json` | Raw receipt (human-readable, pretty-printed) |
| `validation_<timestamp>_<sha>.canonical.json` | Canonical JSON (deterministic format for hashing) |
| `validation_<timestamp>_<sha>.canonical.json.sha256` | SHA256 checksum of canonical receipt |

## Receipt ID Format

```
validation_YYYYMMDD_HHMMSS_<shortsha>
```

- Timestamp is UTC
- Short SHA is first 7 characters of git HEAD at creation time

## SHA256 Checksum Format

```
<hash>  <repo-relative-path>
```

Note: Two spaces between hash and path (standard `shasum` format).

Example:
```
abc123...  ops/evidence/validation/validation_20231215_143022_abc1234.canonical.json
```

## CLI Usage

### Add a Validation Entry

```bash
python3 scripts/ops/log_validation.py add \
  --claim "Validator now enforces orphan checksum policy" \
  --source "repo governance decision" \
  --status verified \
  --confidence medium \
  --tags governance,evidence \
  --notes "Phase 4B validation log automation" \
  --verify
```

### List Recent Entries

```bash
python3 scripts/ops/log_validation.py list --limit 10
```

### Lint the Validation Log

```bash
python3 scripts/ops/log_validation.py lint
```

### Dry Run (Preview)

```bash
python3 scripts/ops/log_validation.py add \
  --claim "Test claim" \
  --source "test" \
  --status verified \
  --confidence low \
  --dry-run
```

## Verify Integrity

```bash
# Validate all evidence files (including validation receipts)
python3 scripts/ci/validate_evidence_integrity.py
```
