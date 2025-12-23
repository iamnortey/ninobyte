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

### CI Enforcement

The index is enforced via `validate_artifacts.py` which runs:

```bash
python3 scripts/ci/validate_evidence_index.py
```

This performs byte-for-byte validation of all three index artifacts. If drift is detected, CI fails with remediation instructions.

### Determinism Contract

- Items sorted by `(kind, sort_timestamp_utc, canonical_path)`
- Timestamps normalized to `YYYY-MM-DDTHH:MM:SSZ` (ISO-8601 Zulu)
- `generated_at_utc` is the latest timestamp among indexed items (not "now")
- Canonical JSON uses sorted keys and compact separators

## Security Note

Sensitive evidence should be marked with `.sensitive` extension and is excluded via `.gitignore`.
