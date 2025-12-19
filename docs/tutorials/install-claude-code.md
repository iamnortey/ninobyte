# Installing Ninobyte Plugins in Claude Code

Official guide for using Ninobyte plugins with Claude Code.

> **✅ Validated (v0.1.1)**: This guide follows official Claude Code plugin conventions per [VALIDATION_LOG.md](../canonical/VALIDATION_LOG.md) entries VL-20251219-004 and VL-20251219-005.

---

## Prerequisites

- Claude Code installed and configured
- Access to the Ninobyte repository

---

## Installation Methods

### Method 1: Via Ninobyte Marketplace (Recommended)

The Ninobyte repository is a plugin marketplace. Add it and install plugins:

```bash
# Add the Ninobyte marketplace (from local clone)
/plugin marketplace add /path/to/ninobyte

# Or if you're inside the ninobyte directory
/plugin marketplace add ./

# List available plugins
/plugin marketplace list ninobyte-marketplace

# Install a plugin
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
```

### Method 2: Direct Plugin Installation

Install a plugin directly from its directory:

```bash
/plugin install /path/to/ninobyte/products/claude-code-plugins/ninobyte-senior-dev-brain
```

### Method 3: Validate Before Installing

Validate the plugin structure before installation:

```bash
/plugin validate /path/to/ninobyte/products/claude-code-plugins/ninobyte-senior-dev-brain
```

---

## Verification

After installation, verify the plugin is loaded:

```bash
# List installed plugins
/plugin list

# Check plugin details
/plugin info ninobyte-senior-dev-brain
```

---

## Using Installed Skills

Once installed, skills are automatically available. Simply use the mode trigger:

```
Mode: Architecture Review

Review the following system design...
```

The skill will be invoked automatically based on task context.

---

## Available Plugins

### ninobyte-senior-dev-brain

Enterprise software engineering skill with:
- Architecture Review mode
- Implementation Planning mode
- Code Review mode
- Incident Triage mode
- ADR Writer mode

**Security Features**:
- Enforces security-first review posture
- Flags authentication/crypto anti-patterns
- Refuses hand-rolled security implementations

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not found | Verify path and marketplace is added |
| Skill not activating | Use exact mode trigger from SKILL.md |
| Validation errors | Run `/plugin validate` and check output |
| Marketplace not loading | Verify `.claude-plugin/marketplace.json` exists |

---

## Plugin Structure Reference

Official plugin structure:
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── skill-name/
│       └── SKILL.md          # Skill definition
├── commands/                  # Optional slash commands
├── agents/                    # Optional agents
├── hooks/                     # Optional hooks
└── README.md
```

---

## See Also

- [Official Claude Code Plugins Docs](https://code.claude.com/docs/en/plugins)
- [Official Plugin Reference](https://code.claude.com/docs/en/plugins-reference)
- [Official Marketplaces Docs](https://code.claude.com/docs/en/plugin-marketplaces)
- [Canonical Skill Location](../../skills/senior-developer-brain/)
- [VALIDATION_LOG.md](../canonical/VALIDATION_LOG.md)
