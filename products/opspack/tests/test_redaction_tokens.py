"""
Token redaction tests for OpsPack.

Verifies that token-like patterns are properly redacted.
"""

import pytest

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from opspack.redact import redact_text, redact_tokens, REDACTED_PLACEHOLDER


class TestAWSKeys:
    """Test AWS key redaction."""

    def test_redacts_aws_access_key_id(self):
        """Should redact AWS access key IDs (AKIA...)."""
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        result = redact_text(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert REDACTED_PLACEHOLDER in result

    def test_preserves_non_aws_key(self):
        """Should not redact strings that look similar but aren't keys."""
        text = "The word AKIA is not a key by itself"
        result = redact_text(text)
        # Short AKIA without 16 following chars should remain
        assert "AKIA" in result


class TestSlackTokens:
    """Test Slack token redaction."""

    def test_redacts_xoxb_token(self):
        """Should redact xoxb- bot tokens."""
        text = "SLACK_TOKEN=xoxb-1234567890-abcdefghij"
        result = redact_text(text)
        assert "xoxb-" not in result
        assert REDACTED_PLACEHOLDER in result

    def test_redacts_xoxp_token(self):
        """Should redact xoxp- user tokens."""
        text = "token: xoxp-9876543210-zyxwvutsrq"
        result = redact_text(text)
        assert "xoxp-" not in result


class TestBearerTokens:
    """Test Bearer token redaction."""

    def test_redacts_bearer_token(self):
        """Should redact Bearer tokens in Authorization headers."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_text(text)
        assert "Bearer" not in result or "eyJ" not in result

    def test_case_insensitive_bearer(self):
        """Should handle case variations of Bearer."""
        text = "bearer abc123xyz"
        result = redact_text(text)
        assert "abc123xyz" not in result


class TestHexStrings:
    """Test long hex string redaction."""

    def test_redacts_32_char_hex(self):
        """Should redact 32-character hex strings (MD5-like)."""
        text = "hash: d41d8cd98f00b204e9800998ecf8427e"
        result = redact_text(text)
        assert "d41d8cd98f00b204e9800998ecf8427e" not in result

    def test_redacts_64_char_hex(self):
        """Should redact 64-character hex strings (SHA256-like)."""
        hex_str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        text = f"sha256: {hex_str}"
        result = redact_text(text)
        assert hex_str not in result


class TestGitHubTokens:
    """Test GitHub token redaction."""

    def test_redacts_ghp_token(self):
        """Should redact GitHub personal access tokens."""
        token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        text = f"GITHUB_TOKEN={token}"
        result = redact_text(text)
        assert "ghp_" not in result


class TestJWTTokens:
    """Test JWT redaction."""

    def test_redacts_jwt(self):
        """Should redact JWT tokens."""
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N"
        text = f"token={jwt}"
        result = redact_text(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result


class TestTokenOnlyRedaction:
    """Test the token-only redaction function."""

    def test_redact_tokens_leaves_ips(self):
        """redact_tokens should not redact IPs."""
        text = "Server at 192.168.1.1 with token AKIAIOSFODNN7EXAMPLE"
        result = redact_tokens(text)
        assert "192.168.1.1" in result  # IP preserved
        assert "AKIAIOSFODNN7EXAMPLE" not in result  # Token redacted
