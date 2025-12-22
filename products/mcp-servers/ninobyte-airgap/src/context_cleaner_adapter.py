"""
AirGap ContextCleaner Adapter

Provides in-process integration with ninobyte-context-cleaner for deterministic
PII redaction. Runs ContextCleaner via argv injection + stream capture without
subprocess invocation.

Consumer Contract:
- Schema v1 JSONL output preserved (meta → normalized → redacted)
- Deterministic across runs
- Reserved token protection intact
- AirGap path security enforced for lexicon paths

Security:
- No subprocess usage (in-process only)
- No network access
- No shell execution
- Reuses AirGap path security for lexicon paths
"""

import io
import os
import sys
from typing import Optional

try:
    from .path_security import PathSecurityContext, PathDenialReason
    from .config import AirGapConfig
except ImportError:
    from path_security import PathSecurityContext, PathDenialReason
    from config import AirGapConfig


class ContextCleanerNotAvailableError(Exception):
    """Raised when ninobyte-context-cleaner is not available for import."""
    pass


class ContextCleanerError(Exception):
    """Raised when ContextCleaner execution fails."""
    pass


class LexiconPathDeniedError(Exception):
    """Raised when lexicon path fails AirGap path security validation."""
    pass


def _validate_lexicon_path_airgap(
    lexicon_path: str,
    allowed_roots: list[str]
) -> str:
    """
    Validate lexicon path using AirGap path security.

    Args:
        lexicon_path: The lexicon file path to validate
        allowed_roots: List of allowed root directories

    Returns:
        Canonical path if valid

    Raises:
        LexiconPathDeniedError: If path fails security validation
    """
    if not allowed_roots:
        raise LexiconPathDeniedError(
            "Error: No allowed roots configured for lexicon path validation"
        )

    config = AirGapConfig(allowed_roots=allowed_roots)
    security_ctx = PathSecurityContext(config)

    result = security_ctx.validate_path(lexicon_path)

    if not result.allowed:
        reason = result.denial_reason
        detail = result.denial_detail or ""

        if reason == PathDenialReason.TRAVERSAL_DETECTED:
            raise LexiconPathDeniedError(
                f"Error: Path traversal detected in lexicon path: {detail}"
            )
        elif reason == PathDenialReason.OUTSIDE_ALLOWED_ROOTS:
            raise LexiconPathDeniedError(
                f"Error: Lexicon path outside allowed roots: {detail}"
            )
        elif reason == PathDenialReason.BLOCKED_PATTERN:
            raise LexiconPathDeniedError(
                f"Error: Lexicon path matches blocked pattern: {detail}"
            )
        elif reason == PathDenialReason.SYMLINK_ESCAPE:
            raise LexiconPathDeniedError(
                f"Error: Lexicon path symlink escapes allowed roots: {detail}"
            )
        else:
            raise LexiconPathDeniedError(
                f"Error: Lexicon path denied: {detail}"
            )

    return result.canonical_path


def clean_context_text(
    text: str,
    *,
    normalize_tables: bool = False,
    lexicon_path: Optional[str] = None,
    input_type: str = "text",
    output_format: str = "jsonl",
    allowed_roots: Optional[list[str]] = None
) -> str:
    """
    Clean context text using ContextCleaner in-process.

    Runs ninobyte-context-cleaner via argv injection and stream capture,
    without subprocess invocation. Preserves Schema v1 JSONL contract.

    Pipeline Order:
    1. (optional) Table normalization
    2. (optional) Lexicon injection
    3. PII redaction (always)
    4. Output formatting

    Args:
        text: Input text to process
        normalize_tables: Enable table normalization (CSV/TSV/pipe tables)
        lexicon_path: Path to lexicon JSON file (AirGap-validated if allowed_roots provided)
        input_type: Input type (text, auto, pdf)
        output_format: Output format (text, jsonl)
        allowed_roots: AirGap allowed roots for lexicon path validation

    Returns:
        Processed output (JSONL line or plain text depending on output_format)

    Raises:
        ContextCleanerNotAvailableError: If ContextCleaner cannot be imported
        ContextCleanerError: If ContextCleaner processing fails
        LexiconPathDeniedError: If lexicon_path fails AirGap security validation
    """
    # Validate lexicon path with AirGap security if provided
    if lexicon_path is not None:
        if allowed_roots is not None:
            # Apply AirGap path security
            _validate_lexicon_path_airgap(lexicon_path, allowed_roots)
        # Note: ContextCleaner also has its own path security (is_safe_lexicon_path)
        # which will be applied by the main() function

    # Try to import ContextCleaner
    try:
        from ninobyte_context_cleaner.__main__ import main as context_cleaner_main
    except ImportError as e:
        raise ContextCleanerNotAvailableError(
            f"Error: ninobyte-context-cleaner not available: {e}"
        ) from e

    # Build argv
    argv = []

    if normalize_tables:
        argv.append("--normalize-tables")

    if lexicon_path is not None:
        argv.extend(["--lexicon", lexicon_path])

    if input_type != "auto":
        argv.extend(["--input-type", input_type])

    argv.extend(["--output-format", output_format])

    # Capture stdin/stdout
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    original_argv = sys.argv

    stdin_capture = io.StringIO(text)
    stdout_capture = io.StringIO()

    try:
        # Inject streams and argv
        sys.stdin = stdin_capture
        sys.stdout = stdout_capture
        sys.argv = ["ninobyte-context-cleaner"] + argv

        # Run ContextCleaner in-process
        exit_code = context_cleaner_main()

        # Get output
        output = stdout_capture.getvalue()

        if exit_code != 0:
            raise ContextCleanerError(
                f"Error: ContextCleaner returned exit code {exit_code}"
            )

        return output

    finally:
        # Restore original streams and argv
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        sys.argv = original_argv
