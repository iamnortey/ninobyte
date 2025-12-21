"""
Ninobyte OpsPack - Read-Only Operational Intelligence Module

Provides deterministic, rule-based operational intelligence functions.
See docs/ROADMAP.md for the implementation plan.

Security constraints (enforced by design):
- Read-only: No write operations
- No network: No HTTP clients or API calls
- No shell: No subprocess with shell=True
- Deny-by-default: Explicit allowlisting required
"""

from .version import __version__
from .triage import triage_incident, TRIAGE_SCHEMA_VERSION

__all__ = ["__version__", "triage_incident", "TRIAGE_SCHEMA_VERSION"]
