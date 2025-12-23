"""
NetOpsPack - Network operations toolkit for SRE/DevOps incident triage.

This package provides deterministic, offline-first network log analysis
with automatic sensitive data redaction.

Security guarantees:
- No network access (stdlib only)
- No shell execution
- No file writes (stdout only)
- Redaction by default
"""

__version__ = "0.9.0"
__all__ = ["__version__"]
