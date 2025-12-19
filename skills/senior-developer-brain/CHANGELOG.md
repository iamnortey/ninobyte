# Changelog — Senior Developer's Brain

All notable changes to this skill will be documented here.

---

## [0.1.1] - 2025-12-19

### Why v0.1.1 Exists

Aligns skill with official Anthropic conventions and adds mandatory security policy enforcement.

### Added
- **YAML Frontmatter** with `name` and `description` (per https://github.com/anthropics/skills)
- **Mandatory Security Policy** section with non-negotiable rules
- **Security Assessment** section in Architecture Review output format
- **Explicit security enforcement rules**:
  - Never approve hand-rolled authentication
  - Never approve plaintext password storage
  - Always flag JWT in localStorage as CRITICAL
  - Always flag single points of failure as CRITICAL

### Changed
- Architecture Review output now includes `### Security Assessment` section
- JWT in localStorage severity raised from HIGH to CRITICAL
- Single points of failure severity raised from HIGH to CRITICAL
- Golden file updated to verify security policy enforcement

### Security
- Security issues must now be flagged at correct severity per policy
- Skill explicitly refuses to approve insecure patterns
- Recommendations must include established secure alternatives

---

## [0.1.0] - 2025-12-19

### Added
- Initial release of Senior Developer's Brain skill
- **5 Operating Modes**:
  - Architecture Review
  - Implementation Planning
  - Code Review
  - Incident Triage
  - ADR Writer
- **Pattern Files**:
  - architecture-review-checklist.md
  - code-review-checklist.md
  - incident-triage-runbook.md
- **Examples**:
  - Vague request transformation
  - Code review demonstration
- **Tests**:
  - Initial fixture and golden files

### Security
- Documented explicit refusals (secrets, credentials, security bypass)
- Safe logging pattern recommendations

### Notes
- Claude Code installation method marked [UNVERIFIED] in v0.1.0
