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
    --input-type <type> Input type: auto (default), text, pdf
    --pdf-mode <mode>   PDF extraction mode: text-only (default)
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
  --input-type <type> Input type: auto (default), text, pdf
                      auto: detect from file extension (.pdf -> pdf, else text)
  --pdf-mode <mode>   PDF extraction mode: text-only (default)
                      text-only: extract embedded text (no OCR)
  --output-format <fmt>  Output format: text (default) or jsonl

Output Formats:
  text    Plain text output (default)
  jsonl   JSON Lines with metadata:
          {"redacted":"...","normalized":"..."|null,"meta":{...}}

Processing Order:
  1. PDF text extraction (if input is PDF)
  2. PII redaction (always applied)
  3. Table normalization (only if --normalize-tables is set)

Examples:
  # Basic PII redaction from STDIN
  echo "Contact john@example.com" | python -m ninobyte_context_cleaner

  # Read from file
  python -m ninobyte_context_cleaner --input document.txt

  # Extract text from PDF and redact PII
  python -m ninobyte_context_cleaner --input document.pdf

  # Force PDF mode for file without .pdf extension
  python -m ninobyte_context_cleaner --input data.bin --input-type pdf

  # JSONL output for pipelines
  echo "test@example.com" | python -m ninobyte_context_cleaner --output-format jsonl

  # Combined: PDF input, table normalization, JSONL output
  python -m ninobyte_context_cleaner --input data.pdf --normalize-tables --output-format jsonl

PDF Support:
  Requires optional dependency: pip install ninobyte-context-cleaner[pdf]
  Only extracts embedded text from text-based PDFs (no OCR support).
"""

# Known flags (without arguments)
KNOWN_FLAGS = {"--help", "--version", "--normalize-tables"}

# Known options (with arguments)
KNOWN_OPTIONS = {"--input", "--input-type", "--pdf-mode", "--output-format"}

# Valid output formats
VALID_OUTPUT_FORMATS = {"text", "jsonl"}

# Valid input types
VALID_INPUT_TYPES = {"auto", "text", "pdf"}

# Valid PDF modes
VALID_PDF_MODES = {"text-only"}


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


def detect_input_type(path: str, explicit_type: str) -> str:
    """
    Determine the input type for a file.

    Args:
        path: File path
        explicit_type: User-specified type (auto, text, pdf)

    Returns:
        Resolved type: "text" or "pdf"
    """
    if explicit_type != "auto":
        return explicit_type

    # Auto-detect from extension
    _, ext = os.path.splitext(path.lower())
    if ext == ".pdf":
        return "pdf"

    return "text"


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
        "input_type": "auto",
        "pdf_mode": "text-only",
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
            elif arg == "--input-type":
                if value not in VALID_INPUT_TYPES:
                    return {}, f"Invalid input type '{value}'. Use: auto, text, pdf"
                options["input_type"] = value
            elif arg == "--pdf-mode":
                if value not in VALID_PDF_MODES:
                    return {}, f"Invalid PDF mode '{value}'. Use: text-only"
                options["pdf_mode"] = value
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
    source: str,
    input_type: str
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
            "source": "stdin" | "file" | "pdf",
            "input_type": "text" | "pdf"
        }
    }

    Field order is deterministic (sorted keys).
    """
    output = {
        "meta": {
            "input_type": input_type,
            "normalize_tables": normalize_tables,
            "source": source,
            "version": __version__,
        },
        "normalized": normalized,
        "redacted": redacted,
    }

    # Use sort_keys for deterministic output
    return json.dumps(output, ensure_ascii=False, sort_keys=True)


def read_pdf_input(path: str) -> Tuple[str, Optional[str]]:
    """
    Read and extract text from a PDF file.

    Args:
        path: Path to PDF file (already validated)

    Returns:
        (extracted_text, error_message)
        On success: (text, None)
        On failure: ("", error_message)
    """
    # Lazy import to avoid loading when not needed
    from ninobyte_context_cleaner.pdf_extractor import (
        is_pdf_available,
        get_pdf_import_error,
        PDFExtractor
    )

    if not is_pdf_available():
        return "", get_pdf_import_error()

    try:
        extractor = PDFExtractor()
        text = extractor.extract_from_file(path)
        return text, None
    except Exception as e:
        return "", f"PDF extraction failed: {e}"


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
    input_type_option = options["input_type"]
    output_format = options["output_format"]

    # Validate: --input-type pdf requires --input
    if input_type_option == "pdf" and not input_path:
        print("Error: --input-type pdf requires --input <path>", file=sys.stderr)
        return 2

    # Validate input path if provided
    if input_path:
        is_safe, path_error = is_safe_path(input_path)
        if not is_safe:
            print(f"Error: {path_error}", file=sys.stderr)
            return 2

    # Determine resolved input type
    if input_path:
        resolved_input_type = detect_input_type(input_path, input_type_option)
    else:
        resolved_input_type = "text"  # STDIN is always text

    # Determine source for metadata
    if not input_path:
        source = "stdin"
    elif resolved_input_type == "pdf":
        source = "pdf"
    else:
        source = "file"

    # Initialize processors
    redactor = PIIRedactor()
    normalizer = TableNormalizer() if normalize_tables else None

    try:
        # Read input based on type
        if resolved_input_type == "pdf":
            input_text, pdf_error = read_pdf_input(input_path)
            if pdf_error:
                print(f"Error: {pdf_error}", file=sys.stderr)
                return 2
        elif input_path:
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
                source=source,
                input_type=resolved_input_type
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
