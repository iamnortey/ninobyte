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
```

## Usage

```bash
# Basic usage: pipe text through the redactor
echo "Contact john@example.com or call 555-123-4567" | python -m ninobyte_context_cleaner
# Output: Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]

# Process a file
cat document.txt | python -m ninobyte_context_cleaner > cleaned.txt

# Check version
python -m ninobyte_context_cleaner --version
```

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

## Design Principles

- **Deterministic**: Same input always produces same output
- **Unix-style**: STDIN → STDOUT, composable with other tools
- **Read-only**: No file writes, no network calls
- **Conservative**: Prefer false negatives over false positives

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Invalid usage (unknown flags, unexpected args) |

## Security Posture

- No networking imports
- No shell execution
- No file system writes
- Pure Python stdlib only
