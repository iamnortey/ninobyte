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

## Installation

```bash
# From repository root
cd products/netopspack
pip install -e .
```

## Commands

### `diagnose`

Analyze network logs and produce structured diagnostic output.

```bash
python -m netopspack diagnose --input access.log --format nginx
python -m netopspack diagnose --input /var/log/syslog --format syslog
python -m netopspack diagnose --input haproxy.log --format haproxy --fixed-time 2025-01-01T00:00:00Z
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
# Analyze nginx access log
python -m netopspack diagnose --input /var/log/nginx/access.log --format nginx

# Analyze syslog with fixed time for testing
python -m netopspack diagnose --input /var/log/syslog --format syslog --fixed-time 2025-01-01T00:00:00Z

# Disable redaction for internal debugging
python -m netopspack diagnose --input debug.log --format syslog --no-redact
```

### CI Integration

```yaml
# .github/workflows/log-analysis.yml
- name: Analyze production logs
  run: |
    python -m netopspack diagnose \
      --input logs/access.log \
      --format nginx \
      --fixed-time 2025-01-01T00:00:00Z \
      > analysis.json
    diff analysis.json expected/analysis.json
```

## Supported Log Formats

| Format | Parser | Status |
|--------|--------|--------|
| syslog | RFC 3164 / RFC 5424 | Planned |
| nginx | Combined log format | Planned |
| haproxy | HTTP log format | Planned |

## License

MIT License - see repository root LICENSE file.
