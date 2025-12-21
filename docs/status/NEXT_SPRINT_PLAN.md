# Next Sprint Plan (2 Weeks)

**Sprint**: v0.2.0 Release + OpsPack MVP
**Duration**: 2025-12-20 to 2026-01-03
**Owner**: Solo
**Goal**: Ship AirGap as v0.2.0, then OpsPack MVP as Phase 1 beachhead

---

## Sprint Objectives

1. **Critical Path**: Commit AirGap, clean working tree, tag v0.2.0
2. **Phase 1 Verticalization**: OpsPack MVP as AirGap profile/wrapper
3. Prepare v0.3.0 planning (vertical expansion)

---

## Week 1: v0.2.0 Release (CRITICAL PATH)

### Task 1.1: Commit AirGap Implementation
| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - BLOCKING |
| **Estimate** | 2 hours |
| **Owner** | Solo |
| **Dependencies** | None |

**Acceptance Criteria**:
- [ ] `products/mcp-servers/ninobyte-airgap/` committed to git
- [ ] `scripts/ci/validate_artifacts.py` changes committed
- [ ] `ops/evidence/ninobyte-airgap_v0.2.0_verification.md` committed
- [ ] Working tree is CLEAN (`git status` shows nothing)
- [ ] CI pipeline passes on main branch

**Commands**:
```bash
cd /Users/isaacnortey/Developer/ninobyte

# Stage all uncommitted work
git add products/mcp-servers/ninobyte-airgap/
git add scripts/ci/validate_artifacts.py
git add ops/evidence/
git add docs/status/
git add docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md

# Commit
git commit -m "feat(v0.2.0): AirGap MCP server + vertical playbook integration

- AirGap MCP server: security-hardened local file browser (60/60 tests)
- Locked 9 vertical playbook integrated into canonical docs
- Updated status docs with implementation fit analysis
- CI validation for AirGap networking/shell restrictions"

# Verify clean
git status -sb
# Expected: ## main...origin/main
```

**Verification**:
```bash
python3 scripts/ci/validate_artifacts.py
# Expected: All validations PASSED

python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v
# Expected: 60/60 PASSED
```

---

### Task 1.2: Create v0.2.0 Tag
| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - BLOCKING |
| **Estimate** | 30 minutes |
| **Owner** | Solo |
| **Dependencies** | Task 1.1 |

**Acceptance Criteria**:
- [ ] CI passes on main with all commits
- [ ] `git tag -a v0.2.0 -m "Release v0.2.0: AirGap MCP Server"`
- [ ] Tag pushed to origin
- [ ] Fresh clone at tag passes all tests

**Commands**:
```bash
git tag -a v0.2.0 -m "Release v0.2.0: AirGap MCP Server + Vertical Playbook"
git push origin v0.2.0
```

**Verification**:
```bash
# Test fresh clone
cd /tmp
git clone --branch v0.2.0 https://github.com/iamnortey/ninobyte.git test-v0.2.0
cd test-v0.2.0
python3 scripts/ci/validate_artifacts.py
python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v
```

---

### Task 1.3: Update CHANGELOG
| Attribute | Value |
|-----------|-------|
| **Priority** | P1 - High |
| **Estimate** | 1 hour |
| **Owner** | Solo |
| **Dependencies** | Task 1.1 |

**Acceptance Criteria**:
- [ ] `docs/canonical/CHANGELOG.md` (or create if missing) updated with v0.2.0 section

**Content**:
```markdown
## [0.2.0] - 2025-12-20

### Added
- **AirGap MCP Server** (`products/mcp-servers/ninobyte-airgap/`)
  - `list_dir`: Directory listing with symlink escape prevention
  - `read_file`: File reading with size limits, offset/limit, actual bytes audited
  - `search_text`: Text search using ripgrep or Python fallback
  - `redact_preview`: Stateless string redaction (no file I/O)
- Security controls: deny-by-default, blocked patterns, path canonicalization
- JSONL audit logging with path redaction
- 60 unit tests with 100% pass rate
- CI validation for networking imports and shell=True usage

### Documentation
- Locked 9 Vertical Playbook v2.0 (`docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md`)
- Updated status docs with implementation fit analysis per vertical

### Security
- No network imports in AirGap code (AST-enforced in CI)
- No shell=True anywhere (AST-enforced in CI)
- Symlink escape prevention via canonicalization
- Traversal attack prevention
```

---

## Week 2: OpsPack MVP (Phase 1 Beachhead)

### Task 2.1: Create OpsPack Directory Structure
| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - Critical |
| **Estimate** | 2 hours |
| **Owner** | Solo |
| **Dependencies** | v0.2.0 tagged |

**Acceptance Criteria**:
- [ ] `products/opspack/` directory created
- [ ] `products/opspack/__init__.py` exists
- [ ] `products/opspack/__main__.py` exists (CLI entry point)
- [ ] `products/opspack/config.py` exists (SRE-specific config)
- [ ] `products/opspack/README.md` exists

**Commands**:
```bash
mkdir -p products/opspack/src
touch products/opspack/__init__.py
touch products/opspack/__main__.py
touch products/opspack/README.md
```

**Structure**:
```
products/opspack/
├── __init__.py
├── __main__.py        # CLI: python -m opspack analyze --log ...
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py      # SRE-specific AirGap config
│   ├── log_parser.py  # Multi-format log parsing
│   └── timeline.py    # Incident timeline generation
└── tests/
    └── test_log_parser.py
```

---

### Task 2.2: OpsPack Config Profile
| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - Critical |
| **Estimate** | 4 hours |
| **Owner** | Solo |
| **Dependencies** | Task 2.1 |

**Acceptance Criteria**:
- [ ] `products/opspack/src/config.py` wraps AirGap config with SRE defaults
- [ ] Default blocked patterns include: IP addresses, customer IDs, tokens, internal hostnames
- [ ] Default allowed roots include: `/var/log/`, project directory
- [ ] Config can be overridden via CLI flags or JSON file

**Implementation**:
```python
# products/opspack/src/config.py
from products.mcp_servers.ninobyte_airgap.src.config import AirGapConfig

class OpsPackConfig(AirGapConfig):
    """SRE-specific AirGap configuration."""

    # Additional blocked patterns for ops logs
    OPS_BLOCKED_PATTERNS = [
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IPv4
        r'customer[_-]?id[=:]\s*\w+',                # Customer IDs
        r'session[_-]?token[=:]\s*\w+',              # Session tokens
        r'internal-\w+\.corp\.local',                 # Internal hostnames
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Extend blocked patterns
        self.blocked_patterns.extend(self.OPS_BLOCKED_PATTERNS)
```

**Verification**:
```bash
python3 -c "from products.opspack.src.config import OpsPackConfig; c = OpsPackConfig(); print(len(c.blocked_patterns))"
# Expected: More patterns than base AirGap
```

---

### Task 2.3: OpsPack CLI Entry Point
| Attribute | Value |
|-----------|-------|
| **Priority** | P0 - Critical |
| **Estimate** | 4 hours |
| **Owner** | Solo |
| **Dependencies** | Task 2.2 |

**Acceptance Criteria**:
- [ ] `python -m opspack --help` works
- [ ] `python -m opspack analyze --log /path/to/log --query "What happened?"` works
- [ ] Output includes: sanitized summary, redaction counts, timeline

**Implementation**:
```python
# products/opspack/__main__.py
import argparse
from .src.config import OpsPackConfig
from products.mcp_servers.ninobyte_airgap.src.read_file import read_file
from products.mcp_servers.ninobyte_airgap.src.redact_preview import redact_preview

def main():
    parser = argparse.ArgumentParser(prog='opspack', description='SRE log analysis with privacy')
    subparsers = parser.add_subparsers(dest='command')

    analyze = subparsers.add_parser('analyze', help='Analyze logs')
    analyze.add_argument('--log', action='append', required=True, help='Log file paths')
    analyze.add_argument('--query', required=True, help='Analysis query')
    analyze.add_argument('--time', help='Time range filter')

    args = parser.parse_args()

    if args.command == 'analyze':
        config = OpsPackConfig(allowed_roots=['/var/log/', '.'])
        # ... analysis logic
        print("OpsPack analysis complete")

if __name__ == '__main__':
    main()
```

**Verification**:
```bash
python -m opspack --help
# Expected: usage: opspack [-h] {analyze} ...

python -m opspack analyze --log /var/log/system.log --query "errors"
# Expected: Analysis output with redaction counts
```

---

### Task 2.4: OpsPack Tests
| Attribute | Value |
|-----------|-------|
| **Priority** | P1 - High |
| **Estimate** | 4 hours |
| **Owner** | Solo |
| **Dependencies** | Task 2.3 |

**Acceptance Criteria**:
- [ ] `products/opspack/tests/` directory exists
- [ ] At least 5 unit tests covering:
  - Config extension works
  - IP redaction works
  - Customer ID redaction works
  - CLI argument parsing works
  - Log file reading respects config

**Verification**:
```bash
python3 -m pytest products/opspack/tests/ -v
# Expected: 5+ tests pass
```

---

### Task 2.5: OpsPack Documentation
| Attribute | Value |
|-----------|-------|
| **Priority** | P1 - High |
| **Estimate** | 2 hours |
| **Owner** | Solo |
| **Dependencies** | Task 2.3 |

**Acceptance Criteria**:
- [ ] `products/opspack/README.md` explains:
  - What OpsPack is
  - Installation
  - Usage examples
  - Security guarantees
  - Vertical alignment (SRE/DevOps beachhead)

---

## Sprint Backlog Summary

| Task | Priority | Estimate | Week | Status |
|------|----------|----------|------|--------|
| 1.1 Commit AirGap | P0 | 2 hours | 1 | NOT STARTED |
| 1.2 Create v0.2.0 Tag | P0 | 30 min | 1 | NOT STARTED |
| 1.3 Update CHANGELOG | P1 | 1 hour | 1 | NOT STARTED |
| 2.1 OpsPack Directory | P0 | 2 hours | 2 | NOT STARTED |
| 2.2 OpsPack Config | P0 | 4 hours | 2 | NOT STARTED |
| 2.3 OpsPack CLI | P0 | 4 hours | 2 | NOT STARTED |
| 2.4 OpsPack Tests | P1 | 4 hours | 2 | NOT STARTED |
| 2.5 OpsPack Docs | P1 | 2 hours | 2 | NOT STARTED |

**Total Estimated Effort**: ~20 hours (~2.5 days)

---

## Success Criteria

| Milestone | Target | Verification |
|-----------|--------|--------------|
| v0.2.0 tag created | Yes | `git tag --list` shows v0.2.0 |
| Working tree clean | Yes | `git status -sb` shows only branch |
| All AirGap tests passing | 60/60 | `python3 -m pytest ...` |
| CI green on main | Yes | GitHub Actions |
| OpsPack CLI works | Yes | `python -m opspack --help` |
| OpsPack tests passing | 5+ | `python3 -m pytest products/opspack/tests/` |

---

## Definition of Done

### v0.2.0 (Week 1)
- [ ] All uncommitted work committed
- [ ] `git status` shows clean working tree
- [ ] v0.2.0 tag created and pushed
- [ ] Fresh clone at tag passes all tests
- [ ] CHANGELOG updated

### OpsPack MVP (Week 2)
- [ ] `products/opspack/` exists with CLI entry point
- [ ] `python -m opspack analyze --log X --query Y` works
- [ ] IP addresses, customer IDs, tokens redacted by default
- [ ] 5+ unit tests passing
- [ ] README documentation complete

---

## Phase 1 Vertical Alignment

Per `docs/canonical/VERTICAL_PLAYBOOK_v2_FINAL.md`:

| Vertical | Product | Status After Sprint |
|----------|---------|---------------------|
| SRE/DevOps (START HERE) | OpsPack | MVP SHIPPED |
| Legal (CASH COW) | DealRoom Sentry | Blocked on ContextCleaner |
| Healthcare (LONG GAME) | AirGap Clinical | Needs PHI patterns |
| Procurement (MOAT) | RFP Defender | Needs knowledge base |
| HR (UNIVERSAL) | PeopleOps Vault | Needs ratio preservation |
| Finance (PREMIUM) | AlphaGap | Needs Excel parsing |
| Legacy Code ($10M) | LegacyLift | Needs COBOL parser |
| M&A Law (HIGH STAKES) | M&A Deep | Blocked on Legal |
| Real Estate (CLEAR) | Lease Abstractor | Blocked on PDF parsing |

**Sprint Focus**: SRE/DevOps only (beachhead strategy)

---

## Post-Sprint Planning (v0.3.0)

After this sprint:
1. Validate OpsPack with real SRE users (dogfood internally)
2. Decide: ContextCleaner MVP scope (PDF first vs Excel first)
3. Phase 2 vertical selection (Legal vs HR vs Healthcare)
