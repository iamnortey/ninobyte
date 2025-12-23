"""
Pack lockfile generation and verification.

Provides supply-chain auditability by generating a deterministic,
reproducible lockfile that captures:
- Schema version
- Canonical metadata hash
- Entries file hash
- Normalized entries hash
- Total entry count
- Fields signature

This prevents silent drift and enables downstream trust guarantees.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from lexicon_packs.canonicalize import (
    canonicalize_json,
    canonicalize_json_compact,
    compute_sha256,
)
from lexicon_packs.load import load_pack, LoadError


# Lockfile schema version
LOCK_SCHEMA_VERSION = "1.0.0"

# Required lockfile keys (in order)
REQUIRED_LOCK_KEYS = [
    "lock_schema_version",
    "generated_at_utc",
    "pack_id",
    "pack_schema_version",
    "pack_json_sha256",
    "entries_file",
    "entries_file_sha256",
    "normalized_entries_sha256",
    "entry_count",
    "fields_signature",
]


class LockfileError(Exception):
    """Raised when lockfile operations fail."""
    pass


def validate_path_security(file_path: Path, pack_root: Path) -> None:
    """
    Validate that a file path is safely within the pack root.

    Args:
        file_path: Path to validate
        pack_root: Pack root directory

    Raises:
        LockfileError: If path traversal is detected
    """
    try:
        file_path.resolve().relative_to(pack_root.resolve())
    except ValueError:
        raise LockfileError(
            f"Path traversal detected: {file_path} is not under {pack_root}"
        )


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of raw file bytes.

    Args:
        file_path: Path to file

    Returns:
        Lowercase hex SHA256 hash
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_fields_signature(fields: list[dict[str, Any]]) -> str:
    """
    Compute signature of field names and order.

    Args:
        fields: List of field definitions from pack.json

    Returns:
        SHA256 hash of joined field names
    """
    field_names = [f["name"] for f in fields]
    joined = "|".join(field_names)
    return compute_sha256(joined)


def normalize_entries_for_hash(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Normalize entries for deterministic hashing.

    Sorting strategy:
    1. By term.casefold()
    2. By full term (for ties)
    3. By category (for ties)

    Args:
        entries: List of entry dictionaries

    Returns:
        Sorted list of entries with sorted keys
    """
    def sort_key(entry: dict[str, str]) -> tuple:
        term = entry.get("term", "")
        category = entry.get("category", "")
        return (term.casefold(), term, category)

    sorted_entries = sorted(entries, key=sort_key)
    # Ensure each entry has sorted keys
    return [dict(sorted(e.items())) for e in sorted_entries]


def compute_normalized_entries_sha256(entries: list[dict[str, str]]) -> str:
    """
    Compute SHA256 of normalized entries.

    Args:
        entries: List of entry dictionaries

    Returns:
        SHA256 hash of canonical normalized entries JSON
    """
    normalized = normalize_entries_for_hash(entries)
    canonical = canonicalize_json_compact(normalized)
    return compute_sha256(canonical)


def generate_lockfile(
    pack_path: str | Path,
    fixed_time: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generate lockfile content for a pack.

    Args:
        pack_path: Path to pack directory
        fixed_time: Fixed timestamp for deterministic output (ISO 8601)

    Returns:
        Lockfile dictionary

    Raises:
        LockfileError: If generation fails
    """
    pack_path = Path(pack_path).resolve()

    # Load and validate pack
    try:
        pack = load_pack(pack_path, validate_first=True)
    except LoadError as e:
        raise LockfileError(f"Pack loading failed: {e}")
    except FileNotFoundError as e:
        raise LockfileError(f"Pack not found: {e}")

    # Compute hashes
    pack_json_path = pack_path / "pack.json"

    # Read pack.json for hashing
    with open(pack_json_path, "r", encoding="utf-8") as f:
        pack_json_data = json.load(f)

    # Hash canonical pack.json
    pack_json_sha256 = compute_sha256(canonicalize_json_compact(pack_json_data))

    # Get entries path from pack.json and validate it's within pack root
    entries_rel_path = pack_json_data.get("entries_path", "entries.csv")

    # Reject absolute paths
    if Path(entries_rel_path).is_absolute():
        raise LockfileError(f"Absolute entries_path not allowed: {entries_rel_path}")

    entries_file_path = pack_path / entries_rel_path

    # Validate entries file is within pack directory (prevents traversal)
    validate_path_security(entries_file_path, pack_path)

    # Hash raw entries file
    entries_file_sha256 = compute_file_sha256(entries_file_path)

    # Compute normalized entries hash
    entry_dicts = [e.to_dict() for e in pack.entries]
    normalized_entries_sha256 = compute_normalized_entries_sha256(entry_dicts)

    # Compute fields signature
    fields_signature = compute_fields_signature(pack.fields)

    # Generate timestamp
    if fixed_time:
        generated_at = fixed_time
    else:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "lock_schema_version": LOCK_SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "pack_id": pack.pack_id,
        "pack_schema_version": pack.schema_version,
        "pack_json_sha256": pack_json_sha256,
        "entries_file": entries_rel_path,
        "entries_file_sha256": entries_file_sha256,
        "normalized_entries_sha256": normalized_entries_sha256,
        "entry_count": pack.entry_count,
        "fields_signature": fields_signature,
    }


def format_lockfile_json(lockfile: dict[str, Any]) -> str:
    """
    Format lockfile as canonical JSON.

    Args:
        lockfile: Lockfile dictionary

    Returns:
        Canonical JSON string with trailing newline
    """
    return canonicalize_json(lockfile)


def validate_lockfile_schema(lockfile: dict[str, Any]) -> list[str]:
    """
    Validate lockfile schema.

    Args:
        lockfile: Lockfile dictionary

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check for required keys
    for key in REQUIRED_LOCK_KEYS:
        if key not in lockfile:
            errors.append(f"Missing required key: {key}")

    # Check for unknown keys
    for key in lockfile:
        if key not in REQUIRED_LOCK_KEYS:
            errors.append(f"Unknown key: {key}")

    # Validate lock_schema_version
    if "lock_schema_version" in lockfile:
        if lockfile["lock_schema_version"] != LOCK_SCHEMA_VERSION:
            errors.append(
                f"Unsupported lock_schema_version: {lockfile['lock_schema_version']}. "
                f"Expected: {LOCK_SCHEMA_VERSION}"
            )

    # Validate types
    if "entry_count" in lockfile and not isinstance(lockfile["entry_count"], int):
        errors.append("entry_count must be an integer")

    string_fields = [
        "lock_schema_version",
        "generated_at_utc",
        "pack_id",
        "pack_schema_version",
        "pack_json_sha256",
        "entries_file",
        "entries_file_sha256",
        "normalized_entries_sha256",
        "fields_signature",
    ]
    for field in string_fields:
        if field in lockfile and not isinstance(lockfile[field], str):
            errors.append(f"{field} must be a string")

    return errors


def load_lockfile(pack_path: str | Path) -> dict[str, Any]:
    """
    Load lockfile from pack directory.

    Args:
        pack_path: Path to pack directory

    Returns:
        Lockfile dictionary

    Raises:
        LockfileError: If loading fails
    """
    pack_path = Path(pack_path).resolve()
    lockfile_path = pack_path / "pack.lock.json"

    if not lockfile_path.is_file():
        raise LockfileError(f"Lockfile not found: {lockfile_path}")

    try:
        with open(lockfile_path, "r", encoding="utf-8") as f:
            lockfile = json.load(f)
    except json.JSONDecodeError as e:
        raise LockfileError(f"Invalid JSON in lockfile: {e}")

    # Validate schema
    errors = validate_lockfile_schema(lockfile)
    if errors:
        raise LockfileError(f"Invalid lockfile schema: {'; '.join(errors)}")

    return lockfile


def verify_lockfile(pack_path: str | Path) -> tuple[bool, list[str]]:
    """
    Verify pack matches its lockfile.

    Args:
        pack_path: Path to pack directory

    Returns:
        (is_valid, errors) tuple
    """
    pack_path = Path(pack_path).resolve()
    errors = []

    # Load existing lockfile
    try:
        existing = load_lockfile(pack_path)
    except LockfileError as e:
        return False, [str(e)]

    # Generate fresh lockfile (using existing timestamp for comparison)
    try:
        fresh = generate_lockfile(
            pack_path,
            fixed_time=existing["generated_at_utc"]
        )
    except LockfileError as e:
        return False, [f"Failed to generate lockfile: {e}"]

    # Compare field by field (excluding generated_at_utc which we already matched)
    for key in REQUIRED_LOCK_KEYS:
        if key == "generated_at_utc":
            continue

        existing_val = existing.get(key)
        fresh_val = fresh.get(key)

        if existing_val != fresh_val:
            errors.append(
                f"Mismatch in {key}: lockfile has '{existing_val}', "
                f"computed '{fresh_val}'"
            )

    return len(errors) == 0, errors


def write_lockfile(pack_path: str | Path, fixed_time: Optional[str] = None) -> Path:
    """
    Generate and write lockfile to pack directory.

    Args:
        pack_path: Path to pack directory
        fixed_time: Fixed timestamp for deterministic output

    Returns:
        Path to written lockfile

    Raises:
        LockfileError: If generation fails
    """
    pack_path = Path(pack_path).resolve()
    lockfile_path = pack_path / "pack.lock.json"

    lockfile = generate_lockfile(pack_path, fixed_time=fixed_time)
    content = format_lockfile_json(lockfile)

    with open(lockfile_path, "w", encoding="utf-8") as f:
        f.write(content)

    return lockfile_path
