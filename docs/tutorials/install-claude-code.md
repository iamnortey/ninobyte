# Installing Skill Packs in Claude Code

**[UNVERIFIED]**: This guide documents best-known methods for using skill packs with Claude Code. The exact mechanism for loading custom skills/prompts in Claude Code has not been validated against official documentation. See `VALIDATION_LOG.md` entry VL-20251219-001.

---

## Prerequisites

- Claude Code installed and configured
- Downloaded skill pack folder

---

## Installation Methods

### Method 1: Project-Level Instructions [UNVERIFIED]

Claude Code may support project-level configuration. Check for:

1. A `.claude` or `.claudecode` directory in your project root
2. Configuration files like `claude.json` or `instructions.md`

If supported:
```bash
# Create config directory (if supported)
mkdir -p .claude

# Copy skill files
cp -r path/to/senior-developer-brain/SKILL.md .claude/
cp -r path/to/senior-developer-brain/patterns/ .claude/patterns/
```

### Method 2: Direct Reference in Prompts

Reference the skill pack directly in your prompts:

```
Please read and follow the instructions in ./docs/skills/SKILL.md

Mode: Code Review

Review the changes in src/api/handlers.ts
```

### Method 3: Session Initialization

At the start of a Claude Code session:

1. Ask Claude to read the SKILL.md file
2. Specify which mode you want to use
3. Proceed with your task

Example:
```
Read ./skills/senior-developer-brain/SKILL.md and operate in "Implementation Planning" mode for this session.
```

---

## Validation Needed

The following needs validation against official Claude Code documentation:

- [ ] Does Claude Code support project-level custom instructions?
- [ ] What is the correct directory/file structure for configuration?
- [ ] Are there official skill/prompt loading mechanisms?
- [ ] How do custom prompts interact with Claude Code's built-in capabilities?

See `VALIDATION_LOG.md` for validation checklist and status.

---

## File Organization Recommendation

Until official patterns are validated, organize skill files in your project:

```
your-project/
├── .claude/                    # If supported
│   └── instructions.md
├── docs/
│   └── skills/
│       └── senior-developer-brain/
│           ├── SKILL.md
│           └── patterns/
└── src/
```

---

## Troubleshooting

| Issue | Possible Solution |
|-------|-------------------|
| Claude Code ignores skill | Try explicit file reading instruction |
| Mode not recognized | Quote mode name exactly as in SKILL.md |
| Patterns not followed | Reference specific pattern files explicitly |

---

## See Also

- [Senior Developer's Brain README](../../products/skill-packs/senior-developer-brain/README.md)
- [SKILL.md](../../products/skill-packs/senior-developer-brain/SKILL.md)
- [VALIDATION_LOG.md](../canonical/VALIDATION_LOG.md)
