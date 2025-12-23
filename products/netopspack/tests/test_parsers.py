"""
Unit tests for NetOpsPack log parsers.

Tests parsing correctness for syslog, nginx, and haproxy formats.
"""

from pathlib import Path

import pytest

from netopspack.parsers.syslog import SyslogParser
from netopspack.parsers.nginx import NginxParser
from netopspack.parsers.haproxy import HaproxyParser


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


class TestSyslogParser:
    """Tests for syslog parser."""

    def test_parse_basic_line_with_pid(self):
        """Parses standard syslog line with PID."""
        parser = SyslogParser()
        line = "Dec 23 14:30:45 myhost sshd[12345]: Accepted publickey for user"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.timestamp == "Dec 23 14:30:45"
        assert entry.hostname == "myhost"
        assert entry.program == "sshd"
        assert entry.pid == "12345"
        assert entry.message == "Accepted publickey for user"

    def test_parse_line_without_pid(self):
        """Parses syslog line without PID."""
        parser = SyslogParser()
        line = "Jan  5 09:15:00 server kernel: TCP connection refused"
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.timestamp == "Jan 5 09:15:00"
        assert entry.hostname == "server"
        assert entry.program == "kernel"
        assert entry.pid is None
        assert "TCP connection refused" in entry.message

    def test_parse_empty_line(self):
        """Empty line returns None."""
        parser = SyslogParser()
        assert parser.parse_line("") is None
        assert parser.parse_line("   ") is None

    def test_parse_malformed_line(self):
        """Malformed line returns None."""
        parser = SyslogParser()
        assert parser.parse_line("not a syslog line") is None
        assert parser.parse_line("Dec 23") is None

    def test_parse_lines_returns_event_dicts(self):
        """parse_lines returns normalized event dicts."""
        parser = SyslogParser()
        lines = [
            "Dec 23 14:30:45 myhost sshd[12345]: Accepted publickey",
            "Dec 23 14:30:46 myhost kernel: Error connecting",
        ]
        events = parser.parse_lines(lines)

        assert len(events) == 2
        assert events[0]["source"] == "myhost"
        assert events[0]["program"] == "sshd"
        assert events[0]["severity"] == "info"  # "Accepted" keyword
        assert events[1]["severity"] == "error"  # "Error" keyword

    def test_severity_inference(self):
        """Severity is inferred from message keywords."""
        parser = SyslogParser()

        # Critical
        entry = parser.parse_line("Dec 23 14:30:45 host app[1]: critical failure")
        events = parser.parse_lines(["Dec 23 14:30:45 host app[1]: critical failure"])
        assert events[0]["severity"] == "critical"

        # Error
        events = parser.parse_lines(["Dec 23 14:30:45 host app[1]: connection failed"])
        assert events[0]["severity"] == "error"

        # Warning
        events = parser.parse_lines(["Dec 23 14:30:45 host app[1]: connection timeout"])
        assert events[0]["severity"] == "warning"

        # Info
        events = parser.parse_lines(["Dec 23 14:30:45 host app[1]: connected successfully"])
        assert events[0]["severity"] == "info"

    def test_parse_file_fixture(self, fixtures_dir: Path):
        """Parses sample syslog fixture file."""
        parser = SyslogParser()
        lines = (fixtures_dir / "sample_syslog.log").read_text().splitlines()
        events = parser.parse_lines(lines)

        assert len(events) == 10
        # Check specific events
        assert events[0]["program"] == "sshd"
        assert events[2]["severity"] == "error"  # "refused" keyword


class TestNginxParser:
    """Tests for nginx parser."""

    def test_parse_combined_format(self):
        """Parses nginx combined log format."""
        parser = NginxParser()
        line = '192.168.1.1 - - [23/Dec/2025:14:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.remote_addr == "192.168.1.1"
        assert entry.method == "GET"
        assert entry.path == "/api/users"
        assert entry.status == 200
        assert entry.body_bytes_sent == 1234
        assert entry.http_user_agent == "Mozilla/5.0"

    def test_parse_with_user_and_referer(self):
        """Parses line with authenticated user and referer."""
        parser = NginxParser()
        line = '10.0.0.50 - admin [23/Dec/2025:14:30:46 +0000] "POST /api/login HTTP/1.1" 401 56 "https://example.com" "curl/7.68"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.remote_user == "admin"
        assert entry.method == "POST"
        assert entry.status == 401
        assert entry.http_referer == "https://example.com"

    def test_parse_dash_values(self):
        """Parses line with dash placeholders."""
        parser = NginxParser()
        line = '192.168.1.1 - - [23/Dec/2025:14:30:45 +0000] "GET / HTTP/1.1" 200 0 "-" "-"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.remote_user is None
        assert entry.http_referer is None
        assert entry.http_user_agent is None

    def test_parse_empty_line(self):
        """Empty line returns None."""
        parser = NginxParser()
        assert parser.parse_line("") is None

    def test_parse_malformed_line(self):
        """Malformed line returns None."""
        parser = NginxParser()
        assert parser.parse_line("not an nginx line") is None

    def test_parse_lines_returns_event_dicts(self):
        """parse_lines returns normalized event dicts."""
        parser = NginxParser()
        lines = [
            '192.168.1.1 - - [23/Dec/2025:14:30:45 +0000] "GET /api HTTP/1.1" 200 100 "-" "test"',
            '10.0.0.1 - - [23/Dec/2025:14:30:46 +0000] "POST /api HTTP/1.1" 500 50 "-" "test"',
        ]
        events = parser.parse_lines(lines)

        assert len(events) == 2
        assert events[0]["status"] == 200
        assert events[0]["severity"] == "info"
        assert events[1]["status"] == 500
        assert events[1]["severity"] == "error"

    def test_status_to_severity(self):
        """Status codes map to correct severity."""
        parser = NginxParser()

        lines = [
            '1.1.1.1 - - [01/Jan/2025:00:00:00 +0000] "GET / HTTP/1.1" 200 0 "-" "-"',
            '1.1.1.1 - - [01/Jan/2025:00:00:00 +0000] "GET / HTTP/1.1" 301 0 "-" "-"',
            '1.1.1.1 - - [01/Jan/2025:00:00:00 +0000] "GET / HTTP/1.1" 404 0 "-" "-"',
            '1.1.1.1 - - [01/Jan/2025:00:00:00 +0000] "GET / HTTP/1.1" 503 0 "-" "-"',
        ]
        events = parser.parse_lines(lines)

        assert events[0]["severity"] == "info"    # 200
        assert events[1]["severity"] == "info"    # 301
        assert events[2]["severity"] == "warning" # 404
        assert events[3]["severity"] == "error"   # 503

    def test_parse_file_fixture(self, fixtures_dir: Path):
        """Parses sample nginx fixture file."""
        parser = NginxParser()
        lines = (fixtures_dir / "sample_nginx.log").read_text().splitlines()
        events = parser.parse_lines(lines)

        assert len(events) == 10
        # Check status distribution
        statuses = [e["status"] for e in events]
        assert 200 in statuses
        assert 500 in statuses
        assert 404 in statuses


class TestHaproxyParser:
    """Tests for haproxy parser."""

    def test_parse_syslog_format(self):
        """Parses haproxy log with syslog prefix."""
        parser = HaproxyParser()
        line = 'Dec 23 14:30:45 lb1 haproxy[1234]: 192.168.1.1:54321 [23/Dec/2025:14:30:45.123] http-in api-backend/web1 0/0/0/1/1 200 1234 - - ---- 1/1/0/0/0 0/0 "GET /api/health HTTP/1.1"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.client_ip == "192.168.1.1"
        assert entry.frontend == "http-in"
        assert entry.backend == "api-backend"
        assert entry.server == "web1"
        assert entry.status == 200
        assert entry.bytes_read == 1234

    def test_parse_with_request(self):
        """Parses request method and path."""
        parser = HaproxyParser()
        line = 'Dec 23 14:30:45 lb1 haproxy[1234]: 10.0.0.1:12345 [23/Dec/2025:14:30:45.000] fe be/srv 0/0/0/1/1 201 100 - - ---- 1/1/0/0/0 0/0 "POST /api/data HTTP/1.1"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.request == "POST /api/data HTTP/1.1"

    def test_parse_empty_line(self):
        """Empty line returns None."""
        parser = HaproxyParser()
        assert parser.parse_line("") is None

    def test_parse_malformed_line(self):
        """Malformed line returns None."""
        parser = HaproxyParser()
        assert parser.parse_line("not a haproxy line") is None

    def test_parse_lines_returns_event_dicts(self):
        """parse_lines returns normalized event dicts."""
        parser = HaproxyParser()
        lines = [
            'Dec 23 14:30:45 lb haproxy[1]: 1.1.1.1:1 [23/Dec/2025:14:30:45.000] fe be/srv 0/0/0/1/1 200 100 - - ---- 1/1/0/0/0 0/0 "GET / HTTP/1.1"',
            'Dec 23 14:30:46 lb haproxy[1]: 1.1.1.2:2 [23/Dec/2025:14:30:46.000] fe be/srv 0/0/0/1/1 503 50 - - sH-- 1/1/0/0/0 0/0 "GET /slow HTTP/1.1"',
        ]
        events = parser.parse_lines(lines)

        assert len(events) == 2
        assert events[0]["status"] == 200
        assert events[0]["severity"] == "info"
        assert events[1]["status"] == 503
        assert events[1]["severity"] == "error"

    def test_termination_state_severity(self):
        """Termination state affects severity."""
        parser = HaproxyParser()

        # Client abort
        line = 'Dec 23 14:30:45 lb haproxy[1]: 1.1.1.1:1 [23/Dec/2025:14:30:45.000] fe be/srv 0/0/0/1/1 200 100 - - CD-- 1/1/0/0/0 0/0 "GET / HTTP/1.1"'
        events = parser.parse_lines([line])
        assert events[0]["severity"] == "warning"

        # Server error
        line = 'Dec 23 14:30:45 lb haproxy[1]: 1.1.1.1:1 [23/Dec/2025:14:30:45.000] fe be/srv 0/0/0/1/1 200 100 - - sH-- 1/1/0/0/0 0/0 "GET / HTTP/1.1"'
        events = parser.parse_lines([line])
        assert events[0]["severity"] == "error"

    def test_parse_file_fixture(self, fixtures_dir: Path):
        """Parses sample haproxy fixture file."""
        parser = HaproxyParser()
        lines = (fixtures_dir / "sample_haproxy.log").read_text().splitlines()
        events = parser.parse_lines(lines)

        assert len(events) == 8
        # Check specific events
        assert events[0]["frontend"] == "http-in"
        assert events[1]["status"] == 500
