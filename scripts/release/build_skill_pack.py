#!/usr/bin/env python3
"""
Deterministic Skill Pack Builder for Ninobyte.

Produces a reproducible ZIP artifact containing a canonical skill and its
associated test fixtures/goldens, with a METADATA.json manifest.

Security:
- No networking (stdlib only)
- No shell=True (subprocess uses list args)
- No auto-update of goldens
- Deterministic output (stable ordering, fixed timestamps, sorted keys)

Usage:
    python scripts/release/build_skill_pack.py \
        --skill-dir skills/senior-developer-brain \
        --name senior-developer-brain \
        --version v0.8.2+pack.1 \
        --out-dir dist

Output:
    dist/senior-developer-brain_v0.8.2+pack.1.zip
    dist/senior-developer-brain_v0.8.2+pack.1.zip.sha256
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple


# =============================================================================
# Constants
# =============================================================================

# Fixed timestamp for deterministic ZIP entries (1980-01-01 00:00:00)
# This is the minimum valid DOS timestamp for ZIP files
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# Files to always exclude from packaging
EXCLUDED_FILES = {'.DS_Store', '.gitkeep', '__pycache__', '.pyc', '.pyo'}

# Required files in skill directory
REQUIRED_FILES = {'SKILL.md'}

# Optional files to include if present
OPTIONAL_ROOT_FILES = {'README.md', 'CHANGELOG.md', 'LICENSE'}

# Optional directories to include recursively
OPTIONAL_DIRS = {'tests/fixtures', 'tests/goldens'}


# =============================================================================
# Git Helpers
# =============================================================================

def get_repo_root() -> Path:
    """Get the repository root directory."""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )
    return Path(result.stdout.strip())


def get_head_sha() -> str:
    """Get the current HEAD commit SHA."""
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )
    return result.stdout.strip()


# =============================================================================
# File Collection
# =============================================================================

def sha256_file(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def should_include_file(filepath: Path) -> bool:
    """Check if a file should be included in the package."""
    name = filepath.name
    if name in EXCLUDED_FILES:
        return False
    if name.startswith('.'):
        return False
    if '__pycache__' in filepath.parts:
        return False
    return True


def collect_files(skill_dir: Path) -> List[Tuple[Path, str]]:
    """
    Collect files to include in the package.

    Returns:
        List of (absolute_path, relative_path_in_zip) tuples, sorted by zip path.
    """
    files: List[Tuple[Path, str]] = []

    # 1. Required files
    for filename in REQUIRED_FILES:
        filepath = skill_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Required file missing: {filepath}")
        zip_path = str(Path(skill_dir.name) / filename)
        files.append((filepath, zip_path))

    # 2. Optional root files
    for filename in OPTIONAL_ROOT_FILES:
        filepath = skill_dir / filename
        if filepath.exists() and should_include_file(filepath):
            zip_path = str(Path(skill_dir.name) / filename)
            files.append((filepath, zip_path))

    # 3. Optional directories (recursive)
    for subdir in OPTIONAL_DIRS:
        dir_path = skill_dir / subdir
        if dir_path.is_dir():
            for root, _, filenames in os.walk(dir_path):
                root_path = Path(root)
                for filename in filenames:
                    filepath = root_path / filename
                    if should_include_file(filepath):
                        # Compute relative path within skill_dir
                        rel_to_skill = filepath.relative_to(skill_dir)
                        zip_path = str(Path(skill_dir.name) / rel_to_skill)
                        files.append((filepath, zip_path))

    # De-duplicate by zip_path and sort
    seen = set()
    unique_files = []
    for abs_path, zip_path in files:
        if zip_path not in seen:
            seen.add(zip_path)
            unique_files.append((abs_path, zip_path))

    # Sort by zip_path for determinism
    unique_files.sort(key=lambda x: x[1])

    return unique_files


# =============================================================================
# Metadata Generation
# =============================================================================

def build_metadata(
    name: str,
    version: str,
    git_sha: str,
    skill_dir: str,
    files: List[Tuple[Path, str]]
) -> Dict[str, Any]:
    """
    Build the METADATA.json content.

    Returns a dict that can be JSON-serialized deterministically.
    """
    file_entries = []
    for abs_path, zip_path in files:
        file_entries.append({
            "path": zip_path,
            "sha256": sha256_file(abs_path),
            "bytes": abs_path.stat().st_size
        })

    # Sort file entries by path for determinism
    file_entries.sort(key=lambda x: x["path"])

    metadata = {
        "name": name,
        "version": version,
        "git_sha": git_sha,
        "skill_dir": skill_dir,
        "files": file_entries
    }

    return metadata


def serialize_metadata(metadata: Dict[str, Any]) -> bytes:
    """Serialize metadata to deterministic JSON bytes."""
    json_str = json.dumps(
        metadata,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )
    # Add trailing newline
    return (json_str + '\n').encode('utf-8')


# =============================================================================
# ZIP Building
# =============================================================================

def build_zip(
    output_path: Path,
    metadata_bytes: bytes,
    files: List[Tuple[Path, str]]
) -> None:
    """
    Build a deterministic ZIP file.

    - METADATA.json is first entry
    - Files follow in sorted order
    - All entries have fixed timestamps
    - All entries use DEFLATED compression
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Add METADATA.json first
        info = zipfile.ZipInfo('METADATA.json', date_time=FIXED_TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16  # Unix permissions
        zf.writestr(info, metadata_bytes)

        # 2. Add files in sorted order
        for abs_path, zip_path in files:
            info = zipfile.ZipInfo(zip_path, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16  # Unix permissions
            with open(abs_path, 'rb') as f:
                zf.writestr(info, f.read())


def sha256_bytes(data: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Build a deterministic skill pack ZIP artifact.'
    )
    parser.add_argument(
        '--skill-dir',
        required=True,
        help='Path to the skill directory (relative to repo root)'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Package name (e.g., senior-developer-brain)'
    )
    parser.add_argument(
        '--version',
        required=True,
        help='Package version (e.g., v0.8.2+pack.1)'
    )
    parser.add_argument(
        '--out-dir',
        default='dist',
        help='Output directory (default: dist)'
    )

    args = parser.parse_args()

    # Resolve paths
    try:
        repo_root = get_repo_root()
    except subprocess.CalledProcessError:
        print("ERROR: Not in a git repository", file=sys.stderr)
        return 1

    skill_dir = repo_root / args.skill_dir
    if not skill_dir.is_dir():
        print(f"ERROR: Skill directory not found: {skill_dir}", file=sys.stderr)
        return 1

    out_dir = repo_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get git SHA
    try:
        git_sha = get_head_sha()
    except subprocess.CalledProcessError:
        print("ERROR: Could not get git HEAD SHA", file=sys.stderr)
        return 1

    print("=" * 60)
    print("Skill Pack Builder")
    print("=" * 60)
    print(f"Name:       {args.name}")
    print(f"Version:    {args.version}")
    print(f"Git SHA:    {git_sha}")
    print(f"Skill Dir:  {skill_dir.relative_to(repo_root)}")
    print(f"Output Dir: {out_dir.relative_to(repo_root)}")
    print()

    # Collect files
    try:
        files = collect_files(skill_dir)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Files to include: {len(files)}")
    for _, zip_path in files:
        print(f"  - {zip_path}")
    print()

    # Build metadata
    metadata = build_metadata(
        name=args.name,
        version=args.version,
        git_sha=git_sha,
        skill_dir=str(skill_dir.relative_to(repo_root)),
        files=files
    )
    metadata_bytes = serialize_metadata(metadata)

    # Build ZIP
    zip_filename = f"{args.name}_{args.version}.zip"
    zip_path = out_dir / zip_filename
    build_zip(zip_path, metadata_bytes, files)

    # Compute ZIP SHA256
    with open(zip_path, 'rb') as f:
        zip_sha256 = sha256_bytes(f.read())

    # Write SHA256 file
    sha_filename = f"{zip_filename}.sha256"
    sha_path = out_dir / sha_filename
    sha_content = f"{zip_sha256}  {zip_filename}\n"
    sha_path.write_text(sha_content, encoding='utf-8')

    print("=" * 60)
    print("Build Complete")
    print("=" * 60)
    print(f"ZIP:    {zip_path.relative_to(repo_root)}")
    print(f"SHA:    {sha_path.relative_to(repo_root)}")
    print(f"SHA256: {zip_sha256}")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
