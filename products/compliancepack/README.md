# Ninobyte CompliancePack

**Contract-first compliance evidence toolkit for audit-ready operations.**

CompliancePack provides deterministic, read-only compliance checking that produces
machine-readable evidence suitable for auditors and automated pipelines.

## Canonical Invocation (Repo-Root)

**Always use `python3` (not `python`)** - macOS/Linux alias `python` inconsistently.

```bash
# From repo root (canonical)
cd ~/Developer/ninobyte
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input products/compliancepack/tests/fixtures/sample_input.txt \
  --pack secrets.v1 \
  --fail-on high \
  --fixed-time "2025-01-01T00:00:00Z"
```

**Do NOT use `pip install -e .`** - repo-root invocation with `PYTHONPATH` is the
supported contract. Editable installs are not tested and may drift from CI behavior.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No findings at/above threshold (or `--exit-zero`) |
| 1 | Unexpected runtime error |
| 2 | CLI usage/config error |
| 3 | Findings at/above threshold exist (policy violation) |

### Quick Examples

```bash
# List available packs
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check --list-packs

# Check with severity threshold (CI mode)
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input path/to/config.txt \
  --pack secrets.v1 \
  --fail-on high

# SARIF-lite output for code review tools
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input path/to/config.txt \
  --pack secrets.v1 \
  --format compliancepack.sariflite.v1

# Force exit 0 for local development
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input path/to/config.txt \
  --pack secrets.v1 \
  --exit-zero
```

### Deterministic Output (for CI/CD)

Use `--fixed-time` for byte-for-byte reproducible output:

```bash
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input products/compliancepack/tests/fixtures/sample_input.txt \
  --pack secrets.v1 \
  --fixed-time "2025-01-01T00:00:00Z"
```

## CLI Contract

### `compliancepack check`

Analyze configuration files for compliance violations.

```bash
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check \
  --input <path>           # Required: path to file (read-only)
  --pack <name>            # Use built-in pack (e.g., secrets.v1, pii.v1)
  --policy <path>          # OR: use custom JSON policy file
  --fixed-time <ISO8601Z>  # Optional: deterministic timestamp
  --redact                 # Optional: redact sensitive values (default: ON)
  --no-redact              # Optional: disable redaction
  --fail-on <severity>     # Threshold for exit code 3 (default: high)
  --format <format>        # Output format (default: compliancepack.check.v1)
  --max-findings <N>       # Limit output findings (0 = unlimited)
  --exit-zero              # Force exit code 0 regardless of findings
  --list-packs             # List available packs and exit
```

**Note**: Exactly one of `--pack` or `--policy` is required (mutually exclusive).

**Output**: JSON to stdout with stable formatting (`sort_keys=True`, fixed separators).

**Formats**:
- `compliancepack.check.v1` - Full compliance report (default)
- `compliancepack.sariflite.v1` - SARIF-adjacent format for code review tools

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
  "exit_code_expected": 3,
  "format": "compliancepack.check.v1",
  "generated_at_utc": "2025-01-01T00:00:00Z",
  "input_path": "tests/fixtures/sample_input.txt",
  "max_findings": null,
  "policy_path": "pack:secrets.v1",
  "redaction_applied": true,
  "summary": {
    "policy_count": 6,
    "finding_count": 2,
    "severity_counts": { "critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0 }
  },
  "threshold": {
    "fail_on": "high",
    "violations": 2
  },
  "truncated": false,
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
# Run tests (from repo root - canonical)
cd ~/Developer/ninobyte
PYTHONPATH=products/compliancepack/src python3 -m pytest products/compliancepack -q

# Run specific test file
PYTHONPATH=products/compliancepack/src python3 -m pytest \
  products/compliancepack/tests/test_determinism.py -v
```

**Note**: Always run from repo root with `PYTHONPATH` prefix. Do not use `pip install -e .`.

## License

MIT License - See [LICENSE](../../LICENSE) for details.
