# PR Merge Receipt Evidence

This directory stores immutable evidence of PR merges for governance and audit purposes.

## File Types

| Pattern | Description |
|---------|-------------|
| `pr_<N>_merge_receipt.json` | Raw receipt from `gh pr view` (human-readable, pretty-printed) |
| `pr_<N>_merge_receipt.canonical.json` | Canonical JSON (deterministic format for hashing) |
| `pr_<N>_merge_receipt.canonical.json.sha256` | SHA256 checksum of canonical receipt |

## Why Canonical Hashing?

The `gh` CLI may return JSON with different field ordering or formatting across runs.
This causes SHA256 mismatches even when the data is semantically identical.

Canonical JSON ensures:
- **Sorted keys**: Fields always appear in alphabetical order
- **Compact format**: No extraneous whitespace (`separators=(",", ":")`)
- **Consistent encoding**: Unicode preserved (`ensure_ascii=False`)
- **Trailing newline**: Single `\n` at EOF

## Generate a Receipt

```bash
# Single PR
python3 scripts/ops/capture_pr_merge_receipt.py 47

# Batch mode (multiple PRs)
python3 scripts/ops/capture_pr_merge_receipt.py 42 44 45 46

# Range mode (inclusive)
python3 scripts/ops/capture_pr_merge_receipt.py --range 42..47

# Capture and verify integrity in one command
python3 scripts/ops/capture_pr_merge_receipt.py 47 --verify

# Dry run (preview without writing)
python3 scripts/ops/capture_pr_merge_receipt.py 47 --dry-run

# Auto-detect current branch PR (no args)
python3 scripts/ops/capture_pr_merge_receipt.py
```

This creates all three files and prints a summary with the SHA256.

## Verify Integrity

```bash
# Compute SHA256 of canonical file
shasum -a 256 ops/evidence/pr/pr_<N>_merge_receipt.canonical.json

# Compare with stored checksum
cat ops/evidence/pr/pr_<N>_merge_receipt.canonical.json.sha256
```

Both should match exactly.

## Canonicalize Existing JSON

To convert any JSON file to canonical format:

```bash
python3 scripts/ops/canonicalize_json.py --in input.json --out output.json
```
