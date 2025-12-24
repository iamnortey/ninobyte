# Ninobyte CompliancePack

**Contract-first compliance evidence toolkit for audit-ready operations.**

CompliancePack provides deterministic, read-only compliance checking that produces
machine-readable evidence suitable for auditors and automated pipelines.

## Quick Start

Use a built-in policy pack for instant compliance checking:

```bash
# From product directory
cd products/compliancepack
PYTHONPATH=src python3 -m compliancepack check \
  --input /path/to/config.txt \
  --pack secrets.v1

# From repo root
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input products/compliancepack/tests/fixtures/sample_input.txt \
  --pack secrets.v1
```

### List Available Packs

```bash
python3 -m compliancepack check --list-packs
# Output:
# Available packs:
#   pii.v1
#   secrets.v1
```

### Deterministic Output (for CI/CD)

Use `--fixed-time` for byte-for-byte reproducible output:

```bash
python3 -m compliancepack check \
  --input tests/fixtures/sample_input.txt \
  --pack secrets.v1 \
  --fixed-time "2025-01-01T00:00:00Z"
```

## CLI Contract

### `compliancepack check`

Analyze configuration files for compliance violations.

```bash
python3 -m compliancepack check \
  --input <path>           # Required: path to file (read-only)
  --pack <name>            # Use built-in pack (e.g., secrets.v1, pii.v1)
  --policy <path>          # OR: use custom JSON policy file
  --fixed-time <ISO8601Z>  # Optional: deterministic timestamp
  --redact                 # Optional: redact sensitive values (default: ON)
  --no-redact              # Optional: disable redaction
  --list-packs             # List available packs and exit
```

**Note**: Exactly one of `--pack` or `--policy` is required (mutually exclusive).

**Output**: JSON to stdout with stable formatting (`sort_keys=True`, fixed separators).

## Built-in Packs

| Pack | Description |
|------|-------------|
| `secrets.v1` | AWS keys, private key markers, JWT tokens, Bearer tokens |
| `pii.v1` | Email addresses, phone numbers, SSNs, credit card numbers |

## Advanced: Custom Policy Files

For custom compliance rules, create a JSON policy file:

```bash
python3 -m compliancepack check \
  --input /path/to/config.txt \
  --policy /path/to/custom-policy.json \
  --fixed-time "2025-01-01T00:00:00Z"
```

See `tests/fixtures/policy_v1.json` for the policy schema.

### Output Schema (v1)

```json
{
  "format": "compliancepack.check.v1",
  "generated_at_utc": "2025-01-01T00:00:00Z",
  "input_path": "tests/fixtures/sample_input.txt",
  "policy_path": "pack:secrets.v1",
  "redaction_applied": true,
  "summary": {
    "policy_count": 6,
    "finding_count": 2,
    "severity_counts": { "critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0 }
  },
  "findings": [
    {
      "id": "SEC002",
      "title": "Private Key Block Marker",
      "severity": "critical",
      "description": "Detect private key material markers.",
      "match_count": 1,
      "samples": [{ "line": 7, "col_start": 5, "col_end": 22, "excerpt": "[REDACTED_TOKEN]" }]
    }
  ]
}
```

## Security Constraints (Non-Goals)

CompliancePack enforces strict security boundaries:

| Constraint | Rationale |
|------------|-----------|
| **No outbound networking** | Offline operation; no telemetry or external calls |
| **No shell execution** | No subprocess, os.system, or pty imports |
| **No file writes** | Read-only analysis; stdout-only output |

These constraints are enforced by:
- CI governance validator (`scripts/ci/validate_compliancepack.py`)
- Non-goals test suite (`tests/test_contract_non_goals.py`)

## Development

```bash
# Run tests
cd products/compliancepack
PYTHONPATH=src python3 -m pytest -q

# Run from repo root
cd ~/Developer/ninobyte
PYTHONPATH=products/compliancepack/src python3 -m pytest products/compliancepack -q
```

## License

MIT License - See [LICENSE](../../LICENSE) for details.
