# Ninobyte AirGap MCP Server - Audit Log Specification

**Version**: 1.0
**Format**: JSON Lines (JSONL)
**Last Updated**: December 2024

## Overview

The AirGap MCP Server maintains an audit log of all filesystem operations. This document specifies the log format, fields, and behavior.

## File Format

Audit logs are stored in **JSON Lines** format (`.jsonl`):
- One JSON object per line
- UTF-8 encoded
- Append-only writes
- No trailing comma between records

## Record Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 format with timezone (e.g., `2024-12-20T14:30:00.123456+00:00`) |
| `operation` | string | Operation type (see Operation Types) |
| `success` | boolean | Whether operation succeeded |
| `session_id` | string | Unique session identifier |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Target path (may be redacted) |
| `error` | string | Error message if `success=false` |
| `denial_reason` | string | Reason for access denial |
| `bytes_read` | integer | Bytes returned for read operations |
| `results_count` | integer | Number of results for search/list |
| `pattern` | string | Search pattern (for search_text) |
| `metadata` | object | Additional operation-specific data |

### Operation Types

| Operation | Description |
|-----------|-------------|
| `read_file` | File content read |
| `list_dir` | Directory listing |
| `search_text` | Text search across files |
| `redact_preview` | Content redaction preview |
| `validate_path` | Path validation check |

## Example Records

### Successful Read

```json
{"timestamp": "2024-12-20T14:30:00.123456+00:00", "operation": "read_file", "success": true, "session_id": "abc123", "path": "/allowed/root/file.txt", "bytes_read": 1024}
```

### Access Denied

```json
{"timestamp": "2024-12-20T14:30:01.234567+00:00", "operation": "read_file", "success": false, "session_id": "abc123", "path": "[REDACTED]", "denial_reason": "blocked_pattern", "error": "matches blocked pattern: .env"}
```

### Search Operation

```json
{"timestamp": "2024-12-20T14:30:02.345678+00:00", "operation": "search_text", "success": true, "session_id": "abc123", "pattern": "TODO", "results_count": 15, "metadata": {"files_scanned": 100, "timeout_reached": false}}
```

## Path Redaction

When `redact_paths_in_audit=true` (default), sensitive paths are replaced:

| Original | Redacted |
|----------|----------|
| `/home/user/project/.env` | `[REDACTED]` |
| `/home/user/project/src/main.py` | `/home/user/project/src/main.py` (allowed paths not redacted) |

Redaction applies to:
- Paths matching blocked patterns
- Paths outside allowed roots
- Paths in error messages

## Determinism

The audit logger is designed for predictable output:

1. **Timestamp precision**: Microsecond precision, always includes timezone
2. **Field ordering**: Fields are written in consistent order (Python dict insertion order)
3. **No floating-point ambiguity**: All numeric fields are integers
4. **UTF-8 normalization**: Paths are normalized to NFC form

## Limits and Buffering

| Setting | Default | Description |
|---------|---------|-------------|
| Buffer size | 1 record | Flush after each write |
| Max path length | 4096 chars | Paths exceeding this are truncated |
| Max error length | 1024 chars | Error messages truncated |

## Backward Compatibility

Future versions will maintain:

1. **Required fields**: Always present, never renamed
2. **Optional fields**: May be added, never removed
3. **Operation types**: New types may be added, existing never changed
4. **Version field**: Recommended to add `"version": "1.0"` for future parsing

### Recommended Future Format

```json
{"version": "1.0", "timestamp": "...", "operation": "...", ...}
```

## Security Considerations

1. **Log location**: Store audit logs outside allowed roots if possible
2. **Permissions**: Restrict read access to audit logs
3. **Rotation**: Implement log rotation to prevent disk exhaustion
4. **Integrity**: Consider cryptographic signing for tamper detection

## Parsing Examples

### Python

```python
import json

def parse_audit_log(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

# Count operations by type
from collections import Counter
ops = Counter(r['operation'] for r in parse_audit_log('audit.jsonl'))
```

### jq (Command Line)

```bash
# Count successful operations
cat audit.jsonl | jq -s '[.[] | select(.success == true)] | length'

# List all denied paths
cat audit.jsonl | jq -r 'select(.success == false) | .path'
```

## References

- [THREAT_MODEL.md](./THREAT_MODEL.md) - Security threat analysis
- [SECURITY.md](../SECURITY.md) - Security policy
