# Git Setup Runbook

Standard git configuration and workflow for Ninobyte repositories.

---

## Default Branch Policy

**Default branch**: `main`

All Ninobyte repositories use `main` as the default branch to align with modern tooling conventions (GitHub, GitLab, CI/CD systems).

---

## Recommended Global Configuration

Configure git to use `main` as the default branch for new repositories:

```bash
git config --global init.defaultBranch main
```

---

## Repository Setup

### New Repository

```bash
mkdir my-repo && cd my-repo
git init
# Creates repository with 'main' as default branch (if global config set)
```

### Cloning This Repository

```bash
git clone <remote-url>
cd ninobyte
```

---

## Remote Configuration

### Setting Up Remote (TODO)

```bash
# TODO: Replace with actual remote URL when repository is published
git remote add origin https://github.com/ninobyte/ninobyte.git

# Verify remote
git remote -v
```

### Pushing to Remote (TODO)

```bash
# First push (sets upstream)
git push -u origin main

# Subsequent pushes
git push
```

---

## Branch Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New feature | `feat/add-mcp-server` |
| `fix/` | Bug fix | `fix/validation-error` |
| `docs/` | Documentation only | `docs/update-readme` |
| `chore/` | Maintenance | `chore/update-deps` |
| `release/` | Release preparation | `release/v0.2.0` |

---

## Commit Message Format

Follow conventional commits:

```
<type>: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`

Example:
```
feat: add architecture review mode to skill pack

- Implements 10-section checklist
- Adds severity rating system
- Includes output format enforcement
```

---

## Pre-Commit Checklist

Before committing:
- [ ] No secrets in staged files
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG updated for user-facing changes

---

## Migration from master to main

If you have a local clone with `master`:

```bash
git branch -m master main
git fetch origin
git branch -u origin/main main
git remote set-head origin -a
```
