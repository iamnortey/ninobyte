# Compatibility Matrix

Tracks compatibility between Ninobyte products and platform versions.

---

## Products

### Senior Developer's Brain (Skill)

| Version | Claude Projects | Claude Code Plugin | Notes |
|---------|-----------------|-------------------|-------|
| 0.1.1   | ✅ Supported    | ✅ Supported (Validated) | Official format per VL-20251219-003/004/005 |
| 0.1.0   | ✅ Supported    | ⚠️ Deprecated | Legacy format, missing frontmatter |

---

## Platform Dependencies

| Platform | Minimum Version | Tested Version | Notes |
|----------|-----------------|----------------|-------|
| Claude Projects | N/A (web interface) | 2025-12 | File upload method |
| Claude Code | Any (plugin system) | 2025-12 | Validated per VL-20251219-004 |
| MCP Protocol | [NOT USED] | N/A | No MCP servers in v0.1.x |

---

## Official Conventions Validated

| Convention | Source | Status |
|------------|--------|--------|
| SKILL.md format | https://github.com/anthropics/skills | ✅ Validated |
| Plugin structure | https://code.claude.com/docs/en/plugins | ✅ Validated |
| Marketplace schema | https://code.claude.com/docs/en/plugin-marketplaces | ✅ Validated |

---

## Validation Status

See `VALIDATION_LOG.md` for detailed validation status:
- VL-20251219-003: SKILL.md format
- VL-20251219-004: Plugin structure
- VL-20251219-005: Marketplace schema

---

## Breaking Changes

| Version | Platform | Change | Migration |
|---------|----------|--------|-----------|
| 0.1.1 | All | SKILL.md requires YAML frontmatter | Add `name` and `description` fields |
| 0.1.1 | Claude Code | Marketplace moved to `.claude-plugin/` | Use `.claude-plugin/marketplace.json` |
| 0.1.1 | All | Skill location is now `skills/` | Use `skills/senior-developer-brain/` |

---

## Deprecations

| Deprecated | Replacement | Removal Version |
|------------|-------------|-----------------|
| `products/skill-packs/` | `skills/` | 0.2.0 |
| `marketplace/marketplace.json` | `.claude-plugin/marketplace.json` | 0.2.0 |

---

## Future Compatibility Notes

- Monitor Anthropic release notes for API changes
- Re-validate compatibility quarterly or on major platform releases
- Document any deprecation warnings immediately
- MCP servers will follow https://spec.modelcontextprotocol.io/ when released
