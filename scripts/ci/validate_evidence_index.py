#!/usr/bin/env python3
"""Validate evidence index artifacts are up-to-date.

This is a CI wrapper that runs the index builder in --check mode
and provides clear remediation instructions on failure.

Usage:
    python3 scripts/ci/validate_evidence_index.py

Exit codes:
    0 - Index artifacts are valid and up-to-date
    1 - Index artifacts are missing, drifted, or build errors occurred
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    builder_script = repo_root / "scripts" / "ops" / "build_evidence_index.py"

    if not builder_script.exists():
        print("❌ Evidence index builder not found:")
        print(f"   Expected: {builder_script}")
        return 1

    print("=" * 60)
    print("Evidence Index Validator")
    print("=" * 60)

    # Run builder in --check mode
    result = subprocess.run(
        [sys.executable, str(builder_script), "--check"],
        cwd=repo_root,
        capture_output=False,  # Let output flow through
    )

    if result.returncode != 0:
        print()
        print("=" * 60)
        print("❌ FAILED: Evidence index validation failed")
        print("=" * 60)
        print()
        print("Remediation:")
        print("  Run: python3 scripts/ops/build_evidence_index.py --write")
        print("  Then commit the updated index files:")
        print("    - ops/evidence/INDEX.json")
        print("    - ops/evidence/INDEX.canonical.json")
        print("    - ops/evidence/INDEX.canonical.json.sha256")
        print()
        return 1

    print()
    print("=" * 60)
    print("✅ PASSED: Evidence index is valid and up-to-date")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
