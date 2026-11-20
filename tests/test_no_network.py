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
APPROVED_IMPORTS = frozenset(
    """
    __future__ abc argparse bisect collections collections.abc contextlib csv dataclasses
    datetime decimal enum functools hashlib io itertools json math os pathlib re shutil
    statistics struct sys tempfile time tomllib typing zoneinfo
    pyarrow pyarrow.compute pyarrow.csv pyarrow.parquet
    """.split()
)
SUBPROCESS_ALLOWED = frozenset({"src/losslens/ticks/dukascopy.py"})


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
    clean = guard.check_imports(
        "import json\nfrom . import x\n", "src/x.py", APPROVED_IMPORTS, SUBPROCESS_ALLOWED
    )
    assert clean == []
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
    bad = guard.check_dangerous_calls("eval('1')\n", "src/x.py")
    assert bad and "src/x.py:1" in bad[0] and "rule 2b" in bad[0]
    bad_os = guard.check_dangerous_calls("os.system('x')\n", "src/x.py")
    assert bad_os and "rule 2b" in bad_os[0]
    assert guard.check_dangerous_calls("re.compile('x')\n", "src/x.py") == []


def test_src_has_no_web_addresses():
    problems = []
    for relative, source in _src_files():
        problems.extend(guard.check_web_addresses(source, relative))
    assert not problems, "No-web-address rule 2c failed:\n" + "\n".join(problems)


def test_web_address_scanner_flags_bad_and_accepts_good():
    bad = guard.check_web_addresses("# " + "https://" + "example.com\n", "src/x.py")
    assert bad and "src/x.py:1" in bad[0] and "rule 2c" in bad[0]
    assert guard.check_web_addresses("# no address here\n", "src/x.py") == []


def test_pyproject_dependencies_are_exact():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    problems = guard.check_pyproject_dependencies(data)
    assert not problems, "Dependency rule 2d failed:\n" + "\n".join(problems)


def test_dependency_scanner_flags_bad_and_accepts_good():
    bad = {
        "project": {
            "dependencies": ["pyarrow", "requests"],
            "optional-dependencies": {"dev": ["pytest", "ruff", "mypy"]},
        }
    }
    assert guard.check_pyproject_dependencies(bad)
    good = {
        "project": {
            "dependencies": ["pyarrow>=14.0"],
            "optional-dependencies": {"dev": ["pytest>=8", "ruff>=0.9", "mypy>=1.15"]},
        }
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
        "packages": {"node_modules/dukascopy-node": {"version": "1.51.1", "hasInstallScript": True}}
    }
    problems = guard.check_node_side(bad_package, bad_lock)
    assert len(problems) >= 3
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
    assert guard.check_mql_online("// nothing online\n", "mql4/x.mq4") == []


def test_repository_has_no_ea_files_outside_mql4():
    problems = guard.check_ea_files(guard.repository_root())
    assert not problems, "EA-file rule 2i failed:\n" + "\n".join(problems)


def test_ea_file_scanner_flags_bad_and_accepts_good(tmp_path):
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "x.mq4").write_text("// ea", encoding="utf-8")
    (tmp_path / "mql4").mkdir()
    (tmp_path / "mql4" / "x.mq4").write_text("// ours", encoding="utf-8")

    problems = guard.check_ea_files(tmp_path)

    assert len(problems) == 1
    assert "scratch/x.mq4" in problems[0]
    assert "EA files do not belong in this folder" in problems[0]
