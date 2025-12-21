# Versioning & Tag Governance

This document defines the versioning policy and tag immutability rules for the ninobyte repository.

## Core Principles

### 1. Tags Are Immutable

Once a git tag is pushed to `origin`, it **must not** be moved, deleted, or rewritten. Tags serve as permanent release artifacts that may be referenced by:

- CI/CD pipelines and caches
- Downstream dependencies
- Changelogs and release notes
- Security advisories

**Policy:** Never use `git tag -f`, `git push --force`, or `git push --delete` on pushed tags.

### 2. Semantic Versioning

All plugin releases follow [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR**: Breaking changes to skill interfaces or behavior
- **MINOR**: New features, backward-compatible enhancements
- **PATCH**: Bug fixes, documentation updates, maintenance

### 3. Version Bump Workflow

The canonical release flow:

```
1. Create atomic version bump PR from main
   - Update plugin.json version field
   - No other changes in the same PR

2. Merge PR to main (squash)

3. Create annotated tag on main
   git tag -a vX.Y.Z -m "vX.Y.Z: <brief description>"

4. Push tag
   git push origin vX.Y.Z
```

## Handling Premature Tags

If a tag is created before the version bump commit lands (or points to incorrect content):

| Scenario | Resolution |
|----------|------------|
| Tag pushed to remote | **Skip to next version** |
| Tag exists locally only | Safe to delete and recreate |

### Example: v0.1.4 Anomaly

In December 2025, tag `v0.1.4` was created prematurely:

- **Issue:** Tag `v0.1.4` was pushed, but at that commit `plugin.json` still showed version `0.1.3`
- **Root cause:** Tag was created before the version bump commit was merged
- **Resolution:** Skipped to `v0.1.5` to preserve tag immutability

```
v0.1.3  ─── correct (plugin.json = 0.1.3)
v0.1.4  ─── premature (plugin.json = 0.1.3, tag message claims 0.1.4)
v0.1.5  ─── correct (plugin.json = 0.1.5)
```

This approach:
- Preserves immutability of the pushed `v0.1.4` tag
- Avoids breaking any references to `v0.1.4`
- Documents the gap in the version history

## Pre-Release Checklist

Before creating a release tag:

- [ ] Version bump PR merged to main
- [ ] `git checkout main && git pull --ff-only`
- [ ] Verify: `cat products/claude-code-plugins/*/. claude-plugin/plugin.json | grep '"version"'`
- [ ] All validations pass: `python3 scripts/ci/validate_artifacts.py`
- [ ] All tests pass: `python3 -m pytest -q`

## Tag Naming Convention

| Type | Format | Example |
|------|--------|---------|
| Release | `vMAJOR.MINOR.PATCH` | `v0.1.5` |
| Pre-release | `vMAJOR.MINOR.PATCH-rc.N` | `v0.2.0-rc.1` |

## Related Documents

- [Claude Code Plugin Runbook](./claude_code_plugin_runbook.md)
