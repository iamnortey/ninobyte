"""
Syslog parser for RFC 3164 format.

Parses lines like:
  Dec 23 14:30:45 myhost sshd[12345]: Accepted publickey for user
  Jan  5 09:15:00 server kernel: TCP connection refused

Output normalized event dicts with:
  - ts: timestamp string (or None if unparseable)
  - source: hostname
  - severity: normalized severity (info, warning, error, critical) or None
  - message: log message
  - raw: original line
  - program: program name
  - pid: process ID (or None)
"""

import re
from dataclasses import dataclass
from typing import Any


# RFC 3164 pattern: Month Day HH:MM:SS hostname program[pid]: message
# Also handles: Month Day HH:MM:SS hostname program: message (no pid)
RFC3164_PATTERN = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<program>[^\s\[:]+)"
    r"(?:\[(?P<pid>\d+)\])?"
    r":\s*"
    r"(?P<message>.*)$",
    re.IGNORECASE,
)

# Keywords for severity inference
SEVERITY_KEYWORDS = {
    "critical": ["critical", "fatal", "panic", "emergency"],
    "error": ["error", "fail", "failed", "failure", "refused", "denied", "unable"],
    "warning": ["warn", "warning", "timeout", "retry", "slow"],
    "info": ["info", "accepted", "connected", "started", "success", "ok"],
}


@dataclass
class SyslogEntry:
    """A parsed syslog entry."""

    timestamp: str
    hostname: str
    program: str
    pid: str | None
    message: str
    raw: str


class SyslogParser:
    """
    Parser for syslog format logs (RFC 3164).

    Produces normalized event dictionaries for diagnostic analysis.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse_line(self, line: str) -> SyslogEntry | None:
        """
        Parse a single syslog line.

        Args:
            line: Raw log line

        Returns:
            Parsed entry or None if unparseable
        """
        line = line.strip()
        if not line:
            return None

        match = RFC3164_PATTERN.match(line)
        if not match:
            return None

        return SyslogEntry(
            timestamp=f"{match.group('month')} {match.group('day')} {match.group('time')}",
            hostname=match.group("hostname"),
            program=match.group("program"),
            pid=match.group("pid"),
            message=match.group("message"),
            raw=line,
        )

    def parse_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        """
        Parse multiple syslog lines into normalized event dicts.

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

    def _to_event_dict(self, entry: SyslogEntry) -> dict[str, Any]:
        """Convert a SyslogEntry to a normalized event dict."""
        return {
            "message": entry.message,
            "pid": entry.pid,
            "program": entry.program,
            "raw": entry.raw,
            "severity": self._infer_severity(entry.message),
            "source": entry.hostname,
            "ts": entry.timestamp,
        }

    def _infer_severity(self, message: str) -> str | None:
        """
        Infer severity from message keywords.

        Returns one of: critical, error, warning, info, or None
        """
        msg_lower = message.lower()

        # Check in priority order
        for severity in ["critical", "error", "warning", "info"]:
            for keyword in SEVERITY_KEYWORDS[severity]:
                if keyword in msg_lower:
                    return severity

        return None
