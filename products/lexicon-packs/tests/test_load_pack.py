"""
Tests for pack loading.
"""

from pathlib import Path

import pytest

from lexicon_packs.load import load_pack, LoadedPack, PackEntry, LoadError


class TestLoadPack:
    """Tests for load_pack function."""

    def test_load_minimal_pack(self, minimal_pack_path: Path):
        """Minimal pack loads correctly."""
        pack = load_pack(minimal_pack_path)

        assert isinstance(pack, LoadedPack)
        assert pack.pack_id == "minimal-test"
        assert pack.name == "Minimal Test Pack"
        assert pack.entry_count == 3

    def test_load_ghana_core(self, ghana_core_path: Path):
        """Ghana core pack loads correctly."""
        pack = load_pack(ghana_core_path)

        assert pack.pack_id == "ghana-core"
        assert pack.name == "Ghana Core Entities"
        assert pack.entry_count == 30
        assert pack.language == "en-GH"
        assert pack.license == "CC0-1.0"

    def test_entries_have_correct_structure(self, minimal_pack_path: Path):
        """Entries have expected structure."""
        pack = load_pack(minimal_pack_path)

        assert len(pack.entries) == 3

        entry = pack.entries[0]
        assert isinstance(entry, PackEntry)
        assert "term" in entry.values
        assert "category" in entry.values
        assert entry.values["term"] == "alpha"
        assert entry.values["category"] == "letter"

    def test_entries_preserve_order(self, minimal_pack_path: Path):
        """Entries preserve CSV row order."""
        pack = load_pack(minimal_pack_path)

        terms = [e.values["term"] for e in pack.entries]
        assert terms == ["alpha", "beta", "gamma"]

    def test_entries_sha256_computed(self, minimal_pack_path: Path):
        """entries_sha256 is computed."""
        pack = load_pack(minimal_pack_path)

        assert pack.entries_sha256
        assert len(pack.entries_sha256) == 64  # SHA256 hex length

    def test_to_dict_includes_metadata(self, minimal_pack_path: Path):
        """to_dict includes all metadata."""
        pack = load_pack(minimal_pack_path)
        data = pack.to_dict()

        assert data["pack_id"] == "minimal-test"
        assert data["name"] == "Minimal Test Pack"
        assert data["entry_count"] == 3
        assert "entries_sha256" in data
        assert "first_entries" not in data  # default = 0

    def test_to_dict_with_entries(self, minimal_pack_path: Path):
        """to_dict includes entries when requested."""
        pack = load_pack(minimal_pack_path)
        data = pack.to_dict(include_entries=2)

        assert "first_entries" in data
        assert len(data["first_entries"]) == 2
        assert data["first_entries"][0]["term"] == "alpha"

    def test_load_invalid_pack_raises(self, invalid_schema_path: Path):
        """Loading invalid pack raises LoadError."""
        with pytest.raises(LoadError) as exc_info:
            load_pack(invalid_schema_path)

        assert "validation failed" in str(exc_info.value).lower()

    def test_load_nonexistent_raises(self, tmp_path: Path):
        """Loading non-existent pack raises LoadError."""
        with pytest.raises(LoadError):
            load_pack(tmp_path / "nonexistent")


class TestPackEntry:
    """Tests for PackEntry class."""

    def test_to_dict_sorts_keys(self):
        """to_dict returns sorted keys."""
        entry = PackEntry(values={"zebra": "z", "alpha": "a", "middle": "m"})

        result = entry.to_dict()
        keys = list(result.keys())

        assert keys == ["alpha", "middle", "zebra"]

    def test_entry_equality(self):
        """Entries with same values are equal."""
        e1 = PackEntry(values={"a": "1", "b": "2"})
        e2 = PackEntry(values={"b": "2", "a": "1"})

        # Same content, different key order
        assert e1.to_dict() == e2.to_dict()
