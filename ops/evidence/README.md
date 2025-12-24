# Evidence Directory

This directory stores evidence artifacts for auditing and compliance.

## Contents

- `pr/` - PR merge receipts with canonical JSON and SHA256 checksums
- `validation/` - Validation log receipts
- `decisions/` - Architecture decision receipts
- `INDEX.json` - Human-readable evidence index
- `INDEX.canonical.json` - Deterministic canonical index (enforced)
- `INDEX.canonical.json.sha256` - Integrity checksum for canonical index

## Evidence Index

The evidence index provides a single pane of glass over all canonical receipts.

### Regenerating the Index

```bash
python3 scripts/ops/build_evidence_index.py --write
```

This updates:
- `ops/evidence/INDEX.json`
- `ops/evidence/INDEX.canonical.json`
- `ops/evidence/INDEX.canonical.json.sha256`

### Printing Index to stdout

```bash
# Human-readable (matches INDEX.json byte-for-byte)
python3 scripts/ops/build_evidence_index.py --print

# Compact canonical (matches INDEX.canonical.json byte-for-byte)
python3 scripts/ops/build_evidence_index.py --print-canonical
```

### Verification

Run the full evidence contract check (cross-platform):

```bash
python3 scripts/ops/evidence_contract_check.py
```

This runs all integrity checks including byte-for-byte verification of `--print` output.

### CI Enforcement

The index is enforced via `validate_artifacts.py` which runs:

```bash
python3 scripts/ci/validate_evidence_index.py
```

This performs byte-for-byte validation of all three index artifacts. If drift is detected, CI fails with remediation instructions.

### Determinism Contract (v0.6.0)

- Items sorted by `(kind, id, canonical_path)` — stable across environments
- Timestamps normalized to `YYYY-MM-DDTHH:MM:SSZ` (ISO-8601 Zulu)
- **No `generated_at_utc`** — removed for determinism
- Canonical JSON uses sorted keys and compact separators

### Regression Tests

Six tests enforce the determinism contract:

| Test | Guarantee |
|------|-----------|
| Idempotent build | Two consecutive builds produce identical output |
| Ordering | Items sorted by `(kind, id, canonical_path)` |
| No timestamps | No `generated_at_utc` in output |
| Counts match | Declared counts match actual item counts |
| `--print` contract | Output matches `INDEX.json` byte-for-byte |
| `--print-canonical` contract | Output matches `INDEX.canonical.json` byte-for-byte |

Run tests:
```bash
python3 scripts/ops/test_evidence_index_determinism.py
```

## Security Note

Sensitive evidence should be marked with `.sensitive` extension and is excluded via `.gitignore`.
