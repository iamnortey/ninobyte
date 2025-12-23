# Ninobyte OpsPack

**Version**: 0.1.0
**Status**: MVP — `triage` command implemented

---

## What is OpsPack?

OpsPack is a deterministic incident triage and log analysis toolkit. It extracts signals from noisy logs, applies automatic redaction of sensitive data, and produces structured, reproducible JSON reports.

### Core Principles

1. **Determinism**: Same input always produces byte-for-byte identical output
2. **Security by default**: Sensitive data is redacted automatically
3. **Local-only**: No network calls, no external dependencies at runtime
4. **Cross-platform**: Works on Linux, macOS, and Windows

---

## What OpsPack is NOT

OpsPack explicitly excludes the following capabilities:

| Non-Goal | Rationale |
|----------|-----------|
| Network access | No HTTP clients, no API calls, no telemetry |
| Shell execution | No subprocess with shell=True, no os.system() |
| ML/NLP | No machine learning or natural language processing |
| Write operations | Read-only by design (except stdout) |
| Agents | No long-running daemons or background processes |
| Connectors | No real-time integrations with external systems |

These are **hard security guarantees**, enforced by CI and static analysis.

---

## Quick Start

### Installation

```bash
# From repository root
pip install -e products/opspack

# Or run directly without installation
cd products/opspack/src
python -m opspack --help
```

### Usage: triage

The `triage` command analyzes an incident log file and produces a structured JSON report.

```bash
# Basic usage
python -m opspack triage --input incident.log

# Write output to file
python -m opspack triage --input incident.log --output-file report.json
```

#### Input

- Plain text file (UTF-8 or Latin-1)
- Log files, incident notes, stack traces, etc.

#### Output (JSON)

```json
{
  "char_count": 1847,
  "generated_at_utc": "2024-01-15T10:30:00Z",
  "input_path": "incident.log",
  "input_path_type": "repo-relative",
  "line_count": 42,
  "redaction_applied": true,
  "schema_version": "1.0.0",
  "signals": {
    "error_keywords": ["error", "failed", "timeout"],
    "stacktrace_markers": ["File \"app.py\", line..."],
    "timestamps": ["2024-01-15T10:30:00Z"]
  },
  "summary": "Analyzed 42 lines: 3 error keyword(s), 1 timestamp(s)."
}
```

#### Options

| Flag | Description |
|------|-------------|
| `--input`, `-i` | Path to input file (required) |
| `--output`, `-o` | Output format: `json` (default) |
| `--output-file`, `-f` | Write output to file instead of stdout |
| `--no-redact` | Disable automatic redaction (NOT RECOMMENDED) |

---

## Data Handling Guarantees

### Redaction Defaults

By default, OpsPack redacts:

| Pattern | Examples |
|---------|----------|
| AWS Access Keys | `AKIA...` |
| AWS Secret Keys | 40-char base64 strings |
| Slack Tokens | `xoxb-...`, `xoxp-...` |
| Bearer Tokens | `Bearer eyJ...` |
| GitHub Tokens | `ghp_...`, `gho_...` |
| JWT Tokens | `eyJ...` format |
| IP Addresses | IPv4 and IPv6 |
| UUIDs | Standard UUID format |
| Long Hex Strings | 32+ character hashes |
| Email Addresses | `user@domain.tld` |

All redacted content is replaced with `[REDACTED]`.

### Local-Only Guarantee

OpsPack operates entirely locally:

- No HTTP/HTTPS requests
- No DNS lookups
- No socket connections
- No external process spawning

This is verified by static analysis in CI.

### Determinism Guarantee

For reproducible automation:

- JSON keys are always sorted alphabetically
- Signal lists are sorted
- Output formatting is consistent (2-space indent)
- Use `--fixed-time` for timestamp-independent testing

---

## Running Tests

```bash
# From products/opspack directory
cd products/opspack

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_cli_smoke.py -v
python -m pytest tests/test_redaction_tokens.py -v
python -m pytest tests/test_determinism.py -v
python -m pytest tests/test_no_network_shell.py -v
```

---

## Project Structure

```
products/opspack/
├── README.md                 # This file
├── SECURITY.md               # Security policy
├── pyproject.toml            # Package configuration
├── src/
│   └── opspack/
│       ├── __init__.py       # Package init + version
│       ├── __main__.py       # Entry point for python -m
│       ├── cli.py            # CLI argument parsing + commands
│       ├── model.py          # Data structures + schema constants
│       └── redact.py         # Stateless redaction primitives
└── tests/
    ├── test_cli_smoke.py          # CLI functionality tests
    ├── test_redaction_tokens.py   # Token redaction tests
    ├── test_redaction_ip.py       # IP redaction tests
    ├── test_determinism.py        # Output determinism tests
    └── test_no_network_shell.py   # Static security assertions
```

---

## AirGap Alignment

OpsPack follows the same constraints as the Ninobyte AirGap MCP Server:

- **Read-only**: All operations are non-mutating
- **Deny-by-default**: Explicit path specification required
- **Canonical path handling**: Paths are validated and normalized
- **Redaction-first**: Sensitive data is redacted before any output
- **Deterministic**: Same input always produces same output

---

## Roadmap

See [docs/ROADMAP.md](./docs/ROADMAP.md) for the phased implementation plan.

---

## Security

See [SECURITY.md](./SECURITY.md) for security posture and contributor guidelines.

Report security issues per `SECURITY.md` in repository root.

---

## License

MIT License. See repository root for details.
