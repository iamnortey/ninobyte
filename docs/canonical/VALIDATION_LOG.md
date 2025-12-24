# Validation Log

Evidence trail for all official source validations.

---

## Official Sources

| Source | URL | Purpose |
|--------|-----|---------|
| Anthropic GitHub | https://github.com/anthropics | SDKs, examples, official implementations |
| **Anthropic Skills Repo** | https://github.com/anthropics/skills | **Official SKILL.md format + examples** |
| Claude Platform Docs | https://platform.claude.com/docs/en/home | API docs, capabilities, best practices |
| **Claude Code Plugins** | https://code.claude.com/docs/en/plugins | **Official plugin structure** |
| **Claude Code Plugin Reference** | https://code.claude.com/docs/en/plugins-reference | **plugin.json manifest schema** |
| **Claude Code Marketplaces** | https://code.claude.com/docs/en/plugin-marketplaces | **marketplace.json schema** |
| Anthropic Engineering | https://www.anthropic.com/engineering | Technical blog, architecture insights |
| **Agent Skills Overview** | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills | **Skills architecture + use cases** |
| Anthropic Research | https://www.anthropic.com/research | Research papers, model capabilities |
| Anthropic Learn | https://www.anthropic.com/learn | Tutorials, guides |
| Claude Resources | https://claude.com/resources/use-cases | Use cases, examples |
| Anthropic Skilljar | https://anthropic.skilljar.com/ | Official training, certifications |

---

## Entry Template

```markdown
### VL-YYYYMMDD-###

**Date**: YYYY-MM-DD
**Author**: [name/agent]
**Topic**: [what was validated]

**Sources Checked**:
- URL: [url]
- GitHub Ref: [repo/commit/tag if applicable]

**Findings**:
[What was confirmed or discovered]

**Impact**:
[How this affects our implementation]

**Status**: VALIDATED | UNVERIFIED | CONFLICT_DETECTED

**Action Required**:
[Files to update, follow-ups needed]
```

---

## Entries

### VL-20251219-001

**Date**: 2025-12-19
**Author**: Claude Agent (initial setup)
**Topic**: Claude Skills, MCP, and Claude Code plugin schema validation

**Sources Checked**:
- Not yet validated (initial repo setup)

**Findings**:
Initial repo creation. Platform-specific schemas for Skills, MCP servers, and Claude Code plugins have NOT been validated against current official documentation.

**Impact**:
- `marketplace/marketplace.json` schema is `[UNVERIFIED]`
- Claude Code installation instructions in skill pack are `[UNVERIFIED]`
- MCP server structure guidelines are `[UNVERIFIED]`

**Status**: UNVERIFIED

**Action Required**:
Validation Checklist:
- [ ] Confirm Claude Skills format/structure (check https://platform.claude.com/docs/en/home)
- [ ] Confirm MCP server specification (check https://github.com/anthropics for MCP repos)
- [ ] Confirm Claude Code plugin/extension format (check Claude Code docs)
- [ ] Confirm marketplace distribution patterns if any official guidance exists
- [ ] Update `marketplace/marketplace.json` with validated schema
- [ ] Update skill pack installation docs with validated instructions
- [ ] Create VL-YYYYMMDD-002 with validation results

---

### VL-20251219-002

**Date**: 2025-12-19
**Author**: Claude Agent (research-based validation)
**Topic**: Official Anthropic specifications for Skills, MCP, and Claude Code extensions

**Sources Checked**:
- GitHub: https://github.com/anthropics (knowledge of public repositories)
- MCP Specification: https://spec.modelcontextprotocol.io/
- Knowledge base through training data

**Findings**:

1. **Claude Skills**
   - No official public specification exists for standalone "Skills"
   - Skills are platform-internal configurations, not a public SDK
   - Custom behaviors for Claude are implemented via: system prompts, MCP servers, or API integrations
   - **Recommendation**: Position Ninobyte "Skill Packs" as "Claude Enhancement Packs" or "Prompt Engineering Patterns" rather than official Skills

2. **Model Context Protocol (MCP)**
   - **OFFICIAL** specification exists: https://spec.modelcontextprotocol.io/
   - Reference implementation: https://github.com/anthropics (MCP-related repos)
   - Standard JSON-RPC 2.0 communication protocol
   - Server structure follows official specification
   - **This is the RECOMMENDED way to extend Claude with tools**

3. **Claude Code Extensions**
   - No official plugin/extension API has been publicly released
   - Available mechanisms: Slash commands, hooks, MCP integration
   - Claude Code is primarily extended via MCP servers, not plugins

4. **Marketplace Distribution**
   - No official Anthropic marketplace exists for Skills or Claude Code extensions
   - MCP servers distributed via: GitHub repositories, package managers (npm, PyPI)
   - No standard distribution format exists

**Impact**:
- Ninobyte "Skill Packs" are a **CUSTOM abstraction**, not an official Anthropic format
- Only MCP servers align with official specifications
- "Claude Code Plugins" directory represents custom configurations, not official plugins
- `marketplace/marketplace.json` schema is **CUSTOM**, not standards-based
- All platform-specific installation instructions remain `[UNVERIFIED]` pending manual web validation

**Status**: PARTIALLY_VALIDATED

**Action Required**:
- [ ] Manual web validation of sources (automated fetch unavailable)
- [ ] Consider renaming "skill-packs" to "enhancement-packs" or "prompt-patterns"
- [ ] Add MCP server conformance validation when MCP servers are built
- [ ] Document custom nature of marketplace catalog
- [ ] Add prominent disclaimer that only MCP follows official specs
- [ ] Create MCP validation checklist per official specification

**Notes**:
This validation was performed using knowledge base information. Direct web access to confirm current state of official documentation was not available. Manual verification of URLs is required before marking as fully VALIDATED.

---

### VL-20251219-003

**Date**: 2025-12-19
**Author**: Claude Agent (live web validation)
**Topic**: Official SKILL.md format validation

**Sources Checked**:
- URL: https://github.com/anthropics/skills
- URL: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

**Findings**:

**SKILL.md Format (VALIDATED)**:
1. Skills are **directories** containing a `SKILL.md` file
2. YAML frontmatter is **REQUIRED** with exactly TWO mandatory fields:
   - `name`: Unique identifier (lowercase, hyphens for spaces)
   - `description`: Complete description of what the skill does and when to use it
3. Format structure:
   ```
   ---
   name: skill-identifier
   description: What this skill does and when to use it
   ---

   # Skill Name

   [Instructions, examples, and guidelines in markdown]
   ```
4. Skills can include supporting reference files and scripts alongside SKILL.md
5. Progressive disclosure: metadata loads at startup, body loads when relevant, additional files load on demand

**Platform Support**:
- Claude.ai (Projects)
- Claude Code
- Claude Agent SDK
- Claude Developer Platform

**Impact**:
- Our existing SKILL.md structure needs YAML frontmatter with `name` and `description` fields
- v0.1 SKILL.md is missing required frontmatter - MUST BE UPDATED
- Skill directory naming should match the `name` field (lowercase, hyphenated)

**Status**: VALIDATED

**Action Required**:
- [x] Update skills/senior-developer-brain/SKILL.md with proper frontmatter
- [x] Ensure `name: senior-developer-brain` and appropriate `description`

---

### VL-20251219-004

**Date**: 2025-12-19
**Author**: Claude Agent (live web validation)
**Topic**: Official Claude Code Plugin structure validation

**Sources Checked**:
- URL: https://code.claude.com/docs/en/plugins
- URL: https://code.claude.com/docs/en/plugins-reference

**Findings**:

**Plugin Directory Structure (VALIDATED)**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata (REQUIRED)
├── commands/                 # Custom slash commands (optional)
├── agents/                   # Custom agents (optional)
├── skills/                   # Agent Skills (optional)
│   └── my-skill/
│       └── SKILL.md
├── hooks/                    # Event handlers (optional)
└── LICENSE, README.md, etc.
```

**plugin.json Required Fields**:
- `name` (string): Unique identifier in kebab-case - **REQUIRED**

**plugin.json Recommended Fields**:
- `version` (string): Semantic versioning
- `description` (string): Purpose explanation
- `author` (object): `{ "name": "...", "email": "...", "url": "..." }`
- `homepage` (string): Documentation URL
- `repository` (string): Source code URL
- `license` (string): License identifier (e.g., "MIT")
- `keywords` (array): Discovery tags

**Path Requirements**:
- All paths in plugin.json must be relative and begin with `./`
- Use `${CLAUDE_PLUGIN_ROOT}` for dynamic path resolution in hooks/MCP configs

**Impact**:
- v0.1 had no plugin structure - MUST CREATE
- Plugin must be at: `products/claude-code-plugins/ninobyte-senior-dev-brain/`
- Plugin manifest at: `.claude-plugin/plugin.json`
- Skills bundled inside plugin at: `skills/senior-developer-brain/`

**Status**: VALIDATED

**Action Required**:
- [x] Create plugin directory structure
- [x] Create `.claude-plugin/plugin.json` with required fields
- [x] Bundle skill into plugin's `skills/` directory

---

### VL-20251219-005

**Date**: 2025-12-19
**Author**: Claude Agent (live web validation)
**Topic**: Official Plugin Marketplace schema validation

**Sources Checked**:
- URL: https://code.claude.com/docs/en/plugin-marketplaces

**Findings**:

**Marketplace File Location (VALIDATED)**:
- File MUST be at: `.claude-plugin/marketplace.json` (repository root)

**Required Fields**:
1. `name` (string): Marketplace identifier (kebab-case, no spaces)
2. `owner` (object): `{ "name": "...", "email": "..." }`
3. `plugins` (array): List of available plugins

**Plugin Entry Required Fields**:
- `name` (string): Plugin identifier (kebab-case)
- `source` (string): Location (relative path, GitHub repo, or git URL)

**Optional Marketplace Fields**:
- `metadata.description`: Brief marketplace overview
- `metadata.version`: Marketplace version tracking
- `metadata.pluginRoot`: Base path for relative plugin sources

**Optional Plugin Entry Fields**:
- `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`
- `tags` (array): Discovery tags
- `strict` (boolean): Whether plugin.json validation is required

**Installation Commands**:
- Add marketplace: `/plugin marketplace add owner/repo` or `/plugin marketplace add ./path`
- Install plugin: `/plugin install plugin-name@marketplace-name`

**Impact**:
- v0.1 had custom `marketplace/marketplace.json` - MUST MIGRATE to `.claude-plugin/marketplace.json`
- Schema was completely wrong - MUST USE OFFICIAL SCHEMA
- Old marketplace should be deprecated with pointer to new location

**Status**: VALIDATED

**Action Required**:
- [x] Create `.claude-plugin/marketplace.json` with official schema
- [x] Deprecate `marketplace/marketplace.json`
- [x] Update installation tutorials

---

### VL-20251219-006

**Date**: 2025-12-19
**Author**: Claude Agent (v0.1.2 release)
**Topic**: Formatting Determinism + Drift Enforcement

**Sources Checked**:
- Internal: `skills/senior-developer-brain/SKILL.md`
- Internal: `scripts/ci/validate_artifacts.py`
- Internal: `scripts/ops/sync_plugin_skills.py`

**Findings**:

1. **Format Enforcement (v0.1.2)**
   - Architecture Review output format now strictly validated
   - 9 required markdown headings checked via regex
   - Concerns table: `| Priority | Concern | Impact | Recommendation |`
   - Risks table: `| Risk | Likelihood | Impact | Mitigation |`
   - CRITICAL flags enforced for: JWT localStorage, Single EC2, Shared PostgreSQL

2. **Drift Prevention**
   - `sync_plugin_skills.py` created with `--check` and `--sync` modes
   - CI now fails if canonical and plugin copies diverge
   - No auto-fix in CI; developers must run `--sync` locally

3. **Distribution Surfaces**
   - Canonical: `skills/senior-developer-brain/` (source of truth)
   - Plugin: `products/claude-code-plugins/ninobyte-senior-dev-brain/skills/senior-developer-brain/` (synced copy)
   - Legacy: `products/skill-packs/` (deprecated, removal in v0.2.0)

**Impact**:
- CI is now a hard gate against drift
- Output format is deterministic and machine-verifiable
- No new external platform assumptions introduced

**Status**: VALIDATED

**Action Required**:
- None. All v0.1.2 changes are internal enforcement mechanisms.

---

### 2025-12-24 17:27:51Z

**Topic**: Evidence Index Determinism Contract v0.6.0
**Status**: VALIDATED
**Priority**: HIGH
**Source**: governance contract upgrade

**Changes Validated**:
- Canonical ordering: `(kind, id, canonical_path)` - stable across environments
- Removed `generated_at_utc` from index artifacts for determinism
- Added `--print` mode for diff verification
- Added contract-grade regression tests

**Gates Passed**:
- validate_artifacts.py: PASSED
- pytest: 92 passed
- evidence index --check: byte-for-byte match
- determinism tests: 4/4 passed
- --print diff: identical

**Receipt**: `ops/evidence/validation/validation_20251224_172751_evidence_index_v0.6.0.canonical.json`

---

## Pending Validations

| ID | Topic | Priority | Assigned |
|----|-------|----------|----------|
| VL-20251219-001 | Skills/MCP/Plugin schemas | HIGH | ✅ RESOLVED by VL-20251219-003/004/005 |
| VL-20251219-002 | Manual web verification | HIGH | ✅ RESOLVED by VL-20251219-003/004/005 |
| 2025-12-23 01:59:16Z | Evidence engine now covers decisions | verified | medium | internal governance decision | `ops/evidence/validation/validation_20251223_015916_2e080e8.canonical.json` |
