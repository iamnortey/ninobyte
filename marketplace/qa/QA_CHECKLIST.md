# Marketplace QA Checklist

Quality assurance gates for products in the Ninobyte marketplace.

---

## Pre-Listing Checklist

Every product must pass these checks before being added to `marketplace.json`.

### Documentation

- [ ] **README.md exists** and includes:
  - [ ] Product description
  - [ ] Installation instructions
  - [ ] Usage examples
  - [ ] Known limitations
  - [ ] Version information

- [ ] **Primary contract exists** (SKILL.md for skill packs, manifest for others)
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
  - [ ] Platform-dependent claims either validated or marked [UNVERIFIED]

- [ ] **[UNVERIFIED] tags present where needed**
  - [ ] All unvalidated platform claims marked
  - [ ] Validation checklist created for pending items

### Marketplace Entry

- [ ] **marketplace.json updated**
  - [ ] Product entry added/updated
  - [ ] All required fields populated
  - [ ] Version matches CHANGELOG
  - [ ] Paths are correct

- [ ] **Tags are appropriate**
  - [ ] Relevant to product functionality
  - [ ] Consistent with existing tag vocabulary

---

## Product-Type Specific Checks

### Skill Packs

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

### Claude Code Plugins (Future)

- [ ] Plugin manifest valid
- [ ] Hook definitions complete
- [ ] Permission requirements documented

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
   - Marketplace.json entry correct
   - CHANGELOG updated

---

## Post-Listing Monitoring

After a product is listed:

- [ ] Monitor for user-reported issues
- [ ] Track validation status (re-validate quarterly)
- [ ] Update on platform changes
- [ ] Respond to security disclosures within 48 hours

---

## Checklist Sign-Off

```
Product: _______________
Version: _______________
Date: _______________
Reviewer: _______________

[ ] All required checks pass
[ ] Security review completed
[ ] Ready for marketplace listing

Signature: _______________
```
