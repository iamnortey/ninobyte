#!/usr/bin/env python3
"""
CompliancePack Governance Validator (v0.10.0)

Validates CompliancePack security posture and governance requirements:
- Directory structure and governance docs exist
- No forbidden networking imports (stdlib-only, no network access)
- No shell execution (subprocess, os.system, os.popen)
- No file writes (stdout-only output)
- CLI contract smoke test (canonical command produces valid output)

Usage:
    python scripts/ci/validate_compliancepack.py

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple


# Global repo root for relative path formatting
_REPO_ROOT: Path = Path(".")


def _rel_path(p: Path) -> str:
    """Convert a path to repo-relative format for clean logging output."""
    try:
        return "./" + str(p.relative_to(_REPO_ROOT))
    except ValueError:
        return "./" + p.name


def log_ok(msg: str) -> None:
    print(f"✅ {msg}")


def log_fail(msg: str) -> None:
    print(f"❌ {msg}")


def log_info(msg: str) -> None:
    print(f"ℹ️  {msg}")


# =============================================================================
# CompliancePack Forbidden Import Sets
# =============================================================================

# Networking modules FORBIDDEN in CompliancePack
COMPLIANCEPACK_FORBIDDEN_NETWORK_MODULES: Set[str] = {
    "socket", "socketserver",
    "ssl",
    "http", "http.client", "http.server",
    "urllib", "urllib.request", "urllib.parse", "urllib.error",
    "ftplib", "smtplib", "poplib", "imaplib", "nntplib", "telnetlib",
    "aiohttp", "httpx", "requests", "urllib3",
    "websocket", "websockets",
    "paramiko", "fabric",
}

# Shell/process execution modules FORBIDDEN in CompliancePack
COMPLIANCEPACK_FORBIDDEN_SHELL_MODULES: Set[str] = {
    "subprocess",
    "pty",
}

# File write methods to detect
COMPLIANCEPACK_FORBIDDEN_WRITE_METHODS: Set[str] = {
    "write_text", "write_bytes", "mkdir", "makedirs",
    "unlink", "remove", "rmdir", "rename", "replace",
    "touch", "symlink_to", "hardlink_to",
}


def scan_imports_ast(filepath: Path) -> List[Tuple[str, int, str]]:
    """
    Scan a Python file for imports using AST (Abstract Syntax Tree).

    Returns:
        List of (module_name, line_number, import_statement) tuples
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports: List[Tuple[str, int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno, f"from {node.module} import ..."))
                parts = node.module.split(".")
                for i in range(len(parts)):
                    parent = ".".join(parts[: i + 1])
                    if parent != node.module:
                        imports.append((parent, node.lineno, f"from {node.module} import ..."))

    return imports


# =============================================================================
# Validation Functions
# =============================================================================


def validate_compliancepack_structure(compliancepack_root: Path) -> bool:
    """
    Validate CompliancePack directory structure and governance docs.
    """
    if not compliancepack_root.exists():
        log_fail(f"CompliancePack directory not found: {_rel_path(compliancepack_root)}")
        return False

    all_passed = True

    # Required governance files
    required_files = [
        ("README.md", "CompliancePack README"),
        ("SECURITY.md", "CompliancePack Security Policy"),
        ("pyproject.toml", "CompliancePack pyproject.toml"),
        ("src/compliancepack/__main__.py", "CompliancePack entry point"),
    ]

    for rel_path, description in required_files:
        filepath = compliancepack_root / rel_path
        if not filepath.exists():
            log_fail(f"Missing {description}: {_rel_path(filepath)}")
            all_passed = False
        else:
            log_ok(f"{description} exists")

    return all_passed


def validate_compliancepack_no_networking(compliancepack_src: Path) -> bool:
    """
    Validate that CompliancePack source has no networking imports.

    Uses AST-based scanning to reduce false positives.
    This is a HARD GATE - CI fails if networking imports are found.
    """
    if not compliancepack_src.exists():
        log_info(f"CompliancePack source not found (skipping): {_rel_path(compliancepack_src)}")
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in compliancepack_src.rglob("*.py"):
        # Skip test files - they may import networking for mocking
        if "test" in py_file.name.lower() or "tests" in py_file.parts:
            continue

        imports = scan_imports_ast(py_file)

        for module, lineno, stmt in imports:
            module_parts = module.split(".")
            for i in range(len(module_parts)):
                check_module = ".".join(module_parts[: i + 1])
                if check_module in COMPLIANCEPACK_FORBIDDEN_NETWORK_MODULES:
                    violations.append(
                        f"{py_file.relative_to(compliancepack_src)}:{lineno}: {stmt} "
                        f"(forbidden: {check_module})"
                    )
                    all_passed = False
                    break

    if violations:
        log_fail("CompliancePack networking import violations found:")
        for v in violations[:20]:
            print(f"    {v}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
        print("\n    CompliancePack security policy: NO networking imports (stdlib-only, offline)")
        return False

    log_ok("CompliancePack: No forbidden networking imports found")
    return True


def validate_compliancepack_no_shell_execution(compliancepack_src: Path) -> bool:
    """
    Validate that CompliancePack source never uses shell execution.

    Checks for:
    - subprocess import (completely forbidden)
    - os.system() and os.popen() calls
    - pty import (forbidden)

    This is a HARD GATE - CI fails if violations are found.
    """
    if not compliancepack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in compliancepack_src.rglob("*.py"):
        if "test" in py_file.name.lower() or "tests" in py_file.parts:
            continue

        # Check imports for subprocess/pty
        imports = scan_imports_ast(py_file)
        for module, lineno, stmt in imports:
            if module in COMPLIANCEPACK_FORBIDDEN_SHELL_MODULES:
                violations.append(
                    f"{py_file.relative_to(compliancepack_src)}:{lineno}: {stmt} "
                    f"(forbidden: {module})"
                )
                all_passed = False

        # Also check for os.system/os.popen calls
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(compliancepack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for os.system() and os.popen()
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "os" and func_name in ("system", "popen"):
                            violations.append(
                                f"{rel_path}:{node.lineno}: "
                                f"os.{func_name}() is forbidden"
                            )
                            all_passed = False

    if violations:
        log_fail("CompliancePack shell execution violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    CompliancePack security policy: NO shell execution (subprocess, os.system, os.popen, pty)")
        return False

    log_ok("CompliancePack: No shell execution violations found")
    return True


def validate_compliancepack_no_file_writes(compliancepack_src: Path) -> bool:
    """
    Validate that CompliancePack source has no file write patterns.

    Basic heuristic checks for:
    - open() with 'w', 'a', 'x' modes
    - pathlib write_text(), write_bytes(), mkdir(), unlink(), etc.

    This is a HARD GATE - CI fails if violations are found.
    """
    if not compliancepack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in compliancepack_src.rglob("*.py"):
        if "test" in py_file.name.lower() or "tests" in py_file.parts:
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(compliancepack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() with write modes
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    # Check mode argument (positional or keyword)
                    mode = None
                    if len(node.args) >= 2:
                        mode_arg = node.args[1]
                        if isinstance(mode_arg, ast.Constant):
                            mode = mode_arg.value
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                            mode = kw.value.value
                    if mode and any(c in mode for c in "wax"):
                        violations.append(
                            f"{rel_path}:{node.lineno}: open() with write mode '{mode}'"
                        )
                        all_passed = False

                # Check for pathlib write methods and filesystem mutation
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in COMPLIANCEPACK_FORBIDDEN_WRITE_METHODS:
                        violations.append(
                            f"{rel_path}:{node.lineno}: {node.func.attr}() call"
                        )
                        all_passed = False

    if violations:
        log_fail("CompliancePack file write violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    CompliancePack security policy: NO file writes (stdout-only output)")
        return False

    log_ok("CompliancePack: No file write violations found")
    return True


def validate_compliancepack_cli_contract(compliancepack_root: Path) -> bool:
    """
    Validate CompliancePack CLI contract via subprocess smoke test.

    Runs canonical command FROM PRODUCT DIRECTORY and verifies:
    - --help succeeds
    - check --help succeeds
    """
    # Run --help
    cmd = [
        sys.executable,
        "-m",
        "compliancepack",
        "--help",
    ]

    env = {
        **dict(os.environ),
        "PYTHONPATH": str(compliancepack_root / "src"),
    }

    try:
        result = subprocess.run(
            cmd,
            cwd=compliancepack_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        log_fail("CompliancePack CLI --help timed out (30s)")
        return False
    except Exception as e:
        log_fail(f"CompliancePack CLI --help failed to run: {e}")
        return False

    if result.returncode != 0:
        log_fail(f"CompliancePack CLI --help exit code {result.returncode} (expected 0)")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
        return False

    # Run check --help
    cmd = [
        sys.executable,
        "-m",
        "compliancepack",
        "check",
        "--help",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=compliancepack_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        log_fail("CompliancePack CLI check --help timed out (30s)")
        return False
    except Exception as e:
        log_fail(f"CompliancePack CLI check --help failed to run: {e}")
        return False

    if result.returncode != 0:
        log_fail(f"CompliancePack CLI check --help exit code {result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
        return False

    # Verify expected arguments are in help
    if "--input" not in result.stdout:
        log_fail("CompliancePack CLI check --help missing --input argument")
        return False

    if "--fixed-time" not in result.stdout:
        log_fail("CompliancePack CLI check --help missing --fixed-time argument")
        return False

    log_ok("CompliancePack CLI contract (product-local) passed")
    return True


def validate_compliancepack_full_contract(compliancepack_root: Path) -> bool:
    """
    Validate CompliancePack full contract with fixtures.

    Runs canonical check command with fixtures and verifies:
    - Output parses as JSON
    - format == "compliancepack.check.v1"
    - policy_count > 0
    - findings is present
    """
    fixtures = compliancepack_root / "tests" / "fixtures"
    input_file = fixtures / "sample_input.txt"
    policy_file = fixtures / "policy_v1.json"

    if not input_file.exists() or not policy_file.exists():
        log_info("CompliancePack fixtures not found, skipping full contract test")
        return True

    cmd = [
        sys.executable,
        "-m",
        "compliancepack",
        "check",
        "--input", str(input_file),
        "--policy", str(policy_file),
        "--fixed-time", "2025-01-01T00:00:00Z",
    ]

    env = {
        **dict(os.environ),
        "PYTHONPATH": str(compliancepack_root / "src"),
    }

    try:
        result = subprocess.run(
            cmd,
            cwd=compliancepack_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        log_fail("CompliancePack full contract test timed out (30s)")
        return False
    except Exception as e:
        log_fail(f"CompliancePack full contract test failed to run: {e}")
        return False

    if result.returncode != 0:
        log_fail(f"CompliancePack full contract test exit code {result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
        return False

    # Parse JSON output
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        log_fail(f"CompliancePack full contract test: invalid JSON output: {e}")
        return False

    # Validate format
    if output.get("format") != "compliancepack.check.v1":
        log_fail(f"CompliancePack: unexpected format '{output.get('format')}'")
        return False

    # Validate policy_count > 0
    policy_count = output.get("summary", {}).get("policy_count", 0)
    if policy_count == 0:
        log_fail("CompliancePack: policy_count is 0")
        return False

    # Validate findings is present
    if "findings" not in output:
        log_fail("CompliancePack: 'findings' field missing from output")
        return False

    log_ok(f"CompliancePack full contract passed ({policy_count} policies, {len(output['findings'])} findings)")
    return True


def validate_compliancepack_pytest(compliancepack_root: Path) -> bool:
    """
    Validate CompliancePack pytest suite passes.

    This runs the product-local pytest and validates all tests pass.
    """
    if not compliancepack_root.exists():
        log_info("CompliancePack not found, skipping pytest validation")
        return True

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--tb=short",
    ]

    env = {
        **dict(os.environ),
        "PYTHONPATH": str(compliancepack_root / "src"),
    }

    try:
        result = subprocess.run(
            cmd,
            cwd=compliancepack_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        log_fail("CompliancePack pytest timed out (120s)")
        return False
    except Exception as e:
        log_fail(f"CompliancePack pytest failed to run: {e}")
        return False

    # Parse test results from output
    if result.returncode != 0:
        log_fail(f"CompliancePack pytest failed (exit code {result.returncode})")
        # Show last 10 lines of output
        lines = result.stdout.strip().split("\n")
        for line in lines[-10:]:
            print(f"    {line}")
        return False

    # Extract passed count from output
    import re
    match = re.search(r"(\d+) passed", result.stdout)
    if match:
        passed_count = int(match.group(1))
        log_ok(f"CompliancePack pytest passed ({passed_count} tests)")
    else:
        log_ok("CompliancePack pytest passed")

    return True


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """Run all CompliancePack governance validations."""
    global _REPO_ROOT

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    _REPO_ROOT = repo_root

    print(f"\n{'=' * 60}")
    print("CompliancePack Governance Validation (v0.10.0)")
    print(f"{'=' * 60}\n")

    all_passed = True

    # CompliancePack canonical path
    compliancepack_root = repo_root / "products" / "compliancepack"
    compliancepack_src = compliancepack_root / "src" / "compliancepack"

    # 1. Directory structure and governance docs
    print("--- [1/7] Directory + Governance Docs ---")
    if not validate_compliancepack_structure(compliancepack_root):
        all_passed = False

    # 2. Security posture: no networking imports
    print("\n--- [2/7] Security Posture: No Networking ---")
    if not validate_compliancepack_no_networking(compliancepack_src):
        all_passed = False

    # 3. Security posture: no shell execution
    print("\n--- [3/7] Security Posture: No Shell Execution ---")
    if not validate_compliancepack_no_shell_execution(compliancepack_src):
        all_passed = False

    # 4. No file write guarantee
    print("\n--- [4/7] No File Write Guarantee ---")
    if not validate_compliancepack_no_file_writes(compliancepack_src):
        all_passed = False

    # 5. CLI contract smoke test (product-local)
    print("\n--- [5/7] CLI Contract (Product-Local) ---")
    if not validate_compliancepack_cli_contract(compliancepack_root):
        all_passed = False

    # 6. Full contract test with fixtures
    print("\n--- [6/7] Full Contract Test ---")
    if not validate_compliancepack_full_contract(compliancepack_root):
        all_passed = False

    # 7. Pytest suite
    print("\n--- [7/7] Pytest Suite ---")
    if not validate_compliancepack_pytest(compliancepack_root):
        all_passed = False

    # Summary
    print(f"\n{'=' * 60}")
    if all_passed:
        print("✅ CompliancePack governance validation PASSED")
        return 0
    else:
        print("❌ CompliancePack governance validation FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
