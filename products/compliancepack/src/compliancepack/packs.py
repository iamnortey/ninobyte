"""
CompliancePack Pack Resolver.

Handles built-in policy packs (Control Packs) with deterministic discovery
and strict name validation.

Packs are stored in the packs/ directory relative to the package root.
Pack names must be strict identifiers (no path separators, no traversal).
"""

import re
from pathlib import Path
from typing import List

from compliancepack.policy import PolicyFileDict, load_policy_file


# Pack name validation: alphanumeric, dots, underscores, hyphens only
# No path separators, no traversal patterns
PACK_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class PackError(Exception):
    """Raised when pack operations fail."""
    pass


def _get_packs_dir() -> Path:
    """Get the packs directory path."""
    # packs/ is a sibling to src/ in the product directory
    package_dir = Path(__file__).parent.parent.parent
    return package_dir / "packs"


def _validate_pack_name(name: str) -> None:
    """
    Validate pack name is safe.

    Args:
        name: Pack name to validate

    Raises:
        PackError: If name is invalid
    """
    if not name:
        raise PackError("Pack name cannot be empty")

    if not PACK_NAME_PATTERN.match(name):
        raise PackError(
            f"Invalid pack name '{name}': must be alphanumeric with dots, "
            "underscores, or hyphens only (no path separators)"
        )

    # Extra safety: reject any path traversal attempts
    if ".." in name or "/" in name or "\\" in name:
        raise PackError(f"Invalid pack name '{name}': path traversal not allowed")


def list_packs() -> List[str]:
    """
    List available built-in packs.

    Returns:
        Sorted list of pack names (without .json extension)

    The list is deterministic (alphabetically sorted) for reproducibility.
    """
    packs_dir = _get_packs_dir()

    if not packs_dir.exists():
        return []

    packs = []
    for path in packs_dir.glob("*.json"):
        if path.is_file():
            # Remove .json extension for pack name
            pack_name = path.stem
            packs.append(pack_name)

    # Sort for deterministic ordering
    packs.sort()

    return packs


def load_pack(name: str) -> PolicyFileDict:
    """
    Load a built-in pack by name.

    Args:
        name: Pack name (without .json extension)

    Returns:
        Validated PolicyFileDict

    Raises:
        PackError: If pack name is invalid or pack not found
    """
    _validate_pack_name(name)

    packs_dir = _get_packs_dir()
    pack_path = packs_dir / f"{name}.json"

    if not pack_path.exists():
        available = list_packs()
        if available:
            raise PackError(
                f"Pack '{name}' not found. Available packs: {', '.join(available)}"
            )
        else:
            raise PackError(f"Pack '{name}' not found. No packs available.")

    # Use the standard policy loader for validation
    return load_policy_file(pack_path)


def get_pack_path(name: str) -> Path:
    """
    Get the filesystem path for a pack.

    Args:
        name: Pack name (without .json extension)

    Returns:
        Path to the pack file

    Raises:
        PackError: If pack name is invalid or pack not found
    """
    _validate_pack_name(name)

    packs_dir = _get_packs_dir()
    pack_path = packs_dir / f"{name}.json"

    if not pack_path.exists():
        raise PackError(f"Pack '{name}' not found")

    return pack_path
