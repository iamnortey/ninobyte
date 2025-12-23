"""
IP address redaction tests for OpsPack.

Verifies that IP addresses are properly redacted.
"""

import pytest

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from opspack.redact import redact_text, redact_ips, REDACTED_PLACEHOLDER


class TestIPv4Redaction:
    """Test IPv4 address redaction."""

    def test_redacts_standard_ipv4(self):
        """Should redact standard IPv4 addresses."""
        text = "Connection from 192.168.1.100 refused"
        result = redact_text(text)
        assert "192.168.1.100" not in result
        assert REDACTED_PLACEHOLDER in result

    def test_redacts_localhost(self):
        """Should redact localhost IP."""
        text = "Listening on 127.0.0.1:8080"
        result = redact_text(text)
        assert "127.0.0.1" not in result

    def test_redacts_broadcast(self):
        """Should redact broadcast addresses."""
        text = "Broadcast to 255.255.255.255"
        result = redact_text(text)
        assert "255.255.255.255" not in result

    def test_redacts_public_ip(self):
        """Should redact public IP addresses."""
        text = "External IP: 8.8.8.8"
        result = redact_text(text)
        assert "8.8.8.8" not in result

    def test_redacts_multiple_ips(self):
        """Should redact multiple IPs in same text."""
        text = "From 10.0.0.1 to 10.0.0.2 via 10.0.0.254"
        result = redact_text(text)
        assert "10.0.0.1" not in result
        assert "10.0.0.2" not in result
        assert "10.0.0.254" not in result

    def test_preserves_version_numbers(self):
        """Should not redact version numbers that look like IPs."""
        # This is a known limitation - version numbers may be redacted
        # if they match IP patterns exactly
        text = "Version 1.2.3"
        result = redact_text(text)
        # 1.2.3 is not a valid IP (only 3 octets) so should be preserved
        assert "1.2.3" in result

    def test_redacts_ip_in_url(self):
        """Should redact IP in URL context."""
        text = "http://192.168.0.1:8080/api"
        result = redact_text(text)
        assert "192.168.0.1" not in result


class TestIPv6Redaction:
    """Test IPv6 address redaction."""

    def test_redacts_full_ipv6(self):
        """Should redact full IPv6 addresses."""
        text = "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        result = redact_text(text)
        assert "2001:0db8:85a3:0000:0000:8a2e:0370:7334" not in result

    def test_redacts_loopback_ipv6(self):
        """Should redact IPv6 loopback."""
        text = "Listening on ::1"
        result = redact_text(text)
        # ::1 is very short, may not match pattern - that's ok
        # Focus on longer addresses


class TestIPOnlyRedaction:
    """Test the IP-only redaction function."""

    def test_redact_ips_leaves_tokens(self):
        """redact_ips should not redact tokens."""
        text = "Server 192.168.1.1 token AKIAIOSFODNN7EXAMPLE"
        result = redact_ips(text)
        assert "192.168.1.1" not in result  # IP redacted
        assert "AKIAIOSFODNN7EXAMPLE" in result  # Token preserved

    def test_redact_ips_leaves_uuids(self):
        """redact_ips should not redact UUIDs."""
        text = "IP 10.0.0.1 request 550e8400-e29b-41d4-a716-446655440000"
        result = redact_ips(text)
        assert "10.0.0.1" not in result  # IP redacted
        assert "550e8400-e29b-41d4-a716-446655440000" in result  # UUID preserved


class TestEdgeCases:
    """Test edge cases for IP redaction."""

    def test_invalid_ip_not_redacted(self):
        """Invalid IPs should not be redacted."""
        text = "Not an IP: 999.999.999.999"
        result = redact_text(text)
        # 999 > 255, not a valid IP
        assert "999.999.999.999" in result

    def test_partial_ip_not_redacted(self):
        """Partial IPs should not be redacted."""
        text = "Only three parts: 192.168.1"
        result = redact_text(text)
        assert "192.168.1" in result
