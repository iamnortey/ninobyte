"""
Tests for pack validation.
"""

from pathlib import Path

import pytest

from lexicon_packs.validate import validate_pack, ValidationResult
from lexicon_packs.schema import validate_pack_json, REQUIRED_KEYS


class TestValidatePack:
    """Tests for validate_pack function."""

    def test_valid_minimal_pack(self, minimal_pack_path: Path):
        """Valid minimal pack passes validation."""
        result = validate_pack(minimal_pack_path)

        assert result.valid
        assert len(result.errors) == 0
        assert isinstance(result, ValidationResult)

    def test_valid_ghana_core_pack(self, ghana_core_path: Path):
        """Ghana core pack passes validation."""
        result = validate_pack(ghana_core_path)

        assert result.valid, f"Errors: {result.errors}"
        assert len(result.errors) == 0

    def test_invalid_schema_fails(self, invalid_schema_path: Path):
        """Pack with missing required keys fails."""
        result = validate_pack(invalid_schema_path)

        assert not result.valid
        assert len(result.errors) > 0
        # Should mention missing keys
        assert any("Missing required keys" in e for e in result.errors)

    def test_invalid_csv_columns_fails(self, invalid_csv_path: Path):
        """Pack with wrong CSV columns fails."""
        result = validate_pack(invalid_csv_path)

        assert not result.valid
        assert any("columns mismatch" in e.lower() for e in result.errors)

    def test_nonexistent_pack_fails(self, tmp_path: Path):
        """Non-existent pack directory fails."""
        result = validate_pack(tmp_path / "nonexistent")

        assert not result.valid
        assert any("not found" in e.lower() for e in result.errors)

    def test_missing_pack_json_fails(self, tmp_path: Path):
        """Pack directory without pack.json fails."""
        pack_dir = tmp_path / "empty_pack"
        pack_dir.mkdir()

        result = validate_pack(pack_dir)

        assert not result.valid
        assert any("pack.json not found" in e for e in result.errors)

    def test_path_traversal_rejected(self, tmp_path: Path):
        """Path with traversal is rejected."""
        result = validate_pack(tmp_path / ".." / "somewhere")

        assert not result.valid
        assert any("traversal" in e.lower() for e in result.errors)


class TestSchemaValidation:
    """Tests for pack.json schema validation."""

    def test_all_required_keys_documented(self):
        """All required keys are in the schema."""
        expected = {
            "schema_version",
            "pack_id",
            "name",
            "description",
            "license",
            "language",
            "entry_format",
            "entries_path",
            "fields",
            "created_at_utc",
            "source_attribution",
        }
        assert REQUIRED_KEYS == expected

    def test_unknown_keys_rejected(self):
        """Unknown top-level keys are rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "test",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "csv",
            "entries_path": "entries.csv",
            "fields": [{"name": "x", "type": "string", "required": True}],
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
            "unknown_key": "should fail",
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any("Unknown keys" in e for e in errors)

    def test_invalid_pack_id_format(self):
        """Invalid pack_id format is rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "Invalid ID With Spaces",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "csv",
            "entries_path": "entries.csv",
            "fields": [{"name": "x", "type": "string", "required": True}],
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any("lowercase" in e.lower() for e in errors)

    def test_path_traversal_in_entries_rejected(self):
        """entries_path with '..' is rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "test",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "csv",
            "entries_path": "../../../etc/passwd",
            "fields": [{"name": "x", "type": "string", "required": True}],
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any(".." in e for e in errors)

    def test_unsupported_entry_format_rejected(self):
        """Unsupported entry_format is rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "test",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "xml",
            "entries_path": "entries.xml",
            "fields": [{"name": "x", "type": "string", "required": True}],
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any("entry_format" in e.lower() for e in errors)


class TestFieldValidation:
    """Tests for field definition validation."""

    def test_empty_fields_rejected(self):
        """Empty fields array is rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "test",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "csv",
            "entries_path": "entries.csv",
            "fields": [],
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any("empty" in e.lower() for e in errors)

    def test_field_missing_required_keys(self):
        """Field without required keys is rejected."""
        data = {
            "schema_version": "1.0.0",
            "pack_id": "test",
            "name": "Test",
            "description": "Test",
            "license": "MIT",
            "language": "en",
            "entry_format": "csv",
            "entries_path": "entries.csv",
            "fields": [{"name": "x"}],  # Missing type and required
            "created_at_utc": "2025-01-01T00:00:00Z",
            "source_attribution": [],
        }

        errors = validate_pack_json(data, "/test")

        assert len(errors) > 0
        assert any("fields[0]" in e for e in errors)
