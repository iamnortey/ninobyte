# Ninobyte OpsPack

**Version**: 0.1.0
**Status**: MVP - `incident-triage` command implemented

## What is OpsPack?

Ninobyte OpsPack is a read-only operational intelligence module designed to collect, validate, and package evidence from infrastructure and application systems. It operates under strict security constraints aligned with the AirGap philosophy: no network calls, no shell execution, no filesystem writes, and deny-by-default access controls.

## Quick Start

### Installation

OpsPack is a standard Python package. From the repository root:

```bash
# Run directly with Python
python -m ninobyte_opspack --help

# Or from the products/opspack directory
cd products/opspack
PYTHONPATH=src python -m ninobyte_opspack --help
```

### Usage: incident-triage

The `incident-triage` command analyzes an incident snapshot and produces a deterministic triage summary.

```bash
# Basic usage
python -m ninobyte_opspack incident-triage --input incident.json

# With explicit JSON format
python -m ninobyte_opspack incident-triage --input incident.json --format json
```

#### Input Format

The input is a JSON file describing an incident snapshot:

```json
{
  "id": "INC-2024-001",
  "title": "Database connection timeout",
  "description": "Users experiencing slow response times...",
  "severity": "high",
  "category": "availability",
  "timestamp": "2024-12-21T14:30:00Z",
  "source": "monitoring_alert",
  "affected_services": ["api", "web"],
  "users_affected": 500,
  "reporter": "automated",
  "tags": ["database", "timeout"]
}
```

#### Output Format

The command produces a JSON triage summary:

```json
{
  "protocol_version": "0.1",
  "incident": {
    "id": "INC-2024-001",
    "title": "Database connection timeout",
    "timestamp": "2024-12-21T14:30:00Z",
    "source": "monitoring_alert"
  },
  "classification": {
    "severity": "high",
    "category": "availability"
  },
  "recommended_actions": [
    {
      "priority": 1,
      "action": "Check service health dashboards",
      "rationale": "Confirm scope of outage"
    }
  ],
  "risk_flags": [
    {
      "flag": "HIGH_USER_IMPACT",
      "reason": "Affects 500 users",
      "action": "Prepare customer communication"
    }
  ],
  "evidence": {
    "source_fields_present": ["id", "title", "..."],
    "source_fields_missing": [],
    "extracted_data": {}
  }
}
```

### Security Posture

- **Read-only**: No filesystem writes (except stdout)
- **No network**: No HTTP clients or API calls
- **No shell**: No subprocess or shell execution
- **Deterministic**: Same input always produces same output

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
