"""
search_text Tool Implementation

Security requirements:
- Python fallback: NO list() materialization of path.rglob() (avoid DoS/memory)
- Python fallback: Lazy iteration with max_files_scanned budget
- Python fallback: TimeoutContext checked per-file and per-line
- ripgrep path: shell=False, explicit argv list
- ripgrep path: --no-follow to avoid symlink escape, bounded results
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional, Tuple

try:
    from .config import AirGapConfig
    from .path_security import PathSecurityContext
    from .audit import AuditLogger
    from .timeout import TimeoutContext, TimeoutExpired, timeout_context
except ImportError:
    from config import AirGapConfig
    from path_security import PathSecurityContext
    from audit import AuditLogger
    from timeout import TimeoutContext, TimeoutExpired, timeout_context


@dataclass
class SearchMatch:
    """A single search match."""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "match_start": self.match_start,
            "match_end": self.match_end
        }


@dataclass
class SearchResult:
    """Result of search_text operation."""
    success: bool
    pattern: str
    root_path: str
    matches: List[SearchMatch] = field(default_factory=list)
    files_scanned: int = 0
    method: str = "python"  # "python" or "ripgrep"
    truncated: bool = False
    timed_out: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "pattern": self.pattern,
            "root_path": self.root_path,
            "matches": [m.to_dict() for m in self.matches],
            "files_scanned": self.files_scanned,
            "method": self.method,
            "truncated": self.truncated,
            "timed_out": self.timed_out,
            "error": self.error
        }


def _iter_files_lazy(
    root: Path,
    security_ctx: PathSecurityContext,
    timeout_ctx: TimeoutContext,
    max_files: int
) -> Generator[Path, None, Tuple[int, bool]]:
    """
    Lazily iterate files under root with security and budget enforcement.

    CRITICAL: Uses generator-based iteration, NO list() materialization.
    Checks timeout per-directory to ensure timely termination.

    Yields:
        Path objects for accessible files

    Returns:
        Tuple of (files_scanned, budget_exhausted)
    """
    files_scanned = 0
    budget_exhausted = False

    # Use os.walk for lazy iteration (NOT Path.rglob which can be eager)
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            # Check timeout at directory level
            timeout_ctx.check()

            # Filter out inaccessible directories to prevent descending into them
            accessible_dirs = []
            for dirname in dirnames:
                dir_full_path = os.path.join(dirpath, dirname)
                if security_ctx.is_entry_in_allowed_scope(dir_full_path):
                    accessible_dirs.append(dirname)
            dirnames[:] = accessible_dirs  # Modify in-place to affect os.walk

            for filename in filenames:
                # Check budget
                if files_scanned >= max_files:
                    budget_exhausted = True
                    return files_scanned, budget_exhausted

                file_path = os.path.join(dirpath, filename)

                # Validate file is accessible
                validation = security_ctx.validate_path(file_path)
                if not validation.allowed:
                    continue

                files_scanned += 1
                yield Path(file_path)

    except TimeoutExpired:
        raise
    except OSError:
        # Permission errors during walk - continue with what we have
        pass

    return files_scanned, budget_exhausted


def _search_file_python(
    file_path: Path,
    pattern: re.Pattern,
    timeout_ctx: TimeoutContext,
    max_results: int,
    current_matches: int
) -> Generator[SearchMatch, None, None]:
    """
    Search a single file using Python regex.

    Checks timeout per-line for responsive termination.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, start=1):
                # Check timeout per-line
                timeout_ctx.check()

                # Check if we've hit max results
                if current_matches >= max_results:
                    return

                # Search for pattern
                for match in pattern.finditer(line):
                    if current_matches >= max_results:
                        return

                    yield SearchMatch(
                        file_path=str(file_path),
                        line_number=line_num,
                        line_content=line.rstrip('\n\r'),
                        match_start=match.start(),
                        match_end=match.end()
                    )
                    current_matches += 1

    except (OSError, UnicodeDecodeError):
        # Skip files that can't be read
        pass


def _search_python_fallback(
    root_path: str,
    pattern: str,
    config: AirGapConfig,
    security_ctx: PathSecurityContext,
    timeout_ctx: TimeoutContext
) -> SearchResult:
    """
    Python-based search implementation.

    Security guarantees:
    - NO list() materialization of file iteration
    - max_files_scanned budget enforced
    - Timeout checked per-file and per-line
    """
    try:
        compiled_pattern = re.compile(pattern)
    except re.error as e:
        return SearchResult(
            success=False,
            pattern=pattern,
            root_path=root_path,
            error=f"Invalid regex pattern: {e}"
        )

    matches: List[SearchMatch] = []
    files_scanned = 0
    truncated = False
    timed_out = False

    root = Path(root_path)

    try:
        # Lazy file iteration with budget
        for file_path in _iter_files_lazy(
            root,
            security_ctx,
            timeout_ctx,
            config.max_files_scanned
        ):
            files_scanned += 1

            # Check timeout per-file
            timeout_ctx.check()

            # Skip files that are too large
            try:
                if file_path.stat().st_size > config.max_file_size_bytes:
                    continue
            except OSError:
                continue

            # Search file
            for match in _search_file_python(
                file_path,
                compiled_pattern,
                timeout_ctx,
                config.max_results,
                len(matches)
            ):
                matches.append(match)
                if len(matches) >= config.max_results:
                    truncated = True
                    break

            if len(matches) >= config.max_results:
                truncated = True
                break

            # Check if we've exhausted file budget
            if files_scanned >= config.max_files_scanned:
                truncated = True
                break

    except TimeoutExpired:
        timed_out = True

    return SearchResult(
        success=True,
        pattern=pattern,
        root_path=root_path,
        matches=matches,
        files_scanned=files_scanned,
        method="python",
        truncated=truncated,
        timed_out=timed_out
    )


def _search_ripgrep(
    root_path: str,
    pattern: str,
    config: AirGapConfig,
    security_ctx: PathSecurityContext,
    timeout_ctx: TimeoutContext
) -> Optional[SearchResult]:
    """
    ripgrep-based search implementation.

    Security guarantees:
    - shell=False with explicit argv list
    - --no-follow to prevent symlink escape
    - Bounded results via --max-count
    - Timeout enforced via subprocess timeout
    """
    rg_path = shutil.which('rg')
    if not rg_path:
        return None  # Fall back to Python

    # Build explicit argv list - NO shell=True
    argv = [
        rg_path,
        '--no-follow',           # Do NOT follow symlinks
        '--no-heading',          # No file grouping
        '--line-number',         # Include line numbers
        '--column',              # Include column numbers
        '--max-count', str(config.max_results),  # Limit matches per file
        '--max-filesize', f'{config.max_file_size_bytes}',  # Skip large files
        '--',                    # End of options
        pattern,
        root_path
    ]

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_ctx.remaining(),
            shell=False  # EXPLICIT: Never use shell=True
        )
    except subprocess.TimeoutExpired:
        return SearchResult(
            success=True,
            pattern=pattern,
            root_path=root_path,
            matches=[],
            files_scanned=0,
            method="ripgrep",
            truncated=True,
            timed_out=True
        )
    except OSError:
        return None  # Fall back to Python

    matches: List[SearchMatch] = []
    files_seen = set()

    # Parse ripgrep output: file:line:column:content
    for line in result.stdout.split('\n'):
        if not line:
            continue

        if len(matches) >= config.max_results:
            break

        # Parse ripgrep output format
        parts = line.split(':', 3)
        if len(parts) >= 4:
            file_path, line_num_str, col_str, content = parts[0], parts[1], parts[2], parts[3]

            # Validate file is accessible (belt-and-suspenders)
            validation = security_ctx.validate_path(file_path)
            if not validation.allowed:
                continue

            files_seen.add(file_path)

            try:
                line_num = int(line_num_str)
                col = int(col_str)
            except ValueError:
                continue

            matches.append(SearchMatch(
                file_path=file_path,
                line_number=line_num,
                line_content=content,
                match_start=col - 1,  # ripgrep columns are 1-indexed
                match_end=col - 1 + len(pattern)  # Approximate
            ))

    return SearchResult(
        success=True,
        pattern=pattern,
        root_path=root_path,
        matches=matches,
        files_scanned=len(files_seen),
        method="ripgrep",
        truncated=len(matches) >= config.max_results
    )


def search_text(
    root_path: str,
    pattern: str,
    config: AirGapConfig,
    security_ctx: Optional[PathSecurityContext] = None,
    audit_logger: Optional[AuditLogger] = None,
    prefer_ripgrep: bool = True
) -> SearchResult:
    """
    Search for text pattern in files under root_path.

    Uses ripgrep if available (faster, more secure), falls back to Python.

    Args:
        root_path: Directory to search in
        pattern: Regex pattern to search for
        config: AirGap configuration
        security_ctx: Optional pre-created security context
        audit_logger: Optional audit logger
        prefer_ripgrep: If True, try ripgrep first (default True)

    Returns:
        SearchResult with matches and metadata
    """
    if security_ctx is None:
        security_ctx = PathSecurityContext(config)

    if audit_logger is None:
        audit_logger = AuditLogger(config)

    # Validate root path
    validation = security_ctx.validate_path(root_path)
    if not validation.allowed:
        audit_logger.log_search(
            path=root_path,
            pattern=pattern,
            files_scanned=0,
            matches_found=0,
            method="none",
            success=False,
            denial_reason=validation.denial_reason.value if validation.denial_reason else "unknown"
        )
        return SearchResult(
            success=False,
            pattern=pattern,
            root_path=root_path,
            error=f"Access denied: {validation.denial_detail}"
        )

    canonical_root = validation.canonical_path
    assert canonical_root is not None

    # Check if it's a directory
    if not os.path.isdir(canonical_root):
        audit_logger.log_search(
            path=canonical_root,
            pattern=pattern,
            files_scanned=0,
            matches_found=0,
            method="none",
            success=False,
            denial_reason="not_a_directory"
        )
        return SearchResult(
            success=False,
            pattern=pattern,
            root_path=canonical_root,
            error="Path is not a directory"
        )

    with timeout_context(config.timeout_seconds) as timeout_ctx:
        result: Optional[SearchResult] = None

        # Try ripgrep first if preferred
        if prefer_ripgrep:
            result = _search_ripgrep(
                canonical_root,
                pattern,
                config,
                security_ctx,
                timeout_ctx
            )

        # Fall back to Python if ripgrep unavailable or failed
        if result is None:
            result = _search_python_fallback(
                canonical_root,
                pattern,
                config,
                security_ctx,
                timeout_ctx
            )

    # Log the search
    audit_logger.log_search(
        path=canonical_root,
        pattern=pattern,
        files_scanned=result.files_scanned,
        matches_found=len(result.matches),
        method=result.method,
        success=result.success,
        timed_out=result.timed_out
    )

    return result
