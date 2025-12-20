"""
AirGap Configuration

Defines security-critical configuration with safe defaults.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json
import os


# Blocked filename patterns (deny-by-default for sensitive files)
DEFAULT_BLOCKED_PATTERNS: List[str] = [
    # Environment and secrets
    ".env", ".env.*",
    # Private keys
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks",
    "id_rsa", "id_rsa.*", "id_ed25519", "id_ed25519.*", "id_ecdsa", "id_ecdsa.*",
    "authorized_keys", "known_hosts",
    # Credentials files
    "credentials", "credentials.*", "secrets", "secrets.*",
    "*_SECRET", "*_KEY", "*_TOKEN", "*_PASSWORD",
    # Databases
    "*.db", "*.sqlite", "*.sqlite3", "*.kdb", "*.kdbx",
    # Config files with potential secrets
    ".git/config", ".npmrc", ".pypirc", ".docker/config.json",
    ".aws/credentials", ".aws/config",
    # Kubernetes secrets
    "*.kubeconfig", "kubeconfig",
]


@dataclass
class AirGapConfig:
    """Configuration for AirGap file browser with security defaults."""

    # Paths allowed for access (deny-by-default: empty = nothing accessible)
    allowed_roots: List[str] = field(default_factory=list)

    # Size limits
    max_file_size_bytes: int = 1_048_576  # 1 MB
    max_response_bytes: int = 524_288  # 512 KB
    max_results: int = 100
    max_files_scanned: int = 10_000  # Budget for search operations

    # Timeouts
    timeout_seconds: float = 30.0

    # Audit configuration
    audit_log_path: Optional[str] = None
    redact_paths_in_audit: bool = True

    # Blocked patterns
    blocked_patterns: List[str] = field(default_factory=lambda: DEFAULT_BLOCKED_PATTERNS.copy())

    def __post_init__(self) -> None:
        """Validate configuration on creation."""
        if not self.allowed_roots:
            # Deny-by-default: no roots = nothing accessible
            pass

        # Normalize allowed roots to absolute paths
        normalized: List[str] = []
        for root in self.allowed_roots:
            abs_path = os.path.abspath(os.path.expanduser(root))
            if os.path.isdir(abs_path):
                normalized.append(abs_path)
        self.allowed_roots = normalized

        # Validate limits are positive
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive")
        if self.max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")
        if self.max_files_scanned <= 0:
            raise ValueError("max_files_scanned must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @classmethod
    def from_json_file(cls, path: str) -> "AirGapConfig":
        """Load configuration from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "AirGapConfig":
        """Create configuration from dictionary."""
        return cls(**data)
