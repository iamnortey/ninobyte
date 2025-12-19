# DEPRECATED

**Status**: DEPRECATED as of v0.1.1 (2025-12-19)
**Removal Planned**: v0.2.0

---

## This Location Is No Longer the Source of Truth

This skill pack location (`products/skill-packs/senior-developer-brain/`) is **deprecated** and will be removed in v0.2.0.

### Use These Instead

| Purpose | Path |
|---------|------|
| **Canonical Source** | `skills/senior-developer-brain/` |
| **Claude Code Plugin** | `products/claude-code-plugins/ninobyte-senior-dev-brain/` |

### Why Deprecated?

1. **Single source of truth**: The canonical skill at `skills/` is the authoritative version
2. **Plugin bundling**: Claude Code plugins now bundle the skill directly
3. **Drift prevention**: Maintaining multiple copies caused silent divergence

### Migration

If you were referencing this path:
- For development: Use `skills/senior-developer-brain/`
- For Claude Code installation: Use the plugin package

### Version at Deprecation

This copy was frozen at **v0.1.0** and is not being updated.
The current version is **v0.1.2** (check `skills/senior-developer-brain/SKILL.md`).

---

**Do not use files from this directory.** They are stale and may contain outdated contracts.
