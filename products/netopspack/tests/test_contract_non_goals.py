"""
Contract tests verifying README contains required sections.

These tests ensure the documentation contract is maintained.
"""

from pathlib import Path

import pytest


class TestReadmeContract:
    """Tests for README.md contract compliance."""

    @pytest.fixture
    def readme_content(self) -> str:
        """Load README.md content."""
        readme_path = Path(__file__).parent.parent / "README.md"
        return readme_path.read_text(encoding="utf-8")

    def test_has_what_netopspack_is_section(self, readme_content: str):
        """README has 'What NetOpsPack Is' section."""
        assert "## What NetOpsPack Is" in readme_content

    def test_has_what_netopspack_is_not_section(self, readme_content: str):
        """README has 'What NetOpsPack is NOT' section."""
        assert "## What NetOpsPack is NOT" in readme_content

    def test_has_non_goals_table(self, readme_content: str):
        """README has non-goals table with required columns."""
        assert "| Non-Goal | Reason |" in readme_content

    def test_non_goals_include_no_network(self, readme_content: str):
        """Non-goals mention no network/cloud connection."""
        lower = readme_content.lower()
        assert "no network" in lower or "offline" in lower or "cloud" in lower

    def test_has_security_posture_section(self, readme_content: str):
        """README has security posture section."""
        assert "## Security Posture" in readme_content

    def test_has_output_contract_section(self, readme_content: str):
        """README has output contract section."""
        assert "## Output Contract" in readme_content

    def test_has_determinism_section(self, readme_content: str):
        """README has determinism section."""
        assert "## Determinism" in readme_content

    def test_has_commands_section(self, readme_content: str):
        """README has commands section."""
        assert "## Commands" in readme_content
        assert "diagnose" in readme_content


class TestSecurityContract:
    """Tests for SECURITY.md contract compliance."""

    @pytest.fixture
    def security_content(self) -> str:
        """Load SECURITY.md content."""
        security_path = Path(__file__).parent.parent / "SECURITY.md"
        return security_path.read_text(encoding="utf-8")

    def test_has_threat_model(self, security_content: str):
        """SECURITY.md has threat model section."""
        assert "## Threat Model" in security_content

    def test_has_prohibited_features(self, security_content: str):
        """SECURITY.md has prohibited features section."""
        assert "## Prohibited Features" in security_content

    def test_prohibits_network(self, security_content: str):
        """SECURITY.md prohibits network imports."""
        assert "socket" in security_content.lower()
        assert "http" in security_content.lower()

    def test_prohibits_shell(self, security_content: str):
        """SECURITY.md prohibits shell execution."""
        assert "subprocess" in security_content.lower()

    def test_has_vulnerability_reporting(self, security_content: str):
        """SECURITY.md has vulnerability reporting section."""
        assert "## Vulnerability Reporting" in security_content
