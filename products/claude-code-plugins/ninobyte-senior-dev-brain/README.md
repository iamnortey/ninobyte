# Ninobyte Senior Developer's Brain — Claude Code Plugin

**Version**: 0.1.1
**Type**: Claude Code Plugin

A self-contained Claude Code plugin providing enterprise-grade software engineering skills.

---

## Installation

### From Ninobyte Marketplace

```bash
# Add the Ninobyte marketplace
/plugin marketplace add ./path/to/ninobyte

# Install this plugin
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
```

### Direct Installation

```bash
/plugin install ./products/claude-code-plugins/ninobyte-senior-dev-brain
```

### Validate Installation

```bash
/plugin validate ./products/claude-code-plugins/ninobyte-senior-dev-brain
```

---

## What's Included

This plugin bundles the **Senior Developer's Brain** skill with:

### Operating Modes

| Mode | Purpose | Trigger |
|------|---------|---------|
| Architecture Review | Evaluate system designs | "Mode: Architecture Review" |
| Implementation Planning | Break down requirements | "Mode: Implementation Planning" |
| Code Review | Structured feedback | "Mode: Code Review" |
| Incident Triage | Systematic analysis | "Mode: Incident Triage" |
| ADR Writer | Decision records | "Mode: ADR Writer" |

### Security Features

- Enforces security-first review posture
- Flags authentication/crypto anti-patterns
- Refuses to approve hand-rolled security
- Requires established libraries/providers

---

## Plugin Structure

```
ninobyte-senior-dev-brain/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── senior-developer-brain/
│       ├── SKILL.md          # Skill definition
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── patterns/         # Review checklists
│       ├── examples/         # Usage examples
│       └── tests/            # Fixtures + goldens
├── LICENSE
├── CHANGELOG.md
└── README.md                 # This file
```

---

## Usage

Once installed, the skill is automatically available. Simply use one of the mode triggers:

```
Mode: Architecture Review

Review the following system design...
```

---

## License

MIT — See [LICENSE](./LICENSE)
