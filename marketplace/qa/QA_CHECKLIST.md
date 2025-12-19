# Marketplace QA Checklist

Quality assurance gates for products in the Ninobyte marketplace.

> **Note (v0.1.1)**: The canonical marketplace is now at `/.claude-plugin/marketplace.json` following official Claude Code conventions. See [VALIDATION_LOG.md](../../docs/canonical/VALIDATION_LOG.md) entry VL-20251219-005.

---

## Pre-Listing Checklist

Every product must pass these checks before being added to `.claude-plugin/marketplace.json`.

### Plugin Structure (Official Format)

- [ ] **Plugin directory exists** at `products/claude-code-plugins/<plugin-name>/`
- [ ] **Plugin manifest exists** at `.claude-plugin/plugin.json`
  - [ ] `name` field present (kebab-case)
  - [ ] `version` field present (semver)
  - [ ] `description` field present
  - [ ] `author.name` field present
- [ ] **Skills directory exists** at `skills/<skill-name>/` within plugin
- [ ] **SKILL.md has valid frontmatter**:
  - [ ] `name` field (lowercase, hyphens)
  - [ ] `description` field (single line recommended)

### Documentation

- [ ] **README.md exists** and includes:
  - [ ] Product description
  - [ ] Installation instructions (plugin install command)
  - [ ] Usage examples
  - [ ] Known limitations
  - [ ] Version information

- [ ] **SKILL.md exists** with:
  - [ ] YAML frontmatter (name + description)
  - [ ] Purpose clearly stated
  - [ ] Scope boundaries defined
  - [ ] Security posture documented

- [ ] **CHANGELOG.md exists** with current version entry

### Testing

- [ ] **Test fixtures exist** in `tests/fixtures/`
  - [ ] At least one fixture per major mode/feature
  - [ ] Fixtures include input, expected behavior, verification criteria

- [ ] **Golden files exist** in `tests/goldens/`
  - [ ] Corresponding golden for each fixture
  - [ ] Golden includes verification checklist

- [ ] **Manual verification completed**
  - [ ] Each fixture tested
  - [ ] Results documented

### Security

- [ ] **No secrets in any files**
  - [ ] No API keys, tokens, or passwords
  - [ ] No hardcoded credentials in examples
  - [ ] Placeholder values used where needed

- [ ] **Security documentation present**
  - [ ] Data handling described
  - [ ] Explicit refusals documented
  - [ ] Safe logging patterns noted (if applicable)

- [ ] **Threat model considerations**
  - [ ] Attack surfaces identified
  - [ ] Mitigations documented

### Validation

- [ ] **VALIDATION_LOG.md updated**
  - [ ] New or updated validation entry
  - [ ] Platform-dependent claims validated against official sources

- [ ] **Follows official conventions**
  - [ ] SKILL.md format per https://github.com/anthropics/skills
  - [ ] Plugin structure per https://code.claude.com/docs/en/plugins
  - [ ] Marketplace schema per https://code.claude.com/docs/en/plugin-marketplaces

### Marketplace Entry

- [ ] **/.claude-plugin/marketplace.json updated**
  - [ ] Plugin entry added with `name` and `source`
  - [ ] Optional fields populated (description, version, keywords)
  - [ ] Version matches CHANGELOG
  - [ ] Source path is correct

---

## Product-Type Specific Checks

### Skills (within Plugins)

- [ ] SKILL.md has valid YAML frontmatter
- [ ] SKILL.md defines all modes
- [ ] Each mode has:
  - [ ] Trigger phrase
  - [ ] Workflow steps
  - [ ] Output format
- [ ] Examples demonstrate each mode
- [ ] Pattern files exist for complex workflows

### MCP Servers (Future)

- [ ] Server manifest valid
- [ ] Tool definitions complete
- [ ] Permission requirements documented
- [ ] Resource access minimal

### Claude Code Plugins

- [ ] `.claude-plugin/plugin.json` valid JSON
- [ ] `name` is kebab-case
- [ ] `skills/` directory contains valid skills
- [ ] Optional: `commands/`, `agents/`, `hooks/` directories if used

---

## Listing Approval Workflow

1. **Developer Self-Review**
   - Complete checklist above
   - Fix any failures

2. **Peer Review** (if applicable)
   - Second person verifies checklist
   - Tests at least one fixture

3. **Security Review**
   - Verify no secrets
   - Verify data handling documentation
   - Verify scope boundaries

4. **Final Approval**
   - All checklist items pass
   - `/.claude-plugin/marketplace.json` entry correct
   - CHANGELOG updated

---

## Post-Listing Monitoring

After a product is listed:

- [ ] Monitor for user-reported issues
- [ ] Track validation status (re-validate quarterly)
- [ ] Update on platform changes
- [ ] Respond to security disclosures within 48 hours

---

## Validation Commands

```bash
# Validate plugin structure
/plugin validate ./products/claude-code-plugins/<plugin-name>

# Add marketplace locally
/plugin marketplace add ./

# Install plugin from marketplace
/plugin install <plugin-name>@ninobyte-marketplace
```

---

## Checklist Sign-Off

```
Product: _______________
Version: _______________
Date: _______________
Reviewer: _______________

[ ] All required checks pass
[ ] Security review completed
[ ] Official conventions validated
[ ] Ready for marketplace listing

Signature: _______________
```
