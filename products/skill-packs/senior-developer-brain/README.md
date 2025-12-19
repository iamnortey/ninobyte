# Senior Developer's Brain

**Version**: 0.1.0
**Type**: Skill Pack

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
- **Security-aware**: Won't generate secrets, flags security concerns
- **Actionable**: Specific recommendations, not vague suggestions

---

## Installation

### Claude Projects (Web Interface)

1. Download this skill pack folder
2. Create a new Claude Project
3. Upload these files:
   - `SKILL.md` (required)
   - All files from `patterns/`
4. In project instructions, add:
   ```
   Follow the instructions in SKILL.md for all interactions.
   ```

See [full tutorial](../../../docs/tutorials/install-claude-project.md)

### Claude Code [UNVERIFIED]

> **Note**: Claude Code integration method not yet validated against official documentation. See `VALIDATION_LOG.md` entry VL-20251219-001.

Option 1: Reference directly in prompts
```
Read ./path/to/SKILL.md and operate in "[Mode Name]" mode.
```

Option 2: Project configuration (if supported)
```bash
# Check if .claude directory is supported
mkdir -p .claude
cp SKILL.md .claude/
```

See [full tutorial](../../../docs/tutorials/install-claude-code.md)

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

## Known Limitations

1. **No code execution**: Reviews code but cannot run it
2. **No external access**: Cannot fetch URLs or access APIs
3. **Context limits**: Very large codebases may need chunking
4. **No persistence**: Each conversation starts fresh
5. **Platform-specific features**: Some installation methods are `[UNVERIFIED]`

---

## Versioning

This skill pack follows semantic versioning:
- **Major**: Breaking changes to output format or mode behavior
- **Minor**: New modes or features, backward compatible
- **Patch**: Bug fixes, documentation updates

---

## Validation Status

| Feature | Status |
|---------|--------|
| Claude Projects installation | Validated (standard file upload) |
| Claude Code installation | [UNVERIFIED] |
| Mode workflows | Validated (self-contained) |
| Output formats | Validated (self-contained) |

See [VALIDATION_LOG.md](../../../docs/canonical/VALIDATION_LOG.md) for details.

---

## Contributing

1. Follow patterns in existing modes
2. Add tests (fixtures + goldens) for new features
3. Update CHANGELOG.md
4. Ensure no secrets or sensitive data in examples

---

## License

MIT — See [LICENSE](../../../LICENSE)
