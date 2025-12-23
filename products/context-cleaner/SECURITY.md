# Security Policy — Ninobyte ContextCleaner

## Security Posture

ContextCleaner is designed with **defense-in-depth** security:

| Guarantee | Enforcement |
|-----------|-------------|
| No network imports | AST-verified in CI (`validate_artifacts.py`) |
| No shell execution | AST-verified in CI (`validate_artifacts.py`) |
| No file writes | Read-only operations only |
| Path traversal protection | Canonicalization + `..` segment rejection |
| Deterministic output | Same input → same output, always |

## What ContextCleaner Does NOT Do

ContextCleaner explicitly excludes:

- **No network calls**: No HTTP clients, no DNS lookups, no telemetry
- **No shell execution**: No `subprocess`, `os.system`, `os.popen`
- **No file writes**: Read-only access to input files and lexicons
- **No external services**: No API calls, no cloud dependencies
- **No OCR**: Scanned PDFs are not processed (text-based only)

## Supported Operations

| Operation | Allowed |
|-----------|---------|
| Read from STDIN | ✅ |
| Read from file (`--input`) | ✅ (path validated) |
| Read lexicon (`--lexicon`) | ✅ (path validated) |
| Write to STDOUT | ✅ |
| Write to file | ❌ |
| Network access | ❌ |
| Shell execution | ❌ |

## Path Security

All file paths are validated before access:

1. **Canonicalization**: Paths are resolved to absolute form
2. **Traversal rejection**: Paths containing `..` after normalization are rejected
3. **Exit code 2**: Invalid paths cause immediate exit with code 2

## Dependency Security

| Dependency | Purpose | When |
|------------|---------|------|
| Python stdlib | Core functionality | Always |
| pypdf | PDF text extraction | Only with `[pdf]` extra |

No runtime dependencies for core text redaction.

## Reporting Security Issues

Report security vulnerabilities to: **security@ninobyte.io**

Do NOT open public issues for security vulnerabilities.

## Contributor Guidelines

When contributing to ContextCleaner:

1. **No networking imports**: Never import `urllib`, `http`, `socket`, `requests`, etc.
2. **No shell execution**: Never use `subprocess`, `os.system`, `os.popen`
3. **No file writes**: Only read operations are permitted
4. **Path validation**: All file paths must be validated before access
5. **Determinism**: Output must be reproducible for the same input

CI will block PRs that violate these constraints.

## Audit Trail

Security constraints are enforced by:

- `scripts/ci/validate_artifacts.py` — AST analysis for forbidden imports
- `tests/test_smoke_script_contract.py` — Contract compliance verification
- Golden file tests — Determinism verification
