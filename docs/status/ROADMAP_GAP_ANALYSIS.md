# Roadmap vs Reality Gap Analysis

**Date**: 2025-12-20
**Auditor**: Principal Engineer Assessment
**Playbook**: `docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md` (LOCKED v2.0)

---

## Source Documents Analyzed

| Document | Location | Purpose |
|----------|----------|---------|
| PROJECT_INSTRUCTIONS.md | `docs/canonical/` | Mission, governance, policies |
| VERTICAL_PLAYBOOK_v2_FINAL.md | `docs/canonical/` | Locked 9 verticals, 4 core products |
| VALIDATION_LOG.md | `docs/canonical/` | Platform validation evidence |
| THREAT_MODEL.md | `docs/architecture/` | Security requirements |
| RELEASE_CHECKLIST.md | `ops/release/` | Release quality gates |

---

## Roadmap Alignment Table

### Ninobyte Internal Milestones

| Milestone | Required Components | Status | Proof | Next Action |
|-----------|---------------------|--------|-------|-------------|
| **v0.1.0 - Initial Release** | Repo structure, governance docs | DONE | Tag `v0.1.1` exists | N/A |
| **v0.1.1 - Claude Code Plugin** | SKILL.md, plugin.json, marketplace.json | DONE | CI validation passes | N/A |
| **v0.1.2 - Drift Enforcement** | Sync scripts, CI gates, format validation | DONE | `validate_artifacts.py` | N/A |
| **v0.1.3 - Marketplace Schema** | Official `.claude-plugin/` location | DONE | Tag `v0.1.3` exists | N/A |
| **v0.1.4 - CI Hardening** | Claude Code invariants | DONE | Tag `v0.1.4` exists | N/A |
| **v0.2.0 - AirGap MCP Server** | MCP server, tests, security validation | PARTIAL | Code complete, not committed | Commit + tag |
| **v0.2.1 - OpsPack MVP** | SRE vertical wrapper | NOT STARTED | Playbook defined | Build after v0.2.0 |
| **v0.3.0 - ContextCleaner** | PDF/Excel parsing | NOT STARTED | Playbook defined | Design spec needed |

---

## Vertical Roadmap (Locked 9)

Per the locked playbook, ninobyte owns **4 core products** configured for **9 verticals**:

### 4-Core Product Stack

| Product | Function | Status | Evidence |
|---------|----------|--------|----------|
| **AirGap** | Privacy gate (PII → tokens → rehydrate) | BUILT (uncommitted) | `products/mcp-servers/ninobyte-airgap/` - 60/60 tests pass |
| **ContextCleaner** | Parse format → extract structure | NOT BUILT | No code exists in repo |
| **Lexicon Packs** | Domain terminology injection | STUB | `products/lexicon-packs/README.md` only |
| **MicroEmployees** | Workflow execution + verification | NOT BUILT | No code exists in repo |

### Vertical-to-Product Mapping

| # | Vertical | Label | AirGap | ContextCleaner | Lexicon | MicroEmployee | Status |
|---|----------|-------|--------|----------------|---------|---------------|--------|
| 1 | SRE/DevOps | START HERE | HIGH | MEDIUM | LOW | HIGH | **NEXT** (OpsPack) |
| 2 | Legal | CASH COW | HIGH | HIGH | MEDIUM | MEDIUM | Blocked on ContextCleaner |
| 3 | Healthcare | LONG GAME | HIGH | LOW | HIGH | MEDIUM | Needs PHI patterns |
| 4 | Procurement | MOAT | HIGH | HIGH | LOW | HIGH | Blocked on ContextCleaner |
| 5 | HR | UNIVERSAL | HIGH | LOW | LOW | MEDIUM | Needs ratio preservation |
| 6 | Finance | PREMIUM | HIGH | HIGH | HIGH | MEDIUM | Blocked on ContextCleaner |
| 7 | Legacy Code | $10M PROBLEM | MEDIUM | HIGH | MEDIUM | HIGH | Blocked on COBOL parser |
| 8 | M&A Law | HIGH STAKES | HIGH | HIGH | MEDIUM | MEDIUM | Blocked on Legal |
| 9 | Real Estate | CLEAR WORKFLOW | MEDIUM | HIGH | LOW | MEDIUM | Blocked on ContextCleaner |

### Product Dependency Graph

```
AirGap (BUILT)
    │
    ├── OpsPack MVP (SRE/DevOps) ──► Phase 1 Beachhead
    │
    └── ContextCleaner (NOT BUILT) ──► Unblocks 5 verticals
            │
            ├── DealRoom Sentry (Legal)
            ├── RFP Defender (Procurement)
            ├── AlphaGap (Finance)
            ├── LegacyLift (Legacy Code)
            └── Lease Abstractor (Real Estate)
```

---

## Gap Register

### G-001: AirGap Not Committed
| Attribute | Value |
|-----------|-------|
| **Severity** | P0 - BLOCKING |
| **Component** | `products/mcp-servers/ninobyte-airgap/` |
| **Issue** | Complete implementation exists but is untracked in git |
| **Impact** | v0.2.0 cannot be released; blocks all vertical work |
| **Resolution** | `git add products/mcp-servers/ninobyte-airgap/ && git commit` |
| **Evidence** | `git status -sb` shows `?? products/mcp-servers/ninobyte-airgap/` |
| **Owner** | Solo |
| **ETA** | 1 day |

### G-002: ContextCleaner Not Built
| Attribute | Value |
|-----------|-------|
| **Severity** | P1 - HIGH |
| **Component** | ContextCleaner |
| **Issue** | Core product not implemented; blocks 5 of 9 verticals |
| **Impact** | Legal, Procurement, Finance, Legacy Code, Real Estate verticals blocked |
| **Resolution** | Build MVP with PDF parsing first (most verticals need it) |
| **Evidence** | No `products/contextcleaner/` directory exists |
| **Owner** | Solo |
| **ETA** | 1-2 weeks |

### G-003: Lexicon Packs Stub Only
| Attribute | Value |
|-----------|-------|
| **Severity** | P2 - MEDIUM |
| **Component** | `products/lexicon-packs/` |
| **Issue** | Only README placeholder exists |
| **Impact** | Healthcare and Finance verticals need domain terminology |
| **Resolution** | Define schema, build first pack (clinical or financial) |
| **Evidence** | `products/lexicon-packs/README.md` - no subdirectories |
| **Owner** | Solo |
| **ETA** | Deferred to Phase 3 |

### G-004: MicroEmployees Not Built
| Attribute | Value |
|-----------|-------|
| **Severity** | P2 - MEDIUM |
| **Component** | MicroEmployees |
| **Issue** | Workflow execution layer not implemented |
| **Impact** | SRE, Procurement, Legacy Code verticals need workflow automation |
| **Resolution** | Build after ContextCleaner; extend Senior Dev Brain patterns |
| **Evidence** | No `products/microemployees/` directory exists |
| **Owner** | Solo |
| **ETA** | Deferred to Phase 3+ |

### G-005: Validate Script Changes Uncommitted
| Attribute | Value |
|-----------|-------|
| **Severity** | P1 - HIGH |
| **Component** | `scripts/ci/validate_artifacts.py` |
| **Issue** | Local modifications not staged |
| **Impact** | CI may differ locally vs remote |
| **Resolution** | Commit with AirGap |
| **Evidence** | `git status -sb` shows ` M scripts/ci/validate_artifacts.py` |
| **Owner** | Solo |
| **ETA** | 1 day |

---

## Milestone Completion Metrics

| Version | Components Required | Components Complete | % Complete |
|---------|---------------------|---------------------|------------|
| v0.1.x | 4 (structure, skill, plugin, marketplace) | 4 | 100% |
| v0.2.0 | 3 (MCP server, tests, CI validation) | 3 (uncommitted) | 100%* |
| v0.2.1 | 4 (OpsPack: dir, config, CLI, tests) | 0 | 0% |
| v0.3.0 | 3 (ContextCleaner: PDF, index, rehydrate) | 0 | 0% |

*Code complete but not committed

---

## Critical Path Analysis

```
CURRENT STATE (v0.1.4)
       │
       ▼
┌──────────────────────────────┐
│ GATE 0: Commit AirGap        │ ◄── P0: BLOCKING ALL VERTICALS
│ Evidence: 60/60 tests pass   │
│ Action: git add && commit    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GATE 1: Tag v0.2.0           │
│ Evidence: Clean working tree │
│ Action: git tag -a v0.2.0    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GATE 2: OpsPack MVP          │ ◄── Phase 1 Beachhead (SRE/DevOps)
│ Evidence: CLI works, 5+ tests│
│ Effort: ~1 week              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GATE 3: ContextCleaner PDF   │ ◄── Unblocks 5 verticals
│ Evidence: PDF → text works   │
│ Effort: 1-2 weeks            │
└──────────────┬───────────────┘
               │
               ▼
     Phase 2 Verticals (Legal, HR, Procurement)
```

---

## Phase Roadmap

### Phase 1: Beachhead (Weeks 1-4)

| Product | Vertical | Core Product Usage | Evidence Required |
|---------|----------|-------------------|-------------------|
| **OpsPack** | SRE/DevOps | AirGap (privacy) | CLI works, 5+ tests |

**Why SRE First**:
- Per playbook: "Our people. Developers will try it today."
- Viral adoption: One dev uses it, whole team adopts
- No procurement: IC can expense $49
- Fastest feedback loop

### Phase 2: Cash Flow (Weeks 5-12)

| Product | Vertical | Core Product Usage | Blocking Dependencies |
|---------|----------|-------------------|----------------------|
| **DealRoom Sentry** | Legal | AirGap + ContextCleaner | ContextCleaner (PDF) |
| **PeopleOps Vault** | HR | AirGap only | Ratio preservation algorithm |
| **RFP Defender** | Procurement | AirGap + ContextCleaner | ContextCleaner + SQLite KB |

### Phase 3: High-Value Expansion (Weeks 13-24)

| Product | Vertical | Core Product Usage | Blocking Dependencies |
|---------|----------|-------------------|----------------------|
| **AirGap Clinical** | Healthcare | AirGap + Lexicon | PHI patterns, Clinical lexicon |
| **AlphaGap** | Finance | AirGap + ContextCleaner | Excel parser, Ratio preservation |

### Phase 4: Premium Markets (Month 6+)

| Product | Vertical | Core Product Usage | Blocking Dependencies |
|---------|----------|-------------------|----------------------|
| **LegacyLift** | Legacy Code | ContextCleaner + MicroEmployee | COBOL parser |
| **M&A Deep** | M&A Law | DealRoom Sentry + integrations | Legal complete |
| **Lease Abstractor** | Real Estate | ContextCleaner | PDF parser + section detection |

---

## Evidence Discipline

Every claim in this document is supported by:

| Claim | Evidence Type | Location |
|-------|---------------|----------|
| AirGap 60/60 tests | Command output | `python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v` |
| AirGap uncommitted | Git status | `git status -sb` → `?? products/mcp-servers/` |
| ContextCleaner NOT BUILT | Directory absence | `ls products/` → no contextcleaner dir |
| Lexicon STUB | File inspection | `products/lexicon-packs/README.md` → no subdirs |
| MicroEmployees NOT BUILT | Directory absence | `ls products/` → no microemployees dir |
| Playbook locked | File header | `docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md:7` → "STATUS: LOCKED" |

---

## Roadmap Recommendations

### Immediate (This Week)
1. **Commit AirGap + status docs** → Unblock v0.2.0
2. **Tag v0.2.0** → First MCP server release
3. **Clean working tree** → Professional repo hygiene

### Short-Term (2 Weeks)
1. **Build OpsPack MVP** → Phase 1 beachhead (SRE/DevOps)
2. **Validate with SREs** → Internal dogfooding
3. **Define ContextCleaner spec** → Prepare for Phase 2

### Medium-Term (1 Month)
1. **Build ContextCleaner (PDF)** → Unblock 5 verticals
2. **Choose Phase 2 vertical** → Legal (cash cow) or HR (simpler)
3. **Publish OpsPack** → pip install opspack

### Long-Term (Quarter)
1. **Expand to 3+ verticals** → Legal, HR, Procurement
2. **Build Lexicon Packs** → Healthcare, Finance domain support
3. **Design MicroEmployees** → Workflow automation layer

---

## No-Claims Zone

The following are **NOT BUILT** and no claims should be made about them:

| Component | Status | Minimal Implementation Plan |
|-----------|--------|----------------------------|
| ContextCleaner | NOT BUILT | `pip install pdfplumber` → parse PDF → extract text → wire to AirGap |
| Lexicon Packs (impl) | NOT BUILT | Define JSON schema → build clinical pack → inject into prompts |
| MicroEmployees | NOT BUILT | Extend Senior Dev Brain patterns → add verification steps |
| OpsPack | NOT BUILT | Create AirGap wrapper with SRE-specific config → CLI entry point |
| DealRoom Sentry | NOT BUILT | Requires ContextCleaner first |
| RFP Defender | NOT BUILT | Requires ContextCleaner + SQLite KB |
| AlphaGap | NOT BUILT | Requires ContextCleaner (Excel) + ratio preservation |
| LegacyLift | NOT BUILT | Requires COBOL parser (high effort) |
| Lease Abstractor | NOT BUILT | Requires ContextCleaner (PDF) |
| AirGap Clinical | NOT BUILT | Requires PHI patterns + clinical lexicon |
| PeopleOps Vault | NOT BUILT | Requires ratio preservation algorithm |
| M&A Deep | NOT BUILT | Requires DealRoom Sentry complete |
