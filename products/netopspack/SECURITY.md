# Security Policy

## Overview

NetOpsPack is designed with security as a primary constraint. This document defines the security model, prohibited features, and reporting procedures.

## Threat Model

### Assets Protected

1. **Network log contents**: May contain IPs, tokens, credentials, internal paths
2. **Infrastructure topology**: Log patterns reveal network structure
3. **User privacy**: Logs may contain PII (emails, usernames)

### Threat Actors

| Actor | Motivation | Mitigation |
|-------|------------|------------|
| Malicious log injection | Code execution via log parsing | Strict parsing, no eval/exec |
| Data exfiltration | Steal sensitive log data | No network access |
| Privilege escalation | Gain system access | No shell execution |
| Supply chain attack | Compromise dependencies | Stdlib-only |

### Attack Vectors Mitigated

1. **Log injection attacks**: Parser rejects malformed input
2. **Path traversal**: Input paths validated against escape attempts
3. **Resource exhaustion**: Line limits and file size checks
4. **Regex DoS**: Bounded regex patterns only

## Prohibited Features

The following features are **permanently prohibited** in NetOpsPack:

| Feature | Reason | Enforcement |
|---------|--------|-------------|
| Network imports | No `socket`, `http.client`, `urllib`, `requests` | AST validation |
| Shell execution | No `subprocess`, `os.system`, `os.popen` | AST validation |
| File writes | No `open(..., 'w')`, no temp files | Code review |
| Dynamic execution | No `eval`, `exec`, `compile` | AST validation |
| Pickle/marshal | Deserialization attacks | Import prohibition |
| External dependencies | Supply chain risk | Stdlib-only |

## Security Guarantees

### What We Guarantee

1. **No network egress**: NetOpsPack will never make network connections
2. **No file system writes**: Output goes to stdout only
3. **No shell spawning**: No subprocess or system calls
4. **Deterministic behavior**: Same input produces same output
5. **Redaction by default**: Sensitive patterns are always matched

### What We Do NOT Guarantee

1. **Complete redaction**: Custom patterns may be missed
2. **Parsing accuracy**: Malformed logs may produce errors
3. **Performance**: Large files may be slow

## Sensitive Data Handling

### Redacted Patterns

NetOpsPack redacts the following by default:

| Pattern | Replacement | Example |
|---------|-------------|---------|
| IPv4 addresses | `[REDACTED_IP]` | `192.168.1.1` → `[REDACTED_IP]` |
| IPv6 addresses | `[REDACTED_IP]` | `2001:db8::1` → `[REDACTED_IP]` |
| Bearer tokens | `[REDACTED_TOKEN]` | `Bearer eyJ...` → `Bearer [REDACTED_TOKEN]` |
| API keys | `[REDACTED_KEY]` | `api_key=abc123` → `api_key=[REDACTED_KEY]` |
| Email addresses | `[REDACTED_EMAIL]` | `user@example.com` → `[REDACTED_EMAIL]` |
| AWS keys | `[REDACTED_AWS]` | `AKIA...` → `[REDACTED_AWS]` |
| Long hex strings | `[REDACTED_HEX]` | 32+ char hex → `[REDACTED_HEX]` |

### Disabling Redaction

Use `--no-redact` only when:
- Analyzing synthetic/test data
- Internal debugging with sanitized logs
- Explicit user acknowledgment of risk

## CI/CD Security

### AST Validation

NetOpsPack is validated by `validate_artifacts.py`:

```python
# Forbidden imports (will fail CI)
FORBIDDEN_IMPORTS = [
    'socket', 'http', 'urllib', 'requests',
    'subprocess', 'os.system', 'os.popen',
    'pickle', 'marshal', 'eval', 'exec'
]
```

### Pre-Commit Checks

All commits must pass:
1. AST import validation
2. Shell execution prohibition
3. Test suite (including security tests)

## Vulnerability Reporting

### Reporting Process

1. **Do NOT open a public issue** for security vulnerabilities
2. Email: security@ninobyte.com (or repository owner)
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Severity | Initial Response | Fix Target |
|----------|------------------|------------|
| Critical | 24 hours | 48 hours |
| High | 48 hours | 1 week |
| Medium | 1 week | 2 weeks |
| Low | 2 weeks | Next release |

### Disclosure Policy

- We follow responsible disclosure
- Credit will be given to reporters (unless anonymity requested)
- Public disclosure after fix is released

## Security Changelog

| Version | Change |
|---------|--------|
| 0.9.0 | Initial security policy |

## Contact

For security concerns, contact the repository maintainers directly.
