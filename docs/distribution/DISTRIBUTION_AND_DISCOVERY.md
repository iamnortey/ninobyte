# Distribution and Discovery Manual

> **Version**: 0.1.2
> **Last Updated**: 2025-12-19

This document describes how Ninobyte skills are distributed, installed, and discovered across supported platforms.

---

## Distribution Surfaces

### 1. Canonical Skill (Source of Truth)

**Path**: `skills/senior-developer-brain/`

This is the authoritative source. All other copies are derived from this location.

**Use for**:
- Development and contribution
- Claude.ai Projects (direct SKILL.md upload)
- Reference implementation

### 2. Claude Code Plugin

**Path**: `products/claude-code-plugins/ninobyte-senior-dev-brain/`

A self-contained plugin package for Claude Code installation via marketplace.

**Structure**:
```
ninobyte-senior-dev-brain/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── senior-developer-brain/
│       ├── SKILL.md
│       ├── CHANGELOG.md
│       ├── README.md
│       ├── patterns/
│       ├── examples/
│       └── tests/
└── README.md
```

**Installation**:
```bash
# Add the marketplace
/plugin marketplace add ninobyte/ninobyte

# Install the plugin
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
```

### 3. Legacy Skill-Packs (DEPRECATED)

**Path**: `products/skill-packs/senior-developer-brain/`

**Status**: Deprecated as of v0.1.1. Removal planned for v0.2.0.

Do not use. See `DEPRECATED.md` in that directory for migration instructions.

---

## Keeping Copies in Sync

### Developer Workflow

When making changes to the skill:

1. **Edit canonical only**: Make all changes in `skills/senior-developer-brain/`
2. **Sync to plugin**: Run `python scripts/ops/sync_plugin_skills.py --sync`
3. **Verify**: Run `python scripts/ci/validate_artifacts.py`
4. **Commit**: Both canonical and plugin copies together

### CI Enforcement

CI runs `validate_artifacts.py` which includes a hard drift check:
- Compares canonical vs plugin copy byte-for-byte
- Fails with clear error listing mismatched files
- Provides remediation command

**If CI fails due to drift**:
```bash
python scripts/ops/sync_plugin_skills.py --sync
git add .
git commit --amend  # or new commit
```

---

## Installation Methods

### Claude Code (Recommended)

```bash
# Via marketplace
/plugin marketplace add ninobyte/ninobyte
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace

# Or direct from local path
/plugin install ./products/claude-code-plugins/ninobyte-senior-dev-brain
```

### Claude.ai Projects

1. Go to project settings
2. Upload `skills/senior-developer-brain/SKILL.md`
3. (Optional) Upload supporting files from `patterns/`

### Claude Agent SDK

Reference the SKILL.md content in your agent's system prompt or skill configuration.

---

## Discovery

### Marketplace

The Ninobyte marketplace is defined in `.claude-plugin/marketplace.json`:

```json
{
  "name": "ninobyte-marketplace",
  "owner": { "name": "Ninobyte" },
  "plugins": [
    {
      "name": "ninobyte-senior-dev-brain",
      "source": "./products/claude-code-plugins/ninobyte-senior-dev-brain"
    }
  ]
}
```

### Version Discovery

To check the current version:
- **Canonical**: `grep Version skills/senior-developer-brain/SKILL.md`
- **Plugin**: `grep Version products/claude-code-plugins/.../SKILL.md`
- **Programmatic**: Use `sync_plugin_skills.py` which extracts version from frontmatter

---

## Troubleshooting

### "Drift detected" in CI

**Cause**: Plugin copy doesn't match canonical.

**Fix**:
```bash
python scripts/ops/sync_plugin_skills.py --sync
git add .
git commit -m "fix: sync plugin to canonical"
```

### Plugin not loading in Claude Code

**Check**:
1. `plugin.json` exists at `.claude-plugin/plugin.json`
2. `name` field is kebab-case
3. SKILL.md has valid YAML frontmatter

### Version mismatch

**Check**:
```bash
python scripts/ops/sync_plugin_skills.py --check
```

If versions differ, run `--sync`.

---

## Related Documentation

- [CHANGELOG.md](../canonical/CHANGELOG.md) — Version history
- [VALIDATION_LOG.md](../canonical/VALIDATION_LOG.md) — Platform validation evidence
- [PROJECT_INSTRUCTIONS.md](../canonical/PROJECT_INSTRUCTIONS.md) — Repository governance
