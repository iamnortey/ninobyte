# Ninobyte OpsPack - Interface Contract

**Version**: 0.1.0
**Status**: MVP implemented (`incident-triage` command)
**Last Updated**: December 2024

## Overview

This document defines the contracts for OpsPack modules and CLI commands.

## Contract Principles

All OpsPack interfaces adhere to:

1. **Read-only**: No mutations to any data source
2. **Explicit consent**: Each data source requires explicit configuration
3. **Redaction-first**: All outputs pass through redaction before return
4. **Auditability**: All operations are logged with structured metadata
5. **Determinism**: Same input always produces same output

---

## CLI Commands

### incident-triage

**Purpose**: Analyze an incident snapshot and produce a deterministic triage summary with classification, recommended actions, and risk flags.

**CLI Interface**:
```
ninobyte-opspack incident-triage --input <path-to-json> [--format json]
python -m ninobyte_opspack incident-triage --input <path-to-json> [--format json]
```

**Input Contract** (JSON file):
```json
{
  "id": "string (required)",
  "title": "string (required)",
  "description": "string (optional)",
  "severity": "string (optional): critical|high|medium|low",
  "category": "string (optional): security|availability|performance|data_integrity|configuration",
  "type": "string (optional)",
  "timestamp": "string (optional, ISO 8601)",
  "source": "string (optional)",
  "affected_services": ["array of strings (optional)"],
  "users_affected": "integer (optional)",
  "reporter": "string (optional)",
  "tags": ["array of strings (optional)"]
}
```

**Output Contract** (JSON to stdout):
```json
{
  "version": "1.0.0",
  "opspack_version": "string",
  "incident": {
    "id": "string",
    "title": "string",
    "timestamp": "string or null",
    "source": "string or null"
  },
  "classification": {
    "severity": "critical|high|medium|low",
    "category": "security|availability|performance|data_integrity|configuration|unknown"
  },
  "recommended_actions": [
    {
      "priority": "integer (1-N)",
      "action": "string",
      "rationale": "string"
    }
  ],
  "risk_flags": [
    {
      "flag": "string (e.g., SECURITY_INCIDENT, CRITICAL_SEVERITY)",
      "reason": "string",
      "action": "string"
    }
  ],
  "evidence": {
    "source_fields_present": ["array of field names"],
    "source_fields_missing": ["array of field names"],
    "extracted_data": {}
  }
}
```

**Guarantees**:
- Pure function: no side effects beyond stdout
- Deterministic: same input always produces same output
- No network calls
- No shell execution
- No filesystem writes

**Exit Codes**:
- 0: Success
- 1: Error (file not found, invalid JSON, permission error)

**Implementation Status**: Implemented (v0.1.0)

---

## Module Contracts

### SourceValidator

**Purpose**: Validate that a data source is allowed before access.

**Contract**:
```
Input:
  - source_path: str (absolute path to data source)
  - allowed_sources: List[str] (configured allowlist)

Output:
  - ValidationResult:
      - allowed: bool
      - canonical_path: Optional[str]
      - denial_reason: Optional[str]

Guarantees:
  - Path is canonicalized before validation
  - Returns False for any path outside allowed_sources
  - No side effects; pure validation only
```

**Implementation Status**: Deferred

---

### EvidenceCollector

**Purpose**: Collect evidence from an allowed data source.

**Contract**:
```
Input:
  - source_path: str (validated, canonical path)
  - collection_type: str (e.g., "metadata", "content_redacted")
  - options: CollectionOptions (limits, filters)

Output:
  - EvidenceResult:
      - data: dict (collected evidence)
      - redactions_applied: int
      - source_metadata: dict

Guarantees:
  - Source must be pre-validated; raises if not
  - All content passes through redaction engine
  - Collection respects configured limits (size, count)
  - No filesystem writes
```

**Implementation Status**: Deferred

---

### RedactionEngine

**Purpose**: Remove sensitive patterns from data before output.

**Contract**:
```
Input:
  - content: str (raw content to redact)
  - patterns: List[RedactionPattern] (configured patterns)

Output:
  - RedactionResult:
      - content: str (redacted content)
      - redactions_applied: int
      - redaction_types: List[str]

Guarantees:
  - Pure function (no side effects)
  - Deterministic (same input = same output)
  - Patterns are applied in priority order
  - Original content is never stored or logged
```

**Implementation Status**: Deferred (may reuse AirGap redact_preview)

---

### EvidencePackager

**Purpose**: Package collected evidence into a structured format.

**Contract**:
```
Input:
  - evidence_items: List[EvidenceResult]
  - pack_metadata: PackMetadata (timestamp, session, config)

Output:
  - EvidencePack:
      - schema_version: str
      - created_at: str (ISO 8601)
      - items: List[dict]
      - metadata: dict

Guarantees:
  - Output conforms to evidence pack schema
  - All items have passed redaction
  - No sensitive data in pack metadata
  - Pack is serializable to JSON
```

**Implementation Status**: Deferred

---

### AuditLogger

**Purpose**: Log all operations for forensic review.

**Contract**:
```
Input:
  - operation: str (operation type)
  - source: Optional[str] (data source, may be redacted)
  - result: str (success/failure)
  - metadata: dict (operation-specific)

Output:
  - None (writes to configured log path)

Guarantees:
  - JSONL format, one record per line
  - Append-only writes
  - Sensitive paths are redacted in log
  - Timestamp includes timezone
```

**Implementation Status**: Deferred (may reuse AirGap audit module)

## Data Types

### ValidationResult

```
{
  "allowed": bool,
  "canonical_path": Optional[str],
  "denial_reason": Optional[str]
}
```

### EvidenceResult

```
{
  "data": dict,
  "redactions_applied": int,
  "source_metadata": {
    "path": str,
    "collected_at": str,
    "collection_type": str
  }
}
```

### EvidencePack

```
{
  "schema_version": "1.0",
  "created_at": str (ISO 8601),
  "session_id": str,
  "items": [EvidenceResult, ...],
  "metadata": {
    "collector_version": str,
    "total_redactions": int
  }
}
```

## Error Handling

All modules follow consistent error handling:

| Error Type | Behavior |
|------------|----------|
| Source not allowed | Return denial result; do not throw |
| Redaction failure | Log and re-raise; do not return unredacted data |
| Collection timeout | Return partial result with timeout flag |
| Invalid configuration | Fail fast at initialization |

## Future Extensions

Contracts may be extended in future phases to include:

- Connector interfaces (Phase 3)
- Schema validation hooks
- Custom redaction pattern registration
- Rate limiting controls

All extensions will maintain backward compatibility with existing contracts.

## References

- [ROADMAP.md](./ROADMAP.md) - Implementation phases
- [THREAT_MODEL.md](./THREAT_MODEL.md) - Security analysis
- [SECURITY.md](../SECURITY.md) - Security policy
