"""
Ninobyte OpsPack - Read-Only Operational Intelligence Module

This is a skeleton package. No implementation exists in this phase.
See docs/ROADMAP.md for the implementation plan.

Security constraints (enforced by design):
- Read-only: No write operations
- No network: No HTTP clients or API calls
- No shell: No subprocess with shell=True
- Deny-by-default: Explicit allowlisting required
"""

from .version import __version__

__all__ = ["__version__"]
