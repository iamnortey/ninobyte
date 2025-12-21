"""
Pytest configuration and shared fixtures for AirGap tests.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports - must be done before importing our modules
_src_path = str(Path(__file__).parent.parent / 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Now import our modules
from config import AirGapConfig
from path_security import PathSecurityContext
from audit import AuditLogger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_tree(temp_dir):
    """Create a sample directory tree for testing."""
    # Create directories
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "nested").mkdir()
    (temp_dir / "denied_dir").mkdir()

    # Create files
    (temp_dir / "file1.txt").write_text("Hello World\nLine 2\nLine 3")
    (temp_dir / "file2.txt").write_text("Another file with searchable content")
    (temp_dir / "subdir" / "file3.txt").write_text("Nested file content")
    (temp_dir / "subdir" / "nested" / "deep.txt").write_text("Deep nested content")

    # Create a blocked pattern file
    (temp_dir / ".env").write_text("SECRET=should_not_be_readable")

    # Create a symlink (if supported)
    try:
        (temp_dir / "link_internal").symlink_to(temp_dir / "file1.txt")
    except OSError:
        pass  # Symlinks not supported on this platform

    return temp_dir


@pytest.fixture
def config_with_temp_dir(temp_dir):
    """Create a config with temp_dir as allowed root."""
    return AirGapConfig(
        allowed_roots=[str(temp_dir)],
        max_file_size_bytes=1_048_576,
        max_response_bytes=524_288,
        max_results=100,
        max_files_scanned=1000,
        timeout_seconds=10.0
    )


@pytest.fixture
def security_ctx(config_with_temp_dir):
    """Create a security context."""
    return PathSecurityContext(config_with_temp_dir)


@pytest.fixture
def audit_logger(temp_dir, config_with_temp_dir):
    """Create an audit logger with temp file."""
    config = AirGapConfig(
        allowed_roots=config_with_temp_dir.allowed_roots,
        audit_log_path=str(temp_dir / "audit.jsonl"),
        redact_paths_in_audit=True
    )
    return AuditLogger(config)


@pytest.fixture
def many_files_tree(temp_dir):
    """Create a tree with many files for budget testing."""
    for i in range(50):
        subdir = temp_dir / f"dir_{i:03d}"
        subdir.mkdir()
        for j in range(20):
            (subdir / f"file_{j:03d}.txt").write_text(f"Content {i}-{j}")

    return temp_dir
