"""
Nginx access log parser for combined log format.

Parses lines like:
  192.168.1.1 - - [23/Dec/2025:14:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
  10.0.0.1 - user [23/Dec/2025:14:30:46 +0000] "POST /login HTTP/1.1" 401 56 "https://example.com" "curl/7.68"

Output normalized event dicts with:
  - ts: timestamp string
  - source: remote_addr (client IP)
  - severity: inferred from status code
  - message: formatted request summary
  - raw: original line
  - method: HTTP method
  - path: request path
  - status: HTTP status code
  - bytes: response bytes
  - user_agent: User-Agent header (or None)
  - referer: Referer header (or None)
"""

import re
from dataclasses import dataclass
from typing import Any


# Combined log format pattern
# $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
COMBINED_PATTERN = re.compile(
    r'^(?P<remote_addr>\S+)\s+'
    r'-\s+'
    r'(?P<remote_user>\S+)\s+'
    r'\[(?P<time_local>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+'
    r'(?P<status>\d+)\s+'
    r'(?P<bytes>\d+|-)\s+'
    r'"(?P<referer>[^"]*)"\s+'
    r'"(?P<user_agent>[^"]*)"'
)

# Common log format (without referer/user_agent)
COMMON_PATTERN = re.compile(
    r'^(?P<remote_addr>\S+)\s+'
    r'-\s+'
    r'(?P<remote_user>\S+)\s+'
    r'\[(?P<time_local>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*)"\s+'
    r'(?P<status>\d+)\s+'
    r'(?P<bytes>\d+|-)'
)


@dataclass
class NginxEntry:
    """A parsed nginx access log entry."""

    remote_addr: str
    remote_user: str | None
    time_local: str
    method: str | None
    path: str | None
    protocol: str | None
    status: int
    body_bytes_sent: int
    http_referer: str | None
    http_user_agent: str | None
    raw: str


class NginxParser:
    """
    Parser for nginx combined/common log format.

    Produces normalized event dictionaries for diagnostic analysis.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse_line(self, line: str) -> NginxEntry | None:
        """
        Parse a single nginx log line.

        Args:
            line: Raw log line

        Returns:
            Parsed entry or None if unparseable
        """
        line = line.strip()
        if not line:
            return None

        # Try combined format first
        match = COMBINED_PATTERN.match(line)
        referer = None
        user_agent = None

        if match:
            referer = match.group("referer")
            if referer == "-":
                referer = None
            user_agent = match.group("user_agent")
            if user_agent == "-":
                user_agent = None
        else:
            # Fall back to common format
            match = COMMON_PATTERN.match(line)
            if not match:
                return None

        # Parse request line
        request = match.group("request")
        method, path, protocol = self._parse_request(request)

        # Parse remote_user
        remote_user = match.group("remote_user")
        if remote_user == "-":
            remote_user = None

        # Parse bytes
        bytes_str = match.group("bytes")
        body_bytes = 0 if bytes_str == "-" else int(bytes_str)

        return NginxEntry(
            remote_addr=match.group("remote_addr"),
            remote_user=remote_user,
            time_local=match.group("time_local"),
            method=method,
            path=path,
            protocol=protocol,
            status=int(match.group("status")),
            body_bytes_sent=body_bytes,
            http_referer=referer,
            http_user_agent=user_agent,
            raw=line,
        )

    def _parse_request(self, request: str) -> tuple[str | None, str | None, str | None]:
        """Parse the request line into method, path, protocol."""
        parts = request.split()
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return parts[0], parts[1], None
        elif len(parts) == 1:
            return None, parts[0], None
        return None, None, None

    def parse_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        """
        Parse multiple nginx log lines into normalized event dicts.

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

    def _to_event_dict(self, entry: NginxEntry) -> dict[str, Any]:
        """Convert a NginxEntry to a normalized event dict."""
        # Build message summary
        method = entry.method or "?"
        path = entry.path or "?"
        message = f"{method} {path} -> {entry.status}"

        return {
            "bytes": entry.body_bytes_sent,
            "message": message,
            "method": entry.method,
            "path": entry.path,
            "raw": entry.raw,
            "referer": entry.http_referer,
            "severity": self._status_to_severity(entry.status),
            "source": entry.remote_addr,
            "status": entry.status,
            "ts": entry.time_local,
            "user_agent": entry.http_user_agent,
        }

    def _status_to_severity(self, status: int) -> str:
        """Map HTTP status code to severity."""
        if status >= 500:
            return "error"
        elif status >= 400:
            return "warning"
        elif status >= 300:
            return "info"
        else:
            return "info"
