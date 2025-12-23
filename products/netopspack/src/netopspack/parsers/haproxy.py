"""
HAProxy log parser for HTTP log format.

Status: Stub implementation
"""

from dataclasses import dataclass
from typing import Iterator


@dataclass
class HaproxyEntry:
    """A parsed HAProxy log entry."""

    timestamp: str
    frontend_name: str
    backend_name: str
    server_name: str
    client_ip: str
    client_port: int
    status_code: int
    bytes_read: int
    request: str
    raw: str


class HaproxyParser:
    """
    Parser for HAProxy HTTP log format.

    Expected format:
    <timestamp> <frontend_name> <backend_name>/<server_name> <timings> <status_code> <bytes_read> ...
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
        # Stub implementation
        raise NotImplementedError("HAProxy parser not yet implemented")

    def parse_file(self, path: str) -> Iterator[HaproxyEntry]:
        """
        Parse a HAProxy log file.

        Args:
            path: Path to log file

        Yields:
            Parsed HAProxy entries
        """
        raise NotImplementedError("HAProxy parser not yet implemented")
