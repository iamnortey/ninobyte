"""
AirGap ContextCleaner Integration Tests

Validates the consumer contract between AirGap and ContextCleaner:
- Schema v1 JSONL contract preserved (meta → normalized → redacted)
- Deterministic output across runs
- Reserved token protection intact
- Security posture (no network, no shell, no writes in src)
- Path traversal blocked for lexicon paths

Test Categories:
A) Schema v1 contract (key order, schema_version)
B) Normalized field explicit null
C) Determinism across runs
D) Reserved token protection (regex proof)
E) Lexicon injection + PII redaction chain
F) Path traversal blocking
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

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
    ContextCleanerNotAvailableError,
    ContextCleanerError,
    LexiconPathDeniedError,
)


class TestJsonlSchemaV1Contract:
    """Test Suite A: JSONL Schema v1 contract preservation."""

    def test_jsonl_schema_v1_key_order_preserved(self):
        """
        A) Verify top-level keys appear in order: meta, normalized, redacted.

        Schema v1 Contract:
        - Top-level key order must be: "meta" then "normalized" then "redacted"
        - meta.schema_version must be "1" (string)
        """
        input_text = "Contact me at john.doe@example.com for more info."

        output = clean_context_text(
            input_text,
            output_format="jsonl"
        )

        # Strip any trailing whitespace/newlines
        output = output.strip()

        # Verify it's valid JSON
        parsed = json.loads(output)

        # Check schema_version is "1" (string)
        assert parsed["meta"]["schema_version"] == "1", \
            "meta.schema_version must be string '1'"

        # Verify key order in raw JSON string
        # Keys must appear in order: meta, normalized, redacted
        meta_pos = output.find('"meta"')
        normalized_pos = output.find('"normalized"')
        redacted_pos = output.find('"redacted"')

        assert meta_pos != -1, "meta key must be present"
        assert normalized_pos != -1, "normalized key must be present"
        assert redacted_pos != -1, "redacted key must be present"

        assert meta_pos < normalized_pos < redacted_pos, \
            f"Key order must be meta({meta_pos}) < normalized({normalized_pos}) < redacted({redacted_pos})"

    def test_email_is_redacted(self):
        """Verify email addresses are properly redacted."""
        input_text = "Email me at test@example.org"

        output = clean_context_text(
            input_text,
            output_format="jsonl"
        )

        parsed = json.loads(output.strip())

        # Redacted field should contain [EMAIL_REDACTED]
        assert "[EMAIL_REDACTED]" in parsed["redacted"], \
            "Email should be redacted to [EMAIL_REDACTED]"
        assert "test@example.org" not in parsed["redacted"], \
            "Original email should not appear in redacted output"


class TestNormalizedFieldContract:
    """Test Suite B: Normalized field explicit null contract."""

    def test_normalized_is_explicit_null_when_normalize_tables_false(self):
        """
        B) Verify normalized field is explicitly null (not missing) when
        normalize_tables is False.
        """
        input_text = "Simple text without tables."

        output = clean_context_text(
            input_text,
            normalize_tables=False,
            output_format="jsonl"
        )

        output = output.strip()

        # Check that "normalized":null appears in the raw JSON
        assert '"normalized":null' in output, \
            "normalized field must be explicitly null, not missing"

        # Verify via parsing too
        parsed = json.loads(output)
        assert "normalized" in parsed, "normalized key must exist"
        assert parsed["normalized"] is None, "normalized value must be None"

    def test_normalized_is_string_when_normalize_tables_true(self):
        """Verify normalized field is a string when normalize_tables is True."""
        input_text = "Name,Email\nJohn,john@test.com"

        output = clean_context_text(
            input_text,
            normalize_tables=True,
            output_format="jsonl"
        )

        parsed = json.loads(output.strip())

        assert parsed["normalized"] is not None, \
            "normalized should not be null when normalize_tables=True"
        assert isinstance(parsed["normalized"], str), \
            "normalized must be a string"


class TestDeterminism:
    """Test Suite C: Deterministic output across runs."""

    def test_determinism_three_runs_identical(self):
        """
        C) Same input 3 times must yield identical output.

        This validates:
        - No timestamps in output that vary
        - No random/unique identifiers
        - Stable key ordering
        - Stable redaction
        """
        input_text = "Contact Jane Smith at jane.smith@company.com or call 555-123-4567."

        outputs = []
        for i in range(3):
            output = clean_context_text(
                input_text,
                output_format="jsonl"
            )
            outputs.append(output.strip())

        # All three runs must produce identical output
        assert outputs[0] == outputs[1], \
            f"Run 1 and 2 differ:\nRun 1: {outputs[0]}\nRun 2: {outputs[1]}"
        assert outputs[1] == outputs[2], \
            f"Run 2 and 3 differ:\nRun 2: {outputs[1]}\nRun 3: {outputs[2]}"

    def test_determinism_with_lexicon(self, temp_lexicon_file):
        """Verify determinism is preserved when using lexicon."""
        input_text = "The ACME company is great."

        outputs = []
        for _ in range(3):
            output = clean_context_text(
                input_text,
                lexicon_path=temp_lexicon_file,
                output_format="jsonl"
            )
            outputs.append(output.strip())

        assert outputs[0] == outputs[1] == outputs[2], \
            "Lexicon-processed output must be deterministic"


class TestReservedTokenProtection:
    """Test Suite D: Reserved token protection (regex proof)."""

    def test_reserved_token_pattern_exists_in_lexicon_module(self):
        r"""
        D) Validate reserved token pattern is present in lexicon.py.

        Uses stdlib regex to verify the pattern r"\[[A-Z0-9_]+\]" is defined.
        This is a proof that the protection mechanism exists.
        """
        lexicon_path = Path(__file__).parent.parent.parent.parent / \
            'context-cleaner' / 'src' / 'ninobyte_context_cleaner' / 'lexicon.py'

        assert lexicon_path.exists(), f"lexicon.py not found at {lexicon_path}"

        content = lexicon_path.read_text(encoding='utf-8')

        # Search for reserved token pattern definition
        # Expected: RESERVED_TOKEN_PATTERN = re.compile(r'\[[A-Z0-9_]+\]')
        pattern = r"\[A-Z0-9_\]\+"

        # Also check for the literal pattern in the file
        assert r"[A-Z0-9_]" in content, \
            "Reserved token pattern not found in lexicon.py"

        # Count occurrences of reserved token pattern usage
        matches = re.findall(r'\[[A-Z0-9_]+\]', content)
        assert len(matches) >= 1, \
            "At least one reserved token pattern usage expected in lexicon.py"

    def test_reserved_tokens_protected_in_output(self):
        """Verify reserved tokens like [EMAIL_REDACTED] are not modified."""
        # Input that will produce redacted tokens
        input_text = "Email: user@test.com"

        output = clean_context_text(
            input_text,
            output_format="jsonl"
        )

        parsed = json.loads(output.strip())

        # The redacted output should contain intact reserved tokens
        assert "[EMAIL_REDACTED]" in parsed["redacted"], \
            "Reserved token [EMAIL_REDACTED] must be present and intact"


class TestLexiconIntegration:
    """Test Suite E: Lexicon injection + PII redaction chain."""

    def test_lexicon_can_inject_then_pii_redacts(self, temp_dir):
        """
        E) Lexicon expands token to email, then PII redactor removes it.

        Flow:
        1. Input: "Contact ACME for details"
        2. Lexicon: "ACME" -> "contact@acme.com"
        3. After lexicon: "Contact contact@acme.com for details"
        4. After PII redaction: "Contact [EMAIL_REDACTED] for details"
        """
        # Create lexicon that expands ACME to an email
        lexicon_path = temp_dir / "email_lexicon.json"
        lexicon_path.write_text(
            json.dumps({"ACME": "contact@acme.com"}),
            encoding='utf-8'
        )

        input_text = "Contact ACME for details"

        output = clean_context_text(
            input_text,
            lexicon_path=str(lexicon_path),
            output_format="jsonl"
        )

        parsed = json.loads(output.strip())

        # The expanded email should be redacted
        assert "[EMAIL_REDACTED]" in parsed["redacted"], \
            "Lexicon-injected email should be redacted"
        assert "contact@acme.com" not in parsed["redacted"], \
            "Original email should not appear in redacted output"
        assert "ACME" not in parsed["redacted"], \
            "ACME should be replaced by lexicon and then redacted"


class TestPathTraversalBlocking:
    """Test Suite F: Path traversal blocking for lexicon paths."""

    def test_path_traversal_blocked_for_lexicon_path(self, temp_dir):
        """
        F) Pass lexicon_path like ../../../etc/passwd and assert failure.

        AirGap path security must block traversal attempts.
        """
        # Attempt path traversal
        traversal_path = "../../../etc/passwd"

        with pytest.raises(LexiconPathDeniedError) as exc_info:
            clean_context_text(
                "test input",
                lexicon_path=traversal_path,
                allowed_roots=[str(temp_dir)],
                output_format="jsonl"
            )

        assert "Error:" in str(exc_info.value), \
            "Error message must start with 'Error:'"
        # Should mention traversal
        error_lower = str(exc_info.value).lower()
        assert "traversal" in error_lower or "outside" in error_lower, \
            "Error should mention traversal or outside allowed roots"

    def test_lexicon_outside_allowed_roots_blocked(self, temp_dir):
        """Lexicon path outside allowed roots is blocked."""
        # Create a file outside allowed roots
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            f.write('{"test": "value"}')
            outside_path = f.name

        try:
            # temp_dir is allowed, but outside_path is in system temp
            # They should be different roots
            with pytest.raises(LexiconPathDeniedError) as exc_info:
                clean_context_text(
                    "test input",
                    lexicon_path=outside_path,
                    allowed_roots=[str(temp_dir)],
                    output_format="jsonl"
                )

            assert "Error:" in str(exc_info.value)
        finally:
            os.unlink(outside_path)

    def test_lexicon_in_allowed_root_succeeds(self, temp_dir):
        """Lexicon path within allowed roots succeeds."""
        # Create lexicon in allowed root
        lexicon_path = temp_dir / "valid_lexicon.json"
        lexicon_path.write_text('{"test": "value"}', encoding='utf-8')

        # Should not raise
        output = clean_context_text(
            "test input",
            lexicon_path=str(lexicon_path),
            allowed_roots=[str(temp_dir)],
            output_format="jsonl"
        )

        assert output.strip(), "Output should not be empty"


class TestSecurityPosture:
    """Verify security posture is maintained."""

    def test_no_subprocess_in_adapter(self):
        """Verify adapter does not use subprocess module."""
        adapter_path = Path(__file__).parent.parent / 'src' / 'context_cleaner_adapter.py'

        content = adapter_path.read_text(encoding='utf-8')

        # Check that subprocess is not imported or used
        assert "import subprocess" not in content, \
            "Adapter must not import subprocess"
        assert "from subprocess" not in content, \
            "Adapter must not import from subprocess"
        assert "subprocess.run" not in content, \
            "Adapter must not use subprocess.run"
        assert "subprocess.Popen" not in content, \
            "Adapter must not use subprocess.Popen"

    def test_no_network_in_adapter(self):
        """Verify adapter does not use networking modules."""
        adapter_path = Path(__file__).parent.parent / 'src' / 'context_cleaner_adapter.py'

        content = adapter_path.read_text(encoding='utf-8')

        forbidden_imports = [
            "import socket",
            "import urllib",
            "import http",
            "import requests",
            "from socket",
            "from urllib",
            "from http",
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in content, \
                f"Adapter must not contain: {forbidden}"

    def test_no_shell_in_adapter(self):
        """Verify adapter does not use shell execution."""
        adapter_path = Path(__file__).parent.parent / 'src' / 'context_cleaner_adapter.py'

        content = adapter_path.read_text(encoding='utf-8')

        forbidden = [
            "os.system",
            "os.popen",
            "shell=True",
        ]

        for pattern in forbidden:
            assert pattern not in content, \
                f"Adapter must not contain: {pattern}"


class TestErrorHandling:
    """Test error handling and exit codes."""

    def test_invalid_output_format_raises(self):
        """Invalid output format should raise ContextCleanerError."""
        with pytest.raises(ContextCleanerError):
            clean_context_text(
                "test input",
                output_format="invalid_format"
            )


# Fixtures

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_lexicon_file(temp_dir):
    """Create a temporary lexicon file."""
    lexicon_path = temp_dir / "test_lexicon.json"
    lexicon_path.write_text(
        json.dumps({"NYC": "New York City", "LA": "Los Angeles"}),
        encoding='utf-8'
    )
    return str(lexicon_path)
