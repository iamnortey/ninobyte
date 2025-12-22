"""
AirGap Contract + Policy Tests (Phase 3.2)

Stabilizes AirGap's external contract and enforces security invariants:
- Public contract snapshot (golden; fail-on-diff)
- Forbidden imports policy via AST static analysis
- Error contract stability
- Adapter contract preservation (schema v1)

Security:
- Uses stdlib-only AST parsing (no third-party deps)
- No networking, no shell execution
- Goldens are gates: fail on diff, never auto-update
"""

import ast
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

# Add src paths for imports
_airgap_src = str(Path(__file__).parent.parent / 'src')
_context_cleaner_src = str(
    Path(__file__).parent.parent.parent.parent / 'context-cleaner' / 'src'
)

if _airgap_src not in sys.path:
    sys.path.insert(0, _airgap_src)
if _context_cleaner_src not in sys.path:
    sys.path.insert(0, _context_cleaner_src)

from context_cleaner_adapter import (
    clean_context_text,
    ContextCleanerError,
    LexiconPathDeniedError,
)


# =============================================================================
# Golden File Paths
# =============================================================================

GOLDENS_DIR = Path(__file__).parent / 'goldens'
AIRGAP_CONTRACT_INPUT = GOLDENS_DIR / 'airgap_contract_input.txt'
AIRGAP_CONTRACT_EXPECTED = GOLDENS_DIR / 'airgap_contract_expected.jsonl'


# =============================================================================
# A) Public Contract Snapshot Tests (Golden; Fail-on-Diff)
# =============================================================================

class TestPublicContractSnapshot:
    """
    Test Suite A: Public contract golden snapshot.

    Validates that adapter output matches committed golden file exactly.
    Any mismatch fails the test - CI never auto-updates goldens.
    """

    def test_contract_snapshot_matches_golden(self):
        """
        Verify adapter output matches committed golden exactly.

        This is the primary contract stability gate.
        """
        # Read input
        input_text = AIRGAP_CONTRACT_INPUT.read_text(encoding='utf-8')

        # Generate output through adapter
        output = clean_context_text(
            input_text,
            output_format="jsonl"
        )

        # Read expected golden
        expected = AIRGAP_CONTRACT_EXPECTED.read_text(encoding='utf-8')

        # Strip trailing whitespace for comparison
        output = output.strip()
        expected = expected.strip()

        assert output == expected, (
            f"Contract snapshot mismatch!\n"
            f"Expected:\n{expected}\n\n"
            f"Actual:\n{output}\n\n"
            f"If this is intentional, update the golden file manually."
        )

    def test_schema_version_is_string_one(self):
        """Verify schema_version is exactly "1" (string)."""
        input_text = "Contact test@example.com"

        output = clean_context_text(input_text, output_format="jsonl")
        parsed = json.loads(output.strip())

        assert parsed["meta"]["schema_version"] == "1", \
            "schema_version must be string '1'"
        assert isinstance(parsed["meta"]["schema_version"], str), \
            "schema_version must be a string, not int"

    def test_toplevel_key_order_preserved(self):
        """Verify top-level keys appear in exact order: meta, normalized, redacted."""
        input_text = "Contact test@example.com"

        output = clean_context_text(input_text, output_format="jsonl")
        output = output.strip()

        # Check raw string positions
        meta_pos = output.find('"meta"')
        normalized_pos = output.find('"normalized"')
        redacted_pos = output.find('"redacted"')

        assert meta_pos != -1, "meta key must be present"
        assert normalized_pos != -1, "normalized key must be present"
        assert redacted_pos != -1, "redacted key must be present"

        assert meta_pos < normalized_pos < redacted_pos, (
            f"Key order must be meta({meta_pos}) < normalized({normalized_pos}) "
            f"< redacted({redacted_pos})"
        )

    def test_normalized_is_explicit_null_when_disabled(self):
        """Verify normalized is explicit null (not missing) when normalize_tables=False."""
        input_text = "Simple text"

        output = clean_context_text(
            input_text,
            normalize_tables=False,
            output_format="jsonl"
        )
        output = output.strip()

        # Check raw string contains explicit null
        assert '"normalized":null' in output, \
            "normalized must be explicitly null, not missing"

        # Verify via parsing
        parsed = json.loads(output)
        assert "normalized" in parsed, "normalized key must exist"
        assert parsed["normalized"] is None, "normalized value must be None"


# =============================================================================
# B) Forbidden Imports Policy - AST Static Analysis
# =============================================================================

# Forbidden modules that AirGap must never import
FORBIDDEN_MODULES: Set[str] = {
    "socket",
    "subprocess",
    "requests",
    "urllib3",
    "httpx",
}

# Forbidden os attribute usages
FORBIDDEN_OS_ATTRS: Set[str] = {"system", "popen"}


class ForbiddenImportVisitor(ast.NodeVisitor):
    """
    AST visitor that detects forbidden imports and usages.

    Detects:
    - import socket, import subprocess, etc.
    - from subprocess import Popen, etc.
    - os.system, os.popen usages
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Detect: import socket, import subprocess"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]  # Get top-level module
            if module_name in FORBIDDEN_MODULES:
                self.violations.append((
                    node.lineno,
                    f"forbidden import: import {alias.name}"
                ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Detect: from subprocess import Popen, etc."""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in FORBIDDEN_MODULES:
                imported_names = ', '.join(a.name for a in node.names)
                self.violations.append((
                    node.lineno,
                    f"forbidden import: from {node.module} import {imported_names}"
                ))
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Detect: os.system, os.popen"""
        if (isinstance(node.value, ast.Name) and
            node.value.id == "os" and
            node.attr in FORBIDDEN_OS_ATTRS):
            self.violations.append((
                node.lineno,
                f"forbidden usage: os.{node.attr}"
            ))
        self.generic_visit(node)


def scan_file_for_violations(filepath: Path) -> List[Tuple[str, int, str]]:
    """
    Scan a single Python file for forbidden imports/usages.

    Returns:
        List of (filepath, lineno, violation_description) tuples
    """
    try:
        source = filepath.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        # Report syntax errors but don't fail the scan
        return [(str(filepath), e.lineno or 0, f"syntax error: {e}")]

    visitor = ForbiddenImportVisitor(str(filepath))
    visitor.visit(tree)

    return [(str(filepath), lineno, desc) for lineno, desc in visitor.violations]


# Allowlist for files that are permitted to use specific forbidden modules.
# Each entry maps filename to a set of allowed module exceptions.
# These exceptions must be documented in the test output.
ALLOWED_EXCEPTIONS: Dict[str, Set[str]] = {
    # search_text.py uses subprocess for ripgrep integration with shell=False
    # This is a documented, reviewed exception for performance reasons.
    # The ripgrep invocation enforces: no shell, no symlink following, timeout.
    "search_text.py": {"subprocess"},
}


def scan_directory_for_violations(src_dir: Path) -> List[Tuple[str, int, str]]:
    """
    Scan all Python files in a directory for forbidden imports/usages.

    Returns:
        List of (filepath, lineno, violation_description) tuples
    """
    violations = []
    files_scanned = 0

    for py_file in src_dir.rglob('*.py'):
        # Skip __pycache__ directories
        if '__pycache__' in str(py_file):
            continue

        files_scanned += 1
        file_violations = scan_file_for_violations(py_file)

        # Filter out allowed exceptions for this file
        filename = py_file.name
        if filename in ALLOWED_EXCEPTIONS:
            allowed = ALLOWED_EXCEPTIONS[filename]
            file_violations = [
                (fp, lineno, desc) for fp, lineno, desc in file_violations
                if not any(mod in desc for mod in allowed)
            ]

        violations.extend(file_violations)

    return violations


class TestForbiddenImportsPolicy:
    """
    Test Suite B: Forbidden imports policy via AST static analysis.

    Uses stdlib ast module to parse all AirGap source files and detect
    forbidden imports/usages. No lazy-import gaps - this is static analysis.
    """

    def test_no_forbidden_imports_in_airgap_src(self):
        """
        Verify no forbidden imports exist in AirGap source files.

        Scans all *.py files under products/mcp-servers/ninobyte-airgap/src
        using AST parsing. Reports file, line number, and violation.
        """
        src_dir = Path(__file__).parent.parent / 'src'

        violations = scan_directory_for_violations(src_dir)

        if violations:
            report_lines = ["Forbidden imports detected:"]
            for filepath, lineno, desc in violations:
                # Use relative path for cleaner output
                rel_path = Path(filepath).relative_to(src_dir.parent)
                report_lines.append(f"  {rel_path}:{lineno}: {desc}")

            pytest.fail('\n'.join(report_lines))

    def test_files_were_actually_scanned(self):
        """Verify the scanner found and processed files."""
        src_dir = Path(__file__).parent.parent / 'src'

        py_files = [
            f for f in src_dir.rglob('*.py')
            if '__pycache__' not in str(f)
        ]

        # AirGap src should have multiple Python files
        assert len(py_files) >= 5, (
            f"Expected at least 5 Python files in {src_dir}, found {len(py_files)}"
        )

        # Key files should exist
        expected_files = [
            'context_cleaner_adapter.py',
            'path_security.py',
            'config.py',
        ]
        found_names = {f.name for f in py_files}
        for expected in expected_files:
            assert expected in found_names, f"Expected {expected} in src"

    def test_forbidden_module_set_is_complete(self):
        """Document the forbidden module set for visibility."""
        expected = {"socket", "subprocess", "requests", "urllib3", "httpx"}
        assert FORBIDDEN_MODULES == expected, \
            f"Forbidden modules set changed: {FORBIDDEN_MODULES}"

    def test_allowed_exceptions_are_documented(self):
        """
        Document allowed exceptions for visibility.

        Exceptions must be explicitly reviewed and documented:
        - search_text.py: subprocess allowed for ripgrep with shell=False
        """
        # Verify exceptions are limited and documented
        assert "search_text.py" in ALLOWED_EXCEPTIONS, \
            "search_text.py should be in allowed exceptions"
        assert ALLOWED_EXCEPTIONS["search_text.py"] == {"subprocess"}, \
            "search_text.py exception should only be subprocess"

        # No other files should have exceptions (add here if needed)
        assert len(ALLOWED_EXCEPTIONS) == 1, \
            f"Only search_text.py should have exceptions, found: {list(ALLOWED_EXCEPTIONS.keys())}"


# =============================================================================
# C) Error Contract Tests
# =============================================================================

class TestErrorContract:
    """
    Test Suite C: Error contract stability.

    Ensures invalid usage produces stable "Error: ..." prefix
    and appropriate exceptions.
    """

    def test_invalid_output_format_raises_context_cleaner_error(self):
        """Invalid output format should raise ContextCleanerError."""
        with pytest.raises(ContextCleanerError) as exc_info:
            clean_context_text("test", output_format="invalid_format")

        # Error message should have "Error:" prefix
        assert "Error:" in str(exc_info.value), \
            "Exception message must contain 'Error:' prefix"

    def test_path_traversal_raises_with_error_prefix(self, temp_dir):
        """Path traversal should raise LexiconPathDeniedError with Error prefix."""
        with pytest.raises(LexiconPathDeniedError) as exc_info:
            clean_context_text(
                "test",
                lexicon_path="../../../etc/passwd",
                allowed_roots=[str(temp_dir)],
                output_format="jsonl"
            )

        assert "Error:" in str(exc_info.value), \
            "LexiconPathDeniedError must contain 'Error:' prefix"

    def test_lexicon_outside_roots_raises_with_error_prefix(self, temp_dir):
        """Lexicon outside allowed roots raises with Error prefix."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write('{"test": "value"}')
            outside_path = f.name

        try:
            with pytest.raises(LexiconPathDeniedError) as exc_info:
                clean_context_text(
                    "test",
                    lexicon_path=outside_path,
                    allowed_roots=[str(temp_dir)],
                    output_format="jsonl"
                )

            assert "Error:" in str(exc_info.value)
        finally:
            os.unlink(outside_path)


# =============================================================================
# D) Adapter Contract Preservation
# =============================================================================

class TestAdapterContractPreservation:
    """
    Test Suite D: Adapter contract preservation.

    Ensures lexicon metadata is additive-only and reserved token
    protection remains intact.
    """

    def test_lexicon_meta_is_optional_and_additive(self, temp_dir):
        """
        Verify meta.lexicon is optional when lexicon not enabled,
        and present when lexicon is enabled (additive-only).
        """
        input_text = "Test text"

        # Without lexicon - meta.lexicon should NOT be present
        output_no_lex = clean_context_text(input_text, output_format="jsonl")
        parsed_no_lex = json.loads(output_no_lex.strip())

        assert "lexicon" not in parsed_no_lex["meta"], \
            "meta.lexicon should not be present when lexicon not enabled"

        # With lexicon - meta.lexicon should be present
        lexicon_path = temp_dir / "test_lexicon.json"
        lexicon_path.write_text('{"NYC": "New York City"}', encoding='utf-8')

        output_with_lex = clean_context_text(
            input_text,
            lexicon_path=str(lexicon_path),
            output_format="jsonl"
        )
        parsed_with_lex = json.loads(output_with_lex.strip())

        assert "lexicon" in parsed_with_lex["meta"], \
            "meta.lexicon should be present when lexicon is enabled"

    def test_reserved_token_protection_behavioral(self):
        """
        Verify reserved tokens like [EMAIL_REDACTED] are not modified by
        subsequent processing.
        """
        # Input that will produce redacted token
        input_text = "Contact user@test.com for info"

        output = clean_context_text(input_text, output_format="jsonl")
        parsed = json.loads(output.strip())

        # Redacted output should contain intact reserved token
        assert "[EMAIL_REDACTED]" in parsed["redacted"], \
            "[EMAIL_REDACTED] token must be present and intact"

        # Original email should not appear
        assert "user@test.com" not in parsed["redacted"], \
            "Original email should be redacted"

    def test_deterministic_output_across_runs(self):
        """Verify same input produces identical output across 3 runs."""
        input_text = "Test contact@example.com"

        outputs = []
        for _ in range(3):
            output = clean_context_text(input_text, output_format="jsonl")
            outputs.append(output.strip())

        assert outputs[0] == outputs[1] == outputs[2], \
            "Output must be deterministic across runs"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
