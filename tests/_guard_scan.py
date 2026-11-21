"""Shared scanners for the SAFETY guards (D-14, D-20)."""

from __future__ import annotations

import ast
import importlib.util
import os
import re
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

ROOT_SKIP_DIRS = frozenset({".teams", "data", "build", "dist"})
ANY_SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        ".pytest_cache",
        ".pytest_tmp",
        ".ruff_cache",
        ".mypy_cache",
        "__pycache__",
    }
)

EA_SUFFIXES = frozenset({".ex4", ".ex5", ".mq4", ".mq5", ".mqh"})
MQL_SUFFIXES = frozenset({".mq4", ".mq5", ".mqh"})
WEB_ADDRESS_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://")
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
MQL_ACCOUNT_NAMES = (
    "AccountNumber",
    "AccountName",
    "AccountCompany",
    "AccountServer",
    "ACCOUNT_LOGIN",
    "ACCOUNT_NAME",
    "ACCOUNT_SERVER",
    "ACCOUNT_COMPANY",
)
IS_TESTING_RE = re.compile(
    r"if\s*\(\s*!\s*IsTesting\s*\(\s*\)\s*\)\s*return\s*\(\s*INIT_FAILED\s*\)\s*;"
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
PROJECT_DEPENDENCIES = frozenset({"pyarrow", "smac", "configspace"})
EA_FILE_MESSAGE = (
    "EA files do not belong in this folder. Keep them in MT4's own folder; "
    "loss-lens never needs a copy."
)


def repository_root() -> Path:
    from losslens.ticks.store import repository_root as find_root

    return find_root()


def iter_repository_files(root: Path, *, include_teams: bool = False) -> Iterator[tuple[str, Path]]:
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        parent_is_root = Path(dirpath) == root
        dirnames[:] = [
            name
            for name in dirnames
            if not _skip_dir(name, parent_is_root=parent_is_root, include_teams=include_teams)
        ]
        for name in filenames:
            path = Path(dirpath) / name
            yield path.relative_to(root).as_posix(), path


def iter_text_files(root: Path) -> Iterator[tuple[str, str]]:
    for relative, path in iter_repository_files(root):
        text = _read_text(path)
        if text is not None:
            yield relative, text


def _skip_dir(name: str, *, parent_is_root: bool, include_teams: bool) -> bool:
    if name in ANY_SKIP_DIRS or name.endswith(".egg-info"):
        return True
    if parent_is_root and name in ROOT_SKIP_DIRS:
        return not (include_teams and name == ".teams")
    return False


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


def _is_ours(name: str) -> bool:
    return name == "losslens" or name.startswith("losslens.")


def _is_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _forbidden_os(attribute: str) -> bool:
    return attribute in BAD_OS_ATTRIBUTES or attribute.startswith(("exec", "spawn"))


def check_imports(
    source: str,
    filename: str,
    allowed: frozenset[str],
    subprocess_allowed: Mapping[str, int],
) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if _is_ours(name) or name in allowed:
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
            if not name or _is_ours(name):
                continue
            if name not in allowed:
                if name == "subprocess" and filename in subprocess_allowed:
                    continue
                problems.append(
                    _problem(filename, node.lineno, "2a", f"import {name!r} is not approved")
                )
                continue
            for alias in node.names:
                full_name = f"{name}.{alias.name}"
                if _is_module(full_name) and full_name not in allowed:
                    problems.append(
                        _problem(
                            filename,
                            node.lineno,
                            "2a",
                            f"import {full_name!r} is not approved",
                        )
                    )
    return problems


def check_dangerous_calls(source: str, filename: str) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and _forbidden_os(node.attr)
            ):
                problems.append(
                    _problem(
                        filename,
                        node.lineno,
                        "2b",
                        f"access to os.{node.attr} is not allowed",
                    )
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os" and alias.asname:
                    problems.append(
                        _problem(
                            filename,
                            node.lineno,
                            "2b",
                            "import os as another name is not allowed",
                        )
                    )
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "os":
            for alias in node.names:
                if alias.name == "*" or _forbidden_os(alias.name):
                    problems.append(
                        _problem(
                            filename,
                            node.lineno,
                            "2b",
                            f"from os import {alias.name} is not allowed",
                        )
                    )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BAD_CALL_NAMES:
                problems.append(
                    _problem(
                        filename,
                        node.lineno,
                        "2b",
                        f"call to {node.func.id!r} is not allowed",
                    )
                )
            if (
                node.func.id == "getattr"
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "os"
            ):
                problems.append(
                    _problem(filename, node.lineno, "2b", "getattr(os, ...) is not allowed")
                )
    return problems


def check_remote_filesystems(source: str, filename: str) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        name: str | None = None
        if isinstance(node, ast.Attribute):
            if node.attr in {"fs", "flight"}:
                name = node.attr
            elif node.attr.endswith("FileSystem"):
                name = node.attr
        elif isinstance(node, ast.Name) and node.id.endswith("FileSystem"):
            name = node.id
        elif isinstance(node, ast.alias) and node.name.endswith("FileSystem"):
            name = node.name
        if name is not None:
            problems.append(
                _problem(
                    filename,
                    getattr(node, "lineno", 0),
                    "2j",
                    f"remote filesystem name {name!r} found",
                )
            )
    return problems


def check_web_addresses(text: str, filename: str) -> list[str]:
    problems: list[str] = []
    for match in WEB_ADDRESS_RE.finditer(text):
        scheme = match.group(0)[:-3]
        problems.append(
            _problem(
                filename,
                _line_of(text, match.start()),
                "2c",
                f"address scheme {scheme!r} found",
            )
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
    build = data.get("build-system", {})
    if not isinstance(build, dict):
        problems.append("pyproject.toml: rule 2d: build-system must be a table")
    else:
        requires = build.get("requires", [])
        requires_names = dependency_names(requires if isinstance(requires, list) else [])
        if requires_names != {"setuptools"}:
            problems.append(
                "pyproject.toml: rule 2d: build-system.requires must be exactly "
                f"{{'setuptools'}}, found {sorted(requires_names)}"
            )
        if build.get("build-backend") != "setuptools.build_meta":
            problems.append(
                "pyproject.toml: rule 2d: build-system.build-backend must be "
                "'setuptools.build_meta'"
            )
    project = data.get("project", {})
    if not isinstance(project, dict):
        return ["pyproject.toml: rule 2d: [project] must be a table"]
    dependencies = project.get("dependencies", [])
    names = dependency_names(dependencies if isinstance(dependencies, list) else [])
    if names != PROJECT_DEPENDENCIES:
        problems.append(
            "pyproject.toml: rule 2d: project.dependencies must be exactly "
            f"{sorted(PROJECT_DEPENDENCIES)}, found {sorted(names)}"
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
            if name == "" or not isinstance(item, dict):
                continue
            if not str(item.get("resolved", "")).startswith("https://registry.npmjs.org/"):
                problems.append(
                    f"package-lock.json: rule 2e: {name} must resolve from "
                    "https://registry.npmjs.org/"
                )
            if not item.get("integrity"):
                problems.append(f"package-lock.json: rule 2e: {name} needs an integrity hash")
            if item.get("hasInstallScript"):
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
    socket_match = re.search(r"(?i)socket", text)
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


def check_ea_files(root: Path, allowed_mql: frozenset[str]) -> list[str]:
    problems: list[str] = []
    for relative, path in iter_repository_files(root, include_teams=True):
        suffix = path.suffix.lower()
        if suffix in {".ex4", ".ex5"}:
            problems.append(f"{relative}: rule 2i: {EA_FILE_MESSAGE}")
        elif suffix in {".mq4", ".mq5", ".mqh"} and relative not in allowed_mql:
            problems.append(f"{relative}: rule 2i: {EA_FILE_MESSAGE}")
    return problems


def check_code_files(
    root: Path, suffixes: frozenset[str], allowed_prefixes: tuple[str, ...]
) -> list[str]:
    problems: list[str] = []
    for relative, path in iter_repository_files(root, include_teams=True):
        suffix = path.suffix.lower()
        if suffix not in suffixes:
            continue
        allowed = suffix == ".py" and relative.startswith(allowed_prefixes)
        if not allowed:
            problems.append(
                f"{relative}: rule 2k: code files are allowed only as .py under "
                "src/ or tests/. Ask the Lead before adding code anywhere else."
            )
    return problems


def check_subprocess_use(source: str, filename: str, allowed_count: int) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(source, filename=filename)
    run_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess" and alias.asname:
                    problems.append(
                        _problem(
                            filename,
                            node.lineno,
                            "2l",
                            "import subprocess as another name is not allowed",
                        )
                    )
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == "subprocess":
            problems.append(
                _problem(
                    filename,
                    node.lineno,
                    "2l",
                    "from subprocess import ... is not allowed",
                )
            )
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "subprocess"
        ):
            if node.attr == "run":
                run_count += 1
            elif node.attr not in {"DEVNULL", "TimeoutExpired"}:
                problems.append(
                    _problem(
                        filename,
                        node.lineno,
                        "2l",
                        f"subprocess.{node.attr} is not allowed",
                    )
                )
    if run_count != allowed_count:
        problems.append(
            f"{filename}: rule 2l: found {run_count} subprocess.run accesses, "
            f"allowed {allowed_count}"
        )
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


def check_mql_account(text: str, filename: str) -> list[str]:
    problems: list[str] = []
    for name in MQL_ACCOUNT_NAMES:
        index = text.find(name)
        if index >= 0:
            problems.append(
                _problem(filename, _line_of(text, index), "2m", f"MQL account name {name!r} found")
            )
    return problems


def check_is_testing(text: str, filename: str) -> list[str]:
    if IS_TESTING_RE.search(text):
        return []
    return [f"{filename}: rule 3f: missing the IsTesting() refusal line"]
