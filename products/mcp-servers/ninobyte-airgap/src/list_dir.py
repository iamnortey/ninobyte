"""
list_dir Tool Implementation

Security requirements:
- Do NOT stat/resolve denied entries in a way that follows symlinks outside allowed roots
- For denied entries, return type="unknown" and accessible=false without calling is_dir()/is_file()
- Handle OSError safely when checking allowed entries
"""

import os
from dataclasses import dataclass, asdict
from typing import List, Optional

try:
    from .config import AirGapConfig
    from .path_security import PathSecurityContext, PathDenialReason
    from .audit import AuditLogger
except ImportError:
    from config import AirGapConfig
    from path_security import PathSecurityContext, PathDenialReason
    from audit import AuditLogger


@dataclass
class DirectoryEntry:
    """Represents a single directory entry."""
    name: str
    path: str
    type: str  # "file", "directory", "symlink", "unknown"
    accessible: bool
    size: Optional[int] = None
    denial_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class ListDirResult:
    """Result of list_dir operation."""
    success: bool
    path: str
    entries: List[DirectoryEntry]
    error: Optional[str] = None
    truncated: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "path": self.path,
            "entries": [e.to_dict() for e in self.entries],
            "error": self.error,
            "truncated": self.truncated
        }


def list_dir(
    path: str,
    config: AirGapConfig,
    security_ctx: Optional[PathSecurityContext] = None,
    audit_logger: Optional[AuditLogger] = None
) -> ListDirResult:
    """
    List directory contents with security-aware metadata.

    Security guarantees:
    - Denied entries are NOT stat'd or resolved (no symlink following)
    - Denied entries return type="unknown", accessible=false
    - OSError is handled safely for all operations
    - Entries are bounded by max_results

    Args:
        path: Directory path to list
        config: AirGap configuration
        security_ctx: Optional pre-created security context
        audit_logger: Optional audit logger

    Returns:
        ListDirResult with entries and metadata
    """
    if security_ctx is None:
        security_ctx = PathSecurityContext(config)

    if audit_logger is None:
        audit_logger = AuditLogger(config)

    # Validate the directory path first
    validation = security_ctx.validate_path(path)

    if not validation.allowed:
        audit_logger.log_denied(
            operation="list_dir",
            path=path,
            reason=validation.denial_reason.value if validation.denial_reason else "unknown"
        )
        return ListDirResult(
            success=False,
            path=path,
            entries=[],
            error=f"Access denied: {validation.denial_detail}"
        )

    canonical_path = validation.canonical_path
    assert canonical_path is not None  # Guaranteed by allowed=True

    # Check if path is a directory
    try:
        if not os.path.isdir(canonical_path):
            audit_logger.log_denied(
                operation="list_dir",
                path=path,
                reason="not_a_directory"
            )
            return ListDirResult(
                success=False,
                path=path,
                entries=[],
                error="Path is not a directory"
            )
    except OSError as e:
        audit_logger.log_denied(
            operation="list_dir",
            path=path,
            reason="os_error"
        )
        return ListDirResult(
            success=False,
            path=path,
            entries=[],
            error=f"Cannot access directory: {e}"
        )

    entries: List[DirectoryEntry] = []
    truncated = False

    try:
        # Use scandir for efficient iteration (no list() materialization)
        with os.scandir(canonical_path) as dir_iter:
            for entry in dir_iter:
                if len(entries) >= config.max_results:
                    truncated = True
                    break

                entry_path = entry.path
                entry_name = entry.name

                # Check if this entry is accessible WITHOUT stating/resolving it
                # Use validate_path_no_follow to avoid symlink resolution for denied paths
                entry_validation = security_ctx.validate_path_no_follow(entry_path)

                if not entry_validation.allowed:
                    # SECURITY: Do NOT stat denied entries
                    # Return type="unknown" and accessible=false
                    entries.append(DirectoryEntry(
                        name=entry_name,
                        path=entry_path,
                        type="unknown",
                        accessible=False,
                        denial_reason=entry_validation.denial_reason.value if entry_validation.denial_reason else None
                    ))
                    continue

                # Entry is accessible - safe to stat
                try:
                    # Check for symlink FIRST (before following)
                    is_symlink = entry.is_symlink()

                    if is_symlink:
                        # For symlinks, validate the TARGET is within bounds
                        target_validation = security_ctx.validate_path(entry_path, follow_symlinks=True)

                        if not target_validation.allowed:
                            # Symlink target escapes allowed roots
                            entries.append(DirectoryEntry(
                                name=entry_name,
                                path=entry_path,
                                type="symlink",
                                accessible=False,
                                denial_reason="symlink_escape"
                            ))
                            continue

                        # Symlink with valid target - determine target type
                        try:
                            if os.path.isdir(entry_path):
                                entry_type = "directory"
                            elif os.path.isfile(entry_path):
                                entry_type = "file"
                            else:
                                entry_type = "symlink"
                        except OSError:
                            entry_type = "symlink"

                        entries.append(DirectoryEntry(
                            name=entry_name,
                            path=entry_path,
                            type=entry_type,
                            accessible=True
                        ))
                    else:
                        # Regular file or directory
                        if entry.is_dir(follow_symlinks=False):
                            entry_type = "directory"
                            size = None
                        elif entry.is_file(follow_symlinks=False):
                            entry_type = "file"
                            try:
                                size = entry.stat(follow_symlinks=False).st_size
                            except OSError:
                                size = None
                        else:
                            entry_type = "unknown"
                            size = None

                        entries.append(DirectoryEntry(
                            name=entry_name,
                            path=entry_path,
                            type=entry_type,
                            accessible=True,
                            size=size
                        ))

                except OSError as e:
                    # Handle OSError gracefully - entry exists but can't be stat'd
                    entries.append(DirectoryEntry(
                        name=entry_name,
                        path=entry_path,
                        type="unknown",
                        accessible=False,
                        denial_reason="permission_denied"
                    ))

    except OSError as e:
        audit_logger.log_denied(
            operation="list_dir",
            path=path,
            reason="os_error"
        )
        return ListDirResult(
            success=False,
            path=path,
            entries=[],
            error=f"Error reading directory: {e}"
        )

    # Log successful operation
    audit_logger.log_list_dir(
        path=canonical_path,
        entry_count=len(entries),
        success=True
    )

    return ListDirResult(
        success=True,
        path=canonical_path,
        entries=entries,
        truncated=truncated
    )
