"""
Tests for path_security module.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import AirGapConfig
from path_security import PathSecurityContext, PathDenialReason


class TestPathValidation:
    """Tests for path validation."""

    def test_allowed_path(self, sample_tree, config_with_temp_dir):
        """Test that paths within allowed roots are accepted."""
        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(sample_tree / "file1.txt"))

        assert result.allowed is True
        assert result.canonical_path is not None
        assert "file1.txt" in result.canonical_path

    def test_path_outside_roots_denied(self, config_with_temp_dir):
        """Test that paths outside allowed roots are denied."""
        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path("/etc/passwd")

        assert result.allowed is False
        assert result.denial_reason == PathDenialReason.OUTSIDE_ALLOWED_ROOTS

    def test_traversal_attack_denied(self, sample_tree, config_with_temp_dir):
        """Test that traversal attempts are blocked."""
        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(sample_tree / ".." / ".." / "etc" / "passwd"))

        assert result.allowed is False
        # Could be TRAVERSAL_DETECTED or OUTSIDE_ALLOWED_ROOTS depending on resolution
        assert result.denial_reason in (
            PathDenialReason.TRAVERSAL_DETECTED,
            PathDenialReason.OUTSIDE_ALLOWED_ROOTS
        )

    def test_blocked_pattern_env_file(self, sample_tree, config_with_temp_dir):
        """Test that .env files are blocked."""
        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(sample_tree / ".env"))

        assert result.allowed is False
        assert result.denial_reason == PathDenialReason.BLOCKED_PATTERN

    def test_blocked_pattern_private_key(self, sample_tree, config_with_temp_dir):
        """Test that private key files are blocked."""
        # Create a .pem file
        pem_file = sample_tree / "server.pem"
        pem_file.write_text("fake key")

        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(pem_file))

        assert result.allowed is False
        assert result.denial_reason == PathDenialReason.BLOCKED_PATTERN

    def test_blocked_pattern_windows_git_config(self, config_with_temp_dir):
        """Test that Windows-style .git/config paths are blocked."""
        ctx = PathSecurityContext(config_with_temp_dir)
        # Directly test the pattern matching with Windows-style backslashes
        windows_path = r"C:\repo\.git\config"
        matched = ctx._matches_blocked_pattern(windows_path)

        assert matched is not None
        assert matched == ".git/config"

    def test_blocked_pattern_windows_aws_credentials(self, config_with_temp_dir):
        """Test that Windows-style .aws/credentials paths are blocked."""
        ctx = PathSecurityContext(config_with_temp_dir)
        # Directly test the pattern matching with Windows-style backslashes
        windows_path = r"C:\repo\.aws\credentials"
        matched = ctx._matches_blocked_pattern(windows_path)

        assert matched is not None
        assert matched == ".aws/credentials"

    def test_no_allowed_roots_denies_all(self):
        """Test that empty allowed_roots denies everything."""
        config = AirGapConfig(allowed_roots=[])
        ctx = PathSecurityContext(config)

        result = ctx.validate_path("/any/path")
        assert result.allowed is False
        assert result.denial_reason == PathDenialReason.OUTSIDE_ALLOWED_ROOTS

    def test_validate_path_no_follow(self, sample_tree, config_with_temp_dir):
        """Test validation without following symlinks.

        Note: On macOS, /var symlinks to /private/var, so we need to use
        the canonicalized path for testing.
        """
        import os
        canonical_sample = os.path.realpath(str(sample_tree))
        config = AirGapConfig(
            allowed_roots=[canonical_sample],
            max_file_size_bytes=config_with_temp_dir.max_file_size_bytes
        )
        ctx = PathSecurityContext(config)
        result = ctx.validate_path_no_follow(os.path.join(canonical_sample, "file1.txt"))

        assert result.allowed is True


class TestSymlinkSecurity:
    """Tests for symlink escape prevention."""

    def test_symlink_within_root_allowed(self, sample_tree, config_with_temp_dir):
        """Test that symlinks within allowed roots work."""
        link_path = sample_tree / "link_internal"
        if not link_path.exists():
            pytest.skip("Symlinks not supported on this platform")

        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(link_path))

        assert result.allowed is True

    def test_symlink_escape_denied(self, sample_tree, config_with_temp_dir):
        """Test that symlinks escaping allowed roots are denied."""
        try:
            escape_link = sample_tree / "escape_link"
            escape_link.symlink_to("/etc/passwd")
        except (OSError, PermissionError):
            pytest.skip("Cannot create symlink to /etc/passwd")

        ctx = PathSecurityContext(config_with_temp_dir)
        result = ctx.validate_path(str(escape_link))

        assert result.allowed is False
        assert result.denial_reason in (
            PathDenialReason.SYMLINK_ESCAPE,
            PathDenialReason.OUTSIDE_ALLOWED_ROOTS
        )
