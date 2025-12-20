# Ninobyte OpsPack - Threat Model

**Scope**: Ninobyte OpsPack
**Version**: 0.0.0 (Skeleton)
**Last Updated**: December 2024

## Overview

This document outlines the threat model for OpsPack, a read-only operational intelligence module. The threat model is aligned with Ninobyte AirGap standards and assumes operation under strict security constraints.

## Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| Evidence Packs | Collected operational data (logs, configs, metrics) | High |
| Source Configurations | Allowlisted data source definitions | Medium |
| Audit Logs | Record of all operations | High (forensic value) |
| Redaction Rules | Patterns for sensitive data detection | Medium |

## Attackers

| Attacker | Capability | Goal |
|----------|------------|------|
| Malicious Prompt | Crafted input via AI agent | Access data outside allowed sources |
| Compromised Agent | AI agent with malicious intent | Exfiltrate sensitive operational data |
| Insider Threat | User with legitimate access | Bypass redaction controls |
| Supply Chain | Malicious dependency | Code execution, data theft |

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    UNTRUSTED ZONE                       │
│  ┌─────────────────┐                                    │
│  │  AI Agent       │ ←── Prompt injection attempts      │
│  │  (Orchestrator) │                                    │
│  └────────┬────────┘                                    │
│           │ Request                                     │
├───────────┼─────────────────────────────────────────────┤
│           ▼          TRUST BOUNDARY                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │              OpsPack Module                     │    │
│  │  ┌───────────────┐  ┌───────────────────────┐   │    │
│  │  │ Source        │  │ Redaction Engine      │   │    │
│  │  │ Validation    │  │ (Pattern Matching)    │   │    │
│  │  └───────────────┘  └───────────────────────┘   │    │
│  │  ┌───────────────┐  ┌───────────────────────┐   │    │
│  │  │ Path Security │  │ Audit Logger          │   │    │
│  │  └───────────────┘  └───────────────────────┘   │    │
│  └─────────────────────────────────────────────────┘    │
│           │                                             │
├───────────┼─────────────────────────────────────────────┤
│           ▼          PROTECTED ZONE                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │       Allowed Data Sources (Read-Only)          │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Abuse Cases and Controls

### AC1: Prompt Injection - Source Expansion

**Abuse Case**: Attacker crafts prompt to convince agent to access data sources outside the allowed list.

**Controls**:
- Source allowlist is defined at initialization, not runtime
- All source access validated against allowlist before read
- No dynamic source addition via agent requests

### AC2: Data Exfiltration via Output

**Abuse Case**: Attacker attempts to extract sensitive data through formatted outputs.

**Controls**:
- All outputs pass through redaction engine
- Known sensitive patterns are replaced with `<REDACTED>`
- Redaction metadata logged for audit

### AC3: Path Traversal

**Abuse Case**: Attacker uses `../` sequences to escape allowed source boundaries.

**Controls**:
- Canonical path handling via `os.path.realpath()`
- Path validation checks canonical path against allowed roots
- Traversal sequences detected before canonicalization

### AC4: Supply Chain Manipulation

**Abuse Case**: Malicious dependency injected into OpsPack package.

**Controls**:
- Minimal dependencies (stdlib-only where possible)
- No networking imports allowed in production code
- AST-based import scanning in CI

### AC5: Sensitive Data in Logs

**Abuse Case**: Sensitive data leaks into audit logs, exposing it to log consumers.

**Controls**:
- Audit log redaction of sensitive paths
- No raw data written to logs; only metadata
- Log path can be placed outside accessible roots

## Controls Summary (Ninobyte Standards)

| Control | Implementation |
|---------|----------------|
| Canonical path handling | `os.path.realpath()` before all access |
| Deny-by-default | Explicit allowlist required for all sources |
| Strict redaction policy | Pattern-based redaction before output |
| Structured audit logging | JSONL format with operation metadata |
| No network | Forbidden imports list enforced by CI |
| No shell | AST-based detection of shell=True |

## Residual Risks

| Risk | Severity | Notes |
|------|----------|-------|
| Redaction pattern gaps | Medium | New sensitive patterns may not be covered |
| Time-of-check/time-of-use | Low | Source content may change between validation and read |
| Allowlist misconfiguration | Medium | Overly permissive allowlist reduces security |
| Audit log tampering | Low | Mitigated by log placement outside accessible roots |

## Future Mitigations

1. **Schema validation**: Enforce evidence pack structure before output
2. **Cryptographic audit logs**: Signed log entries for tamper detection
3. **Rate limiting**: Per-session operation budgets
4. **Content scanning**: ML-based sensitive data detection (beyond regex)

## References

- [SECURITY.md](../SECURITY.md) - Security policy
- [INTERFACE_CONTRACT.md](./INTERFACE_CONTRACT.md) - Module contracts
- [AirGap THREAT_MODEL.md](../../mcp-servers/ninobyte-airgap/docs/THREAT_MODEL.md) - Aligned threat model
