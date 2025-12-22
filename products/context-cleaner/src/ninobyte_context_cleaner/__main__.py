"""
CLI entrypoint for ninobyte-context-cleaner.

Usage:
    python -m ninobyte_context_cleaner [OPTIONS]

Reads text from STDIN, writes redacted output to STDOUT.

Options:
    --help      Show this help message and exit
    --version   Show version and exit

Exit Codes:
    0   Success
    2   Invalid usage (unknown flags, unexpected args)
"""

import sys

from ninobyte_context_cleaner.redactor import PIIRedactor
from ninobyte_context_cleaner.version import __version__


USAGE = """\
Usage: python -m ninobyte_context_cleaner [OPTIONS]

Deterministic PII redaction for LLM context preparation.

Reads text from STDIN, writes redacted output to STDOUT.

Options:
  --help      Show this help message and exit
  --version   Show version and exit

Examples:
  echo "Contact john@example.com" | python -m ninobyte_context_cleaner
  cat document.txt | python -m ninobyte_context_cleaner > cleaned.txt
"""


def main() -> int:
    """
    Main CLI entrypoint.

    Returns:
        Exit code: 0 on success, 2 on invalid usage
    """
    args = sys.argv[1:]

    # Handle flags
    if "--help" in args:
        print(USAGE)
        return 0

    if "--version" in args:
        print(f"ninobyte-context-cleaner {__version__}")
        return 0

    # Check for unknown flags or unexpected arguments
    for arg in args:
        if arg.startswith("-"):
            print(f"Error: Unknown option '{arg}'", file=sys.stderr)
            print("Use --help for usage information.", file=sys.stderr)
            return 2
        else:
            print(f"Error: Unexpected argument '{arg}'", file=sys.stderr)
            print("Use --help for usage information.", file=sys.stderr)
            return 2

    # Read from stdin, redact, write to stdout
    redactor = PIIRedactor()

    try:
        input_text = sys.stdin.read()
        output_text = redactor.redact(input_text)
        sys.stdout.write(output_text)
        return 0
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        return 130


if __name__ == "__main__":
    sys.exit(main())
