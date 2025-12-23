"""
Lexicon Map module for deterministic redaction using Lexicon Packs.

Provides functionality to:
1. Load a Lexicon Pack and build an in-memory match set
2. Produce a deterministic redaction map (what would be redacted, counts, examples)
3. Optionally apply redaction to input text in-memory

Security guarantees:
- No network access
- No shell execution
- No file writes (output to stdout only)
- Path traversal protection
- Deterministic output (stable ordering, canonical formatting)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class LexiconMapError(Exception):
    """Raised when lexicon map operations fail."""
    pass


def is_safe_pack_path(path: str) -> tuple[bool, str]:
    """
    Validate that a pack path is safe for reading.

    Security rules:
    - Reject paths containing ".." after normalization
    - Path must exist and be a directory
    - Must contain pack.json

    Returns:
        (is_safe, error_message)
    """
    # Normalize the path
    normalized = os.path.normpath(path)

    # Reject directory traversal attempts
    if ".." in normalized.split(os.sep):
        return False, "Path traversal not allowed: '..' segments rejected"

    # Check if path exists
    if not os.path.exists(normalized):
        return False, f"Pack directory not found: {path}"

    # Must be a directory
    if not os.path.isdir(normalized):
        return False, f"Not a directory: {path}"

    # Must contain pack.json
    pack_json = os.path.join(normalized, "pack.json")
    if not os.path.isfile(pack_json):
        return False, f"pack.json not found in {path}"

    return True, ""


def load_lexicon_pack(pack_path: str) -> dict[str, Any]:
    """
    Load a lexicon pack from disk.

    Args:
        pack_path: Path to pack directory

    Returns:
        Dictionary with pack metadata and entries

    Raises:
        LexiconMapError: If loading fails
    """
    pack_dir = Path(pack_path).resolve()
    pack_json_path = pack_dir / "pack.json"

    # Load pack.json
    try:
        with open(pack_json_path, "r", encoding="utf-8") as f:
            pack_data = json.load(f)
    except json.JSONDecodeError as e:
        raise LexiconMapError(f"Invalid JSON in pack.json: {e}")
    except IOError as e:
        raise LexiconMapError(f"Failed to read pack.json: {e}")

    # Validate required keys
    required_keys = [
        "schema_version", "pack_id", "name", "entry_format",
        "entries_path", "fields"
    ]
    missing = [k for k in required_keys if k not in pack_data]
    if missing:
        raise LexiconMapError(f"pack.json missing required keys: {missing}")

    # Validate schema version
    if pack_data["schema_version"] != "1.0.0":
        raise LexiconMapError(
            f"Unsupported schema version: {pack_data['schema_version']}. "
            "Only 1.0.0 is supported."
        )

    # Validate entry format
    if pack_data["entry_format"] != "csv":
        raise LexiconMapError(
            f"Unsupported entry format: {pack_data['entry_format']}. "
            "Only 'csv' is supported."
        )

    # Validate entries_path doesn't escape pack directory
    entries_rel_path = pack_data["entries_path"]
    if ".." in entries_rel_path or entries_rel_path.startswith("/"):
        raise LexiconMapError(
            f"Invalid entries_path: {entries_rel_path}. "
            "Path traversal not allowed."
        )

    entries_path = pack_dir / entries_rel_path

    # Ensure entries file is within pack directory
    try:
        entries_path.resolve().relative_to(pack_dir.resolve())
    except ValueError:
        raise LexiconMapError(
            f"Entries file must be within pack directory: {entries_path}"
        )

    if not entries_path.is_file():
        raise LexiconMapError(f"Entries file not found: {entries_path}")

    # Load entries from CSV
    import csv
    entries = []
    field_names = [f["name"] for f in pack_data["fields"]]

    # Validate that 'term' field exists
    if "term" not in field_names:
        raise LexiconMapError(
            "Pack must have a 'term' field for matching"
        )

    try:
        with open(entries_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Validate CSV columns match expected
            if reader.fieldnames is None:
                raise LexiconMapError("CSV file is empty or has no header")

            actual_columns = list(reader.fieldnames)
            if actual_columns != field_names:
                raise LexiconMapError(
                    f"CSV columns mismatch. Expected: {field_names}, "
                    f"Got: {actual_columns}"
                )

            for row in reader:
                entry = {col: row.get(col, "") for col in field_names}
                entries.append(entry)

    except csv.Error as e:
        raise LexiconMapError(f"CSV parsing error: {e}")

    return {
        "pack_id": pack_data["pack_id"],
        "name": pack_data["name"],
        "schema_version": pack_data["schema_version"],
        "entries": entries,
        "field_names": field_names,
    }


def compute_entries_sha256(entries: list[dict[str, str]]) -> str:
    """
    Compute SHA256 hash of canonical entries representation.

    Args:
        entries: List of entry dictionaries

    Returns:
        SHA256 hex digest
    """
    import hashlib

    # Canonical JSON: sorted keys, no whitespace
    canonical = json.dumps(
        [dict(sorted(e.items())) for e in entries],
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_match_set(
    entries: list[dict[str, str]],
    case_fold: bool = True
) -> tuple[set[str], dict[str, str]]:
    """
    Build a match set from entries.

    Args:
        entries: List of entry dictionaries (must have 'term' key)
        case_fold: Whether to use case-insensitive matching

    Returns:
        (match_set, original_terms) where:
        - match_set: Set of terms for matching (possibly casefolded)
        - original_terms: Dict mapping casefolded → original term
    """
    match_set = set()
    original_terms = {}

    for entry in entries:
        term = entry.get("term", "").strip()
        if not term:
            continue

        if case_fold:
            folded = term.casefold()
            match_set.add(folded)
            # Keep first occurrence if duplicates
            if folded not in original_terms:
                original_terms[folded] = term
        else:
            match_set.add(term)
            original_terms[term] = term

    return match_set, original_terms


def find_matches(
    text: str,
    match_set: set[str],
    original_terms: dict[str, str],
    case_fold: bool = True
) -> dict[str, int]:
    """
    Find all matches of terms in text using word boundary matching.

    Uses conservative word boundary matching:
    - ASCII word characters (\\w) plus unicode letters
    - Exact word boundary match

    Args:
        text: Input text to scan
        match_set: Set of terms to match (possibly casefolded)
        original_terms: Dict mapping matched → original term
        case_fold: Whether matching is case-insensitive

    Returns:
        Dict mapping original terms to occurrence counts
    """
    counts: dict[str, int] = {}

    # For each term, find word-boundary matches
    for term in match_set:
        original = original_terms[term]

        # Escape regex special characters
        escaped = re.escape(term)

        # Word boundary pattern
        # Use (?<![\\w]) and (?![\\w]) for word boundaries
        # This is more conservative than \\b for unicode
        pattern = rf"(?<![a-zA-Z0-9_])({escaped})(?![a-zA-Z0-9_])"

        flags = re.IGNORECASE if case_fold else 0
        matches = re.findall(pattern, text, flags=flags)

        if matches:
            counts[original] = len(matches)

    return counts


def generate_redaction_preview(
    text: str,
    match_set: set[str],
    original_terms: dict[str, str],
    pack_id: str,
    limit: int = 10,
    case_fold: bool = True
) -> list[dict[str, str]]:
    """
    Generate preview of redactions that would be applied.

    Args:
        text: Input text
        match_set: Set of terms to match
        original_terms: Dict mapping matched → original term
        pack_id: Pack ID for redaction placeholder
        limit: Maximum number of examples to return
        case_fold: Whether matching is case-insensitive

    Returns:
        List of {original, redacted, context} dictionaries
    """
    previews = []
    seen_terms = set()

    for term in sorted(match_set):
        if len(previews) >= limit:
            break

        original = original_terms[term]
        if original in seen_terms:
            continue

        escaped = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9_])({escaped})(?![a-zA-Z0-9_])"
        flags = re.IGNORECASE if case_fold else 0

        match = re.search(pattern, text, flags=flags)
        if match:
            seen_terms.add(original)

            # Get context (up to 20 chars before and after)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end]

            # Clean up context (remove newlines, normalize whitespace)
            context = " ".join(context.split())

            # Add ellipsis if truncated
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            previews.append({
                "original": match.group(1),
                "redacted": f"[[LEXICON:{pack_id}]]",
                "context": context,
            })

    return previews


def apply_redaction(
    text: str,
    match_set: set[str],
    original_terms: dict[str, str],
    pack_id: str,
    case_fold: bool = True
) -> str:
    """
    Apply redaction to text, replacing matched terms with placeholders.

    Replacement strategy:
    - Sort terms by length (descending) then lexicographically
    - Replace longer terms first to prevent partial matches
    - Use word boundary matching

    Args:
        text: Input text
        match_set: Set of terms to match
        original_terms: Dict mapping matched → original term
        pack_id: Pack ID for redaction placeholder
        case_fold: Whether matching is case-insensitive

    Returns:
        Text with terms replaced by [[LEXICON:<pack_id>]]
    """
    placeholder = f"[[LEXICON:{pack_id}]]"

    # Sort terms: longest first, then lexicographic
    sorted_terms = sorted(match_set, key=lambda t: (-len(t), t))

    result = text
    for term in sorted_terms:
        escaped = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9_])({escaped})(?![a-zA-Z0-9_])"
        flags = re.IGNORECASE if case_fold else 0

        result = re.sub(pattern, placeholder, result, flags=flags)

    return result


def generate_lexicon_map(
    pack_path: str,
    input_text: str,
    fixed_time: Optional[str] = None,
    limit: int = 10,
    apply_redaction_flag: bool = False
) -> dict[str, Any]:
    """
    Generate a complete lexicon map output.

    Args:
        pack_path: Path to lexicon pack directory
        input_text: Text to analyze
        fixed_time: Fixed timestamp for testing (ISO 8601 format)
        limit: Maximum number of preview examples
        apply_redaction_flag: Whether to include redacted text in output

    Returns:
        Dictionary with complete map output
    """
    # Load pack
    pack_data = load_lexicon_pack(pack_path)

    # Compute entries hash
    entries_sha256 = compute_entries_sha256(pack_data["entries"])

    # Build match set
    match_set, original_terms = build_match_set(pack_data["entries"])

    # Find matches
    matches = find_matches(input_text, match_set, original_terms)

    # Generate preview
    preview = generate_redaction_preview(
        input_text, match_set, original_terms,
        pack_data["pack_id"], limit=limit
    )

    # Generate timestamp
    if fixed_time:
        generated_at = fixed_time
    else:
        generated_at = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    # Build output
    output = {
        "schema_version": "1.0.0",
        "generated_at_utc": generated_at,
        "pack_id": pack_data["pack_id"],
        "pack_entries_sha256": entries_sha256,
        "match_strategy": "casefolded_exact",
        "matches": [
            {"term": term, "count": count}
            for term, count in sorted(matches.items())
        ],
        "summary": {
            "total_entries": len(pack_data["entries"]),
            "matched_terms": len(matches),
            "total_occurrences": sum(matches.values()),
        },
        "redaction_preview": preview,
    }

    # Add redacted text if requested
    if apply_redaction_flag:
        redacted = apply_redaction(
            input_text, match_set, original_terms, pack_data["pack_id"]
        )
        output["redacted_text"] = redacted

    return output


def format_output_json(data: dict[str, Any]) -> str:
    """
    Format output as deterministic JSON.

    Uses:
    - Sorted keys (recursive)
    - 2-space indentation
    - No trailing whitespace
    - Trailing newline

    Args:
        data: Dictionary to format

    Returns:
        Canonical JSON string
    """
    return json.dumps(
        data,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
