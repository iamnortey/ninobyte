"""
Tests for pack lockfile generation and verification.
"""

import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

from lexicon_packs.lockfile import (
    LOCK_SCHEMA_VERSION,
    REQUIRED_LOCK_KEYS,
    compute_file_sha256,
    compute_fields_signature,
    compute_normalized_entries_sha256,
    normalize_entries_for_hash,
    generate_lockfile,
    format_lockfile_json,
    validate_lockfile_schema,
    validate_path_security,
    load_lockfile,
    verify_lockfile,
    write_lockfile,
    LockfileError,
)


class TestComputeFileSha256:
    """Tests for raw file hashing."""

    def test_hash_is_sha256_hex(self, minimal_pack_path: Path):
        """Hash is lowercase 64-char hex."""
        entries_path = minimal_pack_path / "entries.csv"
        result = compute_file_sha256(entries_path)

        assert len(result) == 64
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_is_stable(self, minimal_pack_path: Path):
        """Same file produces same hash."""
        entries_path = minimal_pack_path / "entries.csv"

        hash1 = compute_file_sha256(entries_path)
        hash2 = compute_file_sha256(entries_path)

        assert hash1 == hash2


class TestComputeFieldsSignature:
    """Tests for fields signature computation."""

    def test_signature_is_sha256(self):
        """Signature is SHA256 hex."""
        fields = [
            {"name": "term", "type": "string"},
            {"name": "category", "type": "string"},
        ]
        result = compute_fields_signature(fields)

        assert len(result) == 64

    def test_signature_is_order_sensitive(self):
        """Field order affects signature."""
        fields1 = [
            {"name": "term", "type": "string"},
            {"name": "category", "type": "string"},
        ]
        fields2 = [
            {"name": "category", "type": "string"},
            {"name": "term", "type": "string"},
        ]

        sig1 = compute_fields_signature(fields1)
        sig2 = compute_fields_signature(fields2)

        assert sig1 != sig2

    def test_signature_ignores_extra_keys(self):
        """Signature only uses field names."""
        fields1 = [{"name": "term", "type": "string"}]
        fields2 = [{"name": "term", "type": "integer", "extra": "ignored"}]

        sig1 = compute_fields_signature(fields1)
        sig2 = compute_fields_signature(fields2)

        assert sig1 == sig2


class TestNormalizeEntriesForHash:
    """Tests for entry normalization."""

    def test_sorts_by_term_casefolded(self):
        """Entries sorted by term.casefold()."""
        entries = [
            {"term": "Zebra", "category": "animal"},
            {"term": "alpha", "category": "letter"},
        ]
        result = normalize_entries_for_hash(entries)

        assert result[0]["term"] == "alpha"
        assert result[1]["term"] == "Zebra"

    def test_sorts_by_term_for_ties(self):
        """Case-folded ties broken by full term."""
        entries = [
            {"term": "Alpha", "category": "letter"},
            {"term": "alpha", "category": "letter"},
        ]
        result = normalize_entries_for_hash(entries)

        # 'Alpha' comes before 'alpha' lexicographically
        assert result[0]["term"] == "Alpha"
        assert result[1]["term"] == "alpha"

    def test_sorts_by_category_for_ties(self):
        """Same term sorted by category."""
        entries = [
            {"term": "alpha", "category": "letter"},
            {"term": "alpha", "category": "greek"},
        ]
        result = normalize_entries_for_hash(entries)

        assert result[0]["category"] == "greek"
        assert result[1]["category"] == "letter"

    def test_entry_keys_sorted(self):
        """Each entry has sorted keys."""
        entries = [{"zebra_key": "z", "alpha_key": "a"}]
        result = normalize_entries_for_hash(entries)

        keys = list(result[0].keys())
        assert keys == sorted(keys)


class TestComputeNormalizedEntriesSha256:
    """Tests for normalized entries hashing."""

    def test_hash_is_sha256(self):
        """Hash is 64-char hex."""
        entries = [{"term": "test", "category": "cat"}]
        result = compute_normalized_entries_sha256(entries)

        assert len(result) == 64

    def test_hash_is_stable(self):
        """Same entries produce same hash."""
        entries = [
            {"term": "alpha", "category": "letter"},
            {"term": "beta", "category": "letter"},
        ]

        hash1 = compute_normalized_entries_sha256(entries)
        hash2 = compute_normalized_entries_sha256(entries)

        assert hash1 == hash2

    def test_hash_is_order_independent(self):
        """Entry order doesn't affect normalized hash."""
        entries1 = [
            {"term": "alpha", "category": "letter"},
            {"term": "beta", "category": "letter"},
        ]
        entries2 = [
            {"term": "beta", "category": "letter"},
            {"term": "alpha", "category": "letter"},
        ]

        hash1 = compute_normalized_entries_sha256(entries1)
        hash2 = compute_normalized_entries_sha256(entries2)

        assert hash1 == hash2


class TestGenerateLockfile:
    """Tests for lockfile generation."""

    def test_has_all_required_keys(self, minimal_pack_path: Path):
        """Generated lockfile has all required keys."""
        lockfile = generate_lockfile(minimal_pack_path)

        for key in REQUIRED_LOCK_KEYS:
            assert key in lockfile, f"Missing key: {key}"

    def test_lock_schema_version(self, minimal_pack_path: Path):
        """Lock schema version is current."""
        lockfile = generate_lockfile(minimal_pack_path)

        assert lockfile["lock_schema_version"] == LOCK_SCHEMA_VERSION

    def test_pack_id_matches(self, minimal_pack_path: Path):
        """Pack ID matches pack.json."""
        lockfile = generate_lockfile(minimal_pack_path)

        assert lockfile["pack_id"] == "minimal-test"

    def test_entry_count_is_integer(self, minimal_pack_path: Path):
        """Entry count is integer."""
        lockfile = generate_lockfile(minimal_pack_path)

        assert isinstance(lockfile["entry_count"], int)
        assert lockfile["entry_count"] == 3

    def test_fixed_time_is_honored(self, minimal_pack_path: Path):
        """Fixed time is used when provided."""
        fixed_time = "2025-06-15T12:00:00Z"
        lockfile = generate_lockfile(minimal_pack_path, fixed_time=fixed_time)

        assert lockfile["generated_at_utc"] == fixed_time

    def test_hashes_are_64_char_hex(self, minimal_pack_path: Path):
        """All hashes are 64-char lowercase hex."""
        lockfile = generate_lockfile(minimal_pack_path)

        hash_fields = [
            "pack_json_sha256",
            "entries_file_sha256",
            "normalized_entries_sha256",
            "fields_signature",
        ]
        for field in hash_fields:
            value = lockfile[field]
            assert len(value) == 64, f"{field} is not 64 chars"
            assert value == value.lower(), f"{field} is not lowercase"

    def test_generation_is_deterministic(self, minimal_pack_path: Path):
        """Same pack produces same lockfile (with fixed time)."""
        fixed_time = "2025-01-01T00:00:00Z"

        lockfile1 = generate_lockfile(minimal_pack_path, fixed_time=fixed_time)
        lockfile2 = generate_lockfile(minimal_pack_path, fixed_time=fixed_time)

        assert lockfile1 == lockfile2


class TestValidateLockfileSchema:
    """Tests for lockfile schema validation."""

    def test_valid_lockfile_no_errors(self, minimal_pack_path: Path):
        """Valid lockfile has no schema errors."""
        lockfile = generate_lockfile(minimal_pack_path)
        errors = validate_lockfile_schema(lockfile)

        assert errors == []

    def test_missing_key_error(self):
        """Missing required key produces error."""
        lockfile = {"lock_schema_version": LOCK_SCHEMA_VERSION}
        errors = validate_lockfile_schema(lockfile)

        assert len(errors) > 0
        assert any("Missing required key" in e for e in errors)

    def test_unknown_key_error(self, minimal_pack_path: Path):
        """Unknown key produces error."""
        lockfile = generate_lockfile(minimal_pack_path)
        lockfile["unknown_key"] = "value"
        errors = validate_lockfile_schema(lockfile)

        assert any("Unknown key" in e for e in errors)

    def test_wrong_schema_version_error(self, minimal_pack_path: Path):
        """Wrong schema version produces error."""
        lockfile = generate_lockfile(minimal_pack_path)
        lockfile["lock_schema_version"] = "99.0.0"
        errors = validate_lockfile_schema(lockfile)

        assert any("Unsupported lock_schema_version" in e for e in errors)

    def test_entry_count_must_be_int(self, minimal_pack_path: Path):
        """Entry count must be integer."""
        lockfile = generate_lockfile(minimal_pack_path)
        lockfile["entry_count"] = "3"
        errors = validate_lockfile_schema(lockfile)

        assert any("entry_count must be an integer" in e for e in errors)


class TestWriteAndLoadLockfile:
    """Tests for writing and loading lockfiles."""

    def test_write_creates_file(self, minimal_pack_path: Path):
        """Write creates pack.lock.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy minimal pack to temp directory
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            lockfile_path = write_lockfile(tmp_pack)

            assert lockfile_path.exists()
            assert lockfile_path.name == "pack.lock.json"

    def test_load_reads_valid_lockfile(self, minimal_pack_path: Path):
        """Load reads a valid lockfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            write_lockfile(tmp_pack)
            loaded = load_lockfile(tmp_pack)

            assert loaded["pack_id"] == "minimal-test"

    def test_load_missing_lockfile_error(self, minimal_pack_path: Path):
        """Load raises error for missing lockfile."""
        with pytest.raises(LockfileError, match="Lockfile not found"):
            load_lockfile(minimal_pack_path)

    def test_written_lockfile_is_canonical_json(self, minimal_pack_path: Path):
        """Written lockfile is canonical JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            lockfile_path = write_lockfile(tmp_pack)
            content = lockfile_path.read_text()

            # Has trailing newline
            assert content.endswith("\n")

            # Keys are sorted
            data = json.loads(content)
            keys = list(data.keys())
            assert keys == sorted(keys)


class TestVerifyLockfile:
    """Tests for lockfile verification."""

    def test_verify_valid_lockfile(self, minimal_pack_path: Path):
        """Fresh lockfile verifies successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            write_lockfile(tmp_pack)
            is_valid, errors = verify_lockfile(tmp_pack)

            assert is_valid
            assert errors == []

    def test_verify_detects_entries_change(self, minimal_pack_path: Path):
        """Verification fails if entries.csv changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            # Generate lockfile
            write_lockfile(tmp_pack)

            # Modify entries.csv
            entries_path = tmp_pack / "entries.csv"
            entries_path.write_text("term,category\nmodified,test\n")

            is_valid, errors = verify_lockfile(tmp_pack)

            assert not is_valid
            assert len(errors) > 0

    def test_verify_detects_pack_json_change(self, minimal_pack_path: Path):
        """Verification fails if pack.json changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            # Generate lockfile
            write_lockfile(tmp_pack)

            # Modify pack.json
            pack_json_path = tmp_pack / "pack.json"
            pack_data = json.loads(pack_json_path.read_text())
            pack_data["name"] = "Modified Name"
            pack_json_path.write_text(json.dumps(pack_data, indent=2))

            is_valid, errors = verify_lockfile(tmp_pack)

            assert not is_valid
            assert any("pack_json_sha256" in e for e in errors)


class TestCLILock:
    """Tests for lock CLI command."""

    def test_lock_stdout_is_valid_json(self, minimal_pack_path: Path):
        """lock command outputs valid JSON to stdout."""
        src_dir = minimal_pack_path.parent.parent.parent / "src"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lexicon_packs",
                "lock",
                "--pack",
                str(minimal_pack_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(src_dir.parent),
            env={
                **subprocess.os.environ,
                "PYTHONPATH": str(src_dir),
            },
        )

        assert result.returncode == 0
        lockfile = json.loads(result.stdout)
        assert lockfile["pack_id"] == "minimal-test"

    def test_lock_write_creates_file(self, minimal_pack_path: Path):
        """lock --write creates lockfile in pack directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "lock",
                    "--pack",
                    str(tmp_pack),
                    "--write",
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 0
            assert (tmp_pack / "pack.lock.json").exists()


class TestCLIVerify:
    """Tests for verify CLI command."""

    def test_verify_valid_exits_zero(self, minimal_pack_path: Path):
        """verify command exits 0 for valid lockfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            # Write lockfile first
            write_lockfile(tmp_pack)

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "verify",
                    "--pack",
                    str(tmp_pack),
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 0
            assert "verified" in result.stdout.lower()

    def test_verify_invalid_exits_nonzero(self, minimal_pack_path: Path):
        """verify command exits non-zero for drift."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            # Write lockfile
            write_lockfile(tmp_pack)

            # Modify entries
            entries_path = tmp_pack / "entries.csv"
            entries_path.write_text("term,category\nchanged,test\n")

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "verify",
                    "--pack",
                    str(tmp_pack),
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 2
            assert "failed" in result.stderr.lower()

    def test_verify_missing_lockfile_exits_nonzero(self, minimal_pack_path: Path):
        """verify command exits non-zero for missing lockfile."""
        src_dir = minimal_pack_path.parent.parent.parent / "src"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lexicon_packs",
                "verify",
                "--pack",
                str(minimal_pack_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(src_dir.parent),
            env={
                **subprocess.os.environ,
                "PYTHONPATH": str(src_dir),
            },
        )

        assert result.returncode == 2
        assert "not found" in result.stderr.lower()


class TestGhanaCoreIntegration:
    """Integration tests with ghana-core pack."""

    def test_generate_lockfile_for_ghana_core(self, ghana_core_path: Path):
        """Can generate lockfile for ghana-core pack."""
        lockfile = generate_lockfile(ghana_core_path)

        assert lockfile["pack_id"] == "ghana-core"
        assert lockfile["entry_count"] == 30
        assert lockfile["lock_schema_version"] == LOCK_SCHEMA_VERSION

    def test_ghana_core_lockfile_is_deterministic(self, ghana_core_path: Path):
        """Ghana-core lockfile is deterministic."""
        fixed_time = "2025-01-01T00:00:00Z"

        lockfile1 = generate_lockfile(ghana_core_path, fixed_time=fixed_time)
        lockfile2 = generate_lockfile(ghana_core_path, fixed_time=fixed_time)

        assert lockfile1 == lockfile2


class TestPathSecurity:
    """Tests for path traversal protection."""

    def test_validate_path_security_valid(self, minimal_pack_path: Path):
        """Valid path within pack root passes."""
        pack_root = minimal_pack_path.resolve()
        file_path = pack_root / "entries.csv"

        # Should not raise
        validate_path_security(file_path, pack_root)

    def test_validate_path_security_traversal(self, minimal_pack_path: Path):
        """Path traversal is rejected."""
        pack_root = minimal_pack_path.resolve()
        # Try to escape with ..
        file_path = pack_root / ".." / "other_pack" / "entries.csv"

        with pytest.raises(LockfileError, match="Path traversal"):
            validate_path_security(file_path, pack_root)

    def test_generate_rejects_absolute_entries_path(self, minimal_pack_path: Path):
        """Absolute entries_path in pack.json is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            # Modify pack.json to have absolute path
            pack_json_path = tmp_pack / "pack.json"
            pack_data = json.loads(pack_json_path.read_text())
            pack_data["entries_path"] = "/etc/passwd"
            pack_json_path.write_text(json.dumps(pack_data, indent=2))

            # Rejected at schema validation level
            with pytest.raises(LockfileError, match="entries_path must be relative"):
                generate_lockfile(tmp_pack)


class TestCLIFixedTime:
    """Tests for --fixed-time CLI argument."""

    def test_lock_fixed_time_deterministic(self, minimal_pack_path: Path):
        """lock --fixed-time produces byte-for-byte stable output."""
        src_dir = minimal_pack_path.parent.parent.parent / "src"
        fixed_time = "2025-06-15T12:00:00Z"

        def run_lock():
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "lock",
                    "--pack",
                    str(minimal_pack_path),
                    "--fixed-time",
                    fixed_time,
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )
            return result.stdout

        output1 = run_lock()
        output2 = run_lock()

        assert output1 == output2
        assert fixed_time in output1

    def test_lock_fixed_time_in_written_file(self, minimal_pack_path: Path):
        """lock --write --fixed-time writes fixed timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pack = Path(tmpdir) / "pack"
            shutil.copytree(minimal_pack_path, tmp_pack)

            src_dir = minimal_pack_path.parent.parent.parent / "src"
            fixed_time = "2025-06-15T12:00:00Z"

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "lock",
                    "--pack",
                    str(tmp_pack),
                    "--write",
                    "--fixed-time",
                    fixed_time,
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            lockfile_content = (tmp_pack / "pack.lock.json").read_text()
            lockfile = json.loads(lockfile_content)

            assert lockfile["generated_at_utc"] == fixed_time
