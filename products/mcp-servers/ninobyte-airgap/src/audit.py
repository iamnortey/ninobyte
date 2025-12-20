"""
Audit Logging Module

Local JSONL audit logging with security guarantees:
- No content logging (only metadata)
- Path redaction enabled by default
- Actual bytes read logged (not file size)
- Local file only (no network transmission)
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .config import AirGapConfig
except ImportError:
    from config import AirGapConfig


@dataclass
class AuditEntry:
    """Structured audit log entry."""
    timestamp: str
    operation: str
    path: Optional[str] = None
    path_hash: Optional[str] = None
    success: bool = True
    denial_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), separators=(',', ':'))


class AuditLogger:
    """
    Security-focused audit logger.

    Logs operations to local JSONL file with path redaction support.
    """

    def __init__(self, config: AirGapConfig):
        self.config = config
        self._log_path: Optional[Path] = None

        if config.audit_log_path:
            self._log_path = Path(config.audit_log_path)
            # Ensure parent directory exists
            self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _hash_path(self, path: str) -> str:
        """Create a deterministic hash of a path for redacted logging."""
        return hashlib.sha256(path.encode('utf-8')).hexdigest()[:16]

    def _get_timestamp(self) -> str:
        """Get ISO 8601 timestamp in UTC."""
        return datetime.now(timezone.utc).isoformat()

    def log(
        self,
        operation: str,
        path: Optional[str] = None,
        success: bool = True,
        denial_reason: Optional[str] = None,
        **metadata: Any
    ) -> AuditEntry:
        """
        Log an audit entry.

        Args:
            operation: The operation being performed (e.g., "read_file", "list_dir")
            path: The path being accessed (will be redacted if configured)
            success: Whether the operation succeeded
            denial_reason: If denied, the reason for denial
            **metadata: Additional metadata to log (e.g., bytes_read, offset)

        Returns:
            The created AuditEntry
        """
        entry = AuditEntry(
            timestamp=self._get_timestamp(),
            operation=operation,
            success=success,
            denial_reason=denial_reason,
            metadata=metadata
        )

        if path:
            if self.config.redact_paths_in_audit:
                entry.path_hash = self._hash_path(path)
            else:
                entry.path = path

        # Write to log file if configured
        if self._log_path:
            try:
                with open(self._log_path, 'a', encoding='utf-8') as f:
                    f.write(entry.to_json() + '\n')
            except OSError:
                # Fail silently on log write errors (don't break operations)
                pass

        return entry

    def log_read(
        self,
        path: str,
        bytes_read: int,
        offset: int = 0,
        limit: Optional[int] = None,
        success: bool = True,
        denial_reason: Optional[str] = None
    ) -> AuditEntry:
        """
        Log a file read operation with accurate byte count.

        IMPORTANT: bytes_read must be the ACTUAL bytes read, not file size.
        """
        return self.log(
            operation="read_file",
            path=path,
            success=success,
            denial_reason=denial_reason,
            bytes_read=bytes_read,
            offset=offset,
            limit=limit
        )

    def log_list_dir(
        self,
        path: str,
        entry_count: int,
        success: bool = True,
        denial_reason: Optional[str] = None
    ) -> AuditEntry:
        """Log a directory listing operation."""
        return self.log(
            operation="list_dir",
            path=path,
            success=success,
            denial_reason=denial_reason,
            entry_count=entry_count
        )

    def log_search(
        self,
        path: str,
        pattern: str,
        files_scanned: int,
        matches_found: int,
        method: str,  # "ripgrep" or "python"
        success: bool = True,
        denial_reason: Optional[str] = None,
        timed_out: bool = False
    ) -> AuditEntry:
        """Log a search operation."""
        return self.log(
            operation="search_text",
            path=path,
            success=success,
            denial_reason=denial_reason,
            pattern_hash=self._hash_path(pattern),  # Don't log actual pattern
            files_scanned=files_scanned,
            matches_found=matches_found,
            method=method,
            timed_out=timed_out
        )

    def log_denied(
        self,
        operation: str,
        path: str,
        reason: str
    ) -> AuditEntry:
        """Log a denied operation."""
        return self.log(
            operation=operation,
            path=path,
            success=False,
            denial_reason=reason
        )
