#!/usr/bin/env python3
"""Build deterministic evidence index from canonical receipts.

Discovers all canonical evidence files and produces:
- ops/evidence/INDEX.json (human-readable)
- ops/evidence/INDEX.canonical.json (deterministic, compact)
- ops/evidence/INDEX.canonical.json.sha256 (integrity checksum)

Contract (v0.6.0):
- Canonical ordering: (kind, id, canonical_path) - stable across environments
- No timestamps in index artifacts (generated_at_utc removed for determinism)
- Index only changes when underlying evidence set changes

Usage:
    python3 scripts/ops/build_evidence_index.py          # --write (default)
    python3 scripts/ops/build_evidence_index.py --write  # regenerate artifacts
    python3 scripts/ops/build_evidence_index.py --check  # byte-for-byte validation
    python3 scripts/ops/build_evidence_index.py --print  # print canonical to stdout

Exit codes:
    0 - Success (write completed or check passed)
    1 - Failure (missing files, mismatch in check mode, etc.)
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Evidence roots to scan (repo-relative)
EVIDENCE_ROOTS = [
    "ops/evidence/pr",
    "ops/evidence/validation",
    "ops/evidence/decisions",
]

# Output paths (repo-relative)
INDEX_JSON_PATH = "ops/evidence/INDEX.json"
INDEX_CANONICAL_PATH = "ops/evidence/INDEX.canonical.json"
INDEX_CHECKSUM_PATH = "ops/evidence/INDEX.canonical.json.sha256"

# Sentinel for unknown timestamps (sorts last)
UNKNOWN_TIMESTAMP_SENTINEL = "9999-12-31T23:59:59Z"

# ISO-8601 Zulu pattern (with optional fractions)
ISO_TIMESTAMP_PATTERN = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z?$"
)


def canonicalize(data: object) -> str:
    """Return canonical JSON string with trailing newline.

    Canonical format:
    - Keys sorted recursively
    - Compact separators (no extra whitespace)
    - Unicode preserved (no ASCII escaping)
    - Single trailing newline
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"


def compute_sha256(content: str) -> str:
    """Compute SHA256 hash of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def normalize_timestamp(ts: Optional[str]) -> Optional[str]:
    """Normalize timestamp to YYYY-MM-DDTHH:MM:SSZ format.

    Returns None if input is None or unparseable.
    Strips fractional seconds if present.
    """
    if not ts:
        return None

    match = ISO_TIMESTAMP_PATTERN.match(ts)
    if not match:
        return None

    year, month, day, hour, minute, second = match.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"


def get_kind_from_path(canonical_path: str) -> str:
    """Derive kind from folder path.

    - ops/evidence/pr/ -> "pr"
    - ops/evidence/validation/ -> "validation"
    - ops/evidence/decisions/ -> "decision"
    """
    if "/pr/" in canonical_path:
        return "pr"
    elif "/validation/" in canonical_path:
        return "validation"
    elif "/decisions/" in canonical_path:
        return "decision"
    else:
        return "unknown"


def get_id_from_path(canonical_path: str) -> str:
    """Extract ID from canonical path (basename without extensions).

    Example: ops/evidence/pr/pr_49_merge_receipt.canonical.json -> pr_49_merge_receipt
    """
    basename = Path(canonical_path).name
    # Remove .canonical.json suffix
    if basename.endswith(".canonical.json"):
        return basename[:-15]  # len(".canonical.json") == 15
    return basename


def extract_timestamp_from_receipt(data: Dict[str, Any], kind: str) -> Optional[str]:
    """Extract best available timestamp from receipt data.

    For PR receipts: mergedAt
    For validation receipts: created_at_utc
    For decision receipts: created_at_utc
    """
    timestamp = None

    if kind == "pr":
        timestamp = data.get("mergedAt")
    elif kind in ("validation", "decision"):
        timestamp = data.get("created_at_utc")

    return normalize_timestamp(timestamp)


def extract_source_ref(data: Dict[str, Any], kind: str) -> str:
    """Extract best-effort source reference.

    For PR receipts: url
    For validation receipts: source
    For decision receipts: adr_path or source
    """
    if kind == "pr":
        return data.get("url", "")
    elif kind == "validation":
        return data.get("source", "")
    elif kind == "decision":
        return data.get("adr_path") or data.get("source", "")
    return ""


def discover_canonical_files(repo_root: Path) -> List[Path]:
    """Discover all canonical.json files in evidence roots."""
    files = []
    for root in EVIDENCE_ROOTS:
        root_path = repo_root / root
        if root_path.exists():
            files.extend(root_path.glob("*.canonical.json"))
    return sorted(files)


def validate_sibling_sha256(canonical_path: Path) -> Tuple[bool, str, str]:
    """Validate sibling .sha256 file exists and is parseable.

    Returns:
        (success, sha256_hash, error_message)
    """
    sha256_path = Path(str(canonical_path) + ".sha256")
    if not sha256_path.exists():
        return False, "", f"Missing sibling checksum: {sha256_path}"

    try:
        content = sha256_path.read_text().strip()
        if "  " not in content:
            return False, "", f"Invalid checksum format in {sha256_path}"
        sha256_hash = content.split("  ", 1)[0]
        if len(sha256_hash) != 64:
            return False, "", f"Invalid SHA256 hash length in {sha256_path}"
        return True, sha256_hash, ""
    except Exception as e:
        return False, "", f"Error reading {sha256_path}: {e}"


def build_index(repo_root: Path) -> Tuple[Dict[str, Any], List[str]]:
    """Build the evidence index from discovered files.

    Returns:
        (index_data, errors)
    """
    errors = []
    items = []
    counts: Dict[str, int] = {}

    canonical_files = discover_canonical_files(repo_root)

    for canonical_path in canonical_files:
        # Make path repo-relative with forward slashes
        try:
            rel_path = str(canonical_path.relative_to(repo_root)).replace("\\", "/")
        except ValueError:
            rel_path = str(canonical_path).replace("\\", "/")

        # Validate sibling .sha256
        valid, sha256_hash, error = validate_sibling_sha256(canonical_path)
        if not valid:
            errors.append(error)
            continue

        # Parse canonical JSON
        try:
            data = json.loads(canonical_path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {rel_path}: {e}")
            continue

        # Derive metadata
        kind = get_kind_from_path(rel_path)
        item_id = get_id_from_path(rel_path)
        sha256_rel_path = rel_path + ".sha256"
        timestamp = extract_timestamp_from_receipt(data, kind)
        source_ref = extract_source_ref(data, kind)

        # Determine sort_timestamp (for human reference, not for sorting)
        sort_timestamp = timestamp if timestamp else UNKNOWN_TIMESTAMP_SENTINEL

        # Count by kind
        counts[kind] = counts.get(kind, 0) + 1

        # Build item
        item: Dict[str, Any] = {
            "canonical_path": rel_path,
            "id": item_id,
            "kind": kind,
            "sha256": sha256_hash,
            "sha256_path": sha256_rel_path,
            "sort_timestamp_utc": sort_timestamp,
        }

        # Only include timestamp_utc if present
        if timestamp:
            item["timestamp_utc"] = timestamp

        # Only include source_ref if non-empty
        if source_ref:
            item["source_ref"] = source_ref

        items.append(item)

    # Sort items deterministically: (kind, id, canonical_path)
    # This ordering is stable across environments regardless of filesystem traversal order
    items.sort(key=lambda x: (x["kind"], x["id"], x["canonical_path"]))

    # Build index (no generated_at_utc - determinism contract v0.6.0)
    index_data: Dict[str, Any] = {
        "counts": counts,
        "items": items,
    }

    return index_data, errors


def format_human_readable(data: Dict[str, Any]) -> str:
    """Format index data as human-readable JSON."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_index_artifacts(repo_root: Path, index_data: Dict[str, Any]) -> None:
    """Write all three index artifacts."""
    # Human-readable JSON
    human_json = format_human_readable(index_data)
    (repo_root / INDEX_JSON_PATH).write_text(human_json)

    # Canonical JSON
    canonical_json = canonicalize(index_data)
    (repo_root / INDEX_CANONICAL_PATH).write_text(canonical_json)

    # Checksum
    sha256_hash = compute_sha256(canonical_json)
    checksum_content = f"{sha256_hash}  {INDEX_CANONICAL_PATH}\n"
    (repo_root / INDEX_CHECKSUM_PATH).write_text(checksum_content)


def check_index_artifacts(repo_root: Path, index_data: Dict[str, Any]) -> List[str]:
    """Check if tracked artifacts match regenerated versions.

    Returns list of mismatch descriptions.
    """
    mismatches = []

    # Expected content
    expected_human = format_human_readable(index_data)
    expected_canonical = canonicalize(index_data)
    expected_sha256 = compute_sha256(expected_canonical)
    expected_checksum = f"{expected_sha256}  {INDEX_CANONICAL_PATH}\n"

    # Check INDEX.json
    index_json_path = repo_root / INDEX_JSON_PATH
    if not index_json_path.exists():
        mismatches.append(f"Missing: {INDEX_JSON_PATH}")
    else:
        actual = index_json_path.read_text()
        if actual != expected_human:
            mismatches.append(f"Drifted: {INDEX_JSON_PATH}")

    # Check INDEX.canonical.json
    index_canonical_path = repo_root / INDEX_CANONICAL_PATH
    if not index_canonical_path.exists():
        mismatches.append(f"Missing: {INDEX_CANONICAL_PATH}")
    else:
        actual = index_canonical_path.read_text()
        if actual != expected_canonical:
            mismatches.append(f"Drifted: {INDEX_CANONICAL_PATH}")

    # Check INDEX.canonical.json.sha256
    index_checksum_path = repo_root / INDEX_CHECKSUM_PATH
    if not index_checksum_path.exists():
        mismatches.append(f"Missing: {INDEX_CHECKSUM_PATH}")
    else:
        actual = index_checksum_path.read_text()
        if actual != expected_checksum:
            mismatches.append(f"Drifted: {INDEX_CHECKSUM_PATH}")

    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build deterministic evidence index from canonical receipts.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=True,
        help="Write/update index artifacts (default)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if artifacts match regenerated versions (byte-for-byte)",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="print_mode",
        help="Print canonical JSON to stdout (for diff verification)",
    )

    args = parser.parse_args()

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    # Build index
    index_data, errors = build_index(repo_root)

    if errors:
        print("Errors during discovery:", file=sys.stderr)
        for error in errors:
            print(f"  ❌ {error}", file=sys.stderr)
        return 1

    # Handle --print mode (quiet, just output canonical JSON)
    if args.print_mode:
        print(canonicalize(index_data), end="")
        return 0

    # Normal output header
    print("=" * 60)
    print("Evidence Index Builder")
    print("=" * 60)

    # Report counts
    print("\nDiscovered evidence:")
    for kind, count in sorted(index_data.get("counts", {}).items()):
        print(f"  {kind}: {count}")
    print(f"  total: {len(index_data.get('items', []))}")

    if args.check:
        # Check mode: validate byte-for-byte
        print("\n--- Check Mode ---")
        mismatches = check_index_artifacts(repo_root, index_data)

        if mismatches:
            print("\n❌ Index artifacts have drifted:")
            for mismatch in mismatches:
                print(f"  - {mismatch}")
            print("\nRemediation:")
            print("  Run: python3 scripts/ops/build_evidence_index.py --write")
            print("  Then commit the changes.")
            return 1
        else:
            print("\n✅ All index artifacts match (byte-for-byte)")
            return 0
    else:
        # Write mode: regenerate artifacts
        print("\n--- Write Mode ---")
        write_index_artifacts(repo_root, index_data)
        print(f"\n✅ Wrote: {INDEX_JSON_PATH}")
        print(f"✅ Wrote: {INDEX_CANONICAL_PATH}")
        print(f"✅ Wrote: {INDEX_CHECKSUM_PATH}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
