"""
HAProxy HTTP log parser.

Parses lines like:
  Dec 23 14:30:45 lb1 haproxy[1234]: 192.168.1.1:54321 [23/Dec/2025:14:30:45.123] frontend backend/server 0/0/0/1/1 200 1234 - - ---- 1/1/0/0/0 0/0 "GET /api/health HTTP/1.1"

Simplified HAProxy format (common variation):
  192.168.1.1:54321 [23/Dec/2025:14:30:45.123] frontend backend/server 10/20/30/40/50 200 1234 - - ---- 1/1/0/0/0 0/0 "GET /path HTTP/1.1"

Output normalized event dicts with:
  - ts: timestamp string
  - source: client IP
  - severity: inferred from status code or termination state
  - message: formatted summary
  - raw: original line
  - frontend: frontend name
  - backend: backend name
  - server: server name
  - status: HTTP status code
  - bytes: response bytes
  - termination_state: connection termination flags
"""

import re
from dataclasses import dataclass
from typing import Any


# HAProxy HTTP log pattern (with syslog prefix)
# <syslog prefix> <client_ip:port> [<timestamp>] <frontend> <backend>/<server> <timings> <status> <bytes> ...
HAPROXY_SYSLOG_PATTERN = re.compile(
    r'^(?P<syslog_ts>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>\S+)\s+'
    r'haproxy\[\d+\]:\s+'
    r'(?P<client_ip>[^:]+):(?P<client_port>\d+)\s+'
    r'\[(?P<accept_date>[^\]]+)\]\s+'
    r'(?P<frontend>\S+)\s+'
    r'(?P<backend>[^/]+)/(?P<server>\S+)\s+'
    r'(?P<timings>[\d/\-]+)\s+'
    r'(?P<status>\d+)\s+'
    r'(?P<bytes>\d+)\s+'
    r'(?P<captured_request_cookie>\S+)\s+'
    r'(?P<captured_response_cookie>\S+)\s+'
    r'(?P<termination_state>\S+)\s+'
    r'(?P<actconn>[\d/]+)\s+'
    r'(?P<feconn>[\d/]+)\s*'
    r'(?:"(?P<request>[^"]*)")?',
    re.IGNORECASE,
)

# Simplified HAProxy pattern (without syslog prefix)
HAPROXY_SIMPLE_PATTERN = re.compile(
    r'^(?P<client_ip>[^:]+):(?P<client_port>\d+)\s+'
    r'\[(?P<accept_date>[^\]]+)\]\s+'
    r'(?P<frontend>\S+)\s+'
    r'(?P<backend>[^/]+)/(?P<server>\S+)\s+'
    r'(?P<timings>[\d/\-]+)\s+'
    r'(?P<status>\d+)\s+'
    r'(?P<bytes>\d+)\s+'
    r'(?P<captured_request_cookie>\S+)\s+'
    r'(?P<captured_response_cookie>\S+)\s+'
    r'(?P<termination_state>\S+)\s+'
    r'(?P<actconn>[\d/]+)\s+'
    r'(?P<feconn>[\d/]+)\s*'
    r'(?:"(?P<request>[^"]*)")?',
)


@dataclass
class HaproxyEntry:
    """A parsed HAProxy log entry."""

    client_ip: str
    client_port: int
    accept_date: str
    frontend: str
    backend: str
    server: str
    timings: str
    status: int
    bytes_read: int
    termination_state: str
    request: str | None
    raw: str


class HaproxyParser:
    """
    Parser for HAProxy HTTP log format.

    Produces normalized event dictionaries for diagnostic analysis.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse_line(self, line: str) -> HaproxyEntry | None:
        """
        Parse a single HAProxy log line.

        Args:
            line: Raw log line

        Returns:
            Parsed entry or None if unparseable
        """
        line = line.strip()
        if not line:
            return None

        # Try syslog format first
        match = HAPROXY_SYSLOG_PATTERN.match(line)
        if not match:
            # Try simple format
            match = HAPROXY_SIMPLE_PATTERN.match(line)
            if not match:
                return None

        request = match.group("request")

        return HaproxyEntry(
            client_ip=match.group("client_ip"),
            client_port=int(match.group("client_port")),
            accept_date=match.group("accept_date"),
            frontend=match.group("frontend"),
            backend=match.group("backend"),
            server=match.group("server"),
            timings=match.group("timings"),
            status=int(match.group("status")),
            bytes_read=int(match.group("bytes")),
            termination_state=match.group("termination_state"),
            request=request,
            raw=line,
        )

    def parse_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        """
        Parse multiple HAProxy log lines into normalized event dicts.

        Args:
            lines: List of raw log lines

        Returns:
            List of normalized event dictionaries
        """
        events = []
        for line in lines:
            entry = self.parse_line(line)
            if entry is not None:
                events.append(self._to_event_dict(entry))
        return events

    def _to_event_dict(self, entry: HaproxyEntry) -> dict[str, Any]:
        """Convert a HaproxyEntry to a normalized event dict."""
        # Parse request for method/path
        method, path = self._parse_request(entry.request)

        # Build message summary
        message = f"{entry.frontend}->{entry.backend}/{entry.server} {entry.status}"
        if method and path:
            message = f"{method} {path} -> {message}"

        return {
            "backend": entry.backend,
            "bytes": entry.bytes_read,
            "frontend": entry.frontend,
            "message": message,
            "method": method,
            "path": path,
            "raw": entry.raw,
            "server": entry.server,
            "severity": self._infer_severity(entry.status, entry.termination_state),
            "source": entry.client_ip,
            "status": entry.status,
            "termination_state": entry.termination_state,
            "timings": entry.timings,
            "ts": entry.accept_date,
        }

    def _parse_request(self, request: str | None) -> tuple[str | None, str | None]:
        """Parse the request line into method and path."""
        if not request:
            return None, None
        parts = request.split()
        if len(parts) >= 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return None, parts[0]
        return None, None

    def _infer_severity(self, status: int, termination_state: str) -> str:
        """Infer severity from status code and termination state."""
        # Check termination state for connection issues
        if termination_state and termination_state != "----":
            # Any non-normal termination is at least a warning
            if "C" in termination_state or "c" in termination_state:
                # Client aborted
                return "warning"
            if "S" in termination_state or "s" in termination_state:
                # Server error
                return "error"

        # Fall back to status code
        if status >= 500:
            return "error"
        elif status >= 400:
            return "warning"
        else:
            return "info"
