# Ninobyte OpsPack

**Version**: 0.0.0 (Skeleton)
**Status**: Governance docs only; no implementation

## What is OpsPack?

Ninobyte OpsPack is a read-only operational intelligence module designed to collect, validate, and package evidence from infrastructure and application systems. It operates under strict security constraints aligned with the AirGap philosophy: no network calls, no shell execution, no filesystem writes, and deny-by-default access controls.

## What OpsPack is NOT

OpsPack explicitly excludes the following capabilities:

| Non-Goal | Rationale |
|----------|-----------|
| Agents | No long-running daemons or background processes |
| Connectors | No real-time integrations with external systems |
| Automation | No automated remediation or state-changing actions |
| Write operations | Read-only by design; no filesystem or database writes |
| Network access | No HTTP clients, no API calls, no telemetry upload |
| Shell execution | No subprocess with shell=True, no os.system() |

## AirGap Alignment

OpsPack is designed to run under the same constraints as the Ninobyte AirGap MCP Server:

- **Read-only**: All operations are non-mutating
- **Deny-by-default**: Paths and data sources require explicit allowlisting
- **Canonical path handling**: All paths are validated and canonicalized
- **Redaction-first**: Sensitive data is redacted before any output
- **Audit logging**: All operations are logged for forensic review

## How It Will Be Used (Future Phases)

In future phases, OpsPack will provide:

1. **Evidence Packs**: Structured collections of operational data (logs, configs, metrics) packaged for review
2. **Validation Gates**: Schema-based validation of evidence pack contents
3. **Reporting Outputs**: Human-readable and machine-parseable summaries

All features will remain read-only and require explicit consent for data access.

## Roadmap

See [docs/ROADMAP.md](./docs/ROADMAP.md) for the phased implementation plan.

## Security

See [SECURITY.md](./SECURITY.md) for security posture and contributor guidelines.

## References

- [THREAT_MODEL.md](./docs/THREAT_MODEL.md) - Security threat analysis
- [INTERFACE_CONTRACT.md](./docs/INTERFACE_CONTRACT.md) - Future module contracts
