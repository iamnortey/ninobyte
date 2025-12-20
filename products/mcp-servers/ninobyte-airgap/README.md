# Ninobyte AirGap MCP Server

A security-hardened, local-only MCP server for browsing and searching files with strict isolation guarantees.

**Canonical path:** `products/mcp-servers/ninobyte-airgap/`
**Import namespace:** `ninobyte_airgap`

## Security Posture

**AirGap requirements are NON-NEGOTIABLE:**

- **Local-only (stdio)**: No network listeners, stdio transport only
- **Read-only**: No write operations, no file modifications
- **Deny-by-default**: Explicit allowlist of accessible paths required
- **No network access**: Zero networking imports in default code path
- **No shell execution**: No `shell=True`, no `os.system`, no `os.popen`
- **Path security**: Canonicalization + traversal prevention + symlink escape prevention
- **Blocked patterns**: `.env`, `*_KEY`, `*.pem`, `*.key`, credentials, databases
- **Strict limits**: `max_file_size_bytes`, `max_results`, `max_response_bytes`, `timeout_seconds`
- **Audit logging**: Local JSONL, no content logging, path redaction enabled by default

## Tools

| Tool | Description |
|------|-------------|
| `list_dir` | List directory contents with security-aware metadata |
| `read_file` | Read file contents with size limits and offset support |
| `search_text` | Search text in files using ripgrep (preferred) or Python fallback |
| `redact_preview` | Stateless string redaction (no file I/O) |

## Configuration

```json
{
  "allowed_roots": ["/home/user/project"],
  "max_file_size_bytes": 1048576,
  "max_results": 100,
  "max_response_bytes": 524288,
  "timeout_seconds": 30,
  "audit_log_path": "/tmp/airgap-audit.jsonl",
  "redact_paths_in_audit": true
}
```

## Installation

```bash
cd products/mcp-servers/ninobyte-airgap
pip install -e .
```

## Usage

```bash
# stdio transport (required for AirGap)
python3 -m ninobyte_airgap --config config.json
```

## Development

### From Product Root (Recommended)

```bash
cd products/mcp-servers/ninobyte-airgap

# Install dependencies (if using uv)
uv lock
uv sync

# Compile check (CI-parity, recursive)
python3 -m compileall src/ tests/

# Run tests
python3 -m pytest tests/ -v
```

### From Repo Root

```bash
# Compile check (CI-parity, recursive)
python3 -m compileall products/mcp-servers/ninobyte-airgap/src/ products/mcp-servers/ninobyte-airgap/tests/

# Run tests
python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v

# Full CI validation (governance gate)
python3 scripts/ci/validate_artifacts.py
```

## Hard Gates (Must Pass Before Merge)

All commands below must exit 0. Run from product root unless noted.

```bash
# Compile check
python3 -m compileall src/ tests/

# Test suite
python3 -m pytest tests/ -v

# Governance gate (from repo root)
python3 scripts/ci/validate_artifacts.py
```

## License

MIT
