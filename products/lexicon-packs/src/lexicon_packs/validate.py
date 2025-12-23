"""
Pack validation module.

Validates pack structure, schema compliance, and entry format.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

from lexicon_packs.schema import validate_pack_json, SchemaError


class ValidationResult:
    """Result of pack validation."""

    def __init__(self, valid: bool, errors: list[str], pack_path: str):
        self.valid = valid
        self.errors = errors
        self.pack_path = pack_path

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        status = "VALID" if self.valid else "INVALID"
        return f"ValidationResult({status}, errors={len(self.errors)})"


def validate_pack(pack_path: str | Path) -> ValidationResult:
    """
    Validate a lexicon pack.

    Checks:
    1. pack.json exists and is valid JSON
    2. pack.json conforms to schema
    3. entries file exists
    4. entries CSV has correct columns
    5. Required fields are not empty

    Args:
        pack_path: Path to pack directory

    Returns:
        ValidationResult with valid flag and any errors
    """
    # Check for path traversal BEFORE resolving (resolve normalizes away ..)
    original_path_str = str(pack_path)
    errors: list[str] = []

    if ".." in original_path_str:
        errors.append(f"Path traversal not allowed: {original_path_str}")
        return ValidationResult(False, errors, original_path_str)

    pack_path = Path(pack_path).resolve()

    # Check pack directory exists
    if not pack_path.is_dir():
        errors.append(f"Pack directory not found: {pack_path}")
        return ValidationResult(False, errors, str(pack_path))

    # Check pack.json exists
    pack_json_path = pack_path / "pack.json"
    if not pack_json_path.is_file():
        errors.append(f"pack.json not found in {pack_path}")
        return ValidationResult(False, errors, str(pack_path))

    # Parse pack.json
    try:
        with open(pack_json_path, "r", encoding="utf-8") as f:
            pack_data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in pack.json: {e}")
        return ValidationResult(False, errors, str(pack_path))

    # Validate schema
    schema_errors = validate_pack_json(pack_data, str(pack_path))
    errors.extend(schema_errors)

    # If schema is invalid, don't proceed to entry validation
    if errors:
        return ValidationResult(False, errors, str(pack_path))

    # Validate entries file exists
    entries_path = pack_path / pack_data["entries_path"]
    if not entries_path.is_file():
        errors.append(f"Entries file not found: {entries_path}")
        return ValidationResult(False, errors, str(pack_path))

    # Validate entries file is within pack directory
    try:
        entries_path.resolve().relative_to(pack_path.resolve())
    except ValueError:
        errors.append(f"Entries file must be within pack directory: {entries_path}")
        return ValidationResult(False, errors, str(pack_path))

    # Validate CSV structure
    csv_errors = _validate_csv_entries(
        entries_path,
        pack_data["fields"],
    )
    errors.extend(csv_errors)

    return ValidationResult(len(errors) == 0, errors, str(pack_path))


def _validate_csv_entries(
    entries_path: Path,
    field_definitions: list[dict[str, Any]],
) -> list[str]:
    """
    Validate CSV entries against field definitions.

    Args:
        entries_path: Path to entries.csv
        field_definitions: Field definitions from pack.json

    Returns:
        List of validation errors
    """
    errors: list[str] = []
    expected_columns = [f["name"] for f in field_definitions]
    required_columns = [f["name"] for f in field_definitions if f.get("required")]

    try:
        with open(entries_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Validate header
            if reader.fieldnames is None:
                errors.append("CSV file is empty or has no header")
                return errors

            actual_columns = list(reader.fieldnames)

            # Check column order matches exactly
            if actual_columns != expected_columns:
                errors.append(
                    f"CSV columns mismatch. Expected: {expected_columns}, "
                    f"Got: {actual_columns}"
                )
                return errors

            # Validate each row
            for row_num, row in enumerate(reader, start=2):  # 2 = after header
                for col in required_columns:
                    value = row.get(col, "")
                    if not value or not value.strip():
                        errors.append(
                            f"Row {row_num}: Required field '{col}' is empty"
                        )

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")

    return errors
