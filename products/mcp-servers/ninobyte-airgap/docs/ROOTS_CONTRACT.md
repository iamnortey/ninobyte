# Ninobyte AirGap MCP Server - Roots Contract

**Version**: 1.0
**Last Updated**: December 2024

## Overview

The AirGap MCP Server uses "allowed roots" as the primary access control mechanism. This document specifies how roots work, validation behavior, and troubleshooting guidance.

## What Are Allowed Roots?

Allowed roots are directories that the AirGap server is permitted to access. All filesystem operations are constrained to these directories and their subdirectories.

**Key Properties**:
- Defined at server startup via configuration
- Immutable during server runtime
- Must be absolute paths
- Must exist and be accessible

## Configuration

Allowed roots are specified in the `AirGapConfig`:

```python
config = AirGapConfig(
    allowed_roots=[
        "/home/user/project",
        "/home/user/shared-libs"
    ],
    # ... other settings
)
```

### Configuration Rules

| Rule | Description |
|------|-------------|
| Absolute paths only | Relative paths are rejected |
| Must exist | Non-existent directories are silently skipped |
| Duplicates allowed | Deduplicated internally |
| Overlapping allowed | Nested roots are valid (e.g., `/home` and `/home/user`) |

## Path Validation

### Validation Flow

```
Input Path
    │
    ▼
┌─────────────────────┐
│ Expand ~ (home dir) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Make absolute       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Canonicalize        │
│ (resolve symlinks)  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────┐
│ Check blocked patterns  │──→ DENIED (blocked_pattern)
└─────────┬───────────────┘
          │ pass
          ▼
┌─────────────────────────┐
│ Check under allowed     │──→ DENIED (outside_allowed_roots)
│ root + separator        │
└─────────┬───────────────┘
          │ pass
          ▼
      ALLOWED
```

### Canonicalization

All paths are canonicalized before validation:

1. **User expansion**: `~/file` → `/home/user/file`
2. **Absolute resolution**: `./file` → `/current/dir/file`
3. **Symlink resolution**: Follow symlinks to real path
4. **Normalization**: Remove `.` and resolve `..`

### Root Matching

A path is considered under an allowed root if:

```python
canonical_path == root or canonical_path.startswith(root + os.sep)
```

The `+ os.sep` prevents prefix attacks:
- Root: `/home/user`
- `/home/username/file` → DENIED (different directory)
- `/home/user/file` → ALLOWED

## Examples

### Allowed Access

Given root `/home/user/project`:

| Path | Canonical | Result |
|------|-----------|--------|
| `/home/user/project/src/main.py` | Same | ALLOWED |
| `/home/user/project` | Same | ALLOWED (root itself) |
| `~/project/README.md` | `/home/user/project/README.md` | ALLOWED |
| `/home/user/project/./src/../lib` | `/home/user/project/lib` | ALLOWED |

### Denied Access

Given root `/home/user/project`:

| Path | Reason |
|------|--------|
| `/etc/hosts` | Outside allowed roots |
| `/home/user/other` | Outside allowed roots |
| `/home/user/project/../other` | Resolves outside (traversal) |
| `/home/user/project/.env` | Blocked pattern |

### Symlink Behavior

Given:
- Root: `/home/user/project`
- Symlink: `/home/user/project/link` → `/etc/hosts`

| Access | Result |
|--------|--------|
| Read `/home/user/project/link` | DENIED (symlink escape) |
| List `/home/user/project` | Shows `link` as `type: unknown` |

## Blocked Patterns

Even within allowed roots, certain paths are blocked:

| Pattern | Examples |
|---------|----------|
| `.env`, `.env.*` | Environment files |
| `*.pem`, `*.key` | Key files |
| `id_rsa*` | SSH keys |
| `.aws/credentials` | Cloud credentials |
| `.git/config` | Git configuration |

### Cross-Platform Matching

Blocked patterns use forward slashes (`/`) but match Windows-style paths:

```
Pattern: .git/config
Matches: C:\repo\.git\config (Windows)
Matches: /home/user/repo/.git/config (Unix)
```

## Troubleshooting

### "Path is outside allowed roots"

**Symptoms**: Operations fail with `OUTSIDE_ALLOWED_ROOTS` error.

**Checklist**:
1. Verify the path is under a configured root
2. Check for symlinks that resolve outside roots
3. Ensure root paths are absolute and exist
4. On macOS: `/var` symlinks to `/private/var`

### "No allowed roots configured"

**Symptoms**: All operations fail.

**Solution**: Ensure at least one valid root is configured:

```python
config = AirGapConfig(allowed_roots=["/path/to/project"])
```

### "Matches blocked pattern"

**Symptoms**: Access denied to files within allowed roots.

**Check**: The file matches a blocked pattern. This is intentional security behavior.

**Example patterns** (without raw signatures):
- Environment configuration files
- Cryptographic key files
- Credential storage files

### macOS-Specific: /var vs /private/var

On macOS, `/var` is a symlink to `/private/var`. To avoid issues:

```python
# Use the canonical path
import os
root = os.path.realpath("/var/folders/tmp/myproject")
config = AirGapConfig(allowed_roots=[root])
```

## Security Implications

| Configuration | Risk Level | Notes |
|---------------|------------|-------|
| Single project root | Low | Minimal attack surface |
| Home directory root | Medium | More files accessible |
| Filesystem root (`/`) | HIGH | Defeats access control |

**Recommendation**: Use the most restrictive roots possible.

## References

- [THREAT_MODEL.md](./THREAT_MODEL.md) - Security threat analysis
- [AUDIT_LOG_SPEC.md](./AUDIT_LOG_SPEC.md) - Operation logging
- [SECURITY.md](../SECURITY.md) - Security policy
