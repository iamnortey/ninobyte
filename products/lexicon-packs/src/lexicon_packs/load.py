"""
Pack loading module.

Loads validated packs into canonical in-memory representation.
"""

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lexicon_packs.canonicalize import compute_entries_hash
from lexicon_packs.validate import validate_pack


@dataclass
class PackEntry:
    """A single entry from a lexicon pack."""

    values: dict[str, str]

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary (sorted keys for determinism)."""
        return dict(sorted(self.values.items()))


@dataclass
class LoadedPack:
    """A fully loaded and validated lexicon pack."""

    pack_id: str
    name: str
    description: str
    license: str
    language: str
    schema_version: str
    created_at_utc: str
    source_attribution: list[dict[str, Any]]
    fields: list[dict[str, Any]]
    entries: list[PackEntry]
    pack_path: str

    @property
    def entry_count(self) -> int:
        """Number of entries in the pack."""
        return len(self.entries)

    @property
    def entries_sha256(self) -> str:
        """SHA256 hash of canonical entries representation."""
        entry_dicts = [e.to_dict() for e in self.entries]
        return compute_entries_hash(entry_dicts)

    def to_dict(self, include_entries: int = 0) -> dict[str, Any]:
        """
        Convert to dictionary for JSON output.

        Args:
            include_entries: Number of entries to include (0 = none)

        Returns:
            Dictionary with sorted keys
        """
        result = {
            "created_at_utc": self.created_at_utc,
            "description": self.description,
            "entries_sha256": self.entries_sha256,
            "entry_count": self.entry_count,
            "fields": self.fields,
            "language": self.language,
            "license": self.license,
            "name": self.name,
            "pack_id": self.pack_id,
            "schema_version": self.schema_version,
            "source_attribution": self.source_attribution,
        }

        if include_entries > 0:
            result["first_entries"] = [
                e.to_dict() for e in self.entries[:include_entries]
            ]

        return result


class LoadError(Exception):
    """Raised when pack loading fails."""

    pass


def load_pack(pack_path: str | Path, validate_first: bool = True) -> LoadedPack:
    """
    Load a lexicon pack from disk.

    Args:
        pack_path: Path to pack directory
        validate_first: Whether to validate before loading (default: True)

    Returns:
        LoadedPack with all entries loaded

    Raises:
        LoadError: If validation fails or loading encounters errors
    """
    pack_path = Path(pack_path).resolve()

    # Validate first
    if validate_first:
        result = validate_pack(pack_path)
        if not result.valid:
            raise LoadError(
                f"Pack validation failed: {'; '.join(result.errors)}"
            )

    # Load pack.json
    pack_json_path = pack_path / "pack.json"
    with open(pack_json_path, "r", encoding="utf-8") as f:
        pack_data = json.load(f)

    # Load entries
    entries_path = pack_path / pack_data["entries_path"]
    entries = _load_csv_entries(entries_path, pack_data["fields"])

    return LoadedPack(
        pack_id=pack_data["pack_id"],
        name=pack_data["name"],
        description=pack_data["description"],
        license=pack_data["license"],
        language=pack_data["language"],
        schema_version=pack_data["schema_version"],
        created_at_utc=pack_data["created_at_utc"],
        source_attribution=pack_data["source_attribution"],
        fields=pack_data["fields"],
        entries=entries,
        pack_path=str(pack_path),
    )


def _load_csv_entries(
    entries_path: Path,
    field_definitions: list[dict[str, Any]],
) -> list[PackEntry]:
    """
    Load entries from CSV file.

    Args:
        entries_path: Path to entries.csv
        field_definitions: Field definitions from pack.json

    Returns:
        List of PackEntry objects
    """
    entries: list[PackEntry] = []
    expected_columns = [f["name"] for f in field_definitions]

    with open(entries_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Extract only expected columns in defined order
            values = {col: row.get(col, "") for col in expected_columns}
            entries.append(PackEntry(values=values))

    return entries
