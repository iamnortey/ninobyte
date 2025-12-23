#!/usr/bin/env python3
"""
NetOpsPack Governance Validator (v0.9.0)

Validates NetOpsPack security posture and governance requirements:
- Directory structure and governance docs exist
- No forbidden networking imports (stdlib-only, no network access)
- No shell execution (subprocess, os.system, os.popen)
- No file writes (stdout-only output)
- CLI contract smoke test (canonical command produces valid JSON)

Usage:
    python scripts/ci/validate_netopspack.py

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
# NetOpsPack Forbidden Import Sets
# =============================================================================

# Networking modules FORBIDDEN in NetOpsPack (same pattern as AirGap/OpsPack)
NETOPSPACK_FORBIDDEN_NETWORK_MODULES: Set[str] = {
    'socket', 'socketserver',
    'ssl',  # SSL is network-related
    'http', 'http.client', 'http.server',
    'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
    'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib',
    'aiohttp', 'httpx', 'requests', 'urllib3',
    'websocket', 'websockets',
    'paramiko', 'fabric',
}

# Shell/process execution modules FORBIDDEN in NetOpsPack
NETOPSPACK_FORBIDDEN_SHELL_MODULES: Set[str] = {
    'subprocess',
    'pty',
}

# File write methods to detect
NETOPSPACK_FORBIDDEN_WRITE_METHODS: Set[str] = {
    'write_text', 'write_bytes', 'mkdir', 'makedirs',
    'unlink', 'remove', 'rmdir', 'rename', 'replace',
    'touch', 'symlink_to', 'hardlink_to',
}


def scan_imports_ast(filepath: Path) -> List[Tuple[str, int, str]]:
    """
    Scan a Python file for imports using AST (Abstract Syntax Tree).

    Returns:
        List of (module_name, line_number, import_statement) tuples
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
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
                # Also check for submodule imports like 'from http.client import ...'
                parts = node.module.split('.')
                for i in range(len(parts)):
                    parent = '.'.join(parts[:i+1])
                    if parent != node.module:
                        imports.append((parent, node.lineno, f"from {node.module} import ..."))

    return imports


# =============================================================================
# Validation Functions
# =============================================================================

def validate_netopspack_structure(netopspack_root: Path) -> bool:
    """
    Validate NetOpsPack directory structure and governance docs.
    """
    if not netopspack_root.exists():
        log_fail(f"NetOpsPack directory not found: {_rel_path(netopspack_root)}")
        return False

    all_passed = True

    # Required governance files
    required_files = [
        ('README.md', 'NetOpsPack README'),
        ('SECURITY.md', 'NetOpsPack Security Policy'),
        ('pyproject.toml', 'NetOpsPack pyproject.toml'),
        ('src/netopspack/__main__.py', 'NetOpsPack entry point'),
    ]

    for rel_path, description in required_files:
        filepath = netopspack_root / rel_path
        if not filepath.exists():
            log_fail(f"Missing {description}: {_rel_path(filepath)}")
            all_passed = False
        else:
            log_ok(f"{description} exists")

    return all_passed


def validate_netopspack_no_networking(netopspack_src: Path) -> bool:
    """
    Validate that NetOpsPack source has no networking imports.

    Uses AST-based scanning to reduce false positives.
    This is a HARD GATE - CI fails if networking imports are found.
    """
    if not netopspack_src.exists():
        log_info(f"NetOpsPack source not found (skipping): {_rel_path(netopspack_src)}")
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in netopspack_src.rglob('*.py'):
        # Skip test files - they may import networking for mocking
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        imports = scan_imports_ast(py_file)

        for module, lineno, stmt in imports:
            module_parts = module.split('.')
            for i in range(len(module_parts)):
                check_module = '.'.join(module_parts[:i+1])
                if check_module in NETOPSPACK_FORBIDDEN_NETWORK_MODULES:
                    violations.append(
                        f"{py_file.relative_to(netopspack_src)}:{lineno}: {stmt} "
                        f"(forbidden: {check_module})"
                    )
                    all_passed = False
                    break

    if violations:
        log_fail("NetOpsPack networking import violations found:")
        for v in violations[:20]:
            print(f"    {v}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
        print("\n    NetOpsPack security policy: NO networking imports (stdlib-only, offline)")
        return False

    log_ok("NetOpsPack: No forbidden networking imports found")
    return True


def validate_netopspack_no_shell_execution(netopspack_src: Path) -> bool:
    """
    Validate that NetOpsPack source never uses shell execution.

    Checks for:
    - subprocess import (completely forbidden)
    - os.system() and os.popen() calls
    - pty import (forbidden)

    This is a HARD GATE - CI fails if violations are found.
    """
    if not netopspack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in netopspack_src.rglob('*.py'):
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        # Check imports for subprocess/pty
        imports = scan_imports_ast(py_file)
        for module, lineno, stmt in imports:
            if module in NETOPSPACK_FORBIDDEN_SHELL_MODULES:
                violations.append(
                    f"{py_file.relative_to(netopspack_src)}:{lineno}: {stmt} "
                    f"(forbidden: {module})"
                )
                all_passed = False

        # Also check for os.system/os.popen calls
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(netopspack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for os.system() and os.popen()
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'os' and func_name in ('system', 'popen'):
                            violations.append(
                                f"{rel_path}:{node.lineno}: "
                                f"os.{func_name}() is forbidden"
                            )
                            all_passed = False

    if violations:
        log_fail("NetOpsPack shell execution violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    NetOpsPack security policy: NO shell execution (subprocess, os.system, os.popen, pty)")
        return False

    log_ok("NetOpsPack: No shell execution violations found")
    return True


def validate_netopspack_no_file_writes(netopspack_src: Path) -> bool:
    """
    Validate that NetOpsPack source has no file write patterns.

    Basic heuristic checks for:
    - open() with 'w', 'a', 'x' modes
    - pathlib write_text(), write_bytes(), mkdir(), unlink(), etc.

    This is a HARD GATE - CI fails if violations are found.
    """
    if not netopspack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in netopspack_src.rglob('*.py'):
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(netopspack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() with write modes
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check mode argument (positional or keyword)
                    mode = None
                    if len(node.args) >= 2:
                        mode_arg = node.args[1]
                        if isinstance(mode_arg, ast.Constant):
                            mode = mode_arg.value
                    for kw in node.keywords:
                        if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                            mode = kw.value.value
                    if mode and any(c in mode for c in 'wax'):
                        violations.append(
                            f"{rel_path}:{node.lineno}: open() with write mode '{mode}'"
                        )
                        all_passed = False

                # Check for pathlib write methods and filesystem mutation
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in NETOPSPACK_FORBIDDEN_WRITE_METHODS:
                        violations.append(
                            f"{rel_path}:{node.lineno}: {node.func.attr}() call"
                        )
                        all_passed = False

    if violations:
        log_fail("NetOpsPack file write violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    NetOpsPack security policy: NO file writes (stdout-only output)")
        return False

    log_ok("NetOpsPack: No file write violations found")
    return True


def validate_netopspack_cli_contract(netopspack_root: Path) -> bool:
    """
    Validate NetOpsPack CLI contract via subprocess smoke test.

    Runs canonical command and verifies:
    - Exit code 0
    - Output parses as JSON
    - Contains "format": "syslog"
    - Contains "generated_at_utc": "2025-01-01T00:00:00Z"
    """
    fixture_path = netopspack_root / 'tests' / 'fixtures' / 'syslog.log'
    if not fixture_path.exists():
        log_fail(f"Fixture not found for CLI smoke test: {_rel_path(fixture_path)}")
        return False

    # Run canonical command
    cmd = [
        sys.executable,
        '-m',
        'netopspack',
        'diagnose',
        '--format', 'syslog',
        '--input', str(fixture_path),
        '--fixed-time', '2025-01-01T00:00:00Z',
        '--limit', '1',
    ]

    env = {
        **dict(os.environ),
        'PYTHONPATH': str(netopspack_root / 'src'),
    }

    try:
        result = subprocess.run(
            cmd,
            cwd=netopspack_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        log_fail("NetOpsPack CLI smoke test timed out (30s)")
        return False
    except Exception as e:
        log_fail(f"NetOpsPack CLI smoke test failed to run: {e}")
        return False

    # Check exit code
    if result.returncode != 0:
        log_fail(f"NetOpsPack CLI smoke test exit code {result.returncode} (expected 0)")
        if result.stderr:
            print(f"    stderr: {result.stderr[:500]}")
        return False

    # Check output parses as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        log_fail(f"NetOpsPack CLI smoke test output is not valid JSON: {e}")
        print(f"    stdout (first 500 chars): {result.stdout[:500]}")
        return False

    # Check required fields
    all_passed = True

    if output.get('format') != 'syslog':
        log_fail(f"NetOpsPack CLI smoke test: expected 'format': 'syslog', got '{output.get('format')}'")
        all_passed = False

    if output.get('generated_at_utc') != '2025-01-01T00:00:00Z':
        log_fail(
            f"NetOpsPack CLI smoke test: expected 'generated_at_utc': '2025-01-01T00:00:00Z', "
            f"got '{output.get('generated_at_utc')}'"
        )
        all_passed = False

    if all_passed:
        log_ok("NetOpsPack CLI contract smoke test passed")

    return all_passed


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    """Run all NetOpsPack governance validations."""
    global _REPO_ROOT

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    _REPO_ROOT = repo_root

    print(f"\n{'='*60}")
    print("NetOpsPack Governance Validation (v0.9.0)")
    print(f"{'='*60}\n")

    all_passed = True

    # NetOpsPack canonical path
    netopspack_root = repo_root / 'products' / 'netopspack'
    netopspack_src = netopspack_root / 'src' / 'netopspack'

    # 1. Directory structure and governance docs
    print("--- Directory + Governance Docs ---")
    if not validate_netopspack_structure(netopspack_root):
        all_passed = False

    # 2. Security posture: no networking imports
    print("\n--- Security Posture: No Networking ---")
    if not validate_netopspack_no_networking(netopspack_src):
        all_passed = False

    # 3. Security posture: no shell execution
    print("\n--- Security Posture: No Shell Execution ---")
    if not validate_netopspack_no_shell_execution(netopspack_src):
        all_passed = False

    # 4. No file write guarantee
    print("\n--- No File Write Guarantee ---")
    if not validate_netopspack_no_file_writes(netopspack_src):
        all_passed = False

    # 5. CLI contract smoke test
    print("\n--- CLI Contract Smoke Test ---")
    if not validate_netopspack_cli_contract(netopspack_root):
        all_passed = False

    # Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ NetOpsPack governance validation PASSED")
        return 0
    else:
        print("❌ NetOpsPack governance validation FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
