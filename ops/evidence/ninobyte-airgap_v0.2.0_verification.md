# Ninobyte AirGap v0.2.0 Verification Evidence

**Date:** 2025-12-20
**Product:** products/mcp-servers/ninobyte-airgap/
**Version:** v0.2.0

---

## Hard Gates (All Exited 0)

### 1. Compile Gate

```bash
python3 -m compileall products/mcp-servers/ninobyte-airgap/src/ products/mcp-servers/ninobyte-airgap/tests/
```

**Output:**
```
Listing 'products/mcp-servers/ninobyte-airgap/src/'...
Listing 'products/mcp-servers/ninobyte-airgap/tests/'...
```

**Exit Code:** 0

---

### 2. Test Suite

```bash
python3 -m pytest products/mcp-servers/ninobyte-airgap/tests/ -v
```

**Output (summary):**
```
============================== 60 passed in 0.70s ==============================
```

**Exit Code:** 0

---

### 3. Governance Gate

```bash
python3 scripts/ci/validate_artifacts.py
```

**Output (summary):**
```
--- Ninobyte AirGap MCP Server Validation (v0.2.0) ---
✅ AirGap README exists
✅ AirGap Security Policy exists
✅ Source package init exists
✅ AirGap: No forbidden networking imports found
✅ AirGap: No shell execution violations found

============================================================
✅ All validations PASSED
```

**Exit Code:** 0

---

## Drift Scanners (All Clean)

### Old Name References

```bash
rg "airgap-file-browser" -n --no-ignore
```

**Result:** (exit code 1 - NO MATCHES FOUND)

---

### Placeholder/TODO Detection in Governance Script

```bash
rg "\.\.\. \(full implementation\)|TODO|pass\s*$" -n scripts/ci/validate_artifacts.py -S
```

**Result:** (exit code 1 - NO MATCHES FOUND)

---

### Forbidden Network Imports

```bash
rg "import (requests|httpx|aiohttp|urllib3|socket|websockets)" -n products/mcp-servers/ninobyte-airgap/src -S
```

**Result:** (exit code 1 - NO MATCHES FOUND)

---

### Shell Execution Patterns

```bash
rg "(shell\s*=\s*True|os\.system\s*\(|os\.popen\s*\()" -n products/mcp-servers/ninobyte-airgap/src -S
```

**Result:**
```
products/mcp-servers/ninobyte-airgap/src/search_text.py:288:    # Build explicit argv list - NO shell=True
products/mcp-servers/ninobyte-airgap/src/search_text.py:308:            shell=False  # EXPLICIT: Never use shell=True
```

**Analysis:** Matches are COMMENTS documenting security practice, not violations. Actual code uses `shell=False`.

---

## Governance Function Verification

**File:** `scripts/ci/validate_artifacts.py`

| Function | Status | Notes |
|----------|--------|-------|
| `scan_imports_ast()` | FULLY IMPLEMENTED | AST-based import scanning, lines 448-484 |
| `validate_airgap_no_networking()` | FULLY IMPLEMENTED | Hard gate, lines 487-536 |
| `validate_airgap_no_shell_true()` | FULLY IMPLEMENTED | MVP scope: literal shell=True + os.system/os.popen, lines 539-608 |
| `validate_airgap_structure()` | FULLY IMPLEMENTED | Directory/file structure check, lines 611-652 |

**FORBIDDEN_NETWORK_MODULES:** Does NOT include `asyncio` or `ssl` (correct per requirements)

---

## Test Coverage for Smoke Scenarios

| Scenario | Test File | Status |
|----------|-----------|--------|
| list_dir allow/deny | test_list_dir.py | COVERED (9 tests) |
| read_file allow/deny + blocked patterns | test_read_file.py | COVERED (10 tests) |
| search_text bounded results/timeout | test_search_text.py | COVERED (10 tests) |
| redact_preview statelessness | test_redact_preview.py | COVERED (16 tests) |

---

## Claude Code Integration Safety

- No MCP server configuration files in-repo (server is stdio-only, configured externally)
- No references to old name "airgap-file-browser" in any config
- Canonical path `products/mcp-servers/ninobyte-airgap/` used consistently

---

## Product Root Verification

```bash
cd products/mcp-servers/ninobyte-airgap
python3 -m compileall src/ tests/
python3 -m pytest tests/ -v
```

**Results:**
- Compile: Exit 0
- Tests: 60 passed in 0.73s

---

## Summary

**All hard gates exited 0.**

| Gate | Status |
|------|--------|
| Compile (repo root) | PASS |
| Compile (product root) | PASS |
| Tests (repo root) | PASS (60/60) |
| Tests (product root) | PASS (60/60) |
| Governance | PASS |
| Old name drift | CLEAN |
| Placeholder drift | CLEAN |
| Network import drift | CLEAN |
| Shell execution drift | CLEAN |
