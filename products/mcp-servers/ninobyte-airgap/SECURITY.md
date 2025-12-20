# Security Policy

## Threat Model

This MCP server operates under an **AirGap security model**:

1. **Threat T1: Path Traversal** - Attackers attempt to escape allowed roots via `../`, symlinks, or encoding tricks
   - **Mitigation**: Strict path canonicalization, symlink target validation, deny-by-default

2. **Threat T2: Resource Exhaustion (DoS)** - Attackers craft requests causing unbounded memory/CPU usage
   - **Mitigation**: Lazy iteration, file/result budgets, timeout enforcement, size limits

3. **Threat T3: Credential Exfiltration** - Attackers attempt to read secrets via file access
   - **Mitigation**: Blocked filename patterns, content redaction, no `.env`/key files

4. **Threat T4: Symlink Escape** - Attackers create symlinks pointing outside allowed roots
   - **Mitigation**: `O_NOFOLLOW` where possible, symlink target canonicalization, escape detection

5. **Threat T5: Audit Evasion** - Attackers attempt to hide their actions
   - **Mitigation**: Mandatory audit logging before operations, immutable audit format

## Security Controls

### Path Security (`path_security.py`)

- All paths are canonicalized via `os.path.realpath()`
- Symlink targets are validated to remain within allowed roots
- Traversal sequences (`../`) are detected and rejected
- Blocked patterns are enforced before any I/O

### Blocked Patterns (Default)

```
.env, .env.*, *.pem, *.key, *.p12, *.pfx, *.jks
id_rsa, id_ed25519, id_ecdsa, authorized_keys, known_hosts
credentials.*, secrets.*, *_SECRET, *_KEY, *_TOKEN
*.db, *.sqlite, *.sqlite3, *.kdb, *.kdbx
.git/config, .npmrc, .pypirc, .docker/config.json
```

### Audit Logging (`audit.py`)

- Local JSONL format only (no network transmission)
- No file content logged (only metadata)
- Path redaction enabled by default (hash-based)
- Actual bytes read logged (not file size)

### Timeout Enforcement (`timeout.py`)

- Per-operation timeout (default 30s)
- Checked frequently in loops (per-file, per-line)
- Graceful termination with partial results

## Vulnerability Reporting

Report security issues to: security@ninobyte.io

Do NOT open public issues for security vulnerabilities.

## Hardening Checklist

- [ ] Allowed roots configured (never `/` or home directory root)
- [ ] Audit log path writable and monitored
- [ ] Timeout configured appropriately for workload
- [ ] Blocked patterns reviewed for environment
- [ ] ripgrep installed for optimal search performance
