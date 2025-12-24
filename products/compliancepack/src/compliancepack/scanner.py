"""
CompliancePack File Scanner.

Stdlib-only directory traversal with security boundaries.

Contract:
- collect_targets(): Enumerate files deterministically (sorted paths)
- read_file_limited(): Safe read with byte limit and decode fallback
- No network, shell, or file write operations

Security boundaries:
- realpath canonicalization prevents path traversal
- Symlink targets validated against allowed root (optional)
- Max file count caps enumeration
- Max bytes per file prevents memory exhaustion
"""

from pathlib import Path
from typing import List, Optional, Set, Tuple


class ScanError(Exception):
    """Error during file scanning."""

    pass


class PathTraversalError(ScanError):
    """Attempted path traversal detected."""

    pass


class SymlinkEscapeError(ScanError):
    """Symlink target escapes allowed boundary."""

    pass


class MaxFilesExceededError(ScanError):
    """Max file count exceeded."""

    pass


def _normalize_path(path: Path) -> Path:
    """
    Normalize path using realpath canonicalization.

    Args:
        path: Path to normalize

    Returns:
        Canonicalized absolute path
    """
    return Path(path).resolve()


def _is_within_boundary(target: Path, boundary: Path) -> bool:
    """
    Check if target path is within boundary.

    Args:
        target: Path to check
        boundary: Boundary root path

    Returns:
        True if target is within boundary
    """
    try:
        target.relative_to(boundary)
        return True
    except ValueError:
        return False


def _matches_extensions(path: Path, extensions: Optional[Set[str]]) -> bool:
    """
    Check if path matches allowed extensions.

    Args:
        path: Path to check
        extensions: Set of allowed extensions (e.g., {".txt", ".env"})
                   None means match all files

    Returns:
        True if path matches or no extension filter
    """
    if extensions is None:
        return True
    # Handle multi-suffix like .tar.gz - use full suffix
    suffix = path.suffix.lower()
    return suffix in extensions


def collect_targets(
    inputs: List[Path],
    include_extensions: Optional[Set[str]] = None,
    follow_symlinks: bool = False,
    max_files: int = 5000,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """
    Collect target files from input paths (files or directories).

    Args:
        inputs: List of input paths (files or directories)
        include_extensions: Set of allowed extensions (e.g., {".txt", ".env"})
                           None means scan all files
        follow_symlinks: Whether to follow symlinks (default: False)
        max_files: Maximum number of files to collect

    Returns:
        Tuple of (collected_files, skipped_files)
        - collected_files: Sorted list of file paths
        - skipped_files: List of (path, reason) tuples

    Raises:
        PathTraversalError: If path traversal detected
        SymlinkEscapeError: If symlink escapes boundary
        MaxFilesExceededError: If max_files exceeded (only as warning in return)
    """
    if max_files < 1:
        raise ValueError("max_files must be >= 1")

    collected: Set[Path] = set()
    skipped: List[Tuple[Path, str]] = []

    # Normalize all input roots
    boundaries: List[Path] = []
    for input_path in inputs:
        normalized = _normalize_path(input_path)
        if not normalized.exists():
            skipped.append((input_path, "not_found"))
            continue
        # Boundary is the parent directory for files, or the directory itself
        if normalized.is_file():
            boundaries.append(normalized.parent)
        else:
            boundaries.append(normalized)

    def is_within_any_boundary(path: Path) -> bool:
        """Check if path is within any allowed boundary."""
        for boundary in boundaries:
            if _is_within_boundary(path, boundary):
                return True
        return False

    def process_path(path: Path, from_input: Path) -> None:
        """Process a single path, recursing into directories."""
        nonlocal collected, skipped

        # Early exit if we've hit max_files
        if len(collected) >= max_files:
            return

        try:
            normalized = _normalize_path(path)
        except (OSError, RuntimeError) as e:
            skipped.append((path, f"resolve_error:{e}"))
            return

        # Check for path traversal via ..
        if not is_within_any_boundary(normalized):
            skipped.append((path, "path_traversal"))
            return

        # Handle symlinks
        if path.is_symlink():
            if not follow_symlinks:
                skipped.append((path, "symlink_skipped"))
                return
            # Symlink following enabled - verify target is within boundary
            try:
                target = path.resolve()
                if not is_within_any_boundary(target):
                    skipped.append((path, "symlink_escape"))
                    return
            except (OSError, RuntimeError):
                skipped.append((path, "symlink_broken"))
                return

        if normalized.is_file():
            # Check extension filter
            if not _matches_extensions(normalized, include_extensions):
                skipped.append((path, "extension_filtered"))
                return
            collected.add(normalized)
        elif normalized.is_dir():
            # Recurse into directory
            try:
                children = list(normalized.iterdir())
            except PermissionError:
                skipped.append((path, "permission_denied"))
                return
            except OSError as e:
                skipped.append((path, f"read_error:{e}"))
                return

            # Sort children for deterministic traversal
            children.sort(key=lambda p: p.name)
            for child in children:
                if len(collected) >= max_files:
                    break
                process_path(child, from_input)
        else:
            # Special file (socket, device, etc.)
            skipped.append((path, "special_file"))

    # Track if we hit the limit (for reporting)
    hit_max_files = False

    # Process each input
    for input_path in inputs:
        path = Path(input_path)
        process_path(path, path)
        if len(collected) >= max_files:
            hit_max_files = True

    # Sort collected files for deterministic output
    sorted_files = sorted(collected, key=lambda p: str(p))

    # Truncate if over max (deterministic - already sorted)
    if len(sorted_files) > max_files:
        sorted_files = sorted_files[:max_files]
        hit_max_files = True

    # Add truncation notice if we hit the limit
    if hit_max_files and len(sorted_files) == max_files:
        skipped.append((Path("<truncated>"), f"max_files_exceeded:{len(collected)}"))

    return sorted_files, skipped


def read_file_limited(
    path: Path,
    max_bytes: int = 1_000_000,
) -> Tuple[str, bool]:
    """
    Read file content with byte limit and safe decode.

    Args:
        path: Path to file
        max_bytes: Maximum bytes to read

    Returns:
        Tuple of (content, was_truncated)

    Raises:
        ScanError: If file cannot be read
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")

    try:
        file_size = path.stat().st_size
        truncated = file_size > max_bytes

        with open(path, "rb") as f:
            raw = f.read(max_bytes)

        # Try UTF-8 first, then fallback to latin-1 (always succeeds)
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("latin-1")

        return content, truncated

    except PermissionError:
        raise ScanError(f"Permission denied: {path}")
    except FileNotFoundError:
        raise ScanError(f"File not found: {path}")
    except OSError as e:
        raise ScanError(f"Read error: {path}: {e}")


def summarize_skipped(skipped: List[Tuple[Path, str]]) -> dict:
    """
    Summarize skipped files by reason.

    Args:
        skipped: List of (path, reason) tuples

    Returns:
        Dict mapping reason -> count (stable key order)
    """
    counts: dict = {}
    for _, reason in skipped:
        # Normalize reasons with dynamic parts
        if reason.startswith("resolve_error:"):
            reason = "resolve_error"
        elif reason.startswith("read_error:"):
            reason = "read_error"
        elif reason.startswith("max_files_exceeded:"):
            reason = "max_files_exceeded"
        counts[reason] = counts.get(reason, 0) + 1

    # Sort by key for determinism
    return dict(sorted(counts.items()))
