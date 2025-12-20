"""
Tests for read_file module.

Key security tests:
- Audit logs ACTUAL bytes read (not file size)
- offset + limit are respected and recorded
- Blocked patterns enforced
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import AirGapConfig
from audit import AuditLogger
from read_file import read_file


class TestReadFileBasic:
    """Basic functionality tests."""

    def test_read_file_success(self, sample_tree, config_with_temp_dir):
        """Test successful file read."""
        result = read_file(str(sample_tree / "file1.txt"), config_with_temp_dir)

        assert result.success is True
        assert result.content is not None
        assert "Hello World" in result.content

    def test_read_file_blocked_pattern(self, sample_tree, config_with_temp_dir):
        """Test that blocked files cannot be read."""
        result = read_file(str(sample_tree / ".env"), config_with_temp_dir)

        assert result.success is False
        assert result.content is None
        assert "denied" in result.error.lower()

    def test_read_file_outside_roots(self, config_with_temp_dir):
        """Test that files outside roots cannot be read."""
        result = read_file("/etc/passwd", config_with_temp_dir)

        assert result.success is False
        assert "denied" in result.error.lower()


class TestReadFileAuditBytesRead:
    """Tests for accurate bytes_read auditing."""

    def test_audit_logs_actual_bytes_read(self, sample_tree, temp_dir):
        """Test that audit logs ACTUAL bytes read, not file size."""
        # Create a file with known content
        test_file = sample_tree / "known_size.txt"
        test_content = "A" * 1000  # 1000 bytes
        test_file.write_text(test_content)

        audit_log = temp_dir / "audit.jsonl"
        config = AirGapConfig(
            allowed_roots=[str(sample_tree)],
            audit_log_path=str(audit_log),
            redact_paths_in_audit=False
        )

        # Read only first 100 bytes
        result = read_file(str(test_file), config, offset=0, limit=100)

        assert result.success is True
        assert result.bytes_read == 100  # ACTUAL bytes read

        # Check audit log
        with open(audit_log) as f:
            log_entries = [json.loads(line) for line in f]

        assert len(log_entries) == 1
        entry = log_entries[0]
        assert entry["metadata"]["bytes_read"] == 100  # ACTUAL, not 1000

    def test_audit_logs_offset_and_limit(self, sample_tree, temp_dir):
        """Test that offset and limit are recorded in audit."""
        test_file = sample_tree / "offset_test.txt"
        test_file.write_text("0123456789" * 100)

        audit_log = temp_dir / "audit.jsonl"
        config = AirGapConfig(
            allowed_roots=[str(sample_tree)],
            audit_log_path=str(audit_log),
            redact_paths_in_audit=False
        )

        result = read_file(str(test_file), config, offset=50, limit=200)

        assert result.success is True
        assert result.offset == 50
        assert result.limit == 200

        # Check audit log
        with open(audit_log) as f:
            log_entries = [json.loads(line) for line in f]

        entry = log_entries[0]
        assert entry["metadata"]["offset"] == 50
        assert entry["metadata"]["limit"] == 200

    def test_bytes_read_matches_actual_content(self, sample_tree, config_with_temp_dir):
        """Test that bytes_read matches actual content length."""
        test_file = sample_tree / "file1.txt"
        result = read_file(str(test_file), config_with_temp_dir)

        assert result.success is True
        assert result.bytes_read == len(result.content.encode('utf-8'))


class TestReadFileOffsetLimit:
    """Tests for offset and limit handling."""

    def test_offset_skips_bytes(self, sample_tree, config_with_temp_dir):
        """Test that offset correctly skips bytes."""
        test_file = sample_tree / "offset_file.txt"
        test_file.write_text("AAABBBCCC")

        result = read_file(str(test_file), config_with_temp_dir, offset=3)

        assert result.success is True
        assert result.content == "BBBCCC"

    def test_limit_caps_bytes(self, sample_tree, config_with_temp_dir):
        """Test that limit correctly caps bytes read."""
        test_file = sample_tree / "limit_file.txt"
        test_file.write_text("ABCDEFGHIJ")

        result = read_file(str(test_file), config_with_temp_dir, limit=5)

        assert result.success is True
        assert result.content == "ABCDE"
        assert result.bytes_read == 5

    def test_offset_beyond_file_returns_empty(self, sample_tree, config_with_temp_dir):
        """Test that offset beyond file size returns empty content."""
        test_file = sample_tree / "small.txt"
        test_file.write_text("ABC")

        result = read_file(str(test_file), config_with_temp_dir, offset=100)

        assert result.success is True
        assert result.content == ""
        assert result.bytes_read == 0

    def test_limit_greater_than_max_is_clamped(self, sample_tree):
        """Test that limit is clamped to max_file_size_bytes."""
        test_file = sample_tree / "clamp_test.txt"
        test_file.write_text("A" * 100)

        config = AirGapConfig(
            allowed_roots=[str(sample_tree)],
            max_file_size_bytes=50  # Small limit
        )

        result = read_file(str(test_file), config, limit=1000)

        assert result.success is True
        assert result.bytes_read <= 50
        assert result.limit == 50  # Clamped
