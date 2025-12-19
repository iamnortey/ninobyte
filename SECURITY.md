# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it privately:

1. **Do NOT** open a public issue
2. Email: security@ninobyte.io (or create a private security advisory on GitHub)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

We aim to acknowledge reports within 48 hours and provide a resolution timeline within 7 days.

## Security Posture

### Secrets Management

- **No secrets are committed** to this repository
- All sensitive values must use environment variables or external secret stores
- `.gitignore` includes common secret file patterns

### Data Handling

- Products in this repo (Skills, MCP servers, plugins) process user prompts and code
- **Safe logging**: Never log raw user content, secrets, or PII
- **Redaction**: Any logging must redact sensitive patterns before output
- **Least privilege**: Tools request only minimum necessary permissions

### Threat Model

See [docs/architecture/THREAT_MODEL.md](docs/architecture/THREAT_MODEL.md) for:
- Identified threats (prompt injection, tool abuse, exfiltration)
- Mitigations in place
- Assumptions and out-of-scope items

### Supply Chain

- Minimize dependencies
- Pin versions where possible
- Audit dependencies before adoption
- Prefer well-maintained, security-audited libraries

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Checklist for Contributors

Before submitting:
- [ ] No secrets or credentials in code or comments
- [ ] No logging of raw user input or sensitive data
- [ ] Dependencies are necessary and audited
- [ ] Tool permissions follow least-privilege principle
- [ ] Error messages don't leak internal paths or system info

## Out of Scope

- Vulnerabilities in third-party dependencies (report upstream)
- Theoretical attacks without proof of concept
- Social engineering attacks
