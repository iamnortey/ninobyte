# Ninobyte OpsPack - Security Policy

**Version**: 0.0.0 (Skeleton)
**Last Updated**: December 2024

## Security Posture Summary

OpsPack is designed with a security-first architecture:

| Constraint | Enforcement |
|------------|-------------|
| Read-only | No write operations to filesystem, database, or external systems |
| Deny-by-default | All data sources require explicit allowlisting |
| No network | No HTTP clients, no API calls, no telemetry |
| No shell | No subprocess with shell=True, no os.system(), no os.popen() |
| Canonical paths | All paths validated via os.path.realpath() before access |
| Redaction-first | Sensitive data patterns are redacted before output |

## Data Classification

All operational data handled by OpsPack is treated as **sensitive by default**:

- Infrastructure configurations may contain credentials or secrets
- Application logs may contain PII or session tokens
- System metrics may reveal security posture details

### Handling Requirements

1. **No persistence**: OpsPack does not store data beyond the current session
2. **No transmission**: OpsPack does not send data to external systems
3. **Redaction**: Known sensitive patterns are automatically redacted
4. **Audit trail**: All data access is logged for forensic review

## Auditability

OpsPack maintains a structured audit log of all operations:

- **Format**: JSON Lines (JSONL), append-only
- **Fields**: timestamp, operation, source, result, redaction metadata
- **Retention**: Caller-managed; OpsPack does not delete logs
- **Integrity**: Future phases may add cryptographic signing

## Contributor Guidelines

### Markdown Hygiene Policy

All documentation in this product must comply with the repository's markdown secret-scan hygiene policy:

- Do **not** include literal credential patterns (e.g., key markers, credential assignments)
- Do **not** embed cloud secret variable names in raw form
- Use placeholders like `<SENSITIVE_VALUE>` or `<REDACTED>` when examples are needed
- For technical patterns, use composed strings: describe the pattern rather than showing it

### Code Hygiene

When implementation begins:

- No hardcoded credentials or secrets
- No test fixtures containing real-looking credentials
- Use composed strings in tests (e.g., `"pass" + "word="`)
- All imports must be reviewed against the forbidden networking list

## Reporting Security Issues

For security vulnerabilities, please follow the process in the root [SECURITY.md](../../SECURITY.md) or contact the maintainers directly.

## References

- [THREAT_MODEL.md](./docs/THREAT_MODEL.md) - Detailed threat analysis
- [AirGap SECURITY.md](../mcp-servers/ninobyte-airgap/SECURITY.md) - Aligned security policy
