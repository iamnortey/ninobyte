# Security Policy

## Security Model

CompliancePack is designed with defense-in-depth principles:

### Hard Constraints (Enforced by CI)

1. **No Outbound Networking**
   - Forbidden imports: `socket`, `http`, `urllib`, `requests`, `aiohttp`, `httpx`
   - Rationale: Compliance checking must work offline and never phone home

2. **No Shell Execution**
   - Forbidden: `subprocess`, `os.system()`, `os.popen()`, `pty`
   - Rationale: Prevent command injection and privilege escalation

3. **No File Writes**
   - Forbidden: `open(..., 'w')`, `Path.write_text()`, `mkdir()`
   - Rationale: Read-only analysis protects source files from corruption

### Enforcement

These constraints are validated by:
- `scripts/ci/validate_compliancepack.py` - AST-based static analysis
- `tests/test_contract_non_goals.py` - Runtime verification
- CI pipeline hard gates - PRs fail on violations

## Reporting Vulnerabilities

If you discover a security vulnerability, please email security@ninobyte.com
with a description of the issue, steps to reproduce, and any relevant logs.

Do NOT open public issues for security vulnerabilities.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.10.x  | Yes       |
