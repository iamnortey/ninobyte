"""
Core diagnose logic for NetOpsPack.

Produces deterministic canonical JSON reports from log files.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from netopspack.parsers.syslog import SyslogParser
from netopspack.parsers.nginx import NginxParser
from netopspack.parsers.haproxy import HaproxyParser
from netopspack.redact import redact_line, RedactionStats


# Parser registry
PARSERS = {
    "syslog": SyslogParser,
    "nginx": NginxParser,
    "haproxy": HaproxyParser,
}

# Keywords to count for signal analysis
SIGNAL_KEYWORDS = ["error", "fail", "failed", "timeout", "refused", "denied", "warn", "critical"]


def diagnose_file(
    input_path: str,
    format: str,
    fixed_time: str | None = None,
    limit: int = 50,
    redact: bool = True,
) -> dict[str, Any]:
    """
    Analyze a log file and produce a diagnostic report.

    Args:
        input_path: Path to the log file
        format: Log format (syslog, nginx, haproxy)
        fixed_time: Fixed UTC timestamp for deterministic output
        limit: Maximum number of events to include
        redact: Whether to apply redaction

    Returns:
        Deterministic JSON-serializable report dictionary
    """
    # Get parser
    if format not in PARSERS:
        raise ValueError(f"Unknown format: {format}")

    parser = PARSERS[format]()

    # Read file
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # Parse lines
    events = parser.parse_lines(lines)

    # Apply redaction if enabled
    redaction_stats = RedactionStats()
    if redact:
        events = _apply_redaction(events, redaction_stats)

    # Compute signals
    signals = _compute_signals(events, format)

    # Generate timestamp
    if fixed_time:
        generated_at = fixed_time
    else:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build report with sorted keys
    report = {
        "events": events[:limit],
        "format": format,
        "generated_at_utc": generated_at,
        "input_path": str(path.resolve()),
        "line_count": len(lines),
        "event_count": len(events),
        "limit": limit,
        "redaction_applied": redact,
        "redaction_summary": {
            "emails": redaction_stats.emails,
            "hex_strings": redaction_stats.hex_strings,
            "ips": redaction_stats.ips,
            "keys": redaction_stats.keys,
            "tokens": redaction_stats.tokens,
        },
        "schema_version": "1.0.0",
        "signals": signals,
    }

    return report


def _apply_redaction(events: list[dict[str, Any]], stats: RedactionStats) -> list[dict[str, Any]]:
    """Apply redaction to events."""
    redacted_events = []
    for event in events:
        redacted_event = {}
        for key in sorted(event.keys()):
            value = event[key]
            if isinstance(value, str):
                redacted_event[key] = redact_line(value, stats)
            else:
                redacted_event[key] = value
        redacted_events.append(redacted_event)
    return redacted_events


def _compute_signals(events: list[dict[str, Any]], format: str) -> dict[str, Any]:
    """Compute signal statistics from events."""
    signals: dict[str, Any] = {}

    # Severity counts
    severity_counter: Counter[str] = Counter()
    for event in events:
        severity = event.get("severity")
        if severity:
            severity_counter[severity] += 1

    signals["severity_counts"] = dict(sorted(severity_counter.items()))

    # Status code counts (for nginx/haproxy)
    if format in ("nginx", "haproxy"):
        status_counter: Counter[int] = Counter()
        for event in events:
            status = event.get("status")
            if status is not None:
                status_counter[status] += 1
        signals["status_counts"] = {str(k): v for k, v in sorted(status_counter.items())}

    # Path counts (for nginx/haproxy)
    if format in ("nginx", "haproxy"):
        path_counter: Counter[str] = Counter()
        for event in events:
            path = event.get("path")
            if path:
                path_counter[path] += 1
        # Top 10 paths
        signals["top_paths"] = dict(path_counter.most_common(10))

    # Keyword hits
    keyword_counter: Counter[str] = Counter()
    for event in events:
        message = event.get("message", "").lower()
        for keyword in SIGNAL_KEYWORDS:
            if keyword in message:
                keyword_counter[keyword] += 1

    signals["keyword_hits"] = dict(sorted(keyword_counter.items()))

    # Source counts (unique IPs/hosts)
    source_counter: Counter[str] = Counter()
    for event in events:
        source = event.get("source")
        if source:
            source_counter[source] += 1

    signals["unique_sources"] = len(source_counter)
    signals["top_sources"] = dict(source_counter.most_common(10))

    return signals


def format_report_json(report: dict[str, Any]) -> str:
    """
    Format report as canonical JSON.

    Uses sorted keys and 2-space indentation for determinism.
    """
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
