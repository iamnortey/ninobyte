"""
CLI entrypoint for ninobyte-context-cleaner.

Usage:
    python -m ninobyte_context_cleaner [OPTIONS]

Reads text from STDIN (or file), writes processed output to STDOUT.

Options:
    --help              Show this help message and exit
    --version           Show version and exit
    --normalize-tables  Convert table-like content to key:value format
    --input <path>      Read from file instead of STDIN (read-only)
    --output-format <fmt>  Output format: text (default) or jsonl

Exit Codes:
    0   Success
    2   Invalid usage (unknown flags, bad path, etc.)
"""

import json
import os
import sys
from typing import List, Optional, Tuple

from ninobyte_context_cleaner.redactor import PIIRedactor
from ninobyte_context_cleaner.table_normalizer import TableNormalizer
from ninobyte_context_cleaner.version import __version__


USAGE = """\
Usage: python -m ninobyte_context_cleaner [OPTIONS]

Deterministic PII redaction and text normalization for LLM context preparation.

Reads text from STDIN (or file), writes processed output to STDOUT.

Options:
  --help              Show this help message and exit
  --version           Show version and exit
  --normalize-tables  Convert table-like content to key:value format
                      (pipe tables, CSV, TSV)
  --input <path>      Read from file instead of STDIN (read-only)
  --output-format <fmt>  Output format: text (default) or jsonl

Output Formats:
  text    Plain text output (default)
  jsonl   JSON Lines with metadata:
          {"redacted":"...","normalized":"..."|null,"meta":{...}}

Processing Order:
  1. PII redaction (always applied)
  2. Table normalization (only if --normalize-tables is set)

Examples:
  # Basic PII redaction from STDIN
  echo "Contact john@example.com" | python -m ninobyte_context_cleaner

  # Read from file
  python -m ninobyte_context_cleaner --input document.txt

  # JSONL output for pipelines
  echo "test@example.com" | python -m ninobyte_context_cleaner --output-format jsonl

  # Combined: file input, table normalization, JSONL output
  python -m ninobyte_context_cleaner --input data.txt --normalize-tables --output-format jsonl
"""

# Known flags (without arguments)
KNOWN_FLAGS = {"--help", "--version", "--normalize-tables"}

# Known options (with arguments)
KNOWN_OPTIONS = {"--input", "--output-format"}

# Valid output formats
VALID_OUTPUT_FORMATS = {"text", "jsonl"}


def is_safe_path(path: str) -> Tuple[bool, str]:
    """
    Validate that a file path is safe for reading.

    Security rules:
    - Reject paths containing ".." after normalization
    - Path must exist and be a file (not directory)

    Returns:
        (is_safe, error_message)
    """
    # Normalize the path
    normalized = os.path.normpath(path)

    # Reject directory traversal attempts
    if ".." in normalized.split(os.sep):
        return False, "Path traversal not allowed: '..' segments rejected"

    # Check if path exists
    if not os.path.exists(normalized):
        return False, f"File not found: {path}"

    # Must be a file, not a directory
    if not os.path.isfile(normalized):
        return False, f"Not a file: {path}"

    return True, ""


def parse_args(args: List[str]) -> Tuple[dict, Optional[str]]:
    """
    Parse command-line arguments.

    Returns:
        (parsed_options, error_message)
        error_message is None on success
    """
    options = {
        "normalize_tables": False,
        "input_path": None,
        "output_format": "text",
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in KNOWN_FLAGS:
            if arg == "--normalize-tables":
                options["normalize_tables"] = True
            i += 1
            continue

        if arg in KNOWN_OPTIONS:
            # These require a value
            if i + 1 >= len(args):
                return {}, f"Option '{arg}' requires a value"

            value = args[i + 1]

            if arg == "--input":
                options["input_path"] = value
            elif arg == "--output-format":
                if value not in VALID_OUTPUT_FORMATS:
                    return {}, f"Invalid output format '{value}'. Use: text, jsonl"
                options["output_format"] = value

            i += 2
            continue

        # Unknown argument
        if arg.startswith("-"):
            return {}, f"Unknown option '{arg}'"
        else:
            return {}, f"Unexpected argument '{arg}'"

    return options, None


def format_jsonl_output(
    redacted: str,
    normalized: Optional[str],
    normalize_tables: bool,
    source: str
) -> str:
    """
    Format output as JSONL (single line JSON).

    Schema:
    {
        "redacted": "...",
        "normalized": "..." | null,
        "meta": {
            "version": "0.1.0",
            "normalize_tables": true/false,
            "source": "stdin" | "file"
        }
    }

    Field order is deterministic (sorted keys).
    """
    output = {
        "meta": {
            "normalize_tables": normalize_tables,
            "source": source,
            "version": __version__,
        },
        "normalized": normalized,
        "redacted": redacted,
    }

    # Use sort_keys for deterministic output
    return json.dumps(output, ensure_ascii=False, sort_keys=True)


def main() -> int:
    """
    Main CLI entrypoint.

    Returns:
        Exit code: 0 on success, 2 on invalid usage
    """
    args = sys.argv[1:]

    # Handle info flags first (before parsing)
    if "--help" in args:
        print(USAGE)
        return 0

    if "--version" in args:
        print(f"ninobyte-context-cleaner {__version__}")
        return 0

    # Parse arguments
    options, error = parse_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        print("Use --help for usage information.", file=sys.stderr)
        return 2

    normalize_tables = options["normalize_tables"]
    input_path = options["input_path"]
    output_format = options["output_format"]

    # Validate input path if provided
    if input_path:
        is_safe, path_error = is_safe_path(input_path)
        if not is_safe:
            print(f"Error: {path_error}", file=sys.stderr)
            return 2

    # Determine source
    source = "file" if input_path else "stdin"

    # Initialize processors
    redactor = PIIRedactor()
    normalizer = TableNormalizer() if normalize_tables else None

    try:
        # Read input
        if input_path:
            with open(input_path, 'r', encoding='utf-8') as f:
                input_text = f.read()
        else:
            input_text = sys.stdin.read()

        # Step 1: PII redaction (always applied)
        redacted_text = redactor.redact(input_text)

        # Step 2: Table normalization (if flag set)
        normalized_text: Optional[str] = None
        if normalizer:
            normalized_text = normalizer.normalize(redacted_text)

        # Format output
        if output_format == "jsonl":
            output = format_jsonl_output(
                redacted=redacted_text,
                normalized=normalized_text,
                normalize_tables=normalize_tables,
                source=source
            )
            print(output)
        else:
            # Plain text: use normalized if available, else redacted
            final_text = normalized_text if normalized_text is not None else redacted_text
            sys.stdout.write(final_text)

        return 0

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        return 130
    except IOError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
