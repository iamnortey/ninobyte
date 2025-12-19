# Claude Code Plugin Runbook

> Operational guide for the ninobyte-marketplace and ninobyte-senior-dev-brain plugin.

## Quick Reference

| Item | Path |
|------|------|
| Marketplace manifest | `.claude-plugin/marketplace.json` |
| Plugin manifest | `products/claude-code-plugins/ninobyte-senior-dev-brain/.claude-plugin/plugin.json` |
| Products symlink | `.claude-plugin/products -> ../products` |

---

## Why Claude Code Requires "./" Prefix

Claude Code validates marketplace plugin entries against a strict schema:

```
plugins[].source: Invalid input: must start with "./"
```

**Schema rule:** The `source` field in `marketplace.json` MUST begin with `./` (dot-slash).

| Invalid | Valid |
|---------|-------|
| `"source": "products/..."` | `"source": "./products/..."` |
| `"source": "../products/..."` | `"source": "./products/..."` |
| `"source": "/absolute/path/..."` | `"source": "./products/..."` |

---

## Why the Symlink Exists

**Path resolution semantics:** Claude Code resolves the `source` path **relative to the directory containing `marketplace.json`**, not the repository root.

Our layout:
```
ninobyte/
├── .claude-plugin/
│   ├── marketplace.json      ← source: "./products/..."
│   └── products -> ../products  ← SYMLINK (required)
└── products/
    └── claude-code-plugins/
        └── ninobyte-senior-dev-brain/
```

When Claude Code reads `"source": "./products/claude-code-plugins/..."`:
1. It starts from `.claude-plugin/` (the marketplace directory)
2. It looks for `.claude-plugin/products/...`
3. The symlink redirects to `../products/...` (the actual location)

**Without the symlink:** Claude Code reports "Plugin directory not found".

---

## Cache-Bust Commands (Standard Refresh)

Run these in **Claude Code chat** (not terminal) when:
- You've updated marketplace.json or plugin.json
- Plugin appears stale or shows wrong version
- Marketplace shows schema errors after a fix

```
/plugin marketplace remove ninobyte-marketplace
/plugin marketplace add /Users/isaacnortey/Developer/ninobyte/.claude-plugin/marketplace.json
/plugin marketplace update ninobyte-marketplace
/plugin marketplace list
/plugin
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
/plugin list
```

**Expected outcomes:**
| Command | Expected Result |
|---------|-----------------|
| `marketplace list` | Shows `ninobyte-marketplace` with no errors |
| `/plugin` (Discover) | Shows `ninobyte-senior-dev-brain` available |
| `install` | "Successfully installed" message |
| `list` | Shows `ninobyte-senior-dev-brain` with correct version |

---

## Nuclear Option: Full Cache Purge

**Use only as last resort** when standard refresh fails.

### Step 1: Remove cached data (terminal)

```bash
# Remove marketplace cache
rm -rf ~/.claude/plugins/cache/ninobyte-marketplace

# Remove installed plugins registry
rm -f ~/.claude/plugins/installed_plugins.json
rm -f ~/.claude/plugins/installed_plugins_v2.json

# Remove marketplace registry
rm -f ~/.claude/plugins/known_marketplaces.json
```

### Step 2: Clean enabled plugins from settings (optional)

```bash
python3 -c "
import json, pathlib
p = pathlib.Path.home() / '.claude/settings.json'
if p.exists():
    d = json.loads(p.read_text())
    d.pop('enabledPlugins', None)
    p.write_text(json.dumps(d, indent=2))
    print('Cleaned enabledPlugins from settings.json')
"
```

### Step 3: Re-add marketplace (Claude Code chat)

```
/plugin marketplace add /Users/isaacnortey/Developer/ninobyte/.claude-plugin/marketplace.json
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
/plugin list
```

---

## Local Setup Script

Before working with the plugin, run:

```bash
python3 scripts/ops/ensure_claude_marketplace_paths.py
```

This script:
1. Validates marketplace.json and plugin.json syntax
2. Enforces plugins[].source starts with "./" (Claude schema)
3. Creates the symlink if missing (cross-platform)
4. Validates plugin source paths resolve to existing directories
5. Prints "Proof of State" summary

---

## CI Validation

The following checks run automatically in CI:

| Check | Failure Condition |
|-------|-------------------|
| Source prefix | `plugins[].source` does not start with `./` |
| Symlink exists | `.claude-plugin/products` missing or not a symlink |
| Symlink target | Symlink does not point to `../products` |
| Path resolution | Source path does not resolve to existing directory |

Run locally:
```bash
python3 scripts/ci/validate_artifacts.py
```

---

## Troubleshooting

### "Invalid schema: plugins.0.source must start with ./"

**Cause:** `marketplace.json` uses `../` or bare path.

**Fix:**
1. Change `"source": "../products/..."` to `"source": "./products/..."`
2. Ensure symlink exists: `ln -sf ../products .claude-plugin/products`
3. Run cache-bust commands above.

### "Plugin directory not found"

**Cause:** Symlink missing or broken.

**Fix:**
```bash
cd /Users/isaacnortey/Developer/ninobyte
ln -sf ../products .claude-plugin/products
ls -la .claude-plugin/products  # verify it resolves
```

### Plugin shows wrong version

**Cause:** Cached installation from older commit.

**Fix:** Run nuclear option (above), then reinstall.

---

## Version History

| Version | Change |
|---------|--------|
| 0.1.3 | Added symlink + schema-compliant source path |
| 0.1.2 | Initial marketplace setup |

