# Ghana Core Entities

Common Ghanaian geographic entities for entity recognition and text normalization.

## Contents

| Category | Count | Description |
|----------|-------|-------------|
| city | 15 | Major cities and towns |
| region | 10 | Administrative regions |
| landmark | 5 | Notable landmarks |

**Total entries**: 30

## Included

- Capital cities of all 16 regions (subset)
- Major industrial and port cities
- UNESCO World Heritage Sites
- Notable public landmarks

## Intentionally Excluded

- Personal names (privacy)
- Business names (trademark)
- Detailed addresses (privacy)
- Political figures (controversy)
- Religious sites (sensitivity)
- Disputed boundaries (controversy)

## License

CC0-1.0 (Public Domain)

## Sources

- Public domain geographic data
- Official government region names

## Usage

```bash
# Validate
python -m lexicon_packs validate --pack products/lexicon-packs/packs/ghana-core

# View
python -m lexicon_packs show --pack products/lexicon-packs/packs/ghana-core --output json
```
