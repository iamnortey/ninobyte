"""
Pack discovery and fleet verification.

Provides APIs for discovering packs in a directory tree and
verifying all packs in a fleet.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from lexicon_packs.canonicalize import canonicalize_json
from lexicon_packs.load import load_pack, LoadError
from lexicon_packs.lockfile import (
    verify_lockfile,
    LockfileError,
)


class DiscoveryError(Exception):
    """Raised when pack discovery fails."""
    pass


@dataclass
class PackInfo:
    """Information about a discovered pack."""

    pack_id: str
    path: Path
    has_lockfile: bool
    entry_count: Optional[int] = None
    entries_sha256: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result: dict[str, Any] = {
            "pack_id": self.pack_id,
            "path": str(self.path),
            "has_lockfile": self.has_lockfile,
        }
        if self.entry_count is not None:
            result["entry_count"] = self.entry_count
        if self.entries_sha256 is not None:
            result["entries_sha256"] = self.entries_sha256
        if self.error is not None:
            result["error"] = self.error
        return result


@dataclass
class VerifyResult:
    """Result of verifying a single pack."""

    pack_id: str
    path: Path
    valid: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "pack_id": self.pack_id,
            "path": str(self.path),
            "valid": self.valid,
            "errors": self.errors,
        }


def validate_discovery_root(root: Path) -> None:
    """
    Validate that discovery root is safe.

    Args:
        root: Root directory to validate

    Raises:
        DiscoveryError: If root is invalid or unsafe
    """
    if not root.exists():
        raise DiscoveryError(f"Discovery root does not exist: {root}")

    if not root.is_dir():
        raise DiscoveryError(f"Discovery root is not a directory: {root}")


def discover_packs(root: Path) -> list[Path]:
    """
    Discover all packs under a root directory.

    Finds directories containing pack.json and returns them
    in deterministic order (sorted by repo-relative path).

    Args:
        root: Root directory to search

    Returns:
        List of pack directory paths, sorted deterministically

    Raises:
        DiscoveryError: If root is invalid
    """
    root = Path(root).resolve()
    validate_discovery_root(root)

    pack_dirs: list[Path] = []

    for pack_json in root.rglob("pack.json"):
        # Ensure pack.json is a file, not a directory
        if pack_json.is_file():
            pack_dirs.append(pack_json.parent)

    # Sort by path string for deterministic ordering
    pack_dirs.sort(key=lambda p: str(p.relative_to(root)))

    return pack_dirs


def discover_packs_with_info(
    root: Path,
    relative_to: Optional[Path] = None,
) -> list[PackInfo]:
    """
    Discover packs and gather metadata about each.

    Args:
        root: Root directory to search
        relative_to: Optional path to make pack paths relative to

    Returns:
        List of PackInfo objects with metadata

    Raises:
        DiscoveryError: If root is invalid
    """
    root = Path(root).resolve()
    pack_dirs = discover_packs(root)

    results: list[PackInfo] = []

    for pack_dir in pack_dirs:
        # Determine path to report
        if relative_to:
            try:
                display_path = pack_dir.relative_to(relative_to.resolve())
            except ValueError:
                display_path = pack_dir
        else:
            display_path = pack_dir

        # Check for lockfile
        has_lockfile = (pack_dir / "pack.lock.json").is_file()

        # Try to load pack for metadata
        try:
            pack = load_pack(pack_dir, validate_first=True)
            results.append(PackInfo(
                pack_id=pack.pack_id,
                path=display_path,
                has_lockfile=has_lockfile,
                entry_count=pack.entry_count,
                entries_sha256=pack.entries_sha256,
            ))
        except (LoadError, FileNotFoundError) as e:
            # Still include pack but mark as having error
            # Try to get pack_id from pack.json if possible
            pack_id = "unknown"
            try:
                import json
                with open(pack_dir / "pack.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pack_id = data.get("pack_id", "unknown")
            except Exception:
                pass

            results.append(PackInfo(
                pack_id=pack_id,
                path=display_path,
                has_lockfile=has_lockfile,
                error=str(e),
            ))

    return results


def format_discovery_json(
    packs: list[PackInfo],
    fixed_time: Optional[str] = None,
) -> str:
    """
    Format discovery results as canonical JSON.

    Args:
        packs: List of PackInfo objects
        fixed_time: Fixed timestamp for deterministic output

    Returns:
        Canonical JSON string with trailing newline
    """
    if fixed_time:
        generated_at = fixed_time
    else:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    output = {
        "generated_at_utc": generated_at,
        "pack_count": len(packs),
        "packs": [p.to_dict() for p in packs],
    }

    return canonicalize_json(output)


def verify_all_packs(
    root: Path,
    fail_fast: bool = True,
) -> tuple[bool, list[VerifyResult]]:
    """
    Verify lockfiles for all packs under a root directory.

    Args:
        root: Root directory to search
        fail_fast: If True, stop at first failure

    Returns:
        (all_valid, results) tuple
    """
    root = Path(root).resolve()
    pack_dirs = discover_packs(root)

    results: list[VerifyResult] = []
    all_valid = True

    for pack_dir in pack_dirs:
        # Get pack_id
        pack_id = "unknown"
        try:
            import json
            with open(pack_dir / "pack.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                pack_id = data.get("pack_id", "unknown")
        except Exception:
            pass

        # Check lockfile exists
        lockfile_path = pack_dir / "pack.lock.json"
        if not lockfile_path.is_file():
            result = VerifyResult(
                pack_id=pack_id,
                path=pack_dir,
                valid=False,
                errors=["Lockfile not found: pack.lock.json"],
            )
            results.append(result)
            all_valid = False

            if fail_fast:
                return False, results
            continue

        # Verify lockfile
        is_valid, errors = verify_lockfile(pack_dir)

        result = VerifyResult(
            pack_id=pack_id,
            path=pack_dir,
            valid=is_valid,
            errors=errors,
        )
        results.append(result)

        if not is_valid:
            all_valid = False
            if fail_fast:
                return False, results

    return all_valid, results
