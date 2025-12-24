"""
CompliancePack non-goals contract tests.

Validates that CompliancePack source code does NOT contain:
- Networking imports (socket, http, urllib, requests, etc.)
- Shell execution (subprocess, os.system, os.popen, pty)
- File write operations (open(...,'w'), Path.write_text, mkdir, etc.)

These are hard security constraints enforced by CI.
"""

import ast
from pathlib import Path
from typing import List, Set, Tuple

import pytest


# Source directory for CompliancePack
SRC_DIR = Path(__file__).parent.parent / "src" / "compliancepack"


# Forbidden networking modules
FORBIDDEN_NETWORK_MODULES: Set[str] = {
    "socket", "socketserver",
    "ssl",
    "http", "http.client", "http.server",
    "urllib", "urllib.request", "urllib.parse", "urllib.error",
    "ftplib", "smtplib", "poplib", "imaplib", "nntplib", "telnetlib",
    "aiohttp", "httpx", "requests", "urllib3",
    "websocket", "websockets",
    "paramiko", "fabric",
}

# Forbidden shell execution modules
FORBIDDEN_SHELL_MODULES: Set[str] = {
    "subprocess",
    "pty",
}

# Forbidden file write methods
FORBIDDEN_WRITE_METHODS: Set[str] = {
    "write_text", "write_bytes", "mkdir", "makedirs",
    "unlink", "remove", "rmdir", "rename", "replace",
    "touch", "symlink_to", "hardlink_to",
}


def scan_imports_ast(filepath: Path) -> List[Tuple[str, int, str]]:
    """Scan a Python file for imports using AST."""
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


def get_source_files() -> List[Path]:
    """Get all Python source files (excluding tests)."""
    return list(SRC_DIR.rglob("*.py"))


class TestNoNetworkingImports:
    """Verify no networking imports in source code."""

    def test_no_forbidden_network_imports(self):
        """Source files must not import networking modules."""
        violations = []

        for py_file in get_source_files():
            imports = scan_imports_ast(py_file)
            for module, lineno, stmt in imports:
                module_parts = module.split(".")
                for i in range(len(module_parts)):
                    check_module = ".".join(module_parts[: i + 1])
                    if check_module in FORBIDDEN_NETWORK_MODULES:
                        violations.append(
                            f"{py_file.name}:{lineno}: {stmt} (forbidden: {check_module})"
                        )
                        break

        assert not violations, (
            "Networking imports found:\n" + "\n".join(f"  - {v}" for v in violations)
        )


class TestNoShellExecution:
    """Verify no shell execution in source code."""

    def test_no_forbidden_shell_imports(self):
        """Source files must not import shell execution modules."""
        violations = []

        for py_file in get_source_files():
            imports = scan_imports_ast(py_file)
            for module, lineno, stmt in imports:
                if module in FORBIDDEN_SHELL_MODULES:
                    violations.append(
                        f"{py_file.name}:{lineno}: {stmt} (forbidden: {module})"
                    )

        assert not violations, (
            "Shell execution imports found:\n" + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_os_system_calls(self):
        """Source files must not call os.system() or os.popen()."""
        violations = []

        for py_file in get_source_files():
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == "os" and func_name in ("system", "popen"):
                                violations.append(
                                    f"{py_file.name}:{node.lineno}: os.{func_name}() is forbidden"
                                )

        assert not violations, (
            "os.system/popen calls found:\n" + "\n".join(f"  - {v}" for v in violations)
        )


class TestNoFileWrites:
    """Verify no file write operations in source code."""

    def test_no_open_write_mode(self):
        """Source files must not use open() with write modes."""
        violations = []

        for py_file in get_source_files():
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "open":
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
                                f"{py_file.name}:{node.lineno}: open() with write mode '{mode}'"
                            )

        assert not violations, (
            "File write operations found:\n" + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_pathlib_write_methods(self):
        """Source files must not use pathlib write methods."""
        violations = []

        for py_file in get_source_files():
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in FORBIDDEN_WRITE_METHODS:
                            violations.append(
                                f"{py_file.name}:{node.lineno}: {node.func.attr}() is forbidden"
                            )

        assert not violations, (
            "Pathlib write methods found:\n" + "\n".join(f"  - {v}" for v in violations)
        )
