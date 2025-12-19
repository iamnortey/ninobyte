# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.2] - 2025-12-19

### Why v0.1.2 Exists

"Formatting Determinism + Distribution Maturity" — ensures Architecture Review output passes strict formatting validation, and eliminates drift between canonical and plugin-bundled skill copies.

### Added

- **Sync/Check Tool** (`scripts/ops/sync_plugin_skills.py`)
  - `--check` mode for CI: detect drift, exit non-zero if found
  - `--sync` mode for developers: copy canonical → plugin bundle
  - Derives version dynamically from canonical SKILL.md

- **CI Drift Gate**
  - `validate_artifacts.py` now includes hard drift check
  - CI fails with clear error if canonical and plugin copies diverge
  - Remediation instructions included in output

- **Format Enforcement** (Architecture Review mode)
  - All 9 required headings validated via regex
  - Concerns table header: `| Priority | Concern | Impact | Recommendation |`
  - Risks table header: `| Risk | Likelihood | Impact | Mitigation |`
  - CRITICAL flags enforced for known security issues

### Changed

- **SKILL.md Output Format**
  - Risks section changed from bullet list to markdown pipe table
  - All headings now explicitly require `##`/`###` tokens
  - Added Format Enforcement Rules section

- **Legacy Skill-Packs**
  - `products/skill-packs/` now has explicit deprecation marker
  - Removal planned for v0.2.0

### Fixed

- Plugin copy synced to canonical v0.1.2 (was at v0.1.1)
- Eliminated silent drift between distribution surfaces

---

## [0.1.1] - 2025-12-19

### Why v0.1.1 Exists

This release aligns the repository with **official Anthropic conventions** for Skills, Claude Code plugins, and marketplaces. All platform-dependent structures have been validated against official documentation.

### Added

- **Official Skills Convention**
  - Canonical skill location at `skills/senior-developer-brain/`
  - YAML frontmatter with required `name` and `description` fields (per https://github.com/anthropics/skills)
  - Security Policy section with mandatory enforcement rules

- **Claude Code Plugin Package**
  - Official plugin at `products/claude-code-plugins/ninobyte-senior-dev-brain/`
  - `.claude-plugin/plugin.json` manifest (per https://code.claude.com/docs/en/plugins-reference)
  - Self-contained skill bundle

- **Official Marketplace**
  - Marketplace at `.claude-plugin/marketplace.json` (per https://code.claude.com/docs/en/plugin-marketplaces)
  - Official schema with `name`, `owner`, `plugins[]` structure

- **CI Hardening**
  - `scripts/ci/validate_artifacts.py` validation script
  - Plugin structure validation
  - SKILL.md frontmatter validation
  - Security pattern scanning

- **Validation Evidence**
  - VL-20251219-003: SKILL.md format validated
  - VL-20251219-004: Plugin structure validated
  - VL-20251219-005: Marketplace schema validated

### Changed

- **Branch renamed** from `master` to `main`
- **Marketplace location** moved from `marketplace/marketplace.json` to `.claude-plugin/marketplace.json`
- **Skill pack location** canonical source now at `skills/` (legacy location deprecated)
- **SKILL.md format** now includes YAML frontmatter and Security Assessment section
- **Golden files** updated to verify security policy enforcement
- **CI workflow** updated to validate official conventions

### Deprecated

- `products/skill-packs/senior-developer-brain/` — Use `skills/senior-developer-brain/` instead
- `marketplace/marketplace.json` — Use `.claude-plugin/marketplace.json` instead

### Security

- Added mandatory Security Policy to SKILL.md
- JWT in localStorage now flagged as CRITICAL (not HIGH)
- Single points of failure flagged as CRITICAL
- Security Assessment section required in Architecture Review output

---

## [0.1.0] - 2025-12-19

### Added
- **Governance Layer**
  - PROJECT_INSTRUCTIONS.md with mission, policies, validation requirements
  - PINNED_PROJECT_PROMPT.md execution contract
  - VALIDATION_LOG.md for official source tracking
  - THREAT_MODEL.md baseline security model
  - RELEASE_CHECKLIST.md quality gates

- **First Product: Senior Developer's Brain (Skill Pack)**
  - SKILL.md execution contract with 5 operating modes
  - Architecture Review, Implementation Planning, Code Review, Incident Triage, ADR Writer
  - Pattern files: architecture-review-checklist, code-review-checklist, incident-triage-runbook
  - Example files demonstrating usage
  - Test fixtures and golden files for verification

- **Marketplace**
  - marketplace.json catalog structure [UNVERIFIED schema]
  - QA_CHECKLIST.md acceptance criteria

- **Infrastructure**
  - .github/workflows/ci.yml minimal pipeline
  - .gitignore with security patterns
  - .editorconfig for consistency
  - SECURITY.md policy document

### Security
- Established no-secrets-committed policy
- Created threat model covering prompt injection, tool abuse, exfiltration
- Documented safe logging patterns

### Notes
- Platform-specific schemas marked [UNVERIFIED] pending official source validation
- See VALIDATION_LOG.md VL-20251219-001 for validation checklist
