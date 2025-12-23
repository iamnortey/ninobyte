"""
Data models for NetOpsPack.

Defines the output schema and diagnostic structures.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiagnosticItem:
    """A single diagnostic finding."""

    category: str
    severity: str  # "info", "warning", "error", "critical"
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category,
            "details": self.details,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class Summary:
    """Summary statistics for log analysis."""

    total_lines: int = 0
    parsed_lines: int = 0
    error_lines: int = 0
    unique_ips: int = 0
    unique_paths: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_lines": self.error_lines,
            "parsed_lines": self.parsed_lines,
            "total_lines": self.total_lines,
            "unique_ips": self.unique_ips,
            "unique_paths": self.unique_paths,
        }


@dataclass
class RedactionSummary:
    """Summary of redactions applied."""

    ips_redacted: int = 0
    tokens_redacted: int = 0
    emails_redacted: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "emails_redacted": self.emails_redacted,
            "ips_redacted": self.ips_redacted,
            "tokens_redacted": self.tokens_redacted,
        }


@dataclass
class DiagnoseResult:
    """Complete result of a diagnose operation."""

    schema_version: str = "1.0.0"
    generated_at_utc: str = ""
    input_file: str = ""
    input_format: str = ""
    redaction_applied: bool = True
    summary: Summary = field(default_factory=Summary)
    diagnostics: list[DiagnosticItem] = field(default_factory=list)
    redaction_summary: RedactionSummary = field(default_factory=RedactionSummary)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization (sorted keys)."""
        return {
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "generated_at_utc": self.generated_at_utc,
            "input_file": self.input_file,
            "input_format": self.input_format,
            "redaction_applied": self.redaction_applied,
            "redaction_summary": self.redaction_summary.to_dict(),
            "schema_version": self.schema_version,
            "summary": self.summary.to_dict(),
        }
