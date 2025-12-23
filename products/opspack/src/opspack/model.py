"""
Data models and schema constants for OpsPack.

All structures are designed for deterministic JSON serialization.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Schema version for triage output format
TRIAGE_SCHEMA_VERSION = "1.0.0"

# Redaction placeholder (consistent across all redactions)
REDACTED_PLACEHOLDER = "[REDACTED]"


@dataclass
class TriageSignals:
    """Extracted signals from incident text."""

    timestamps: List[str] = field(default_factory=list)
    error_keywords: List[str] = field(default_factory=list)
    stacktrace_markers: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict with stable key ordering."""
        return {
            "error_keywords": sorted(self.error_keywords),
            "stacktrace_markers": sorted(self.stacktrace_markers),
            "timestamps": sorted(self.timestamps),
        }


@dataclass
class TriageResult:
    """Complete triage analysis result."""

    schema_version: str
    generated_at_utc: str
    input_path: str
    input_path_type: str  # "repo-relative" or "absolute"
    redaction_applied: bool
    signals: TriageSignals
    line_count: int
    char_count: int

    def to_dict(self) -> dict:
        """Convert to dict with stable key ordering for deterministic JSON."""
        return {
            "char_count": self.char_count,
            "generated_at_utc": self.generated_at_utc,
            "input_path": self.input_path,
            "input_path_type": self.input_path_type,
            "line_count": self.line_count,
            "redaction_applied": self.redaction_applied,
            "schema_version": self.schema_version,
            "signals": self.signals.to_dict(),
            "summary": self._generate_summary(),
        }

    def _generate_summary(self) -> str:
        """Generate deterministic summary string."""
        parts = []

        error_count = len(self.signals.error_keywords)
        if error_count > 0:
            parts.append(f"{error_count} error keyword(s)")

        ts_count = len(self.signals.timestamps)
        if ts_count > 0:
            parts.append(f"{ts_count} timestamp(s)")

        st_count = len(self.signals.stacktrace_markers)
        if st_count > 0:
            parts.append(f"{st_count} stacktrace marker(s)")

        if not parts:
            return f"Analyzed {self.line_count} lines, no notable signals detected."

        return f"Analyzed {self.line_count} lines: " + ", ".join(parts) + "."
