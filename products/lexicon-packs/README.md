# Lexicon Packs

Deterministic vocabulary pack validation, loading, and management.

**Version**: 0.1.0

---

## What Lexicon Packs is NOT

Lexicon Packs explicitly excludes the following capabilities:

| Non-Goal | Rationale |
|----------|-----------|
| Network access | No HTTP clients, no API calls, no telemetry |
| Shell execution | No subprocess with shell=True, no os.system() |
| File writes | Read-only operations only |
| Fuzzy matching | Exact matching only for determinism |

These are **hard security guarantees**, enforced by CI and static analysis.

---

## Quick Start

```bash
# Validate a pack
python -m lexicon_packs validate --pack packs/ghana-core

# Show pack metadata
python -m lexicon_packs show --pack packs/ghana-core --output json --limit 5
```

## Structure

```
lexicon-packs/
├── packs/
│   └── ghana-core/
│       ├── pack.json      # Pack schema v1.0.0 metadata
│       ├── entries.csv    # CSV entries
│       └── README.md      # Pack documentation
├── src/lexicon_packs/
│   ├── cli.py             # CLI implementation
│   ├── schema.py          # Schema validation
│   ├── load.py            # Pack loading
│   ├── validate.py        # Pack validation
│   └── canonicalize.py    # Deterministic JSON
└── tests/
```

## Available Packs

| Pack ID | Description | Entries | License |
|---------|-------------|---------|---------|
| `ghana-core` | Ghanaian cities, regions, landmarks | 30 | CC0-1.0 |

## Consumer Integration

### ContextCleaner Integration

Lexicon Packs can be used with [ContextCleaner](../context-cleaner/) for deterministic entity detection and redaction:

```bash
# Generate redaction map using a Lexicon Pack
echo "Visit Accra and Kumasi" | ninobyte-context-cleaner lexicon-map \
  --pack products/lexicon-packs/packs/ghana-core

# Include redacted text
ninobyte-context-cleaner lexicon-map \
  --pack packs/ghana-core \
  --input document.txt \
  --apply
```

The `lexicon-map` command:
- Loads pack entries as a deterministic entity list
- Produces a JSON report with match counts and examples
- Optionally applies redaction with `--apply`
- Supports deterministic output with `--fixed-time`

See [ContextCleaner README](../context-cleaner/README.md#lexicon-map-command) for full documentation.

## Pack Schema v1.0.0

Each pack contains a `pack.json` with:

```json
{
  "schema_version": "1.0.0",
  "pack_id": "ghana-core",
  "name": "Ghana Core Entities",
  "description": "Common Ghanaian cities, regions, and landmarks",
  "license": "CC0-1.0",
  "language": "en-GH",
  "entry_format": "csv",
  "entries_path": "entries.csv",
  "fields": [
    {"name": "term", "type": "string", "required": true},
    {"name": "category", "type": "string", "required": true}
  ],
  "created_at_utc": "2025-12-23T00:00:00Z",
  "source_attribution": [{"name": "Public Domain Data", "url": null}]
}
```

## CLI Commands

### validate

Validate a pack against the schema:

```bash
python -m lexicon_packs validate --pack packs/ghana-core
```

### show

Display pack metadata:

```bash
python -m lexicon_packs show --pack packs/ghana-core --output json --limit 5
```

## Security

- **No network**: Completely offline operation
- **No shell**: No subprocess execution
- **No writes**: Read-only operations
- **Path security**: Traversal protection on all paths
- **Schema validation**: Strict validation rejects unknown keys

## Development Guidelines

- Follow [THREAT_MODEL.md](../../docs/architecture/THREAT_MODEL.md) security requirements
- Include usage examples
- Document terminology sources
- Use CC0-1.0 or similar permissive licenses for packs
