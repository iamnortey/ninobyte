"""
Path Security Module

Provides path validation, canonicalization, and traversal prevention.

Security guarantees:
- All paths are canonicalized before use
- Symlink targets are validated to remain within allowed roots
- Traversal sequences are detected and rejected
- Blocked patterns are enforced
"""

import fnmatch
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from .config import AirGapConfig
except ImportError:
    from config import AirGapConfig


class PathDenialReason(Enum):
    """Reasons why a path may be denied access."""
    OUTSIDE_ALLOWED_ROOTS = "outside_allowed_roots"
    TRAVERSAL_DETECTED = "traversal_detected"
    SYMLINK_ESCAPE = "symlink_escape"
    BLOCKED_PATTERN = "blocked_pattern"
    NOT_EXISTS = "not_exists"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class PathValidationResult:
    """Result of path validation."""
    allowed: bool
    canonical_path: Optional[str] = None
    denial_reason: Optional[PathDenialReason] = None
    denial_detail: Optional[str] = None


class PathSecurityContext:
    """
    Security context for path operations.

    Provides safe path validation without following symlinks for denied entries.
    """

    def __init__(self, config: AirGapConfig):
        self.config = config
        self._allowed_roots_canonical: List[str] = []

        # Pre-canonicalize allowed roots
        for root in config.allowed_roots:
            try:
                canonical = os.path.realpath(root)
                if os.path.isdir(canonical):
                    self._allowed_roots_canonical.append(canonical)
            except OSError:
                # Skip roots that can't be resolved
                pass

    def _is_under_allowed_root(self, canonical_path: str) -> bool:
        """Check if canonical path is under an allowed root."""
        for root in self._allowed_roots_canonical:
            # Ensure we check with trailing separator to avoid prefix attacks
            # e.g., /home/user vs /home/username
            if canonical_path == root:
                return True
            if canonical_path.startswith(root + os.sep):
                return True
        return False

    def _matches_blocked_pattern(self, path: str) -> Optional[str]:
        """Check if path matches any blocked pattern. Returns matching pattern or None."""
        basename = os.path.basename(path)
        # Normalize path separators for cross-platform pattern matching
        # Windows paths use backslashes, but blocked patterns use forward slashes
        normalized_path = path.replace("\\", "/")

        for pattern in self.config.blocked_patterns:
            # Check basename match
            if fnmatch.fnmatch(basename, pattern):
                return pattern
            # Check if pattern appears in path (for patterns like .git/config)
            if '/' in pattern and pattern in normalized_path:
                return pattern

        return None

    def validate_path(self, path: str, follow_symlinks: bool = True) -> PathValidationResult:
        """
        Validate a path for access.

        Args:
            path: The path to validate
            follow_symlinks: If True, resolve symlinks and validate target.
                           If False, validate the path as-is (for denied entry handling).

        Returns:
            PathValidationResult with access decision and canonical path if allowed.
        """
        if not self._allowed_roots_canonical:
            return PathValidationResult(
                allowed=False,
                denial_reason=PathDenialReason.OUTSIDE_ALLOWED_ROOTS,
                denial_detail="no allowed roots configured"
            )

        # Detect obvious traversal attempts in input
        if '..' in path.split(os.sep):
            return PathValidationResult(
                allowed=False,
                denial_reason=PathDenialReason.TRAVERSAL_DETECTED,
                denial_detail="path contains traversal sequence"
            )

        try:
            # Expand user home directory
            expanded = os.path.expanduser(path)

            # Make absolute
            if not os.path.isabs(expanded):
                expanded = os.path.abspath(expanded)

            if follow_symlinks:
                # Full canonicalization (follows symlinks)
                canonical = os.path.realpath(expanded)
            else:
                # Normalize without following symlinks
                canonical = os.path.normpath(expanded)

        except OSError as e:
            return PathValidationResult(
                allowed=False,
                denial_reason=PathDenialReason.PERMISSION_DENIED,
                denial_detail=str(e)
            )

        # Check blocked patterns BEFORE checking existence (fail fast)
        blocked_match = self._matches_blocked_pattern(canonical)
        if blocked_match:
            return PathValidationResult(
                allowed=False,
                canonical_path=canonical,
                denial_reason=PathDenialReason.BLOCKED_PATTERN,
                denial_detail=f"matches blocked pattern: {blocked_match}"
            )

        # Check if within allowed roots
        if not self._is_under_allowed_root(canonical):
            return PathValidationResult(
                allowed=False,
                canonical_path=canonical,
                denial_reason=PathDenialReason.OUTSIDE_ALLOWED_ROOTS,
                denial_detail="path is outside allowed roots"
            )

        # If following symlinks, check for symlink escape
        if follow_symlinks and os.path.islink(expanded):
            # The symlink target (canonical) is already validated above
            # But double-check the resolved path is still within bounds
            if not self._is_under_allowed_root(canonical):
                return PathValidationResult(
                    allowed=False,
                    canonical_path=canonical,
                    denial_reason=PathDenialReason.SYMLINK_ESCAPE,
                    denial_detail="symlink target escapes allowed roots"
                )

        return PathValidationResult(
            allowed=True,
            canonical_path=canonical
        )

    def validate_path_no_follow(self, path: str) -> PathValidationResult:
        """
        Validate path WITHOUT following symlinks.

        Use this for checking if a path component (like a directory entry)
        is accessible without triggering symlink resolution.
        """
        return self.validate_path(path, follow_symlinks=False)

    def is_path_accessible(self, path: str) -> bool:
        """Quick check if path is accessible (follows symlinks)."""
        return self.validate_path(path).allowed

    def is_entry_in_allowed_scope(self, entry_path: str) -> bool:
        """
        Check if a directory entry is within allowed scope WITHOUT stating it.

        This is used for list_dir to determine if an entry should be accessible
        without actually resolving symlinks or checking file type.
        """
        result = self.validate_path_no_follow(entry_path)
        return result.allowed
