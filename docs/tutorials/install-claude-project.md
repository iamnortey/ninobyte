# Installing Skill Packs in Claude Projects

Guide for using Ninobyte skill packs with Claude Projects (web interface).

---

## Prerequisites

- Claude Pro or Team account with Projects access
- Downloaded skill pack folder

---

## Installation Steps

### Step 1: Download the Skill Pack

Download or clone the skill pack directory. For example:
```
senior-developer-brain/
├── README.md
├── SKILL.md
├── patterns/
└── examples/
```

### Step 2: Create a New Project

1. Go to [claude.ai](https://claude.ai)
2. Click "Projects" in the sidebar
3. Click "New Project"
4. Name your project (e.g., "Senior Developer Assistant")

### Step 3: Upload Skill Files

1. In your project, click "Add content"
2. Upload the following files:
   - `SKILL.md` (required - the execution contract)
   - All files from `patterns/` directory
   - Optionally: files from `examples/` for reference

### Step 4: Set Project Instructions

In the project settings, add a reference to the skill:

```
Follow the instructions in SKILL.md for all interactions.
When I specify a mode (e.g., "Architecture Review"), use that mode's workflow.
```

### Step 5: Start Using

Begin a conversation and specify the mode:
```
Mode: Architecture Review

Please review the following system design...
```

---

## Tips

- Upload your codebase or documentation as additional project files
- Reference specific files in your prompts
- Use the mode names exactly as specified in SKILL.md

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Claude doesn't follow the skill | Ensure SKILL.md is uploaded and referenced in instructions |
| Wrong mode activated | Use exact mode names from SKILL.md |
| Missing context | Upload relevant files to the project |

---

## See Also

- [Senior Developer's Brain README](../../products/skill-packs/senior-developer-brain/README.md)
- [SKILL.md](../../products/skill-packs/senior-developer-brain/SKILL.md)
