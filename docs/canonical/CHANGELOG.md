# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.8.8] - 2025-12-23

### Added

- **Lexicon Packs Lockfiles** (`products/lexicon-packs/`)
  - Supply-chain auditability via deterministic pack lockfiles
  - New `lockfile.py` module with generation and verification
  - `python -m lexicon_packs lock --pack <path>` — Print lockfile JSON to stdout
  - `python -m lexicon_packs lock --pack <path> --write` — Write `pack.lock.json`
  - `python -m lexicon_packs verify --pack <path>` — Verify pack matches lockfile
  - `--fixed-time` flag for deterministic timestamps (ISO 8601)

- **Lockfile Schema v1.0.0**
  - `lock_schema_version` — Lockfile schema version
  - `generated_at_utc` — Timestamp (deterministic with `--fixed-time`)
  - `pack_id` — Lexicon Pack ID
  - `pack_schema_version` — Pack schema version
  - `pack_json_sha256` — SHA256 of canonical pack.json
  - `entries_file` — Relative path to entries file
  - `entries_file_sha256` — SHA256 of raw entries file bytes
  - `normalized_entries_sha256` — SHA256 of normalized entries (order-independent)
  - `entry_count` — Total entry count
  - `fields_signature` — SHA256 of field names in order

- **Lockfile CI Gate**
  - `scripts/ci/validate_lexicon_packs_lockfiles.py`
  - Wired into `validate_artifacts.py` (v0.8.8)
  - Fails on missing, invalid, or drifted lockfiles

- **Lockfile Test Suite** (43 tests)
  - File and entries hashing
  - Determinism (byte-for-byte stable output)
  - Schema validation
  - Drift detection
  - CLI commands
  - Path traversal protection

- **Ghana Core Lockfile**
  - Committed `pack.lock.json` with fixed timestamp `2025-01-01T00:00:00Z`

### Security

- Path traversal protection via `resolve()` + `relative_to()` pattern
- Absolute `entries_path` rejected at schema validation
- Lockfile verification prevents silent drift

---

## [0.8.7] - 2025-12-23

### Added

- **ContextCleaner ↔ Lexicon Packs Integration** (`products/context-cleaner/`)
  - New `lexicon-map` subcommand: deterministic redaction using Lexicon Packs
  - `python -m ninobyte_context_cleaner lexicon-map --pack <path>` — Generate redaction map
  - Loads Lexicon Pack entries as deterministic entity list
  - Produces JSON report with match counts, examples, and statistics
  - `--apply` flag to include redacted text in output
  - `--fixed-time` flag for deterministic testing
  - Case-insensitive matching with Unicode casefolding
  - Word boundary matching (no partial word matches)
  - Path traversal protection on `--pack` and `--input` paths
  - Schema validation: rejects invalid pack schemas

- **Lexicon Map Output Schema v1.0.0**
  - `schema_version` — Output schema version
  - `generated_at_utc` — Timestamp (deterministic with `--fixed-time`)
  - `pack_id` — Lexicon Pack ID
  - `pack_entries_sha256` — Deterministic hash of pack entries
  - `match_strategy` — Matching strategy used (casefolded_exact)
  - `matches` — Sorted list of matched terms with counts
  - `summary` — Statistics (total entries, matched, occurrences)
  - `redaction_preview` — Example replacements with context
  - `redacted_text` — Redacted text (only with `--apply`)

- **Lexicon Map Test Suite** (24 tests)
  - Pack loading and SHA256 computation
  - Term matching and counting
  - Determinism (byte-for-byte stable output)
  - Apply mode produces expected redacted text
  - Path traversal protection
  - Invalid pack schema rejection
  - Invalid CSV rejection

- **Documentation Updates**
  - ContextCleaner README: `lexicon-map` command documentation
  - Lexicon Packs README: ContextCleaner integration section

### Security

- No network access in lexicon-map command
- No shell execution
- No file writes (stdout only)
- Path traversal protection on all paths
- Strict schema validation

### PRs Included

- #XX: feat(contextcleaner): lexicon-map command (Lexicon Packs integration)

---

## [0.8.6] - 2025-12-23

### Added

- **Lexicon Packs MVP** (`products/lexicon-packs/`)
  - New product: Deterministic vocabulary pack validation and loading
  - Pack schema v1.0.0 with strict validation (unknown keys rejected)
  - `python -m lexicon_packs validate` — Validate pack against schema
  - `python -m lexicon_packs show` — Display pack metadata with deterministic JSON
  - Canonical JSON output with sorted keys, SHA256 hashing
  - Path traversal protection on all file operations

- **Ghana Core Pack** (`packs/ghana-core/`)
  - First real pack: 30 entries (15 cities, 10 regions, 5 landmarks)
  - CC0-1.0 licensed, public domain geographic data
  - Language: en-GH (English - Ghana)

- **Lexicon Packs Test Suite**
  - 38 tests across 3 modules
  - `test_validate_pack.py` — Schema and CSV validation (14 tests)
  - `test_load_pack.py` — Pack loading and entry structure (11 tests)
  - `test_determinism.py` — Byte-for-byte output stability (13 tests)

- **Lexicon Packs Security**
  - `SECURITY.md` — Security policy with contributor guidelines
  - "What Lexicon Packs is NOT" section in README
  - No network, no shell, no file writes, pure stdlib

### PRs Included

- #62: Lexicon Packs MVP (schema + validator + loader + ghana-core pack)

---

## [0.8.5] - 2025-12-23

### Added

- **ContextCleaner Release-Grade Documentation**
  - `SECURITY.md` — Security policy with contributor guidelines
  - "What ContextCleaner is NOT" section in README (non-goals table)
  - Security guarantees: no network, no shell, no file writes, no OCR

### Fixed

- Fixed pytest return warnings in `test_smoke_script_contract.py`
  - Renamed imported smoke test functions to avoid pytest auto-discovery
  - 17 tests now run without warnings

### PRs Included

- #60: ContextCleaner v0.8.5 release surface (contract + docs)

---

## [0.8.4] - 2025-12-23

### Added

- **OpsPack MVP** (`products/opspack/`)
  - New product: Deterministic incident triage and log analysis toolkit
  - `python -m opspack triage` — Analyze incident logs with structured JSON output
  - Stateless redaction primitives for sensitive data:
    - AWS keys, Slack tokens, Bearer tokens, GitHub tokens, JWTs
    - IPv4/IPv6 addresses, UUIDs, email addresses
    - Long hex strings (32+ chars)
  - Deterministic output: sorted JSON keys, stable formatting, reproducible results
  - Security guarantees enforced by static analysis:
    - No network imports (AST-verified)
    - No shell execution (AST-verified)
    - Redaction applied by default

- **OpsPack Test Suite**
  - 68 tests across 5 modules
  - `test_cli_smoke.py` — CLI functionality verification
  - `test_redaction_tokens.py` — Token pattern redaction (11 tests)
  - `test_redaction_ip.py` — IP address redaction (14 tests)
  - `test_determinism.py` — Output reproducibility (5 tests)
  - `test_no_network_shell.py` — Static security assertions (6 tests)

### PRs Included

- #56: OpsPack MVP scaffold + triage CLI + redaction + tests
- #57: Evidence closure for PR #56

---

## [0.8.3] - 2025-12-22

### Added

- **Evidence Integrity System**
  - Canonical JSON receipts with SHA256 integrity verification (`ops/evidence/`)
  - `scripts/ops/capture_pr_merge_receipt.py` for PR merge evidence capture
  - `scripts/ops/log_validation.py` for validation log entries
  - `scripts/ops/log_decision.py` for ADR decision receipts
  - `scripts/ops/build_evidence_index.py` for deterministic INDEX generation
  - `scripts/ops/canonicalize_json.py` for reproducible JSON formatting

- **CI Governance Gates**
  - `validate_evidence_integrity.py` — SHA256 verification of all canonical files
  - `validate_validation_log_links.py` — Cross-link enforcement for validation receipts
  - `validate_adr_links.py` — Cross-link enforcement for ADR decision receipts
  - `validate_evidence_index.py` — Deterministic INDEX byte-for-byte check
  - `validate_no_os_artifacts.py` — macOS `.DS_Store` drift prevention

- **ADR Governance**
  - ADR template at `docs/adr/TEMPLATE.md`
  - First ADR: `ADR-20251223-025526-adr-evidence-receipts-and-cross-link-governance.md`
  - Decision receipts linked to ADRs via canonical JSON

### Changed

- Evidence receipts now use canonical JSON format (sorted keys, 2-space indent)
- All evidence files have companion `.sha256` checksum files
- CI runs evidence integrity checks on every push/PR

### PRs Included

- #39: Deterministic skill pack builder + CI gate
- #40-#41: Repo-root pytest stabilization
- #42-#43: CI run evidence capture
- #44-#45: Canonical JSON receipts with SHA256
- #46: Evidence integrity gate + relative paths
- #47: Validator hardening + PR receipt backfill
- #48: Single-command capture+verify workflow
- #49: Validation log CLI with canonical receipts
- #50: Validation log cross-link enforcement
- #51: ADR receipts and cross-link governance
- #52: Deterministic evidence index
- #53: macOS artifact drift prevention

---

## [0.8.0] - 2025-12-21

### Added

- **ContextCleaner Core** (`products/context-cleaner/`)
  - JSONL output with schema v1 contract
  - Redactor with PII pattern matching
  - Lexicon-based term normalization
  - Table normalizer for structured data
  - PDF extractor with pdfplumber integration
  - CLI entrypoints: `ninobyte-context-cleaner`, `context-cleaner`

- **AirGap + ContextCleaner Integration**
  - `context_cleaner_adapter.py` bridges AirGap and ContextCleaner
  - Stdlib-only AirGap runtime (no third-party deps at runtime)
  - Contract policy tests for JSONL compatibility

### Changed

- CI now includes ContextCleaner test matrix (core, PDF, wheel audit)
- AirGap isolated tests prove stdlib-only runtime

---

## [0.7.0] - 2025-12-21

### Added

- **Senior Developer's Brain v1.0.0** — Major skill update with enhanced modes
- Release workflow for skill pack distribution

---

## [0.6.0] - 2025-12-20

### Added

- **ContextCleaner MVP** — Initial implementation
- PDF parsing with pdfplumber
- JSONL schema v1 contract

---

## [0.2.3] - 2025-12-20

### Fixed

- Additional AirGap security hardening

---

## [0.2.2] - 2025-12-20

### Fixed

- AirGap test coverage improvements

---

## [0.2.1] - 2025-12-20

### Fixed

- Windows-safe blocked path patterns in AirGap (#9)

---

## [0.2.0] - 2025-12-20

### Added

- **AirGap MCP Server** (`products/mcp-servers/ninobyte-airgap/`)
  - `list_dir` — Directory listing with symlink escape prevention
  - `read_file` — File reading with size limits, offset/limit, actual bytes audited
  - `search_text` — Text search using ripgrep or Python fallback
  - `redact_preview` — Stateless string redaction (no file I/O)
  - Security: deny-by-default, blocked patterns, path canonicalization
  - JSONL audit logging with path redaction
  - 60+ unit tests

- **Vertical Playbook v2.0** (`docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md`)
  - Locked 9 verticals strategy
  - 4-core product stack mapping

- **CI Validation**
  - AirGap networking import prohibition (AST-enforced)
  - AirGap shell=True prohibition (AST-enforced)

### Security

- No network imports in AirGap code
- No shell=True anywhere in AirGap
- Symlink escape prevention via canonicalization
- Traversal attack prevention

---

## [0.1.5] - 2025-12-19

### Fixed

- CI workflow refinements

---

## [0.1.4] - 2025-12-19

### Fixed

- Marketplace source path fix

---

## [0.1.3] - 2025-12-19

### Fixed

- Claude Code marketplace hardening

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
