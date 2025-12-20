"""
read_file Tool Implementation

Security requirements:
- Audit must log the ACTUAL bytes read, not file size
- offset + limit are respected and recorded properly in audit metadata
- Size limits enforced before reading
- Blocked patterns checked before any I/O
"""

import os
from dataclasses import dataclass
from typing import Optional

try:
    from .config import AirGapConfig
    from .path_security import PathSecurityContext
    from .audit import AuditLogger
except ImportError:
    from config import AirGapConfig
    from path_security import PathSecurityContext
    from audit import AuditLogger


@dataclass
class ReadFileResult:
    """Result of read_file operation."""
    success: bool
    path: str
    content: Optional[str] = None
    bytes_read: int = 0
    offset: int = 0
    limit: Optional[int] = None
    truncated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "path": self.path,
            "content": self.content,
            "bytes_read": self.bytes_read,
            "offset": self.offset,
            "limit": self.limit,
            "truncated": self.truncated,
            "error": self.error
        }


def read_file(
    path: str,
    config: AirGapConfig,
    offset: int = 0,
    limit: Optional[int] = None,
    security_ctx: Optional[PathSecurityContext] = None,
    audit_logger: Optional[AuditLogger] = None
) -> ReadFileResult:
    """
    Read file contents with security controls.

    Security guarantees:
    - Path is validated before any I/O
    - Blocked patterns are enforced
    - Size limits prevent reading huge files
    - ACTUAL bytes read are logged (not file size)
    - offset + limit are respected and audited

    Args:
        path: File path to read
        config: AirGap configuration
        offset: Byte offset to start reading from (default 0)
        limit: Maximum bytes to read (default: max_file_size_bytes)
        security_ctx: Optional pre-created security context
        audit_logger: Optional audit logger

    Returns:
        ReadFileResult with content and metadata
    """
    if security_ctx is None:
        security_ctx = PathSecurityContext(config)

    if audit_logger is None:
        audit_logger = AuditLogger(config)

    # Apply default limit
    effective_limit = limit if limit is not None else config.max_file_size_bytes

    # Clamp limit to max
    if effective_limit > config.max_file_size_bytes:
        effective_limit = config.max_file_size_bytes

    # Validate path
    validation = security_ctx.validate_path(path)

    if not validation.allowed:
        audit_logger.log_read(
            path=path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            success=False,
            denial_reason=validation.denial_reason.value if validation.denial_reason else "unknown"
        )
        return ReadFileResult(
            success=False,
            path=path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            error=f"Access denied: {validation.denial_detail}"
        )

    canonical_path = validation.canonical_path
    assert canonical_path is not None

    # Check if it's a file
    try:
        if not os.path.isfile(canonical_path):
            audit_logger.log_read(
                path=canonical_path,
                bytes_read=0,
                offset=offset,
                limit=effective_limit,
                success=False,
                denial_reason="not_a_file"
            )
            return ReadFileResult(
                success=False,
                path=canonical_path,
                bytes_read=0,
                offset=offset,
                limit=effective_limit,
                error="Path is not a file"
            )
    except OSError as e:
        audit_logger.log_read(
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            success=False,
            denial_reason="os_error"
        )
        return ReadFileResult(
            success=False,
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            error=f"Cannot access file: {e}"
        )

    # Check file size before reading
    try:
        file_size = os.path.getsize(canonical_path)
    except OSError as e:
        audit_logger.log_read(
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            success=False,
            denial_reason="os_error"
        )
        return ReadFileResult(
            success=False,
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            error=f"Cannot get file size: {e}"
        )

    # Check if offset is beyond file
    if offset >= file_size:
        audit_logger.log_read(
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            success=True
        )
        return ReadFileResult(
            success=True,
            path=canonical_path,
            content="",
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            truncated=False
        )

    # Calculate how much we can read
    available_bytes = file_size - offset
    bytes_to_read = min(available_bytes, effective_limit)
    truncated = available_bytes > effective_limit

    # Read the file
    try:
        with open(canonical_path, 'rb') as f:
            if offset > 0:
                f.seek(offset)

            raw_content = f.read(bytes_to_read)
            actual_bytes_read = len(raw_content)

            # Try to decode as UTF-8
            try:
                content = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                # Fall back to latin-1 (never fails)
                content = raw_content.decode('latin-1')

    except OSError as e:
        audit_logger.log_read(
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            success=False,
            denial_reason="os_error"
        )
        return ReadFileResult(
            success=False,
            path=canonical_path,
            bytes_read=0,
            offset=offset,
            limit=effective_limit,
            error=f"Error reading file: {e}"
        )

    # Check response size limit
    response_truncated = False
    if len(content.encode('utf-8')) > config.max_response_bytes:
        # Truncate content to fit response limit
        # This is approximate but safe
        content = content[:config.max_response_bytes]
        response_truncated = True
        truncated = True

    # CRITICAL: Log ACTUAL bytes read, not file size
    audit_logger.log_read(
        path=canonical_path,
        bytes_read=actual_bytes_read,  # ACTUAL bytes read
        offset=offset,
        limit=effective_limit,
        success=True
    )

    return ReadFileResult(
        success=True,
        path=canonical_path,
        content=content,
        bytes_read=actual_bytes_read,  # ACTUAL bytes read
        offset=offset,
        limit=effective_limit,
        truncated=truncated
    )
