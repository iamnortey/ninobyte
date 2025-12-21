# Ninobyte AirGap MCP Server - Threat Model

**Scope**: Ninobyte AirGap MCP Server
**Version**: 0.2.x
**Last Updated**: December 2024

## Overview

The AirGap MCP Server provides filesystem access to AI agents with strict security constraints. This document outlines the threat model, trust boundaries, and mitigations.

## Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| Allowed Roots | Directories the server can access | Configuration |
| File Contents | Data read from filesystem | Variable (may contain secrets) |
| Audit Logs | Record of all operations | High (forensic value) |
| Blocked Patterns | Sensitive file patterns to deny | Configuration |

## Attackers

| Attacker | Capability | Goal |
|----------|------------|------|
| Malicious Prompt | Crafted input via AI agent | Access files outside allowed roots |
| Compromised Agent | AI agent with malicious intent | Exfiltrate sensitive data |
| Insider Threat | User with legitimate access | Bypass security controls |

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    UNTRUSTED ZONE                       │
│  ┌─────────────┐                                        │
│  │  AI Agent   │ ←── Prompt injection attempts          │
│  │  (Claude)   │                                        │
│  └──────┬──────┘                                        │
│         │ MCP Protocol                                  │
├─────────┼───────────────────────────────────────────────┤
│         ▼          TRUST BOUNDARY                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │           AirGap MCP Server                     │    │
│  │  ┌───────────────┐  ┌───────────────────────┐   │    │
│  │  │ Path Security │  │ Blocked Pattern Check │   │    │
│  │  │ (Canonical)   │  │ (.env, keys, etc.)    │   │    │
│  │  └───────────────┘  └───────────────────────────┘    │
│  │  ┌───────────────┐  ┌───────────────────────┐   │    │
│  │  │ Audit Logger  │  │ Redact Preview        │   │    │
│  │  └───────────────┘  └───────────────────────┘   │    │
│  └──────────────────────────────────────────────────┘    │
│         │                                               │
├─────────┼───────────────────────────────────────────────┤
│         ▼          PROTECTED ZONE                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Filesystem (Allowed Roots Only)       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Key Threats and Mitigations

### T1: Path Traversal Attack

**Threat**: Attacker uses `../` sequences to escape allowed roots.

**Mitigations**:
- All paths are canonicalized via `os.path.realpath()` before access
- Explicit check that canonical path starts with allowed root + separator
- Traversal sequences detected and rejected before canonicalization

### T2: Symlink Escape

**Threat**: Attacker creates symlink pointing outside allowed roots.

**Mitigations**:
- Symlink targets are resolved and validated against allowed roots
- `SYMLINK_ESCAPE` denial reason for symlinks pointing outside boundaries
- Option to validate without following symlinks for directory listings

### T3: Sensitive File Access

**Threat**: Attacker reads credential files, keys, or secrets.

**Mitigations**:
- Blocked pattern list denies access to sensitive files:
  - Environment files (`.env`, `.env.*`)
  - Key files (`*.pem`, `*.key`, `id_rsa`, etc.)
  - Credential stores (`.aws/credentials`, `.git/config`, etc.)
- Pattern matching on both basename and full path
- Cross-platform: Windows backslash paths normalized for pattern matching

### T4: Prompt Injection Bypass

**Threat**: Crafted prompts attempt to convince agent to bypass constraints.

**Mitigations**:
- All security checks are in server code, not prompt-dependent
- Deny-by-default: paths must explicitly pass validation
- No dynamic allowlisting based on agent requests

### T5: Resource Exhaustion

**Threat**: Attacker triggers expensive operations (large files, deep searches).

**Mitigations**:
- `max_file_size_bytes`: Limit on individual file reads
- `max_response_bytes`: Limit on total response size
- `max_results`: Limit on search/list results
- `timeout_seconds`: Operation timeout enforcement
- `max_files_scanned`: Budget for search operations

### T6: Audit Log Tampering

**Threat**: Attacker modifies or deletes audit logs to hide activity.

**Mitigations**:
- Audit log path configurable (can be outside allowed roots)
- JSONL append-only format
- Path redaction option to protect sensitive paths in logs

## Non-Goals (Explicit Exclusions)

The AirGap server explicitly does NOT:

| Capability | Reason |
|------------|--------|
| Write files | Read-only by design |
| Network access | No networking imports allowed |
| Execute commands | No shell execution |
| Modify system state | Stateless operations only |

## Residual Risks

| Risk | Severity | Notes |
|------|----------|-------|
| Time-of-check/time-of-use | Low | File content may change between validation and read |
| Blocked pattern coverage | Medium | New sensitive file types may not be covered |
| Symbolic link races | Low | Mitigated by canonical path validation |

## Future Hardening

1. **Content scanning**: Detect secrets in file content before returning
2. **Rate limiting**: Per-session operation limits
3. **Cryptographic audit logs**: Signed/hashed log entries
4. **Allowlist mode**: Explicit file allowlisting instead of root-based

## References

- [SECURITY.md](../SECURITY.md) - Security policy and reporting
- [ROOTS_CONTRACT.md](./ROOTS_CONTRACT.md) - Allowed roots configuration
- [AUDIT_LOG_SPEC.md](./AUDIT_LOG_SPEC.md) - Audit log format specification
