"""
CLI entrypoint for ninobyte-context-cleaner.

Usage:
    ninobyte-context-cleaner [OPTIONS]
    ninobyte-context-cleaner lexicon-map [OPTIONS]
    python -m ninobyte_context_cleaner [OPTIONS]

Deterministic PII redaction and text normalization for LLM context preparation.
Reads text from STDIN (or file), writes processed output to STDOUT.

Commands:
    (default)       PII redaction and text normalization
    lexicon-map     Generate redaction map using Lexicon Pack

Exit Codes:
    0   Success
    2   Invalid usage (unknown flags, bad path, missing dependency)

Run with --help for full usage information.
"""

import json
import os
import sys
from typing import List, Optional, Tuple

from ninobyte_context_cleaner.redactor import PIIRedactor
from ninobyte_context_cleaner.table_normalizer import TableNormalizer
from ninobyte_context_cleaner.version import __version__


USAGE = """\
Usage: ninobyte-context-cleaner [OPTIONS]
       python -m ninobyte_context_cleaner [OPTIONS]

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
  --lexicon <path>    Load lexicon substitutions from local JSON file
  --lexicon-mode <mode>  Lexicon mode: replace (default)
  --lexicon-target <target>  Apply lexicon to: input, normalized, both
                      input: apply to raw input stream (default)
                      normalized: apply to normalized output only
                      both: apply to both streams

Output Formats:
  text    Plain text output (default)
  jsonl   JSON Lines (Schema v1) with deterministic key ordering:
          {"meta":{...},"normalized":"..."|null,"redacted":"..."}

Processing Order:
  1. PDF text extraction (if input is PDF)
  2. Table normalization (only if --normalize-tables is set)
  3. Lexicon injection (only if --lexicon is set)
  4. PII redaction (always applied)

Lexicon Format:
  JSON object mapping "from" strings to "to" strings:
  {"Acme Inc": "ACME Incorporated", "NYC": "New York City"}

Examples:
  # Basic PII redaction from STDIN
  echo "Contact john@example.com" | ninobyte-context-cleaner

  # Read from file
  ninobyte-context-cleaner --input document.txt

  # Table normalization (CSV/TSV/pipe tables to key:value)
  cat data.csv | ninobyte-context-cleaner --normalize-tables

  # Extract text from PDF and redact PII
  ninobyte-context-cleaner --input document.pdf

  # Apply lexicon substitutions before PII redaction
  ninobyte-context-cleaner --lexicon mappings.json --input doc.txt

  # JSONL output for pipelines
  echo "test@example.com" | ninobyte-context-cleaner --output-format jsonl

  # Combined: PDF input, table normalization, JSONL output
  ninobyte-context-cleaner --input data.pdf --normalize-tables --output-format jsonl

Exit Codes:
  0   Success
  2   Invalid usage (unknown flags, bad path, missing dependency)

PDF Support:
  Requires optional dependency: pip install ninobyte-context-cleaner[pdf]
  Only extracts embedded text from text-based PDFs (no OCR support).

Subcommands:
  lexicon-map    Generate redaction map using Lexicon Pack
                 Run: ninobyte-context-cleaner lexicon-map --help
"""

# Known flags (without arguments)
KNOWN_FLAGS = {"--help", "--version", "--normalize-tables"}

# Known options (with arguments)
KNOWN_OPTIONS = {
    "--input", "--input-type", "--pdf-mode", "--output-format",
    "--lexicon", "--lexicon-mode", "--lexicon-target"
}

# Valid output formats
VALID_OUTPUT_FORMATS = {"text", "jsonl"}

# Valid input types
VALID_INPUT_TYPES = {"auto", "text", "pdf"}

# Valid PDF modes
VALID_PDF_MODES = {"text-only"}

# Valid lexicon modes
VALID_LEXICON_MODES = {"replace"}

# Valid lexicon targets
VALID_LEXICON_TARGETS = {"input", "normalized", "both"}


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
        "lexicon_path": None,
        "lexicon_mode": "replace",
        "lexicon_target": "input",
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
            elif arg == "--lexicon":
                options["lexicon_path"] = value
            elif arg == "--lexicon-mode":
                if value not in VALID_LEXICON_MODES:
                    return {}, f"Invalid lexicon mode '{value}'. Use: replace"
                options["lexicon_mode"] = value
            elif arg == "--lexicon-target":
                if value not in VALID_LEXICON_TARGETS:
                    return {}, f"Invalid lexicon target '{value}'. Use: input, normalized, both"
                options["lexicon_target"] = value

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
    input_type: str,
    lexicon_meta: Optional[str] = None
) -> str:
    """
    Format output as JSONL (single line JSON) following Schema v1 contract.

    Schema v1 Contract:
    - Top-level key order: "meta", "normalized", "redacted"
    - "normalized" is always present (null if normalization not requested)
    - "redacted" is always a string
    - Schema is additive: future keys may be added without breaking v1 consumers

    meta object contains (in this order):
    - "schema_version": "1" (hardcoded, identifies contract version)
    - "version": tool version string
    - "source": "stdin" | "file" | "pdf"
    - "input_type": "text" | "pdf"
    - "normalize_tables": true | false
    - "lexicon": {...} (optional, only when lexicon is used)

    Returns:
        Single-line JSON string with deterministic key ordering
    """
    # Build JSON string manually to guarantee key order
    # This ensures stable output for downstream pipelines

    # Meta object with explicit key order
    meta_parts = [
        f'"schema_version":"1"',
        f'"version":{json.dumps(__version__, ensure_ascii=False)}',
        f'"source":{json.dumps(source, ensure_ascii=False)}',
        f'"input_type":{json.dumps(input_type, ensure_ascii=False)}',
        f'"normalize_tables":{json.dumps(normalize_tables)}',
    ]

    # Add lexicon metadata if provided (additive schema)
    if lexicon_meta:
        meta_parts.append(f'"lexicon":{lexicon_meta}')

    meta_json = "{" + ",".join(meta_parts) + "}"

    # Normalized field: explicit null or string
    normalized_json = "null" if normalized is None else json.dumps(normalized, ensure_ascii=False)

    # Redacted field: always a string
    redacted_json = json.dumps(redacted, ensure_ascii=False)

    # Top-level object with explicit key order: meta, normalized, redacted
    return f'{{"meta":{meta_json},"normalized":{normalized_json},"redacted":{redacted_json}}}'


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


# ============================================================================
# lexicon-map subcommand
# ============================================================================

LEXICON_MAP_USAGE = """\
Usage: ninobyte-context-cleaner lexicon-map [OPTIONS]
       python -m ninobyte_context_cleaner lexicon-map [OPTIONS]

Generate a deterministic redaction map using a Lexicon Pack.

Uses Lexicon Pack entries as a deterministic entity list for redaction/normalization.
Produces a JSON report showing what would be redacted, counts, and examples.

Options:
  --help              Show this help message and exit
  --pack <path>       Path to Lexicon Pack directory (required)
  --input <path>      Read from file instead of STDIN
  --output <format>   Output format: json (default)
  --limit <n>         Maximum redaction preview examples (default: 10)
  --fixed-time <ts>   Fixed timestamp for deterministic output (ISO 8601)
  --apply             Include redacted text in output (default: map only)

Output JSON includes:
  schema_version      Output schema version (1.0.0)
  generated_at_utc    Timestamp (or --fixed-time value for tests)
  pack_id             Lexicon Pack ID
  pack_entries_sha256 SHA256 hash of pack entries (deterministic)
  match_strategy      Matching strategy used (casefolded_exact)
  matches             List of matched terms with counts
  summary             Statistics (total entries, matched, occurrences)
  redaction_preview   Example replacements (up to --limit)
  redacted_text       Redacted text (only with --apply)

Examples:
  # Generate map from file
  ninobyte-context-cleaner lexicon-map \\
    --pack products/lexicon-packs/packs/ghana-core \\
    --input document.txt

  # Generate map from stdin
  echo "Visit Accra and Kumasi" | ninobyte-context-cleaner lexicon-map \\
    --pack products/lexicon-packs/packs/ghana-core

  # Deterministic output for tests
  ninobyte-context-cleaner lexicon-map \\
    --pack packs/ghana-core \\
    --input doc.txt \\
    --fixed-time 2025-01-01T00:00:00Z

  # Include redacted text
  ninobyte-context-cleaner lexicon-map \\
    --pack packs/ghana-core \\
    --input doc.txt \\
    --apply

Security:
  - No network access
  - No shell execution
  - No file writes (output to stdout only)
  - Path traversal protection on --pack and --input

Exit Codes:
  0   Success
  2   Invalid usage (bad path, missing pack, invalid schema)
"""

# Known lexicon-map flags (without arguments)
LEXICON_MAP_FLAGS = {"--help", "--apply"}

# Known lexicon-map options (with arguments)
LEXICON_MAP_OPTIONS = {"--pack", "--input", "--output", "--limit", "--fixed-time"}


def parse_lexicon_map_args(args: List[str]) -> Tuple[dict, Optional[str]]:
    """
    Parse lexicon-map subcommand arguments.

    Returns:
        (parsed_options, error_message)
        error_message is None on success
    """
    options = {
        "pack_path": None,
        "input_path": None,
        "output_format": "json",
        "limit": 10,
        "fixed_time": None,
        "apply": False,
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in LEXICON_MAP_FLAGS:
            if arg == "--apply":
                options["apply"] = True
            i += 1
            continue

        if arg in LEXICON_MAP_OPTIONS:
            if i + 1 >= len(args):
                return {}, f"Option '{arg}' requires a value"

            value = args[i + 1]

            if arg == "--pack":
                options["pack_path"] = value
            elif arg == "--input":
                options["input_path"] = value
            elif arg == "--output":
                if value != "json":
                    return {}, f"Invalid output format '{value}'. Use: json"
                options["output_format"] = value
            elif arg == "--limit":
                try:
                    options["limit"] = int(value)
                    if options["limit"] < 0:
                        return {}, "--limit must be a non-negative integer"
                except ValueError:
                    return {}, f"Invalid --limit value: '{value}'. Must be integer."
            elif arg == "--fixed-time":
                options["fixed_time"] = value

            i += 2
            continue

        # Unknown argument
        if arg.startswith("-"):
            return {}, f"Unknown option '{arg}'"
        else:
            return {}, f"Unexpected argument '{arg}'"

    return options, None


def lexicon_map_main(args: List[str]) -> int:
    """
    Main entrypoint for lexicon-map subcommand.

    Args:
        args: Command-line arguments (after 'lexicon-map')

    Returns:
        Exit code: 0 on success, 2 on error
    """
    # Handle help
    if "--help" in args:
        print(LEXICON_MAP_USAGE)
        return 0

    # Parse arguments
    options, error = parse_lexicon_map_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        print("Use 'lexicon-map --help' for usage information.", file=sys.stderr)
        return 2

    pack_path = options["pack_path"]
    input_path = options["input_path"]
    limit = options["limit"]
    fixed_time = options["fixed_time"]
    apply_flag = options["apply"]

    # Validate required options
    if not pack_path:
        print("Error: --pack is required", file=sys.stderr)
        print("Use 'lexicon-map --help' for usage information.", file=sys.stderr)
        return 2

    # Import lexicon_map module
    from ninobyte_context_cleaner.lexicon_map import (
        is_safe_pack_path,
        generate_lexicon_map,
        format_output_json,
        LexiconMapError,
    )

    # Validate pack path
    is_safe, path_error = is_safe_pack_path(pack_path)
    if not is_safe:
        print(f"Error: {path_error}", file=sys.stderr)
        return 2

    # Validate input path if provided
    if input_path:
        is_safe_input, input_error = is_safe_path(input_path)
        if not is_safe_input:
            print(f"Error: {input_error}", file=sys.stderr)
            return 2

    try:
        # Read input
        if input_path:
            with open(input_path, 'r', encoding='utf-8') as f:
                input_text = f.read()
        else:
            input_text = sys.stdin.read()

        # Generate map
        result = generate_lexicon_map(
            pack_path=pack_path,
            input_text=input_text,
            fixed_time=fixed_time,
            limit=limit,
            apply_redaction_flag=apply_flag,
        )

        # Output
        output = format_output_json(result)
        sys.stdout.write(output)

        return 0

    except LexiconMapError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except IOError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def main() -> int:
    """
    Main CLI entrypoint with subcommand dispatch.

    Returns:
        Exit code: 0 on success, 2 on invalid usage
    """
    args = sys.argv[1:]

    # Check for subcommand
    if args and args[0] == "lexicon-map":
        return lexicon_map_main(args[1:])

    # Otherwise, run default command
    return default_main(args)


def default_main(args: List[str]) -> int:
    """
    Default command: PII redaction and text normalization.

    Pipeline Order (authoritative):
    1. Read input (STDIN, file, or PDF)
    2. Table normalization (if --normalize-tables)
    3. Lexicon injection (if --lexicon)
    4. PII redaction (always)
    5. Output formatting

    Returns:
        Exit code: 0 on success, 2 on invalid usage
    """
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
    lexicon_path = options["lexicon_path"]
    lexicon_mode = options["lexicon_mode"]
    lexicon_target = options["lexicon_target"]

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

    # Validate lexicon path if provided (reuse path security)
    lexicon_injector = None
    lexicon_meta = None

    if lexicon_path:
        from ninobyte_context_cleaner.lexicon import (
            is_safe_lexicon_path,
            load_lexicon,
            LexiconInjector,
            create_lexicon_meta
        )

        is_safe, path_error = is_safe_lexicon_path(lexicon_path)
        if not is_safe:
            print(f"Error: {path_error}", file=sys.stderr)
            return 2

        lexicon, load_error = load_lexicon(lexicon_path)
        if load_error:
            print(f"Error: {load_error}", file=sys.stderr)
            return 2

        lexicon_injector = LexiconInjector(lexicon)
        lexicon_meta = create_lexicon_meta(
            path=lexicon_path,
            rules_count=lexicon_injector.rules_count,
            target=lexicon_target,
            mode=lexicon_mode
        )

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
        # ===== STEP 1: Read input =====
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

        # ===== STEP 2: Table normalization (if enabled) =====
        normalized_text: Optional[str] = None
        if normalizer:
            normalized_text = normalizer.normalize(input_text)

        # ===== STEP 3: Lexicon injection (if enabled) =====
        # Apply to appropriate streams based on target
        if lexicon_injector:
            if lexicon_target in ("input", "both"):
                input_text = lexicon_injector.apply(input_text)

            if lexicon_target in ("normalized", "both") and normalized_text is not None:
                normalized_text = lexicon_injector.apply(normalized_text)

        # ===== STEP 4: PII redaction (always applied) =====
        redacted_text = redactor.redact(input_text)

        # Also redact normalized text if it exists
        if normalized_text is not None:
            normalized_text = redactor.redact(normalized_text)

        # ===== STEP 5: Format output =====
        if output_format == "jsonl":
            output = format_jsonl_output(
                redacted=redacted_text,
                normalized=normalized_text,
                normalize_tables=normalize_tables,
                source=source,
                input_type=resolved_input_type,
                lexicon_meta=lexicon_meta
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
