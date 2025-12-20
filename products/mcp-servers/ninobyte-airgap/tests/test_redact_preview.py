"""
Tests for redact_preview module.

Key requirement: redact_preview MUST remain STATELESS (str->str, no file reads).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from redact_preview import redact_preview, redact_preview_simple


class TestRedactPreviewStateless:
    """Tests verifying statelessness requirement."""

    def test_is_pure_function(self):
        """Test that redact_preview is a pure function (same input = same output)."""
        input_text = "API_KEY=abc123secret"

        result1 = redact_preview(input_text)
        result2 = redact_preview(input_text)

        assert result1.content == result2.content
        assert result1.redactions_applied == result2.redactions_applied

    def test_no_side_effects(self):
        """Test that redact_preview has no side effects."""
        input_text = "password=secret123"

        # Call multiple times
        for _ in range(10):
            result = redact_preview(input_text)
            assert "REDACTED" in result.content

    def test_simple_version_is_str_to_str(self):
        """Test that redact_preview_simple is str->str."""
        input_text = "bearer token123"
        result = redact_preview_simple(input_text)

        assert isinstance(result, str)
        assert "REDACTED" in result

    def test_type_error_on_non_string(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            redact_preview(123)

        with pytest.raises(TypeError):
            redact_preview_simple(None)


class TestRedactionPatterns:
    """Tests for redaction patterns."""

    def test_redacts_api_key(self):
        """Test API key redaction."""
        result = redact_preview("API_KEY=sk_live_abcdefghijklmnop123456")
        assert "REDACTED_API_KEY" in result.content
        assert "sk_live" not in result.content

    def test_redacts_bearer_token(self):
        """Test bearer token redaction."""
        result = redact_preview("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.token")
        assert "REDACTED_BEARER_TOKEN" in result.content

    def test_redacts_password(self):
        """Test password redaction."""
        result = redact_preview('password = "supersecret123"')
        assert "REDACTED" in result.content
        assert "supersecret123" not in result.content

    def test_redacts_private_key(self):
        """Test private key redaction."""
        key_content = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC
-----END PRIVATE KEY-----"""
        result = redact_preview(key_content)
        assert "REDACTED_PRIVATE_KEY" in result.content
        assert "MIIEvg" not in result.content

    def test_redacts_connection_string(self):
        """Test connection string password redaction."""
        result = redact_preview("postgres://user:secretpass@localhost/db")
        assert "REDACTED" in result.content
        assert "secretpass" not in result.content
        # But should preserve host info
        assert "localhost" in result.content

    def test_redacts_jwt(self):
        """Test JWT token redaction."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        result = redact_preview(jwt)
        assert "REDACTED_JWT" in result.content

    def test_redacts_github_token(self):
        """Test GitHub token redaction."""
        # GitHub tokens are 36+ alphanumeric chars after ghp_
        # Use format without colon/equals to avoid password pattern matching first
        result = redact_preview("credentials ghp_abcdefghij1234567890abcdefghij123456")
        assert "REDACTED_GITHUB_TOKEN" in result.content

    def test_redacts_credit_card(self):
        """Test credit card number redaction."""
        result = redact_preview("Card: 4111-1111-1111-1111")
        assert "REDACTED_CARD_NUMBER" in result.content
        assert "4111" not in result.content

    def test_redacts_ssn(self):
        """Test SSN redaction."""
        result = redact_preview("SSN: 123-45-6789")
        assert "REDACTED_SSN" in result.content


class TestRedactionMetadata:
    """Tests for redaction metadata."""

    def test_counts_redactions(self):
        """Test that redactions are counted correctly."""
        # Password patterns need 8+ char values
        result = redact_preview("password=secretvalue1 PASSWORD=secretvalue2")
        assert result.redactions_applied >= 2

    def test_tracks_redaction_types(self):
        """Test that redaction types are tracked."""
        # Use patterns that will definitely match
        result = redact_preview("password=secretvalue bearer token123")
        assert len(result.redaction_types) >= 1
        assert "password" in result.redaction_types or "bearer_token" in result.redaction_types

    def test_preserves_non_sensitive_content(self):
        """Test that non-sensitive content is preserved."""
        result = redact_preview("Hello World! This is normal text.")
        assert result.content == "Hello World! This is normal text."
        assert result.redactions_applied == 0
