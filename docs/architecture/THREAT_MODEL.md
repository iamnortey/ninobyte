# Threat Model

Baseline security threat model for Ninobyte products.

**Version**: 0.1
**Last Updated**: 2025-12-19

---

## Scope

This threat model covers:
- Skill packs executed in Claude Projects and Claude Code
- Future MCP servers
- Future Claude Code plugins
- Repository and distribution infrastructure

---

## Assets to Protect

| Asset | Sensitivity | Notes |
|-------|-------------|-------|
| User prompts/data | HIGH | Processed by skills/tools |
| User code | HIGH | May contain secrets, IP |
| Repository secrets | CRITICAL | API keys, tokens, credentials |
| Skill/tool source code | MEDIUM | IP, but open source |
| Execution logs | MEDIUM | May contain sensitive patterns |

---

## Threat Categories

### T1: Prompt Injection

**Description**: Malicious input in user prompts or processed data that manipulates skill/tool behavior.

**Attack Vectors**:
- Direct injection in user input
- Indirect injection via processed files/data
- Injection in tool outputs fed back to model

**Impact**: Unauthorized actions, data exfiltration, bypassed safety controls

**Mitigations**:
- Skills define strict scope boundaries and refuse out-of-scope requests
- Output format enforcement limits freeform responses
- Evidence discipline requires citing sources for all claims
- Document what skills explicitly refuse to do

### T2: Tool Abuse

**Description**: Misuse of tool capabilities beyond intended scope.

**Attack Vectors**:
- Requesting tools perform unauthorized file operations
- Chaining tools to achieve escalated capabilities
- Using tools to access resources outside intended scope

**Impact**: Data access/modification, system compromise

**Mitigations**:
- Least privilege principle in tool design
- Explicit scope boundaries in SKILL.md
- Tool capabilities documented with limits
- MCP servers define minimal required permissions

### T3: Data Exfiltration

**Description**: Sensitive data extracted from user context or system.

**Attack Vectors**:
- Skill outputs containing sensitive data
- Tool outputs logged or transmitted unsafely
- Secrets in prompts/responses

**Impact**: Data breach, credential exposure

**Mitigations**:
- Safe logging patterns (never log raw user content)
- Redaction utilities for sensitive patterns
- Skills refuse to output credentials/secrets
- No external network calls from skills (execution is local to Claude)

### T4: Secrets Exposure

**Description**: Credentials, API keys, or tokens exposed in repository or logs.

**Attack Vectors**:
- Secrets committed to git
- Secrets in error messages or logs
- Secrets in example files

**Impact**: Credential compromise, unauthorized access

**Mitigations**:
- Strong `.gitignore` patterns
- Pre-commit hooks (recommended)
- Security scanning in CI
- Example files use placeholder values only
- SECURITY.md checklist for contributors

### T5: Unsafe Logging

**Description**: Logging practices that expose sensitive information.

**Attack Vectors**:
- Logging raw user prompts
- Logging full tool outputs
- Logging error details with sensitive context

**Impact**: Data exposure, compliance violations

**Mitigations**:
- Never log raw user content
- Redact before logging
- Structured logging with explicit allow-lists
- Document safe logging patterns in SECURITY.md

### T6: Supply Chain

**Description**: Compromised dependencies or tooling.

**Attack Vectors**:
- Malicious npm/pip packages
- Compromised CI/CD actions
- Typosquatting attacks

**Impact**: Code execution, backdoors, data theft

**Mitigations**:
- Minimize dependencies
- Pin dependency versions
- Audit new dependencies before adoption
- Use official/well-maintained packages only
- Verify GitHub Action sources

---

## Assumptions

1. Claude's underlying safety systems are functioning correctly
2. User's local environment (Claude Code) is not compromised
3. Claude Projects web interface is secure
4. Users follow documented installation procedures
5. Official Anthropic infrastructure is trustworthy

---

## Out of Scope

1. Attacks on Anthropic's infrastructure
2. Physical access attacks
3. Social engineering of end users (outside our control)
4. Vulnerabilities in Claude model itself
5. Network-level attacks on user's systems
6. Attacks requiring compromised user credentials

---

## Security Controls Summary

| Control | Implementation | Status |
|---------|---------------|--------|
| No secrets in repo | `.gitignore`, contributor checklist | ✅ Active |
| Safe logging | Documentation, patterns | ✅ Documented |
| Scope boundaries | `SKILL.md` contracts | ✅ Active |
| Least privilege | Tool design guidelines | ✅ Documented |
| Dependency audit | Manual review | ⚠️ Manual |
| Security scanning | CI integration | 🔜 Planned |

---

## Incident Response

1. Security issues: Follow `SECURITY.md` reporting process
2. Suspected compromise: Rotate any potentially exposed credentials
3. Vulnerability disclosure: Coordinate responsible disclosure timeline
4. Post-incident: Update threat model with lessons learned

---

## Review Schedule

- Quarterly review of threat model
- Review after any security incident
- Review when adding new product categories (MCP servers, plugins)
