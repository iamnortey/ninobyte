# Security Policy — Ninobyte Lexicon Packs

## Security Posture

Lexicon Packs is designed with **defense-in-depth** security:

| Guarantee | Enforcement |
|-----------|-------------|
| No network imports | AST-verified in CI (`validate_artifacts.py`) |
| No shell execution | AST-verified in CI (`validate_artifacts.py`) |
| No file writes | Read-only operations only |
| Path traversal protection | Canonicalization + `..` segment rejection |
| Deterministic output | Same input → same output, always |

## What Lexicon Packs Does NOT Do

Lexicon Packs explicitly excludes:

- **No network calls**: No HTTP clients, no DNS lookups, no telemetry
- **No shell execution**: No `subprocess`, `os.system`, `os.popen`
- **No file writes**: Read-only access to pack files
- **No external services**: No API calls, no cloud dependencies
- **No copyrighted data**: No scraped datasets, no proprietary content

## Supported Operations

| Operation | Allowed |
|-----------|---------|
| Read pack.json | Yes (path validated) |
| Read entries.csv | Yes (path validated) |
| Write to STDOUT | Yes |
| Write to file | No |
| Network access | No |
| Shell execution | No |

## Path Security

All file paths are validated before access:

1. **Canonicalization**: Paths are resolved to absolute form
2. **Traversal rejection**: Paths containing `..` after normalization are rejected
3. **Pack boundary**: Entry paths must be within pack directory
4. **Exit code 2**: Invalid paths cause immediate exit with code 2

## Dependency Security

| Dependency | Purpose | When |
|------------|---------|------|
| Python stdlib | Core functionality | Always |

No external dependencies. Pure stdlib implementation.

## Reporting Security Issues

Report security vulnerabilities to: **security@ninobyte.io**

Do NOT open public issues for security vulnerabilities.

## Contributor Guidelines

When contributing to Lexicon Packs:

1. **No networking imports**: Never import `urllib`, `http`, `socket`, `requests`, etc.
2. **No shell execution**: Never use `subprocess`, `os.system`, `os.popen`
3. **No file writes**: Only read operations are permitted
4. **Path validation**: All file paths must be validated before access
5. **Determinism**: Output must be reproducible for the same input
6. **No copyrighted data**: Packs must contain only public domain or properly licensed content

CI will block PRs that violate these constraints.

## Audit Trail

Security constraints are enforced by:

- `scripts/ci/validate_artifacts.py` — AST analysis for forbidden imports
- `tests/test_validate_pack.py` — Schema compliance verification
- `tests/test_determinism.py` — Determinism verification
