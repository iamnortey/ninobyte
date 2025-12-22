#!/usr/bin/env python3
"""
Deterministic smoke harness for ninobyte-context-cleaner.

Validates contract compliance without subprocess calls by directly invoking
the CLI's main() function with argv injection.

Security:
- No networking imports
- No file writes (except optional /tmp for diff if needed)
- Stdlib only

Exit Codes:
    0   SMOKE: PASS
    1   SMOKE: FAIL

Usage:
    PYTHONPATH=products/context-cleaner/src python products/context-cleaner/scripts/smoke_context_cleaner.py
"""

import io
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from typing import Callable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Test Infrastructure
# ---------------------------------------------------------------------------

class SmokeResult:
    """Result of a smoke test."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message


def capture_cli(args: List[str], stdin_text: str = "") -> Tuple[str, str, int]:
    """
    Run the CLI main() with captured stdout/stderr.

    Uses argv injection and stream redirection to avoid subprocess.

    Args:
        args: CLI arguments (without the program name)
        stdin_text: Text to provide as stdin

    Returns:
        (stdout, stderr, exit_code)
    """
    # Import here to avoid circular imports and ensure PYTHONPATH is set
    from ninobyte_context_cleaner.__main__ import main

    # Save originals
    orig_argv = sys.argv
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    # Capture streams
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    fake_stdin = io.StringIO(stdin_text)

    exit_code = 0

    try:
        sys.argv = ["ninobyte-context-cleaner"] + args
        sys.stdin = fake_stdin
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        exit_code = main()
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = orig_argv
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr

    return captured_stdout.getvalue(), captured_stderr.getvalue(), exit_code


# ---------------------------------------------------------------------------
# Smoke Tests
# ---------------------------------------------------------------------------

def test_stdin_jsonl_key_order() -> SmokeResult:
    """
    Test 1: stdin → jsonl produces valid JSONL with required key order.

    Contract: top-level keys must be meta → normalized → redacted
    """
    name = "stdin_jsonl_key_order"

    stdout, stderr, code = capture_cli(
        ["--output-format", "jsonl"],
        stdin_text="Contact test@example.com\n"
    )

    if code != 0:
        return SmokeResult(name, False, f"Exit code {code}, expected 0. Stderr: {stderr}")

    try:
        data = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        return SmokeResult(name, False, f"Invalid JSON: {e}")

    # Verify required keys exist
    required = ["meta", "normalized", "redacted"]
    for key in required:
        if key not in data:
            return SmokeResult(name, False, f"Missing required key: {key}")

    # Verify key order in raw string
    raw = stdout.strip()
    positions = {key: raw.find(f'"{key}"') for key in required}

    if not (positions["meta"] < positions["normalized"] < positions["redacted"]):
        return SmokeResult(name, False,
            f"Key order violation. Positions: {positions}")

    # Verify schema_version is "1" (string)
    if data["meta"].get("schema_version") != "1":
        return SmokeResult(name, False,
            f"schema_version must be '1', got: {data['meta'].get('schema_version')!r}")

    return SmokeResult(name, True)


def test_normalized_explicit_null() -> SmokeResult:
    """
    Test 2: normalized is explicitly null when --normalize-tables is OFF.

    Contract: "normalized":null must appear in raw output (not omitted).
    """
    name = "normalized_explicit_null"

    stdout, stderr, code = capture_cli(
        ["--output-format", "jsonl"],
        stdin_text="test@example.com\n"
    )

    if code != 0:
        return SmokeResult(name, False, f"Exit code {code}")

    # Check raw string contains explicit null
    if '"normalized":null' not in stdout:
        return SmokeResult(name, False,
            f"Expected '\"normalized\":null' in output. Got: {stdout[:200]}")

    # Also verify via parsing
    data = json.loads(stdout.strip())
    if data.get("normalized") is not None:
        return SmokeResult(name, False, "normalized should be null")

    return SmokeResult(name, True)


def test_normalized_string_with_tables() -> SmokeResult:
    """
    Test 3: normalized becomes a string when --normalize-tables is ON.

    Contract: with a pipe table input, normalized should be a string (not null).
    """
    name = "normalized_string_with_tables"

    # Simple pipe table
    table_input = "| Name | Email |\n|------|-------|\n| John | john@test.com |\n"

    stdout, stderr, code = capture_cli(
        ["--output-format", "jsonl", "--normalize-tables"],
        stdin_text=table_input
    )

    if code != 0:
        return SmokeResult(name, False, f"Exit code {code}")

    data = json.loads(stdout.strip())

    # normalized must be a string, not null
    if data.get("normalized") is None:
        return SmokeResult(name, False, "normalized should be a string, got null")

    if not isinstance(data["normalized"], str):
        return SmokeResult(name, False,
            f"normalized should be str, got {type(data['normalized']).__name__}")

    # Verify table was actually normalized (should contain key:value style)
    # The exact format is implementation-dependent, but it should differ from input
    if data["normalized"] == table_input:
        return SmokeResult(name, False, "normalized output equals raw input (no normalization)")

    return SmokeResult(name, True)


def test_lexicon_meta_present() -> SmokeResult:
    """
    Test 4: meta.lexicon exists when --lexicon is used.

    Contract: lexicon metadata is additive; reserved tokens are preserved.
    """
    name = "lexicon_meta_present"

    # Create a temporary lexicon file
    lexicon = {"NYC": "New York City"}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(lexicon, f)
        lexicon_path = f.name

    try:
        stdout, stderr, code = capture_cli(
            ["--output-format", "jsonl", "--lexicon", lexicon_path],
            stdin_text="Visit NYC today!\n"
        )

        if code != 0:
            return SmokeResult(name, False, f"Exit code {code}. Stderr: {stderr}")

        data = json.loads(stdout.strip())

        # Verify lexicon meta exists
        if "lexicon" not in data.get("meta", {}):
            return SmokeResult(name, False, "meta.lexicon not present")

        lexicon_meta = data["meta"]["lexicon"]

        # Verify expected fields
        if not lexicon_meta.get("enabled"):
            return SmokeResult(name, False, "lexicon.enabled should be true")

        if lexicon_meta.get("rules_count") != 1:
            return SmokeResult(name, False,
                f"lexicon.rules_count should be 1, got {lexicon_meta.get('rules_count')}")

        # Verify substitution occurred
        if "New York City" not in data.get("redacted", ""):
            return SmokeResult(name, False, "Lexicon substitution did not occur")

    finally:
        os.unlink(lexicon_path)

    return SmokeResult(name, True)


def test_reserved_token_protection() -> SmokeResult:
    """
    Test 4b: Reserved tokens ([UPPER_CASE]) are protected from lexicon.

    Contract: existing placeholders like [EMAIL_REDACTED] are never modified.
    """
    name = "reserved_token_protection"

    # Lexicon that tries to replace a reserved token
    lexicon = {"EMAIL": "electronic mail", "[EMAIL_REDACTED]": "BROKEN"}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(lexicon, f)
        lexicon_path = f.name

    try:
        # Input contains a pre-existing reserved token
        stdout, stderr, code = capture_cli(
            ["--output-format", "jsonl", "--lexicon", lexicon_path],
            stdin_text="Contact: [EMAIL_REDACTED] and user@test.com\n"
        )

        if code != 0:
            return SmokeResult(name, False, f"Exit code {code}")

        data = json.loads(stdout.strip())
        redacted = data.get("redacted", "")

        # Reserved token must NOT be modified to "BROKEN"
        if "BROKEN" in redacted:
            return SmokeResult(name, False,
                "Reserved token was modified by lexicon (contract violation)")

        # Email in input should be redacted (not the pre-existing token, but new email)
        if "[EMAIL_REDACTED]" not in redacted:
            return SmokeResult(name, False, "Expected [EMAIL_REDACTED] in output")

    finally:
        os.unlink(lexicon_path)

    return SmokeResult(name, True)


def test_path_traversal_rejected() -> SmokeResult:
    """
    Test 5: Path traversal is rejected with exit code 2.

    Contract: --input with '..' segments must fail with code 2.
    """
    name = "path_traversal_rejected"

    # Attempt path traversal with RELATIVE path (survives normpath)
    # Absolute paths like /tmp/../../../etc/passwd normalize to /etc/passwd
    # which loses the ".." segments. Relative paths preserve them.
    stdout, stderr, code = capture_cli(
        ["--input", "../../../etc/passwd"],
        stdin_text=""
    )

    if code != 2:
        return SmokeResult(name, False,
            f"Expected exit code 2 for path traversal, got {code}")

    # Should have error message about traversal
    if "traversal" not in stderr.lower() and ".." not in stderr:
        return SmokeResult(name, False,
            f"Expected traversal error message. Stderr: {stderr}")

    return SmokeResult(name, True)


def test_pdf_extras_handling() -> SmokeResult:
    """
    Test 6: PDF extras handling.

    If pdf extras installed: PDF input works.
    If not installed: clear error and exit 2 (SKIPPED, not FAIL).
    """
    name = "pdf_extras_handling"

    # Check if pypdf is available
    try:
        import pypdf
        pdf_available = True
    except ImportError:
        pdf_available = False

    if not pdf_available:
        # Extras not installed - verify clear error message
        # Use --input-type pdf to force PDF mode without needing a file
        # This should fail because we need a file, but error should mention dependency

        # Create a minimal "PDF" file (just for path check - will fail on parse)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 minimal')
            pdf_path = f.name

        try:
            stdout, stderr, code = capture_cli(
                ["--input", pdf_path],
                stdin_text=""
            )

            if code != 2:
                return SmokeResult(name, False,
                    f"Expected exit 2 when PDF extras missing, got {code}")

            # Should mention pip install or optional dependency
            if "pdf" not in stderr.lower():
                return SmokeResult(name, False,
                    f"Expected PDF-related error. Stderr: {stderr}")

        finally:
            os.unlink(pdf_path)

        return SmokeResult(name, True, "SKIPPED (pdf extras not installed)")

    # PDF extras ARE installed - verify PDF processing works
    # Create a minimal valid PDF is complex, so we just verify the import works
    # and the extractor can be instantiated
    try:
        from ninobyte_context_cleaner.pdf_extractor import PDFExtractor, is_pdf_available

        if not is_pdf_available():
            return SmokeResult(name, False, "is_pdf_available() returns False but pypdf imported")

        # Instantiation should work
        extractor = PDFExtractor()

    except Exception as e:
        return SmokeResult(name, False, f"PDF extractor error: {e}")

    return SmokeResult(name, True, "pdf extras available")


def test_determinism() -> SmokeResult:
    """
    Test 7: Same input produces identical output across runs.

    Contract: deterministic output (no timestamps, random IDs, etc.)
    """
    name = "determinism"

    input_text = "Contact john@example.com or call 555-123-4567\n"

    outputs = []
    for _ in range(3):
        stdout, stderr, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text=input_text
        )

        if code != 0:
            return SmokeResult(name, False, f"Exit code {code} on run")

        outputs.append(stdout)

    # All outputs must be byte-identical
    if not all(o == outputs[0] for o in outputs):
        return SmokeResult(name, False,
            "Output differs across runs (non-deterministic)")

    return SmokeResult(name, True)


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------

def run_smoke_tests() -> bool:
    """
    Run all smoke tests and print results.

    Returns:
        True if all tests pass, False otherwise.
    """
    tests = [
        test_stdin_jsonl_key_order,
        test_normalized_explicit_null,
        test_normalized_string_with_tables,
        test_lexicon_meta_present,
        test_reserved_token_protection,
        test_path_traversal_rejected,
        test_pdf_extras_handling,
        test_determinism,
    ]

    print("=" * 60)
    print("SMOKE HARNESS: ninobyte-context-cleaner")
    print("=" * 60)
    print()

    results = []
    for test_fn in tests:
        try:
            result = test_fn()
        except Exception as e:
            result = SmokeResult(test_fn.__name__, False, f"Exception: {e}")

        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        msg = f" ({result.message})" if result.message else ""
        print(f"[{status}] {result.name}{msg}")

    print()
    print("-" * 60)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    print(f"Results: {passed} passed, {failed} failed")
    print()

    if failed == 0:
        print("SMOKE: PASS")
        return True
    else:
        print("SMOKE: FAIL")
        return False


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
