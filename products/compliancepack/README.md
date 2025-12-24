# Ninobyte CompliancePack

**Contract-first compliance evidence toolkit for audit-ready operations.**

CompliancePack provides deterministic, read-only compliance checking that produces
machine-readable evidence suitable for auditors and automated pipelines.

## Quick Start

```bash
# From repo root
PYTHONPATH=products/compliancepack/src python3 -m compliancepack check --help

# From product directory
cd products/compliancepack
PYTHONPATH=src python3 -m compliancepack check --input /path/to/config.json
```

## CLI Contract

### `compliancepack check`

Analyze configuration files for compliance violations.

```bash
python3 -m compliancepack check \
  --input <path>           # Required: path to file (read-only)
  --fixed-time <ISO8601Z>  # Optional: deterministic timestamp
  --redact                 # Optional: redact sensitive values (default: ON)
  --no-redact              # Optional: disable redaction
```

**Output**: JSON to stdout with stable formatting (`sort_keys=True`, fixed separators).

### Output Schema (v1)

```json
{
  "format": "compliance-check",
  "version": "1.0.0",
  "generated_at_utc": "2025-01-01T00:00:00Z",
  "input_file": "/path/to/config.json",
  "violations": [],
  "summary": {
    "total_checks": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0
  }
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
