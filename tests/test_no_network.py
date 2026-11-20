# SAFETY GUARD (D-20). Only the Lead changes these lists, through a brief.
# If this test fails, do not edit the lists: change your code, or stop and ask.

import json
import socket
import subprocess
import tomllib
from datetime import UTC, date, datetime
from pathlib import Path

import _guard_scan as guard
import pyarrow as pa
import pytest

from losslens.cli import main
from losslens.ticks.store import TickStore, make_entry

ROOT = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = frozenset(
    """
    .py .pyw .pyi .pyc .pyd .ipynb
    .js .mjs .cjs .ts .tsx .jsx
    .ps1 .psm1 .bat .cmd .sh .vbs .wsf
    .exe .dll .msi .scr .com .jar .lnk
    """.split()
)
CODE_ALLOWED_PREFIXES = ("src/", "tests/")
APPROVED_IMPORTS = frozenset(
    """
    __future__ abc argparse bisect collections collections.abc contextlib csv dataclasses
    datetime decimal enum functools hashlib io itertools json math os pathlib re shutil
    statistics struct sys tempfile time tomllib typing zoneinfo
    pyarrow pyarrow.compute pyarrow.csv pyarrow.parquet
    """.split()
)
SUBPROCESS_ALLOWED = {"src/losslens/ticks/dukascopy.py": 1}


def _src_files():
    root = guard.repository_root()
    for path in sorted((root / "src").rglob("*.py")):
        yield path.relative_to(root).as_posix(), path.read_text(encoding="utf-8")


def test_src_imports_are_approved():
    problems = []
    for relative, source in _src_files():
        problems.extend(guard.check_imports(source, relative, APPROVED_IMPORTS, SUBPROCESS_ALLOWED))
    assert not problems, "Approved-import rule 2a failed:\n" + "\n".join(problems)


def test_import_scanner_flags_bad_and_accepts_good():
    bad = guard.check_imports("import socket\n", "src/x.py", APPROVED_IMPORTS, SUBPROCESS_ALLOWED)
    assert bad and "src/x.py:1" in bad[0] and "rule 2a" in bad[0]
    for source in (
        "from pyarrow import flight\n",
        "from pyarrow import fs\n",
        "from losslens_evil import x\n",
    ):
        problem = guard.check_imports(source, "src/x.py", APPROVED_IMPORTS, SUBPROCESS_ALLOWED)
        assert problem and "rule 2a" in problem[0]
    clean = guard.check_imports(
        "import json\nfrom . import x\n", "src/x.py", APPROVED_IMPORTS, SUBPROCESS_ALLOWED
    )
    assert clean == []
    assert (
        guard.check_imports(
            "from pyarrow import compute\n", "src/x.py", APPROVED_IMPORTS, SUBPROCESS_ALLOWED
        )
        == []
    )
    assert (
        guard.check_imports(
            "from losslens.ticks import store\n",
            "src/x.py",
            APPROVED_IMPORTS,
            SUBPROCESS_ALLOWED,
        )
        == []
    )
    allowed = guard.check_imports(
        "import subprocess\n",
        "src/losslens/ticks/dukascopy.py",
        APPROVED_IMPORTS,
        SUBPROCESS_ALLOWED,
    )
    assert allowed == []


def test_src_has_no_hidden_execution():
    problems = []
    for relative, source in _src_files():
        problems.extend(guard.check_dangerous_calls(source, relative))
    assert not problems, "Hidden-execution rule 2b failed:\n" + "\n".join(problems)


def test_hidden_execution_scanner_flags_bad_and_accepts_good():
    for source in (
        "eval('1')\n",
        "os.system('x')\n",
        "f = os.system\n",
        "from os import system\n",
        "from os import *\n",
        "import os as o\n",
        'x = getattr(os, "system")\n',
    ):
        bad = guard.check_dangerous_calls(source, "src/x.py")
        assert bad and "rule 2b" in bad[0]
    assert guard.check_dangerous_calls("re.compile('x')\n", "src/x.py") == []
    assert (
        guard.check_dangerous_calls(
            "import os\nfrom os import path\nos.path.join('a', 'b')\n", "src/x.py"
        )
        == []
    )
    assert guard.check_dangerous_calls('getattr(other, "system")\n', "src/x.py") == []


def test_src_has_no_remote_filesystems():
    problems = []
    for relative, source in _src_files():
        problems.extend(guard.check_remote_filesystems(source, relative))
    assert not problems, "Remote-filesystem rule 2j failed:\n" + "\n".join(problems)


def test_remote_filesystem_scanner_flags_bad_and_accepts_good():
    for source in ("pa.fs\n", "pa.flight\n", "x = S3FileSystem()\n"):
        bad = guard.check_remote_filesystems(source, "src/x.py")
        assert bad and "rule 2j" in bad[0]
    assert guard.check_remote_filesystems("pa.compute\n", "src/x.py") == []


def test_src_has_no_web_addresses():
    problems = []
    for relative, source in _src_files():
        problems.extend(guard.check_web_addresses(source, relative))
    assert not problems, "No-web-address rule 2c failed:\n" + "\n".join(problems)


def test_web_address_scanner_flags_bad_and_accepts_good():
    for scheme in ("https", "s3", "wss", "gs", "file"):
        bad = guard.check_web_addresses(scheme + "://bucket\n", "src/x.py")
        assert bad and "src/x.py:1" in bad[0] and "rule 2c" in bad[0]
        assert scheme in bad[0]
    assert guard.check_web_addresses("# no address here\n", "src/x.py") == []


def test_code_files_are_only_py_under_src_or_tests():
    problems = guard.check_code_files(guard.repository_root(), CODE_SUFFIXES, CODE_ALLOWED_PREFIXES)
    assert not problems, "Code-place rule 2k failed:\n" + "\n".join(problems)


def test_code_file_scanner_flags_bad_and_accepts_good(tmp_path):
    for relative in (
        "scripts/upload.py",
        "setup.py",
        "src/losslens/x.pyw",
        "tools/send.ps1",
        "notes/run.bat",
        ".teams/teams/builder/work/helper.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")
    for relative in ("src/losslens/x.py", "tests/x.py", "mql4/x.mq4"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")

    problems = guard.check_code_files(tmp_path, CODE_SUFFIXES, CODE_ALLOWED_PREFIXES)

    assert len(problems) == 6
    for relative in (
        "scripts/upload.py",
        "setup.py",
        "src/losslens/x.pyw",
        "tools/send.ps1",
        "notes/run.bat",
        ".teams/teams/builder/work/helper.py",
    ):
        assert any(problem.startswith(relative + ":") for problem in problems)
    assert all("rule 2k" in problem for problem in problems)


def test_subprocess_use_is_limited():
    problems = []
    for relative, source in _src_files():
        allowed = SUBPROCESS_ALLOWED.get(relative, 0)
        problems.extend(guard.check_subprocess_use(source, relative, allowed))
    assert not problems, "Subprocess rule 2l failed:\n" + "\n".join(problems)


def test_subprocess_scanner_flags_bad_and_accepts_good():
    clean = "import subprocess\nsubprocess.run([])\nsubprocess.DEVNULL\nsubprocess.TimeoutExpired\n"
    assert guard.check_subprocess_use(clean, "src/losslens/ticks/dukascopy.py", 1) == []
    for source, allowed in (
        ("import subprocess as sp\n", 0),
        ("from subprocess import run\n", 0),
        ("subprocess.Popen([])\n", 0),
        ("subprocess.run([])\nsubprocess.run([])\n", 1),
    ):
        bad = guard.check_subprocess_use(source, "src/losslens/ticks/dukascopy.py", allowed)
        assert bad and "rule 2l" in bad[0]


def test_pyproject_dependencies_are_exact():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    problems = guard.check_pyproject_dependencies(data)
    assert not problems, "Dependency rule 2d failed:\n" + "\n".join(problems)


def test_dependency_scanner_flags_bad_and_accepts_good():
    build = {"requires": ["setuptools>=68"], "build-backend": "setuptools.build_meta"}
    bad = {
        "build-system": build,
        "project": {
            "dependencies": ["pyarrow", "requests"],
            "optional-dependencies": {"dev": ["pytest", "ruff", "mypy"]},
        },
    }
    assert guard.check_pyproject_dependencies(bad)
    bad_backend = {
        "build-system": {"requires": ["setuptools"], "build-backend": "hatchling.build"},
        "project": {
            "dependencies": ["pyarrow"],
            "optional-dependencies": {"dev": ["pytest", "ruff", "mypy"]},
        },
    }
    assert guard.check_pyproject_dependencies(bad_backend)
    good = {
        "build-system": build,
        "project": {
            "dependencies": ["pyarrow>=14.0"],
            "optional-dependencies": {"dev": ["pytest>=8", "ruff>=0.9", "mypy>=1.15"]},
        },
    }
    assert guard.check_pyproject_dependencies(good) == []


def test_node_side_is_pinned():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    problems = guard.check_node_side(package, lock)
    assert not problems, "Node-pin rule 2e failed:\n" + "\n".join(problems)


def test_node_scanner_flags_bad_and_accepts_good():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    bad_package = {"dependencies": {"dukascopy-node": "^1.51.1"}, "scripts": {}}
    bad_lock = {
        "packages": {
            "": {},
            "node_modules/dukascopy-node": {
                "version": "1.51.1",
                "integrity": "sha512-x",
                "resolved": "https://registry.npmjs.org/dukascopy-node/-/dukascopy-node-1.51.1.tgz",
                "hasInstallScript": True,
            },
            "node_modules/evil": {
                "version": "1.0.0",
                "resolved": "https://evil.example/evil-1.0.0.tgz",
            },
        }
    }
    problems = guard.check_node_side(bad_package, bad_lock)
    assert len(problems) >= 4
    assert guard.check_node_side(package, lock) == []


def test_only_sync_can_start_a_process(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        date(2026, 3, 3),
        pa.table(
            {
                "ts_ms": [1772496000000],
                "bid": [100.0],
                "ask": [101.0],
                "bid_vol": [0.0],
                "ask_vol": [0.0],
            }
        ),
    )
    manifest = store.load_manifest()
    manifest["days"]["2026-03-03"] = make_entry(
        date(2026, 3, 3),
        "complete",
        1,
        1772496000000,
        1772496000000,
        "test",
        datetime(2026, 11, 20, 12, 0, tzinfo=UTC),
    )
    store.save_manifest(manifest)
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))

    def forbidden(*args, **kwargs):
        raise AssertionError("a process was started outside ticks sync")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)

    assert main(["ticks", "status", "--symbol", "XAUUSD"]) == 0
    assert (
        main(
            ["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]
        )
        == 0
    )
    assert (
        main(
            [
                "ticks",
                "query",
                "--symbol",
                "XAUUSD",
                "--from",
                "2026-03-03T00:00:00Z",
                "--to",
                "2026-03-03T00:01:00Z",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "ticks",
                "import",
                "--symbol",
                "XAUUSD",
                "--file",
                str(ROOT / "tests" / "fixtures" / "import_sample.csv"),
                "--ts-col",
                "time",
                "--bid-col",
                "bid",
                "--ask-col",
                "ask",
                "--ts-format",
                "iso",
                "--utc-offset-minutes",
                "120",
            ]
        )
        == 0
    )


def test_network_is_blocked_in_tests():
    with pytest.raises(RuntimeError, match="network is blocked in tests"):
        socket.create_connection(("127.0.0.1", 9), timeout=1)


def test_repository_has_no_mql_online_calls():
    root = guard.repository_root()
    problems = []
    for relative, text in guard.iter_text_files(root):
        if Path(relative).suffix.lower() in guard.MQL_SUFFIXES:
            problems.extend(guard.check_mql_online(text, relative))
    assert not problems, "MQL-online rule 2h failed:\n" + "\n".join(problems)


def test_mql_scanner_flags_bad_and_accepts_good():
    bad = guard.check_mql_online("Web" + "Request('GET','x')\n", "mql4/x.mq4")
    assert bad and "mql4/x.mq4:1" in bad[0] and "rule 2h" in bad[0]
    bad_import = guard.check_mql_online('  #import "user32.dll"\n', "mql4/x.mq4")
    assert bad_import and "rule 2h" in bad_import[0]
    bad_socket = guard.check_mql_online("soc" + "ket\n", "mql4/x.mq4")
    assert bad_socket and "rule 2h" in bad_socket[0]
    bad_socket_create = guard.check_mql_online("Socket" + "Create();\n", "mql4/x.mq4")
    assert bad_socket_create and "rule 2h" in bad_socket_create[0]
    assert guard.check_mql_online("// nothing online\n", "mql4/x.mq4") == []


def test_text_scan_skips_only_root_place_folders(tmp_path):
    (tmp_path / "src" / "losslens" / "data").mkdir(parents=True)
    (tmp_path / "src" / "losslens" / "data" / "x.py").write_text(
        "Order" + "Send(", encoding="utf-8"
    )
    (tmp_path / "docs" / "build").mkdir(parents=True)
    (tmp_path / "docs" / "build" / "x.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "x.py").write_text("x = 1\n", encoding="utf-8")

    relative = {path for path, _ in guard.iter_text_files(tmp_path)}

    assert "src/losslens/data/x.py" in relative
    assert "docs/build/x.py" in relative
    assert "data/x.py" not in relative


def test_repository_has_no_ea_files_outside_mql4():
    problems = guard.check_ea_files(guard.repository_root())
    assert not problems, "EA-file rule 2i failed:\n" + "\n".join(problems)


def test_ea_file_scanner_flags_bad_and_accepts_good(tmp_path):
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "x.mq4").write_text("// ea", encoding="utf-8")
    (tmp_path / "docs" / "build").mkdir(parents=True)
    (tmp_path / "docs" / "build" / "my_ea.ex4").write_text("// ea", encoding="utf-8")
    (tmp_path / ".teams" / "teams" / "builder" / "work").mkdir(parents=True)
    (tmp_path / ".teams" / "teams" / "builder" / "work" / "my_ea.ex4").write_text(
        "// ea", encoding="utf-8"
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "my_ea.ex4").write_text("// ea", encoding="utf-8")
    (tmp_path / "mql4").mkdir()
    (tmp_path / "mql4" / "x.mq4").write_text("// ours", encoding="utf-8")

    problems = guard.check_ea_files(tmp_path)

    assert len(problems) == 3
    assert any("scratch/x.mq4" in problem for problem in problems)
    assert any("docs/build/my_ea.ex4" in problem for problem in problems)
    assert any(".teams/teams/builder/work/my_ea.ex4" in problem for problem in problems)
    assert all("EA files do not belong in this folder" in problem for problem in problems)
