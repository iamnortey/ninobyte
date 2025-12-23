"""
Static security assertions for OpsPack.

Verifies that the codebase does not contain forbidden patterns:
- No network imports
- No shell execution

These are static checks, not runtime hooks.
"""

import ast
import sys
from pathlib import Path

import pytest

OPSPACK_SRC = Path(__file__).parent.parent / "src" / "opspack"

# Forbidden network-related imports
FORBIDDEN_NETWORK_MODULES = {
    "socket",
    "http",
    "urllib",
    "urllib.request",
    "urllib.parse",
    "urllib.error",
    "http.client",
    "http.server",
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "telnetlib",
    "requests",
    "httpx",
    "aiohttp",
    "websocket",
    "websockets",
}

# Forbidden shell execution patterns
FORBIDDEN_SHELL_FUNCTIONS = {
    "os.system",
    "os.popen",
    "os.spawn",
    "os.spawnl",
    "os.spawnle",
    "os.spawnlp",
    "os.spawnlpe",
    "os.spawnv",
    "os.spawnve",
    "os.spawnvp",
    "os.spawnvpe",
    "subprocess.call",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.check_call",
    "subprocess.check_output",
}


def get_python_files():
    """Get all Python files in OpsPack source."""
    return list(OPSPACK_SRC.glob("**/*.py"))


class TestNoNetworkImports:
    """Verify no network-related imports exist."""

    def test_no_forbidden_imports(self):
        """No forbidden network modules should be imported."""
        violations = []

        for py_file in get_python_files():
            content = py_file.read_text()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in FORBIDDEN_NETWORK_MODULES:
                            violations.append(
                                f"{py_file.name}:{node.lineno} imports '{alias.name}'"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in FORBIDDEN_NETWORK_MODULES:
                        violations.append(
                            f"{py_file.name}:{node.lineno} imports from '{node.module}'"
                        )

        assert not violations, f"Forbidden network imports found:\n" + "\n".join(violations)


class TestNoShellExecution:
    """Verify no shell execution patterns exist."""

    def test_no_os_system(self):
        """No os.system calls should exist."""
        violations = []

        for py_file in get_python_files():
            content = py_file.read_text()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for os.system, os.popen, etc.
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            full_name = f"{node.func.value.id}.{node.func.attr}"
                            if full_name in FORBIDDEN_SHELL_FUNCTIONS:
                                violations.append(
                                    f"{py_file.name}:{node.lineno} calls '{full_name}'"
                                )

        assert not violations, f"Forbidden shell calls found:\n" + "\n".join(violations)

    def test_no_subprocess_with_shell_true(self):
        """No subprocess calls with shell=True should exist."""
        violations = []

        for py_file in get_python_files():
            content = py_file.read_text()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for shell=True in any call
                    for keyword in node.keywords:
                        if keyword.arg == "shell":
                            if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                violations.append(
                                    f"{py_file.name}:{node.lineno} uses shell=True"
                                )

        assert not violations, f"shell=True usage found:\n" + "\n".join(violations)


class TestNoEval:
    """Verify no eval/exec usage."""

    def test_no_eval_or_exec(self):
        """No eval() or exec() calls should exist."""
        violations = []

        for py_file in get_python_files():
            content = py_file.read_text()
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ("eval", "exec"):
                            violations.append(
                                f"{py_file.name}:{node.lineno} calls '{node.func.id}'"
                            )

        assert not violations, f"eval/exec usage found:\n" + "\n".join(violations)


class TestSourceFileIntegrity:
    """Basic source file checks."""

    def test_all_files_parseable(self):
        """All Python files should be syntactically valid."""
        errors = []

        for py_file in get_python_files():
            content = py_file.read_text()
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{py_file.name}: {e}")

        assert not errors, f"Syntax errors found:\n" + "\n".join(errors)

    def test_source_files_exist(self):
        """Required source files should exist."""
        required = [
            "__init__.py",
            "__main__.py",
            "cli.py",
            "redact.py",
            "model.py",
        ]

        for filename in required:
            filepath = OPSPACK_SRC / filename
            assert filepath.exists(), f"Required file missing: {filename}"
