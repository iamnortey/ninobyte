# Ninobyte OpsPack - Interface Contract

**Version**: 0.0.0 (Contract Only)
**Status**: Design specification; implementation deferred
**Last Updated**: December 2024

## Overview

This document defines the contracts for OpsPack modules. These are design specifications only; no implementation exists in this phase.

## Contract Principles

All OpsPack interfaces adhere to:

1. **Read-only**: No mutations to any data source
2. **Explicit consent**: Each data source requires explicit configuration
3. **Redaction-first**: All outputs pass through redaction before return
4. **Auditability**: All operations are logged with structured metadata

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
