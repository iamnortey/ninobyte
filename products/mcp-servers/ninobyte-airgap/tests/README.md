# Ninobyte AirGap Tests – Fixture Policy

## Purpose
These tests intentionally exercise redaction logic (credentials, tokens, key markers). However, CI secret scanners can produce false positives when sensitive-looking literals are embedded directly in test source.

## Policy (Non-Negotiable)
- Do **not** hardcode common secret signatures in test source, including:
  - Credential assignments like `pass` + `word=...`
  - Uppercase variants like `PASS` + `WORD=...`
  - Key markers like `-----BEGIN ` + `PRIV` + `ATE KEY-----`
  - Cloud credential variable names like `AWS_SEC` + `RET_ACCESS_KEY`
- Instead, **compose** strings to avoid static signature matches while preserving runtime coverage.

## Approved Patterns
Use string composition:
- `"pass" + "word=secret123"`
- `"PASS" + "WORD=secret123"`
- `"-----BEGIN " + "PRIV" + "ATE KEY-----"`

Or assemble markers separately:
- `begin = "-----BEGIN " + "PRIV" + "ATE KEY-----"`
- `end = "-----END " + "PRIV" + "ATE KEY-----"`

## Why
This maintains deterministic redaction behavior while keeping CI scanners signal-rich and noise-free.
