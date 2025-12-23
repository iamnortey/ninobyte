# Ninobyte ContextCleaner

Deterministic PII redaction for LLM context preparation.

**Version**: 0.1.0

---

## What ContextCleaner is NOT

ContextCleaner explicitly excludes the following capabilities:

| Non-Goal | Rationale |
|----------|-----------|
| Network access | No HTTP clients, no API calls, no telemetry |
| Shell execution | No subprocess with shell=True, no os.system() |
| File writes | Read-only operations only (STDIN/file → STDOUT) |
| OCR | No optical character recognition for scanned PDFs |
| ML/NLP | No machine learning, no named entity recognition |
| External services | No cloud dependencies, no API integrations |

These are **hard security guarantees**, enforced by CI and static analysis.

---

## Install & Run Matrix

### Installation Methods

| Method | Command |
|--------|---------|
| pip install | `pip install ninobyte-context-cleaner` |
| pipx install | `pipx install ninobyte-context-cleaner` |
| With PDF support | `pip install ninobyte-context-cleaner[pdf]` |
| Editable (dev) | `pip install -e products/context-cleaner` |

### Console Scripts

| Script | Description |
|--------|-------------|
| `ninobyte-context-cleaner` | Primary entrypoint (recommended) |
| `context-cleaner` | Legacy alias |
| `python -m ninobyte_context_cleaner` | Module invocation |

### Trust Examples (Copy-Paste Ready)

```bash
# 1. stdin → jsonl (basic pipeline)
echo "Contact john@example.com" | ninobyte-context-cleaner --output-format jsonl
# Output: {"meta":{"schema_version":"1",...},"normalized":null,"redacted":"Contact [EMAIL_REDACTED]\n"}

# 2. File input (text)
ninobyte-context-cleaner --input document.txt

# 3. PDF input (requires [pdf] extras)
pip install ninobyte-context-cleaner[pdf]
ninobyte-context-cleaner --input report.pdf --output-format jsonl

# 4. Full pipeline: normalize-tables + lexicon
cat data.csv | ninobyte-context-cleaner --normalize-tables --lexicon mappings.json --output-format jsonl

# 5. Verify determinism (same input → same output)
echo "test@example.com" | ninobyte-context-cleaner --output-format jsonl > out1.jsonl
echo "test@example.com" | ninobyte-context-cleaner --output-format jsonl > out2.jsonl
diff out1.jsonl out2.jsonl && echo "Deterministic: PASS"
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `2` | Invalid usage (unknown flags, bad path, missing dependency, path traversal) |

---

## Quick Start

```bash
# Install
pip install ninobyte-context-cleaner

# Basic usage: redact PII from text
echo "Contact john@example.com" | ninobyte-context-cleaner
# Output: Contact [EMAIL_REDACTED]

# From file
ninobyte-context-cleaner --input document.txt

# JSONL output for pipelines
echo "test@example.com" | ninobyte-context-cleaner --output-format jsonl

# With PDF support
pip install ninobyte-context-cleaner[pdf]
ninobyte-context-cleaner --input document.pdf
```

## Overview

ContextCleaner provides a Unix-style CLI tool that reads text from STDIN and writes
redacted output to STDOUT. It identifies and replaces common PII patterns with
stable placeholders, ensuring deterministic output suitable for LLM workflows.

## Installation

```bash
# Install from PyPI (when published)
pip install ninobyte-context-cleaner

# Or run directly from source
cd products/context-cleaner
pip install -e .

# Verify installation
ninobyte-context-cleaner --version

# With PDF support (optional)
pip install ninobyte-context-cleaner[pdf]
```

**Available commands:**
- `ninobyte-context-cleaner` - Primary entrypoint (recommended)
- `context-cleaner` - Legacy alias
- `python -m ninobyte_context_cleaner` - Module invocation

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

### Lexicon Injection

Apply custom text substitutions before PII redaction:

```bash
# Create a lexicon file (JSON)
cat > lexicon.json << 'EOF'
{
    "NYC": "New York City",
    "Acme Inc": "ACME Incorporated"
}
EOF

# Apply lexicon substitutions
echo "Visit NYC and contact Acme Inc" | python -m ninobyte_context_cleaner --lexicon lexicon.json
# Output: Visit New York City and contact ACME Incorporated

# Lexicon with JSONL output (includes lexicon metadata)
echo "Visit NYC" | python -m ninobyte_context_cleaner --lexicon lexicon.json --output-format jsonl

# Apply lexicon only to normalized stream (with table normalization)
cat data.csv | python -m ninobyte_context_cleaner --normalize-tables --lexicon lexicon.json --lexicon-target normalized
```

## Commands

ContextCleaner provides two commands:

### Default Command (PII Redaction)

```bash
ninobyte-context-cleaner [OPTIONS]
```

Standard PII redaction and text normalization.

### lexicon-map Command (Lexicon Pack Integration)

```bash
ninobyte-context-cleaner lexicon-map [OPTIONS]
```

Generate a deterministic redaction map using a Lexicon Pack. This bridges Lexicon Packs into operational value by using pack entries as a deterministic entity list for redaction analysis.

See [Lexicon Map Command](#lexicon-map-command) section for details.

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
| `--lexicon <path>` | Load lexicon substitutions from JSON file |
| `--lexicon-mode <mode>` | Lexicon mode: `replace` (default) |
| `--lexicon-target <target>` | Apply to: `input` (default), `normalized`, `both` |

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
6. `lexicon` - (optional) Lexicon metadata object, only present when `--lexicon` used

**Lexicon metadata keys (when present):**
1. `enabled` - Always `true`
2. `source` - Always `"file"`
3. `path_basename` - Filename (no directory path for security)
4. `rules_count` - Number of substitution rules
5. `target` - Target stream: `"input"`, `"normalized"`, or `"both"`
6. `mode` - Replacement mode: `"replace"`

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

## Contract Stability

ContextCleaner maintains strict contract guarantees for downstream consumers:

### JSONL Schema v1 Contract

| Guarantee | Description |
|-----------|-------------|
| Key ordering | Top-level: `meta` → `normalized` → `redacted` (guaranteed stable) |
| Schema version | `meta.schema_version` is always `"1"` (string, not integer) |
| Field presence | `normalized` always present (null if not produced) |
| Additive-only | New meta keys may be added; existing keys never removed/renamed |

### Reserved Token Protection

Redaction placeholders follow the pattern `[UPPER_CASE_TOKEN]` and are protected:
- Pattern: `[A-Z0-9_]+` within square brackets
- Examples: `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`
- Lexicon injection never modifies existing placeholders

### Path Security

All file paths are validated:
- Path traversal blocked (rejects `..` segments after normalization)
- Applies to `--input` and `--lexicon` paths
- Canonicalization enforced before access

### Processing Pipeline

The authoritative processing order is fixed:
```
input read → table normalize → lexicon inject → PII redact → output
```

This order is guaranteed and will not change without a major version bump.

## Lexicon Injection

Lexicon injection allows deterministic text substitution before PII redaction. This is useful for:
- Normalizing company names, abbreviations, or acronyms
- Expanding shorthand before context preparation
- Ensuring consistent terminology in LLM prompts

### Lexicon Format

Lexicons are JSON files mapping "from" strings to "to" strings:

```json
{
    "NYC": "New York City",
    "Acme Inc": "ACME Incorporated",
    "API": "Application Programming Interface"
}
```

### Replacement Rules

1. **Longer keys first**: Keys are applied in descending length order (then lexicographic for ties)
2. **Case-sensitive**: Matching is exact (case-sensitive)
3. **Reserved token protection**: Existing placeholders like `[EMAIL_REDACTED]` are never modified
4. **Deterministic**: Same input + lexicon always produces identical output

### Lexicon Target

The `--lexicon-target` flag controls which stream receives substitutions:

| Target | Description |
|--------|-------------|
| `input` | Apply to raw input before normalization (default) |
| `normalized` | Apply only to normalized output |
| `both` | Apply to both streams |

### Pipeline Order

```
input read → table normalize → lexicon injection → PII redaction → output
```

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

## Lexicon Map Command

The `lexicon-map` command integrates with [Lexicon Packs](../lexicon-packs/) to provide deterministic entity detection and redaction mapping.

### What It Does

- Loads a Lexicon Pack (local path only)
- Builds an in-memory match set from pack entries
- Produces a deterministic redaction map (JSON output)
- Optionally applies redaction to input text (with `--apply`)

### What It Does NOT Do

- No file writes (output to stdout only)
- No network access
- No shell execution
- No fuzzy matching (exact word boundaries only)

### Usage

```bash
# Generate redaction map from stdin
echo "Visit Accra and Kumasi" | ninobyte-context-cleaner lexicon-map \
  --pack products/lexicon-packs/packs/ghana-core

# Generate map from file
ninobyte-context-cleaner lexicon-map \
  --pack products/lexicon-packs/packs/ghana-core \
  --input document.txt

# Include redacted text output
ninobyte-context-cleaner lexicon-map \
  --pack products/lexicon-packs/packs/ghana-core \
  --input document.txt \
  --apply

# Deterministic output for testing
ninobyte-context-cleaner lexicon-map \
  --pack products/lexicon-packs/packs/ghana-core \
  --input document.txt \
  --fixed-time 2025-01-01T00:00:00Z
```

### lexicon-map Options

| Option | Description |
|--------|-------------|
| `--pack <path>` | Path to Lexicon Pack directory (required) |
| `--input <path>` | Read from file instead of STDIN |
| `--output <format>` | Output format: `json` (default) |
| `--limit <n>` | Maximum preview examples (default: 10) |
| `--fixed-time <ts>` | Fixed timestamp for deterministic output (ISO 8601) |
| `--apply` | Include redacted text in output |

### Output Schema (v1.0.0)

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "2025-01-01T00:00:00Z",
  "pack_id": "ghana-core",
  "pack_entries_sha256": "406aed33...",
  "match_strategy": "casefolded_exact",
  "matches": [
    {"term": "Accra", "count": 2},
    {"term": "Kumasi", "count": 1}
  ],
  "summary": {
    "total_entries": 30,
    "matched_terms": 2,
    "total_occurrences": 3
  },
  "redaction_preview": [
    {
      "original": "Accra",
      "redacted": "[[LEXICON:ghana-core]]",
      "context": "...Visit Accra today..."
    }
  ],
  "redacted_text": "..."  // Only with --apply
}
```

### Matching Strategy

- **Case-insensitive**: Uses Unicode casefolding for matching
- **Word boundaries**: Only matches complete words (no partial matches)
- **Deterministic**: Same input always produces same output
- **Sorted output**: Matches sorted alphabetically for stability

### Security Posture

- **Path traversal protection**: `--pack` and `--input` paths validated
- **No network**: Completely offline operation
- **No writes**: Output to stdout only
- **Schema validation**: Rejects invalid pack schemas

## Trust & Governance

### Deterministic Output

ContextCleaner guarantees deterministic output: **same input → same output**, always.
This is enforced through:
- Explicit key ordering in JSONL output (no reliance on dict ordering)
- Lexicon replacement in length-descending, then lexicographic order
- No timestamps, random IDs, or non-deterministic metadata in output

### Schema v1 Contract Stability

The JSONL Schema v1 contract is **non-negotiable**:
- Top-level key order: `meta` → `normalized` → `redacted`
- `schema_version` is always `"1"` (string, not integer)
- `normalized` is always present (explicit `null` if not requested)
- Contract is **additive-only**: new keys may be added, existing keys never removed

Breaking changes will increment `schema_version` to `"2"`.

### Tag Immutability

Published releases are immutable:
- Git tags are never force-pushed or deleted
- PyPI versions are never yanked except for security issues
- Consumers can pin versions with confidence

### Security Boundaries

The `src/` directory enforces strict security boundaries:
- **No networking**: No imports from `urllib`, `http`, `socket`, `requests`, etc.
- **No shell execution**: No `subprocess`, `os.system`, `os.popen`, etc.
- **No file writes**: Read-only operations only (input files, lexicon files)
- **Path traversal protection**: All file paths validated; `..` segments rejected after normalization

### Smoke Harness

A deterministic smoke harness validates contract compliance:
```bash
PYTHONPATH=products/context-cleaner/src python products/context-cleaner/scripts/smoke_context_cleaner.py
```

The smoke harness verifies:
1. JSONL key ordering matches contract
2. `normalized` is explicit `null` when `--normalize-tables` is off
3. `normalized` becomes a string when `--normalize-tables` is on
4. Lexicon metadata appears when `--lexicon` is used
5. Reserved tokens (`[EMAIL_REDACTED]`, etc.) are protected from lexicon replacement
6. Path traversal attempts exit with code 2
7. PDF extras availability (skipped if not installed, not failed)
