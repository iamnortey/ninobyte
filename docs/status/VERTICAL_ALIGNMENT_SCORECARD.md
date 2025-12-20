# Vertical Alignment Scorecard — Locked 9

**Date**: 2025-12-20
**Source**: `docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md` (LOCKED v2.0)
**Status**: Aligned to final playbook

---

## The Locked 9 Verticals

Per the locked playbook, we are executing on **9 specific verticals** in priority order:

| Priority | Vertical | Label | Build Effort |
|----------|----------|-------|--------------|
| 1 | SRE/DevOps | **START HERE** | LOW (2-3 weeks) |
| 2 | Legal Services | **CASH COW** | MEDIUM (4-6 weeks) |
| 3 | Healthcare | **LONG GAME** | MEDIUM (4-6 weeks) |
| 4 | Procurement/RFP | **MOAT** | MEDIUM (6-8 weeks) |
| 5 | HR/People Ops | **UNIVERSAL** | LOW-MEDIUM (4-6 weeks) |
| 6 | Financial Analysis | **PREMIUM** | MEDIUM (6-8 weeks) |
| 7 | Legacy Code | **$10M PROBLEM** | HIGH (8-12 weeks) |
| 8 | M&A Law | **HIGH STAKES** | MEDIUM-HIGH (6-8 weeks) |
| 9 | Real Estate | **CLEAR WORKFLOW** | MEDIUM (6-8 weeks) |

---

## 4-Core Product Stack Mapping

All 9 verticals are configurations of 4 core products:

| Product | Function | Status in Repo |
|---------|----------|----------------|
| **AirGap** | Privacy gate (PII → tokens → rehydrate) | BUILT (uncommitted) |
| **ContextCleaner** | Parse format → extract structure | NOT BUILT |
| **Lexicon Packs** | Domain terminology injection | STUB ONLY |
| **MicroEmployees** | Workflow execution + verification | NOT BUILT |

---

## Vertical-to-Product Matrix

| Vertical | AirGap | ContextCleaner | Lexicon | MicroEmployee | Primary Product |
|----------|--------|----------------|---------|---------------|-----------------|
| SRE/DevOps | HIGH | MEDIUM | LOW | HIGH | **OpsPack** |
| Legal | HIGH | HIGH | MEDIUM | MEDIUM | **DealRoom Sentry** |
| Healthcare | HIGH | LOW | HIGH | MEDIUM | **AirGap Clinical** |
| Procurement | HIGH | HIGH | LOW | HIGH | **RFP Defender** |
| HR | HIGH | LOW | LOW | MEDIUM | **PeopleOps Vault** |
| Finance | HIGH | HIGH | HIGH | MEDIUM | **AlphaGap** |
| Legacy Code | MEDIUM | HIGH | MEDIUM | HIGH | **LegacyLift** |
| M&A Law | HIGH | HIGH | MEDIUM | MEDIUM | **M&A Deep** |
| Real Estate | MEDIUM | HIGH | LOW | MEDIUM | **Lease Abstractor** |

---

## Implementation Fit Now — Per Vertical

### #1: SRE/DevOps (START HERE)

**Priority Label**: START HERE
**Playbook Product**: OpsPack

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap path_security | `products/mcp-servers/ninobyte-airgap/src/path_security.py` | BUILT |
| AirGap read_file | `products/mcp-servers/ninobyte-airgap/src/read_file.py` | BUILT |
| AirGap search_text | `products/mcp-servers/ninobyte-airgap/src/search_text.py` | BUILT |
| AirGap redact_preview | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| AirGap audit logging | `products/mcp-servers/ninobyte-airgap/src/audit.py` | BUILT |
| Senior Dev Brain (Incident Triage) | `skills/senior-developer-brain/SKILL.md:252-301` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| Log parsing (multi-format) | P1 | 2-3 days |
| Timestamp correlation | P1 | 1-2 days |
| OpsPack CLI wrapper | P0 | 1 day |
| OpsPack config profiles | P2 | 1 day |

**Smallest Viable Next Step**:
```bash
# Create OpsPack as AirGap profile/wrapper
mkdir -p products/opspack/
# Create __main__.py that wraps AirGap with SRE-specific config
# - Blocked patterns: *.log → redact IPs, customer IDs, tokens
# - Default search paths: /var/log/
# - Output: incident timeline format
```

**Verification Command**:
```bash
python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v
# Should pass 60/60 tests (AirGap core ready)
```

---

### #2: Legal Services (CASH COW)

**Priority Label**: CASH COW
**Playbook Product**: DealRoom Sentry

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap read_file with pagination | `products/mcp-servers/ninobyte-airgap/src/read_file.py` | BUILT |
| AirGap redact_preview (stateless) | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| Path security (traversal prevention) | `products/mcp-servers/ninobyte-airgap/src/path_security.py` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| Document indexing (local SQLite) | P0 | 3-5 days |
| PDF/DOCX parsing (ContextCleaner) | P0 | 5-7 days |
| Citation extraction | P1 | 2-3 days |
| Rehydration engine | P0 | 2-3 days |
| Desktop app shell | P2 | 5-7 days |

**Smallest Viable Next Step**:
```bash
# Add PDF parsing to ContextCleaner stub
pip install pdfplumber  # MIT licensed
# Create products/contextcleaner/parsers/pdf.py
# Wire into AirGap flow: parse → redact → send → rehydrate
```

---

### #3: Healthcare (LONG GAME)

**Priority Label**: LONG GAME
**Playbook Product**: AirGap Clinical

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap redact_preview | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| PII pattern matching | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py:PATTERNS` | BUILT |
| Audit logging (JSONL) | `products/mcp-servers/ninobyte-airgap/src/audit.py` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| PHI-specific patterns (MRN, DOB, lab values) | P0 | 2-3 days |
| Clinical lexicon pack | P1 | 5-7 days |
| Trust indicator UI | P1 | 3-5 days |
| Rehydration with clinical context | P0 | 2-3 days |

**Smallest Viable Next Step**:
```bash
# Extend redact_preview.py with HIPAA PHI patterns
# Add to PATTERNS dict:
#   - MRN: r'\b\d{6,10}\b' (after context check)
#   - DOB: existing date patterns
#   - SSN: existing pattern
#   - Lab values: r'\b\d+\.?\d*\s*(mg|mL|U|IU)\b'
```

---

### #4: Procurement/RFP (MOAT)

**Priority Label**: MOAT
**Playbook Product**: RFP Defender

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap local file access | `products/mcp-servers/ninobyte-airgap/src/` | BUILT |
| Search text (regex) | `products/mcp-servers/ninobyte-airgap/src/search_text.py` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| Local SQLite knowledge base | P0 | 3-5 days |
| Questionnaire parser (PDF/Excel/Word) | P0 | 5-7 days |
| Similarity matching | P1 | 3-5 days |
| Answer learning loop | P2 | 3-5 days |
| Web app shell | P2 | 5-7 days |

**Smallest Viable Next Step**:
```bash
# Knowledge base as SQLite
pip install sqlite-utils  # Simple local DB
# Schema: CREATE TABLE answers (
#   question TEXT, answer TEXT, source TEXT, created_at TEXT
# )
```

---

### #5: HR/People Ops (UNIVERSAL)

**Priority Label**: UNIVERSAL
**Playbook Product**: PeopleOps Vault

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap redact_preview | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| Name redaction | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| Numeric redaction | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | PARTIAL |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| Salary/compensation patterns | P0 | 1 day |
| Department/title patterns | P1 | 1 day |
| Ratio preservation (12% gap) | P1 | 2-3 days |
| Rehydration engine | P0 | 2-3 days |

**Smallest Viable Next Step**:
```bash
# Add HR-specific patterns to redact_preview.py
# - Salary: r'\$[\d,]+(?:\.\d{2})?'
# - Department: Named entity recognition or keyword list
```

---

### #6: Financial Analysis (PREMIUM)

**Priority Label**: PREMIUM
**Playbook Product**: AlphaGap

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap redact_preview | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |
| Numeric pattern matching | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | PARTIAL |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| Excel parsing (ContextCleaner) | P0 | 5-7 days |
| Ratio preservation algorithm | P0 | 3-5 days |
| Financial entity patterns | P1 | 2-3 days |
| Desktop app (Excel integration) | P2 | 7-10 days |

**Smallest Viable Next Step**:
```bash
pip install openpyxl  # Excel parsing
# Create products/contextcleaner/parsers/excel.py
# Extract cell values, preserve relative relationships
```

---

### #7: Legacy Code ($10M PROBLEM)

**Priority Label**: $10M PROBLEM
**Playbook Product**: LegacyLift

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| Senior Dev Brain skill | `skills/senior-developer-brain/SKILL.md` | BUILT |
| AirGap read_file | `products/mcp-servers/ninobyte-airgap/src/read_file.py` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| COBOL parser (ContextCleaner) | P0 | 10-14 days |
| COPY statement resolver | P0 | 3-5 days |
| Paragraph call graph | P1 | 3-5 days |
| Semantic chunking | P1 | 3-5 days |
| Business rule extraction | P2 | 5-7 days |

**Smallest Viable Next Step**:
```bash
# Research COBOL parsing libraries
# Options: koopa (ANTLR), cobol-parser (Python)
# Start with: products/contextcleaner/parsers/cobol.py
```

---

### #8: M&A Law (HIGH STAKES)

**Priority Label**: HIGH STAKES
**Playbook Product**: M&A Deep (DealRoom Sentry + M&A specifics)

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| Same as Legal (#2) | See Legal section | See Legal |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| All of Legal (#2) | P0 | See Legal |
| Intralinks/Datasite API integration | P1 | 5-7 days |
| M&A-specific clause patterns | P1 | 3-5 days |
| Deal timeline tracker | P2 | 3-5 days |

**Smallest Viable Next Step**:
Build Legal (#2) first, then add M&A-specific features.

---

### #9: Real Estate (CLEAR WORKFLOW)

**Priority Label**: CLEAR WORKFLOW
**Playbook Product**: Lease Abstractor

| What Exists Today | File Path | Status |
|-------------------|-----------|--------|
| AirGap read_file | `products/mcp-servers/ninobyte-airgap/src/read_file.py` | BUILT |
| AirGap redact_preview | `products/mcp-servers/ninobyte-airgap/src/redact_preview.py` | BUILT |

| What's Missing | Priority | Build Effort |
|----------------|----------|--------------|
| PDF parsing (ContextCleaner) | P0 | 5-7 days |
| Lease section detection | P0 | 3-5 days |
| Term extraction (dates, amounts, options) | P0 | 3-5 days |
| JSON output schema | P1 | 1-2 days |
| Web app upload | P2 | 5-7 days |

**Smallest Viable Next Step**:
```bash
# Same as Legal: PDF parsing first
# Then: lease-specific section patterns
# - "PREMISES", "TERM", "RENT", "OPTIONS"
```

---

## Summary: What Exists vs What's Needed

| Core Product | Status | Location | Tests |
|--------------|--------|----------|-------|
| **AirGap** | BUILT (uncommitted) | `products/mcp-servers/ninobyte-airgap/` | 60/60 pass |
| **ContextCleaner** | NOT BUILT | N/A | N/A |
| **Lexicon Packs** | STUB | `products/lexicon-packs/README.md` | N/A |
| **MicroEmployees** | NOT BUILT | N/A | N/A |

| Vertical | Can Ship MVP Now? | Blocking Components |
|----------|-------------------|---------------------|
| SRE/DevOps | YES (with wrapper) | OpsPack CLI wrapper |
| Legal | NO | ContextCleaner (PDF), rehydration |
| Healthcare | PARTIAL | PHI patterns, lexicon |
| Procurement | NO | ContextCleaner, knowledge base |
| HR | PARTIAL | Ratio preservation |
| Finance | NO | ContextCleaner (Excel), ratio preservation |
| Legacy Code | NO | ContextCleaner (COBOL) |
| M&A Law | NO | All of Legal |
| Real Estate | NO | ContextCleaner (PDF) |

---

## Critical Path

```
CURRENT STATE
    │
    ▼
┌──────────────────────────────┐
│ GATE 0: Commit AirGap        │ ◄── BLOCKING ALL VERTICALS
│ Location: products/mcp-servers/ninobyte-airgap/
│ Action: git add && git commit
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GATE 1: OpsPack MVP          │ ◄── Phase 1 Beachhead
│ Effort: 1 week
│ Depends: AirGap committed
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ GATE 2: ContextCleaner PDF   │ ◄── Unblocks Legal, M&A, Real Estate
│ Effort: 5-7 days
└──────────────┬───────────────┘
               │
               ▼
     Phase 2+ Verticals
```

---

## Verification Commands

```bash
# Verify AirGap is ready
python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v
# Expected: 60/60 PASSED

# Verify CI validation
python3 scripts/ci/validate_artifacts.py
# Expected: All validations PASSED

# Check for uncommitted work
git status -sb
# Expected: Shows AirGap as untracked
```
