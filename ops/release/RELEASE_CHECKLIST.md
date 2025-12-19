# Release Checklist

Quality gates for releasing Ninobyte products.

---

## Pre-Release Checklist

### Documentation
- [ ] README.md is complete and accurate
- [ ] SKILL.md (for skill packs) is complete with all modes documented
- [ ] CHANGELOG.md is updated with version changes
- [ ] All `[UNVERIFIED]` tags have corresponding validation tasks
- [ ] Installation instructions tested and working

### Testing
- [ ] `tests/fixtures/` contains test inputs
- [ ] `tests/goldens/` contains expected outputs
- [ ] Verification harness README explains how to run tests
- [ ] Manual testing completed for all documented modes
- [ ] Edge cases documented and tested

### Security
- [ ] No secrets in any committed files
- [ ] SECURITY.md is present and current
- [ ] THREAT_MODEL.md reviewed for new attack surfaces
- [ ] Safe logging patterns followed
- [ ] Dependencies audited (if any)

### Validation
- [ ] VALIDATION_LOG.md updated with any new validations
- [ ] Platform-dependent features either validated or marked `[UNVERIFIED]`
- [ ] Official source URLs checked and accessible

### Marketplace (if applicable)
- [ ] `marketplace/marketplace.json` updated with new product/version
- [ ] `marketplace/qa/QA_CHECKLIST.md` criteria met
- [ ] Listing metadata complete and accurate

### Version Management
- [ ] Version number incremented appropriately
- [ ] CHANGELOG.md entry added
- [ ] COMPATIBILITY_MATRIX.md updated
- [ ] Git tag created (after merge)

---

## Release Process

1. **Prepare**
   - Complete all checklist items above
   - Create release branch: `release/v{version}`

2. **Review**
   - Self-review all changes
   - Security review for new features
   - Documentation review

3. **Test**
   - Run verification harness
   - Manual smoke test
   - Cross-platform test if applicable

4. **Merge**
   - Merge to main branch
   - Verify CI passes

5. **Tag**
   - Create annotated git tag: `git tag -a v{version} -m "Release v{version}"`
   - Push tag: `git push origin v{version}`

6. **Document**
   - Update any external documentation
   - Announce release if applicable

---

## Post-Release

- [ ] Verify release artifacts are correct
- [ ] Monitor for immediate issues
- [ ] Update roadmap/backlog
- [ ] Schedule next validation review

---

## Rollback Procedure

If critical issues discovered post-release:

1. Document the issue
2. Create hotfix branch from previous release tag
3. Fix and test
4. Follow release process for patch version
5. Post-mortem and update THREAT_MODEL if security-related
