"""
Tests for audit module.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import AirGapConfig
from audit import AuditLogger, AuditEntry


class TestAuditLogging:
    """Tests for audit logging."""

    def test_log_creates_entry(self, temp_dir):
        """Test that logging creates an audit entry."""
        config = AirGapConfig(
            allowed_roots=[str(temp_dir)],
            audit_log_path=str(temp_dir / "audit.jsonl")
        )
        logger = AuditLogger(config)

        entry = logger.log("test_op", path="/test/path", success=True)

        assert entry.operation == "test_op"
        assert entry.success is True

    def test_log_writes_to_file(self, temp_dir):
        """Test that logs are written to file."""
        audit_path = temp_dir / "audit.jsonl"
        config = AirGapConfig(
            allowed_roots=[str(temp_dir)],
            audit_log_path=str(audit_path),
            redact_paths_in_audit=False
        )
        logger = AuditLogger(config)

        logger.log("test_op", path="/test/path")

        assert audit_path.exists()
        with open(audit_path) as f:
            lines = f.readlines()
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["operation"] == "test_op"
        assert entry["path"] == "/test/path"

    def test_path_redaction(self, temp_dir):
        """Test that paths are redacted when configured."""
        audit_path = temp_dir / "audit.jsonl"
        config = AirGapConfig(
            allowed_roots=[str(temp_dir)],
            audit_log_path=str(audit_path),
            redact_paths_in_audit=True
        )
        logger = AuditLogger(config)

        logger.log("test_op", path="/secret/path/to/file.txt")

        with open(audit_path) as f:
            entry = json.loads(f.readline())

        # Path should be redacted (hashed)
        assert entry.get("path") is None
        assert entry.get("path_hash") is not None
        assert len(entry["path_hash"]) == 16  # SHA256 truncated

    def test_log_read_records_bytes(self, temp_dir):
        """Test that log_read records actual bytes."""
        audit_path = temp_dir / "audit.jsonl"
        config = AirGapConfig(
            allowed_roots=[str(temp_dir)],
            audit_log_path=str(audit_path),
            redact_paths_in_audit=False
        )
        logger = AuditLogger(config)

        logger.log_read(
            path="/test/file.txt",
            bytes_read=1234,
            offset=100,
            limit=2000
        )

        with open(audit_path) as f:
            entry = json.loads(f.readline())

        assert entry["metadata"]["bytes_read"] == 1234
        assert entry["metadata"]["offset"] == 100
        assert entry["metadata"]["limit"] == 2000


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def test_to_json(self):
        """Test JSON serialization."""
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00Z",
            operation="test",
            success=True
        )

        json_str = entry.to_json()
        data = json.loads(json_str)

        assert data["operation"] == "test"
        assert data["success"] is True
