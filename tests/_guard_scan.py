"""Shared scanners for the SAFETY guards (D-14, D-20)."""

from __future__ import annotations

import ast
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

SKIP_DIR_NAMES = frozenset(
    {
        ".teams",
        ".git",
        "node_modules",
        "data",
        ".venv",
        ".pytest_cache",
        ".pytest_tmp",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
        "build",
        "dist",
    }
)

EA_SUFFIXES = frozenset({".ex4", ".ex5", ".mq4", ".mq5", ".mqh"})
MQL_SUFFIXES = frozenset({".mq4", ".mq5", ".mqh"})
WEB_MARKERS = ("http://", "https://", "ftp://", "ws://")
BAD_CALL_NAMES = frozenset({"eval", "exec", "compile", "__import__"})
BAD_OS_ATTRIBUTES = frozenset({"system", "popen", "startfile"})
MQL_ONLINE_NAMES = (
    "WebRequest",
    "SendMail",
    "SendFTP",
    "SendNotification",
    "InternetOpen",
    "InternetConnect",
    "HttpOpenRequest",
    "URLDownloadToFile",
)
ORDER_FUNCTION_RE = re.compile(r"\bOrder(Send|Close|CloseBy|Modify|Delete)\s*\(")
PASSWORD_RE = re.compile(r"(?i)\b(password|passwd|investor[_ ]?password)\s*[=:]\s*\S")
TRADING_LIBRARIES = frozenset(
    {
        "metatrader5",
        "metaapi",
        "ccxt",
        "oandapyv20",
        "ib_insync",
        "ibapi",
        "alpaca",
        "binance",
        "fxcmpy",
        "pymt5",
        "zmq",
        "pyzmq",
    }
)
EA_FILE_MESSAGE = (
    "EA files do not belong in this folder. Keep them in MT4's own folder; "
    "loss-lens never needs a copy."
)


def repository_root() -> Path:
    from losslens.ticks.store import repository_root as find_root

    return find_root()


def iter_repository_files(root: Path) -> Iterator[tuple[str, Path]]:
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not _skip_dir(name)]
        for name in filenames:
            path = Path(dirpath) / name
            yield path.relative_to(root).as_posix(), path


def iter_text_files(root: Path) -> Iterator[tuple[str, str]]:
    for relative, path in iter_repository_files(root):
        text = _read_text(path)
        if text is not None:
            yield relative, text


def _skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.endswith(".egg-info")


def _read_text(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            head = handle.read(4096)
    except OSError:
        return None
    if b"\x00" in head:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _problem(filename: str, line: int, rule: str, message: str) -> str:
    return f"{filename}:{line}: rule {rule}: {message}"


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_imports(
    source: str,
    filename: str,
    allowed: frozenset[str],
    subprocess_allowed: frozenset[str],
) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in allowed:
                    continue
                if name == "subprocess" and filename in subprocess_allowed:
                    continue
                problems.append(
                    _problem(filename, node.lineno, "2a", f"import {name!r} is not approved")
                )
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            name = node.module or ""
            if not name or name.startswith("losslens") or name in allowed:
                continue
            if name == "subprocess" and filename in subprocess_allowed:
                continue
            problems.append(
                _problem(filename, node.lineno, "2a", f"import {name!r} is not approved")
            )
    return problems


def check_dangerous_calls(source: str, filename: str) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in BAD_CALL_NAMES:
            problems.append(
                _problem(filename, node.lineno, "2b", f"call to {func.id!r} is not allowed")
            )
        elif (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "os"
        ):
            attribute = func.attr
            if attribute in BAD_OS_ATTRIBUTES or attribute.startswith(("exec", "spawn")):
                problems.append(
                    _problem(
                        filename,
                        node.lineno,
                        "2b",
                        f"call to os.{attribute} is not allowed",
                    )
                )
    return problems


def check_web_addresses(text: str, filename: str) -> list[str]:
    problems: list[str] = []
    for marker in WEB_MARKERS:
        index = text.find(marker)
        if index >= 0:
            problems.append(
                _problem(filename, _line_of(text, index), "2c", f"web address {marker!r} found")
            )
    return problems


def dependency_names(items: list[str]) -> set[str]:
    names: set[str] = set()
    for item in items:
        name = re.split(r"[<>=!~;\[\]\s]", str(item).strip(), maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    return names


def check_pyproject_dependencies(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    project = data.get("project", {})
    if not isinstance(project, dict):
        return ["pyproject.toml: rule 2d: [project] must be a table"]
    dependencies = project.get("dependencies", [])
    names = dependency_names(dependencies if isinstance(dependencies, list) else [])
    if names != {"pyarrow"}:
        problems.append(
            "pyproject.toml: rule 2d: project.dependencies must be exactly "
            f"{{'pyarrow'}}, found {sorted(names)}"
        )
    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict):
        problems.append("pyproject.toml: rule 2d: optional-dependencies must be a table")
    else:
        if set(optional) != {"dev"}:
            problems.append(
                "pyproject.toml: rule 2d: only the 'dev' optional group is allowed, "
                f"found {sorted(optional)}"
            )
        dev = optional.get("dev", [])
        dev_names = dependency_names(dev if isinstance(dev, list) else [])
        if dev_names != {"pytest", "ruff", "mypy"}:
            problems.append(
                "pyproject.toml: rule 2d: optional-dependencies.dev must be exactly "
                f"{{'mypy', 'pytest', 'ruff'}}, found {sorted(dev_names)}"
            )
    return problems


def check_node_side(package: dict[str, Any], lock: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if package.get("dependencies") != {"dukascopy-node": "1.51.1"}:
        problems.append(
            'package.json: rule 2e: dependencies must be exactly {"dukascopy-node": "1.51.1"}'
        )
    for key in ("devDependencies", "optionalDependencies", "scripts"):
        if key in package:
            problems.append(f"package.json: rule 2e: {key} is not allowed")
    packages = lock.get("packages", {})
    entry = packages.get("node_modules/dukascopy-node", {}) if isinstance(packages, dict) else {}
    if not isinstance(entry, dict) or entry.get("version") != "1.51.1":
        problems.append("package-lock.json: rule 2e: dukascopy-node must be version 1.51.1")
    if not isinstance(entry, dict) or not entry.get("integrity"):
        problems.append("package-lock.json: rule 2e: dukascopy-node needs an integrity hash")
    if isinstance(packages, dict):
        for name, item in packages.items():
            if isinstance(item, dict) and item.get("hasInstallScript"):
                problems.append(f"package-lock.json: rule 2e: {name} has an install script")
    return problems


def check_mql_online(text: str, filename: str) -> list[str]:
    problems: list[str] = []
    for token in MQL_ONLINE_NAMES:
        index = text.find(token)
        if index >= 0:
            problems.append(
                _problem(filename, _line_of(text, index), "2h", f"MQL online call {token!r} found")
            )
    socket_match = re.search(r"(?i)\bsocket\b", text)
    if socket_match:
        problems.append(
            _problem(filename, _line_of(text, socket_match.start()), "2h", "MQL socket found")
        )
    import_match = re.search(r"(?m)^\s*#import\b", text)
    if import_match:
        problems.append(
            _problem(filename, _line_of(text, import_match.start()), "2h", "MQL #import found")
        )
    return problems


def check_ea_files(root: Path) -> list[str]:
    problems: list[str] = []
    for relative, path in iter_repository_files(root):
        if path.suffix.lower() not in EA_SUFFIXES:
            continue
        if relative.startswith("mql4/"):
            continue
        problems.append(f"{relative}: rule 2i: {EA_FILE_MESSAGE}")
    return problems


def check_order_functions(text: str, filename: str, allowed: frozenset[str]) -> list[str]:
    if filename in allowed:
        return []
    problems: list[str] = []
    for match in ORDER_FUNCTION_RE.finditer(text):
        problems.append(
            _problem(
                filename,
                _line_of(text, match.start()),
                "3a",
                f"order function {match.group(0)!r} found",
            )
        )
    return problems


def check_trading_dependencies(pyproject: dict[str, Any], package: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    project = pyproject.get("project", {})
    if isinstance(project, dict):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            names |= dependency_names(dependencies)
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group in optional.values():
                if isinstance(group, list):
                    names |= dependency_names(group)
    for key in ("dependencies", "devDependencies", "optionalDependencies"):
        group = package.get(key, {})
        if isinstance(group, dict):
            names |= {str(name).lower() for name in group}
    problems: list[str] = []
    for name in sorted(names & TRADING_LIBRARIES):
        problems.append(f"rule 3b: trading library {name!r} found in a dependency file")
    return problems


def check_passwords(text: str, filename: str) -> list[str]:
    problems: list[str] = []
    for match in PASSWORD_RE.finditer(text):
        problems.append(
            _problem(
                filename,
                _line_of(text, match.start()),
                "3c",
                "stored password or investor password found",
            )
        )
    return problems
