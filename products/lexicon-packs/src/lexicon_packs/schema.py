"""
Pack schema definitions and validation.

Schema v1.0.0 defines the required structure for lexicon packs.
"""

from typing import Any

# Schema version
SCHEMA_VERSION = "1.0.0"

# Required top-level keys in pack.json
REQUIRED_KEYS = frozenset({
    "schema_version",
    "pack_id",
    "name",
    "description",
    "license",
    "language",
    "entry_format",
    "entries_path",
    "fields",
    "created_at_utc",
    "source_attribution",
})

# Allowed top-level keys (strict schema - no extras allowed)
ALLOWED_KEYS = REQUIRED_KEYS

# Supported entry formats
SUPPORTED_ENTRY_FORMATS = frozenset({"csv"})

# Required field definition keys
REQUIRED_FIELD_KEYS = frozenset({"name", "type", "required"})

# Supported field types
SUPPORTED_FIELD_TYPES = frozenset({"string", "integer", "boolean"})


class SchemaError(Exception):
    """Raised when pack schema validation fails."""
    pass


def validate_pack_json(data: dict[str, Any], pack_path: str) -> list[str]:
    """
    Validate pack.json against schema v1.0.0.

    Args:
        data: Parsed pack.json content
        pack_path: Path to pack directory (for error messages)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # Check for required keys
    missing_keys = REQUIRED_KEYS - set(data.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {sorted(missing_keys)}")

    # Check for unknown keys (strict schema)
    unknown_keys = set(data.keys()) - ALLOWED_KEYS
    if unknown_keys:
        errors.append(f"Unknown keys not allowed: {sorted(unknown_keys)}")

    # Validate schema_version
    if "schema_version" in data:
        if data["schema_version"] != SCHEMA_VERSION:
            errors.append(
                f"Unsupported schema_version: {data['schema_version']!r} "
                f"(expected {SCHEMA_VERSION!r})"
            )

    # Validate pack_id format (lowercase, hyphens, alphanumeric)
    if "pack_id" in data:
        pack_id = data["pack_id"]
        if not isinstance(pack_id, str):
            errors.append(f"pack_id must be a string, got {type(pack_id).__name__}")
        elif not pack_id:
            errors.append("pack_id cannot be empty")
        elif not all(c.islower() or c.isdigit() or c == "-" for c in pack_id):
            errors.append(
                f"pack_id must be lowercase alphanumeric with hyphens: {pack_id!r}"
            )

    # Validate string fields
    string_fields = ["name", "description", "license", "language", "entries_path"]
    for field in string_fields:
        if field in data:
            if not isinstance(data[field], str):
                errors.append(f"{field} must be a string")
            elif not data[field].strip():
                errors.append(f"{field} cannot be empty")

    # Validate entry_format
    if "entry_format" in data:
        if data["entry_format"] not in SUPPORTED_ENTRY_FORMATS:
            errors.append(
                f"Unsupported entry_format: {data['entry_format']!r} "
                f"(supported: {sorted(SUPPORTED_ENTRY_FORMATS)})"
            )

    # Validate entries_path (no path traversal)
    if "entries_path" in data:
        entries_path = data["entries_path"]
        if isinstance(entries_path, str):
            if ".." in entries_path:
                errors.append(
                    f"entries_path cannot contain '..': {entries_path!r}"
                )
            if entries_path.startswith("/"):
                errors.append(
                    f"entries_path must be relative: {entries_path!r}"
                )

    # Validate fields array
    if "fields" in data:
        fields = data["fields"]
        if not isinstance(fields, list):
            errors.append(f"fields must be an array, got {type(fields).__name__}")
        elif not fields:
            errors.append("fields array cannot be empty")
        else:
            for i, field in enumerate(fields):
                field_errors = _validate_field_definition(field, i)
                errors.extend(field_errors)

    # Validate created_at_utc (basic ISO 8601 check)
    if "created_at_utc" in data:
        timestamp = data["created_at_utc"]
        if not isinstance(timestamp, str):
            errors.append("created_at_utc must be a string")
        elif not timestamp.endswith("Z") and "+" not in timestamp:
            errors.append(
                f"created_at_utc should be UTC (end with 'Z'): {timestamp!r}"
            )

    # Validate source_attribution array
    if "source_attribution" in data:
        sources = data["source_attribution"]
        if not isinstance(sources, list):
            errors.append(
                f"source_attribution must be an array, got {type(sources).__name__}"
            )
        else:
            for i, source in enumerate(sources):
                if not isinstance(source, dict):
                    errors.append(
                        f"source_attribution[{i}] must be an object"
                    )
                elif "name" not in source:
                    errors.append(
                        f"source_attribution[{i}] missing required 'name' key"
                    )

    return errors


def _validate_field_definition(field: Any, index: int) -> list[str]:
    """Validate a single field definition in the fields array."""
    errors: list[str] = []
    prefix = f"fields[{index}]"

    if not isinstance(field, dict):
        errors.append(f"{prefix} must be an object, got {type(field).__name__}")
        return errors

    # Check required keys
    missing = REQUIRED_FIELD_KEYS - set(field.keys())
    if missing:
        errors.append(f"{prefix} missing required keys: {sorted(missing)}")

    # Validate name
    if "name" in field:
        if not isinstance(field["name"], str):
            errors.append(f"{prefix}.name must be a string")
        elif not field["name"]:
            errors.append(f"{prefix}.name cannot be empty")

    # Validate type
    if "type" in field:
        if field["type"] not in SUPPORTED_FIELD_TYPES:
            errors.append(
                f"{prefix}.type unsupported: {field['type']!r} "
                f"(supported: {sorted(SUPPORTED_FIELD_TYPES)})"
            )

    # Validate required
    if "required" in field:
        if not isinstance(field["required"], bool):
            errors.append(f"{prefix}.required must be a boolean")

    return errors
