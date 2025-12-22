# Ninobyte ContextCleaner

Deterministic PII redaction for LLM context preparation.

## Overview

ContextCleaner provides a Unix-style CLI tool that reads text from STDIN and writes
redacted output to STDOUT. It identifies and replaces common PII patterns with
stable placeholders, ensuring deterministic output suitable for LLM workflows.

## Installation

```bash
# From repo root
cd products/context-cleaner
python -m ninobyte_context_cleaner --version

# With PDF support (optional)
pip install ninobyte-context-cleaner[pdf]
```

## Usage

### Basic PII Redaction

```bash
# Pipe text through the redactor
echo "Contact john@example.com or call 555-123-4567" | python -m ninobyte_context_cleaner
# Output: Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]

# Process a file
python -m ninobyte_context_cleaner --input document.txt

# JSONL output for pipelines
echo "test@example.com" | python -m ninobyte_context_cleaner --output-format jsonl
```

### Table Normalization

```bash
# Convert tables to key:value format
cat data.csv | python -m ninobyte_context_cleaner --normalize-tables
```

### PDF Text Extraction

```bash
# Extract text from PDF and redact PII
python -m ninobyte_context_cleaner --input document.pdf

# Force PDF mode for file without .pdf extension
python -m ninobyte_context_cleaner --input data.bin --input-type pdf

# Combined: PDF input with JSONL output
python -m ninobyte_context_cleaner --input report.pdf --output-format jsonl
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |
| `--input <path>` | Read from file instead of STDIN |
| `--input-type <type>` | Input type: `auto` (default), `text`, `pdf` |
| `--pdf-mode <mode>` | PDF extraction mode: `text-only` (default) |
| `--normalize-tables` | Convert tables to key:value format |
| `--output-format <fmt>` | Output format: `text` (default), `jsonl` |

## Supported PII Patterns

| Pattern | Replacement | Example |
|---------|-------------|---------|
| Email addresses | `[EMAIL_REDACTED]` | `user@domain.com` → `[EMAIL_REDACTED]` |
| Phone numbers | `[PHONE_REDACTED]` | `(555) 867-5309` → `[PHONE_REDACTED]` |

### Phone Pattern Rules

Conservative matching to avoid false positives:
- Matches if total digits >= 10
- Matches if digits >= 7 AND phone-format signals present (parentheses, +, dashes, dots, spaces between digit groups)
- Does NOT match short numeric sequences like years (e.g., "2025")
- Does NOT match hex-like tokens (e.g., Git SHAs)

## PDF Support

PDF text extraction requires the optional `[pdf]` extra:

```bash
pip install ninobyte-context-cleaner[pdf]
```

Features:
- Extracts embedded text from text-based PDFs
- Automatically detects `.pdf` extension
- Force PDF mode with `--input-type pdf`
- Deterministic output (normalized newlines, trimmed whitespace)

Limitations:
- No OCR support (scanned PDFs produce minimal output)
- Text-based PDFs only

## Output Formats

### Text (default)
Plain text output, suitable for direct use.

### JSONL Schema v1

JSON Lines format with deterministic key ordering, suitable for ETL pipelines and downstream processing.

**Schema Contract (v1):**

```json
{"meta":{...},"normalized":"..."|null,"redacted":"..."}
```

**Key Order (guaranteed stable):**

Top-level keys appear in this exact order:
1. `meta` - Metadata object
2. `normalized` - Normalized text (string or null)
3. `redacted` - Redacted text (always string)

**Meta object keys appear in this exact order:**
1. `schema_version` - Always `"1"` (string)
2. `version` - Tool version (e.g., `"0.1.0"`)
3. `source` - Input source: `"stdin"`, `"file"`, or `"pdf"`
4. `input_type` - Input type: `"text"` or `"pdf"`
5. `normalize_tables` - Boolean flag state

**Field Presence Rules:**
- `normalized`: Always present. Value is `null` if `--normalize-tables` not set, otherwise contains normalized string.
- `redacted`: Always present. Always a string (may include trailing newline).

**Example output:**

```bash
$ echo "test@example.com" | python -m ninobyte_context_cleaner --output-format jsonl
{"meta":{"schema_version":"1","version":"0.1.0","source":"stdin","input_type":"text","normalize_tables":false},"normalized":null,"redacted":"[EMAIL_REDACTED]\n"}
```

**Schema Stability:**
- Schema v1 is **additive-only**: Future versions may add new keys to `meta` or top-level without breaking v1 consumers.
- Breaking changes (field renames, type changes) will increment `schema_version` to `"2"`.
- Lexicon injection (custom redaction tokens) is planned for Phase 2.3B.

## Design Principles

- **Deterministic**: Same input always produces same output
- **Unix-style**: STDIN → STDOUT, composable with other tools
- **Read-only**: No file writes, no network calls
- **Conservative**: Prefer false negatives over false positives
- **Contract-stable**: JSONL schema v1 guarantees key ordering and field presence

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Invalid usage (unknown flags, bad path, missing dependency) |

## Security Posture

- No networking imports
- No shell execution
- No file system writes
- Path traversal protection (rejects `..` segments)
- Pure Python stdlib for core (optional pypdf for PDF)
