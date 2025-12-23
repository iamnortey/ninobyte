"""
Canonical JSON formatting for deterministic output.

Ensures byte-for-byte identical output for the same input.
"""

import hashlib
import json
from typing import Any


def canonicalize_json(data: Any) -> str:
    """
    Convert data to canonical JSON string.

    Guarantees:
    - Sorted keys (recursive)
    - 2-space indentation
    - No trailing whitespace
    - UTF-8 encoding
    - Trailing newline

    Args:
        data: Any JSON-serializable data

    Returns:
        Canonical JSON string
    """
    return json.dumps(
        data,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": "),
    ) + "\n"


def canonicalize_json_compact(data: Any) -> str:
    """
    Convert data to compact canonical JSON string (no whitespace).

    Used for hashing.

    Args:
        data: Any JSON-serializable data

    Returns:
        Compact canonical JSON string
    """
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def compute_sha256(data: str) -> str:
    """
    Compute SHA256 hash of string data.

    Args:
        data: String to hash (will be UTF-8 encoded)

    Returns:
        Lowercase hex SHA256 hash
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_entries_hash(entries: list[dict[str, Any]]) -> str:
    """
    Compute deterministic hash of entry list.

    Args:
        entries: List of entry dictionaries

    Returns:
        SHA256 hash of canonical JSON representation
    """
    canonical = canonicalize_json_compact(entries)
    return compute_sha256(canonical)
