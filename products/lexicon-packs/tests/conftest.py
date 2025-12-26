"""
Pytest configuration for lexicon-packs tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return TESTS_DIR / "fixtures"


@pytest.fixture
def minimal_pack_path(fixtures_dir: Path) -> Path:
    """Path to minimal valid test pack."""
    return fixtures_dir / "minimal_pack"


@pytest.fixture
def invalid_schema_path(fixtures_dir: Path) -> Path:
    """Path to pack with invalid schema."""
    return fixtures_dir / "invalid_schema"


@pytest.fixture
def invalid_csv_path(fixtures_dir: Path) -> Path:
    """Path to pack with invalid CSV."""
    return fixtures_dir / "invalid_csv"


@pytest.fixture
def ghana_core_path() -> Path:
    """Path to ghana-core pack."""
    return PRODUCT_ROOT / "packs" / "ghana-core"
