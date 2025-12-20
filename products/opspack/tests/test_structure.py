"""
OpsPack Contract Hardening Tests

Structure-only governance tests that verify:
1. Required skeleton files are present
2. Required documentation sections exist
3. No disallowed imports in source (read-only posture guardrail)

This is NOT a functionality test suite. No OpsPack runtime features are tested.
"""

import os
from pathlib import Path
from typing import List, Set


def find_repo_root() -> Path:
    """
    Find repository root by walking up from this file until .git is found.
    Falls back to parent of products/ if .git not found.
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    # Fallback: assume tests/test_structure.py is under products/opspack/tests/
    return Path(__file__).resolve().parent.parent.parent.parent


REPO_ROOT = find_repo_root()
OPSPACK_ROOT = REPO_ROOT / "products" / "opspack"
OPSPACK_SRC = OPSPACK_ROOT / "src"


class TestRequiredFilesExist:
    """Verify all required skeleton files are present."""

    REQUIRED_FILES = [
        "README.md",
        "SECURITY.md",
        "docs/THREAT_MODEL.md",
        "docs/ROADMAP.md",
        "docs/INTERFACE_CONTRACT.md",
        "src/ninobyte_opspack/__init__.py",
        "src/ninobyte_opspack/version.py",
    ]

    def test_readme_exists(self):
        """README.md must exist."""
        filepath = OPSPACK_ROOT / "README.md"
        assert filepath.exists(), f"Required file missing: README.md"

    def test_security_exists(self):
        """SECURITY.md must exist."""
        filepath = OPSPACK_ROOT / "SECURITY.md"
        assert filepath.exists(), f"Required file missing: SECURITY.md"

    def test_threat_model_exists(self):
        """docs/THREAT_MODEL.md must exist."""
        filepath = OPSPACK_ROOT / "docs" / "THREAT_MODEL.md"
        assert filepath.exists(), f"Required file missing: docs/THREAT_MODEL.md"

    def test_roadmap_exists(self):
        """docs/ROADMAP.md must exist."""
        filepath = OPSPACK_ROOT / "docs" / "ROADMAP.md"
        assert filepath.exists(), f"Required file missing: docs/ROADMAP.md"

    def test_interface_contract_exists(self):
        """docs/INTERFACE_CONTRACT.md must exist."""
        filepath = OPSPACK_ROOT / "docs" / "INTERFACE_CONTRACT.md"
        assert filepath.exists(), f"Required file missing: docs/INTERFACE_CONTRACT.md"

    def test_init_py_exists(self):
        """src/ninobyte_opspack/__init__.py must exist."""
        filepath = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "__init__.py"
        assert filepath.exists(), f"Required file missing: src/ninobyte_opspack/__init__.py"

    def test_version_py_exists(self):
        """src/ninobyte_opspack/version.py must exist."""
        filepath = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "version.py"
        assert filepath.exists(), f"Required file missing: src/ninobyte_opspack/version.py"


class TestDocumentationSections:
    """Verify required documentation sections are present."""

    def _read_file(self, rel_path: str) -> str:
        """Read file content as UTF-8 with error replacement."""
        filepath = OPSPACK_ROOT / rel_path
        return filepath.read_text(encoding="utf-8", errors="replace")

    def test_readme_has_what_opspack_is_not_section(self):
        """README.md must contain '## What OpsPack is NOT' heading."""
        content = self._read_file("README.md")
        assert "## What OpsPack is NOT" in content, (
            "README.md must contain '## What OpsPack is NOT' section heading"
        )

    def test_readme_has_airgap_alignment_section(self):
        """README.md must contain '## AirGap Alignment' heading."""
        content = self._read_file("README.md")
        assert "## AirGap Alignment" in content, (
            "README.md must contain '## AirGap Alignment' section heading"
        )

    def test_roadmap_has_non_goals_section(self):
        """ROADMAP.md must contain '## Non-Goals (Permanent)' heading."""
        content = self._read_file("docs/ROADMAP.md")
        assert "## Non-Goals (Permanent)" in content, (
            "docs/ROADMAP.md must contain '## Non-Goals (Permanent)' section heading"
        )

    def test_security_has_contributor_guidelines_section(self):
        """SECURITY.md must contain '## Contributor Guidelines' heading."""
        content = self._read_file("SECURITY.md")
        assert "## Contributor Guidelines" in content, (
            "SECURITY.md must contain '## Contributor Guidelines' section heading"
        )


class TestReadOnlyPosture:
    """Verify no disallowed imports exist in OpsPack source (guardrail)."""

    # Tokens that would indicate non-read-only behavior
    FORBIDDEN_TOKENS = {
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "aiohttp",
        "paramiko",
    }

    def _scan_file_for_tokens(self, filepath: Path) -> List[str]:
        """
        Scan a Python file for forbidden import tokens.
        Returns list of found forbidden tokens.
        """
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        found = []
        for token in self.FORBIDDEN_TOKENS:
            # Check for import patterns: "import token" or "from token"
            if f"import {token}" in content or f"from {token}" in content:
                found.append(token)

        return found

    def test_no_forbidden_imports_in_source(self):
        """OpsPack source must not contain forbidden imports."""
        if not OPSPACK_SRC.exists():
            # No source directory yet; pass (skeleton may be minimal)
            return

        violations = []

        for py_file in OPSPACK_SRC.rglob("*.py"):
            forbidden_found = self._scan_file_for_tokens(py_file)
            if forbidden_found:
                rel_path = py_file.relative_to(OPSPACK_ROOT)
                for token in forbidden_found:
                    violations.append(f"{rel_path}: forbidden import '{token}'")

        assert not violations, (
            "Read-only posture violation: forbidden imports found:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
