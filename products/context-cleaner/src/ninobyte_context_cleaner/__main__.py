"""
CLI entrypoint for ninobyte-context-cleaner.

Usage:
    python -m ninobyte_context_cleaner [OPTIONS]

Reads text from STDIN, writes processed output to STDOUT.

Options:
    --help              Show this help message and exit
    --version           Show version and exit
    --normalize-tables  Convert table-like content to key:value format

Exit Codes:
    0   Success
    2   Invalid usage (unknown flags, unexpected args)
"""

import sys

from ninobyte_context_cleaner.redactor import PIIRedactor
from ninobyte_context_cleaner.table_normalizer import TableNormalizer
from ninobyte_context_cleaner.version import __version__


USAGE = """\
Usage: python -m ninobyte_context_cleaner [OPTIONS]

Deterministic PII redaction and text normalization for LLM context preparation.

Reads text from STDIN, writes processed output to STDOUT.

Options:
  --help              Show this help message and exit
  --version           Show version and exit
  --normalize-tables  Convert table-like content to key:value format
                      (pipe tables, CSV, TSV)

Processing Order:
  1. PII redaction (always applied)
  2. Table normalization (only if --normalize-tables is set)

Examples:
  # Basic PII redaction
  echo "Contact john@example.com" | python -m ninobyte_context_cleaner

  # With table normalization
  echo "| Name | Email |
  | John | john@example.com |" | python -m ninobyte_context_cleaner --normalize-tables

  # Process a file with all transforms
  cat document.txt | python -m ninobyte_context_cleaner --normalize-tables > cleaned.txt
"""

# Known flags that we accept
KNOWN_FLAGS = {"--help", "--version", "--normalize-tables"}


def main() -> int:
    """
    Main CLI entrypoint.

    Returns:
        Exit code: 0 on success, 2 on invalid usage
    """
    args = sys.argv[1:]

    # Handle info flags first
    if "--help" in args:
        print(USAGE)
        return 0

    if "--version" in args:
        print(f"ninobyte-context-cleaner {__version__}")
        return 0

    # Parse flags
    normalize_tables = "--normalize-tables" in args

    # Check for unknown flags or unexpected arguments
    for arg in args:
        if arg.startswith("-"):
            if arg not in KNOWN_FLAGS:
                print(f"Error: Unknown option '{arg}'", file=sys.stderr)
                print("Use --help for usage information.", file=sys.stderr)
                return 2
        else:
            print(f"Error: Unexpected argument '{arg}'", file=sys.stderr)
            print("Use --help for usage information.", file=sys.stderr)
            return 2

    # Initialize processors
    redactor = PIIRedactor()
    normalizer = TableNormalizer() if normalize_tables else None

    try:
        input_text = sys.stdin.read()

        # Step 1: PII redaction (always applied)
        output_text = redactor.redact(input_text)

        # Step 2: Table normalization (if flag set)
        if normalizer:
            output_text = normalizer.normalize(output_text)

        sys.stdout.write(output_text)
        return 0
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        return 130


if __name__ == "__main__":
    sys.exit(main())
