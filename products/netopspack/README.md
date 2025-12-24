# NetOpsPack

Network operations toolkit for SRE/DevOps incident triage and log analysis.

## What NetOpsPack Is

NetOpsPack is a **deterministic, offline-first** network log analysis toolkit designed for:

- **Incident Triage**: Parse and normalize network logs from multiple sources
- **Sensitive Data Redaction**: Automatically redact IPs, tokens, and credentials
- **Structured Output**: JSON output with sorted keys for reproducible results
- **CI/CD Integration**: Deterministic output enables diff-based testing

## What NetOpsPack is NOT

| Non-Goal | Reason |
|----------|--------|
| Network monitoring agent | We parse logs, not capture packets |
| Real-time alerting system | Batch processing only |
| Log aggregation platform | Single-file analysis, not storage |
| Cloud-connected service | 100% offline, no network calls |
| Configuration management | Read-only analysis |
| Packet capture/inspection | Log-level analysis only |

## Environment Setup

> **Warning**: On macOS and some Linux distributions, `python` may point to
> Anaconda, system Python 2.x, or other non-standard installations. Always
> use `python3` explicitly to ensure consistent behavior.

### Canonical Invocation (From Repo Root)

The recommended way to run NetOpsPack from the repository root:

```bash
# From repo root (ninobyte/)
PYTHONPATH=products/netopspack/src python3 -m netopspack diagnose \
  --format syslog \
  --input products/netopspack/tests/fixtures/syslog.log \
  --fixed-time "2025-01-01T00:00:00Z" \
  --limit 3
```

This method:
- Works from anywhere in the repo
- Requires no `pip install`
- Uses explicit `python3` for portability
- Uses full repo-relative paths for fixtures

### Product-Local Invocation

When working within the NetOpsPack directory:

```bash
cd products/netopspack
PYTHONPATH=src python3 -m netopspack diagnose \
  --input tests/fixtures/syslog.log \
  --format syslog
```

### Quick Import Check

Verify NetOpsPack is importable without installation:

```bash
# From repo root
PYTHONPATH=products/netopspack/src python3 -c "import netopspack; print(netopspack.__version__)"
# Output: 0.9.0
```

### Optional: Development Install

For frequent use, install in editable mode:

```bash
cd products/netopspack
python3 -m pip install -e .

# Then run without PYTHONPATH:
python3 -m netopspack diagnose --input tests/fixtures/syslog.log --format syslog
```

## Commands

### `diagnose`

Analyze network logs and produce structured diagnostic output.

```bash
# Recommended: explicit PYTHONPATH
cd products/netopspack
PYTHONPATH=src python3 -m netopspack diagnose --input access.log --format nginx
PYTHONPATH=src python3 -m netopspack diagnose --input /var/log/syslog --format syslog
PYTHONPATH=src python3 -m netopspack diagnose --input haproxy.log --format haproxy --fixed-time 2025-01-01T00:00:00Z
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Path to log file (required) | — |
| `--format` | Log format: `syslog`, `nginx`, `haproxy` | `syslog` |
| `--fixed-time` | Fixed UTC timestamp for deterministic output | Current time |
| `--output` | Output format: `json` | `json` |
| `--redact` | Apply redaction to sensitive data | Enabled |
| `--no-redact` | Disable redaction | — |

## Output Contract

All output is **canonical JSON** with the following guarantees:

1. **Sorted keys**: All object keys are sorted alphabetically
2. **Deterministic timestamps**: Use `--fixed-time` for reproducible output
3. **Stable ordering**: Array elements maintain insertion order
4. **UTF-8 encoding**: All output is UTF-8 encoded

### Schema (v1.0.0)

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2025-01-01T00:00:00Z",
  "input_file": "access.log",
  "input_format": "nginx",
  "redaction_applied": true,
  "summary": {
    "total_lines": 1000,
    "parsed_lines": 985,
    "error_lines": 15,
    "unique_ips": 42,
    "unique_paths": 128
  },
  "diagnostics": [
    {
      "category": "error_rate",
      "severity": "warning",
      "message": "5xx error rate: 2.3%",
      "details": {
        "count": 23,
        "percentage": 2.3
      }
    }
  ],
  "redaction_summary": {
    "ips_redacted": 42,
    "tokens_redacted": 3,
    "emails_redacted": 0
  }
}
```

## Security Posture

NetOpsPack enforces strict security constraints:

| Constraint | Enforcement |
|------------|-------------|
| No network access | AST-verified: no `socket`, `http`, `urllib` imports |
| No shell execution | AST-verified: no `subprocess`, `os.system` |
| No file writes | Stdout-only output |
| Redaction by default | Sensitive data patterns always matched |

See [SECURITY.md](SECURITY.md) for full security policy.

## Determinism

NetOpsPack guarantees **byte-for-byte reproducible output** when:

1. Same input file
2. Same `--format` flag
3. Same `--fixed-time` value
4. Same `--redact`/`--no-redact` setting

This enables:
- Golden file testing in CI
- Diff-based regression detection
- Reproducible incident reports

## Examples

### Basic Usage

```bash
cd products/netopspack

# Analyze nginx access log
PYTHONPATH=src python3 -m netopspack diagnose --input /var/log/nginx/access.log --format nginx

# Analyze syslog with fixed time for testing
PYTHONPATH=src python3 -m netopspack diagnose --input /var/log/syslog --format syslog --fixed-time 2025-01-01T00:00:00Z

# Disable redaction for internal debugging
PYTHONPATH=src python3 -m netopspack diagnose --input debug.log --format syslog --no-redact
```

### CI Integration

```yaml
# .github/workflows/log-analysis.yml
- name: Analyze production logs
  run: |
    cd products/netopspack
    PYTHONPATH=src python3 -m netopspack diagnose \
      --input logs/access.log \
      --format nginx \
      --fixed-time 2025-01-01T00:00:00Z \
      > analysis.json
    diff analysis.json expected/analysis.json
```

## Supported Log Formats

| Format | Parser | Status |
|--------|--------|--------|
| syslog | RFC 3164 | ✅ Implemented |
| nginx | Combined log format | ✅ Implemented |
| haproxy | HTTP log format | ✅ Implemented |

## License

MIT License - see repository root LICENSE file.
