# Senior Developer's Brain

**Version**: 0.1.1
**Type**: Agent Skill (Official Format)

A job system for enterprise software engineering execution. Transform Claude into a disciplined engineering partner with structured, auditable workflows.

---

## Features

### Operating Modes

| Mode | Purpose | Trigger |
|------|---------|---------|
| Architecture Review | Evaluate system designs | "Mode: Architecture Review" |
| Implementation Planning | Break down requirements into tasks | "Mode: Implementation Planning" |
| Code Review | Structured code feedback | "Mode: Code Review" |
| Incident Triage | Systematic incident analysis | "Mode: Incident Triage" |
| ADR Writer | Draft Architecture Decision Records | "Mode: ADR Writer" |

### Key Capabilities

- **Structured outputs**: Consistent, scannable formats for all modes
- **Evidence discipline**: Citations, assumptions marked, uncertainty flagged
- **Security-first**: Enforces security policy, flags vulnerabilities, refuses insecure patterns
- **Actionable**: Specific recommendations, not vague suggestions

---

## Installation

### Via Claude Code Plugin (Recommended)

Install from the Ninobyte marketplace:

```bash
# Add this repository as a marketplace
/plugin marketplace add ./path/to/ninobyte

# Install the plugin
/plugin install ninobyte-senior-dev-brain@ninobyte-marketplace
```

Or install directly from the plugin directory:
```bash
/plugin install ./products/claude-code-plugins/ninobyte-senior-dev-brain
```

### Claude Projects (Web Interface)

1. Download this skill folder
2. Create a new Claude Project
3. Upload these files:
   - `SKILL.md` (required)
   - All files from `patterns/` (recommended)
4. In project instructions, add:
   ```
   Follow the instructions in SKILL.md for all interactions.
   ```

See [full tutorial](../../docs/tutorials/install-claude-project.md)

### Direct Reference

Reference the skill directly in Claude Code:
```
Read ./skills/senior-developer-brain/SKILL.md and operate in "[Mode Name]" mode.
```

---

## Quick Start Examples

### Example 1: Architecture Review

```
Mode: Architecture Review

Review this microservices architecture:
- API Gateway (Kong)
- Auth Service (Node.js + JWT)
- User Service (Python + PostgreSQL)
- Notification Service (Go + Redis pub/sub)
- Message Queue (RabbitMQ)
```

### Example 2: Implementation Planning

```
Mode: Implementation Planning

I need to add user preferences to our app. Users should be able to:
- Set notification preferences (email, push, SMS)
- Choose dark/light theme
- Set timezone and language

We have a React frontend and Node.js backend with PostgreSQL.
```

### Example 3: Code Review

```
Mode: Code Review

Review this authentication middleware:

[paste code here]
```

---

## File Structure

```
senior-developer-brain/
├── README.md           # This file
├── SKILL.md            # Execution contract (main skill definition)
├── CHANGELOG.md        # Version history
├── patterns/
│   ├── architecture-review-checklist.md
│   ├── code-review-checklist.md
│   └── incident-triage-runbook.md
├── examples/
│   ├── example_001_vague_request.md
│   └── example_002_code_review.md
└── tests/
    ├── fixtures/
    │   └── fixture_001.md
    └── goldens/
        └── golden_001_expected.md
```

---

## Security Policy

This skill enforces a **mandatory security policy**:

- ❌ Never approves hand-rolled authentication or cryptography
- ❌ Never approves plaintext password storage
- ✅ Always recommends established identity providers and libraries
- ✅ Always flags missing rate limiting on auth endpoints
- ✅ Always flags JWT in localStorage (recommends httpOnly cookies)
- ✅ Always flags single points of failure as CRITICAL

See `SKILL.md` → Security Policy section for full details.

---

## Known Limitations

1. **No code execution**: Reviews code but cannot run it
2. **No external access**: Cannot fetch URLs or access APIs
3. **Context limits**: Very large codebases may need chunking
4. **No persistence**: Each conversation starts fresh

---

## Versioning

This skill follows semantic versioning:
- **Major**: Breaking changes to output format or mode behavior
- **Minor**: New modes or features, backward compatible
- **Patch**: Bug fixes, documentation updates

---

## Validation Status

| Feature | Status |
|---------|--------|
| SKILL.md format | ✅ Validated (VL-20251219-003) |
| Claude Code plugin | ✅ Validated (VL-20251219-004) |
| Marketplace distribution | ✅ Validated (VL-20251219-005) |
| Claude Projects installation | ✅ Validated |
| Mode workflows | ✅ Validated (self-contained) |

See [VALIDATION_LOG.md](../../docs/canonical/VALIDATION_LOG.md) for details.

---

## License

MIT — See [LICENSE](../../LICENSE)
