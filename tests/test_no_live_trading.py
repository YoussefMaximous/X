# SAFETY GUARD (D-14). Only the Lead changes these lists, through a brief.
# If this test fails, do not edit the lists: change your code, or stop and ask.

import json
import subprocess
import tomllib
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import _guard_scan as guard

from losslens.mt4 import copy as mt4_copy
from losslens.mt4 import programs, startfile

ROOT = Path(__file__).resolve().parents[1]
ORDER_FUNCTION_ALLOWED: frozenset[str] = frozenset()
MQL_FILES_ALLOWED = frozenset({"mql4/Experts/LossLensProbe.mq4"})
MT4_COPY_FILES = (
    "terminal.exe",
    "metaeditor.exe",
    "history/<server>/symbols.raw",
    "history/<server>/symgroups.raw",
)
TESTER_KEYS = frozenset(
    {
        "TestExpert",
        "TestSymbol",
        "TestPeriod",
        "TestModel",
        "TestSpread",
        "TestOptimization",
        "TestDateEnable",
        "TestFromDate",
        "TestToDate",
        "TestReport",
        "TestReplaceReport",
        "TestShutdownTerminal",
        "TestVisualEnable",
    }
)
TESTER_FIXED_LINES = (
    "ExpertsEnable=false",
    "ExpertsTrades=false",
    "ExpertsDllImport=false",
    "ExpertsExpImport=false",
    "EnableNews=false",
    "EnableDDE=false",
    "AutoConfiguration=false",
    "ProxyEnable=true",
    "ProxyServer=127.0.0.1:9",
    "ProxyType=HTTP",
)


def test_repository_has_no_order_functions():
    problems = []
    for relative, text in guard.iter_text_files(guard.repository_root()):
        if relative == "tests/test_no_live_trading.py":
            continue
        problems.extend(guard.check_order_functions(text, relative, ORDER_FUNCTION_ALLOWED))
    assert not problems, "No-order-function rule 3a failed:\n" + "\n".join(problems)


def test_order_function_scanner_flags_bad_and_accepts_good():
    bad = guard.check_order_functions("Order" + "Send(", "src/x.py", ORDER_FUNCTION_ALLOWED)
    assert bad and "src/x.py:1" in bad[0] and "rule 3a" in bad[0]
    assert (
        guard.check_order_functions("// no order here\n", "src/x.py", ORDER_FUNCTION_ALLOWED) == []
    )


def test_no_trading_or_broker_library():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    problems = guard.check_trading_dependencies(pyproject, package)
    assert not problems, "No-trading-library rule 3b failed:\n" + "\n".join(problems)


def test_trading_dependency_scanner_flags_bad_and_accepts_good():
    bad = {
        "project": {
            "dependencies": ["pyarrow", "ccxt"],
            "optional-dependencies": {"dev": ["pytest"]},
        }
    }
    assert guard.check_trading_dependencies(bad, {"dependencies": {}})
    good = {
        "project": {
            "dependencies": ["pyarrow"],
            "optional-dependencies": {"dev": ["pytest", "ruff", "mypy"]},
        }
    }
    assert guard.check_trading_dependencies(good, {"dependencies": {}}) == []


def test_repository_has_no_stored_login():
    problems = []
    for relative, text in guard.iter_text_files(guard.repository_root()):
        problems.extend(guard.check_passwords(text, relative))
    assert not problems, "No-stored-login rule 3c failed:\n" + "\n".join(problems)


def test_password_scanner_flags_bad_and_accepts_good():
    bad = guard.check_passwords("pass" + "word = hunter2\n", "src/x.py")
    assert bad and "src/x.py:1" in bad[0] and "rule 3c" in bad[0]
    assert guard.check_passwords("no secret here\n", "src/x.py") == []


def _mql_texts():
    for relative, text in guard.iter_text_files(guard.repository_root()):
        if Path(relative).suffix.lower() in guard.MQL_SUFFIXES:
            yield relative, text


def test_repository_mql_files_are_an_exact_list():
    problems = guard.check_ea_files(guard.repository_root(), MQL_FILES_ALLOWED)
    assert not problems, "MQL exact-list rule 2i failed:\n" + "\n".join(problems)


def test_mql_files_never_ask_who_the_user_is():
    problems = []
    for relative, text in _mql_texts():
        problems.extend(guard.check_mql_account(text, relative))
    assert not problems, "MQL-account rule 2m failed:\n" + "\n".join(problems)


def test_mql_account_scanner_flags_bad_and_accepts_good():
    bad = guard.check_mql_account("Account" + "Number()\n", "mql4/x.mq4")
    assert bad and "mql4/x.mq4:1" in bad[0] and "rule 2m" in bad[0]
    assert guard.check_mql_account("AccountBalance()\n", "mql4/x.mq4") == []


def test_every_mql_refuses_to_run_outside_the_tester():
    problems = []
    for relative, text in _mql_texts():
        if relative.lower().endswith(".mq4"):
            problems.extend(guard.check_is_testing(text, relative))
    assert not problems, "IsTesting rule 3f failed:\n" + "\n".join(problems)


def test_is_testing_scanner_flags_bad_and_accepts_good():
    bad = guard.check_is_testing("int OnInit(){return(0);}\n", "mql4/x.mq4")
    assert bad and "rule 3f" in bad[0]
    assert guard.check_is_testing("if(!IsTesting()) return(INIT_FAILED);\n", "mql4/x.mq4") == []


def test_start_file_constants_and_checker():
    assert startfile.TESTER_KEYS == TESTER_KEYS, (
        "src/losslens/mt4/startfile.py: rule 3d: TESTER_KEYS changed"
    )
    assert startfile.TESTER_FIXED_LINES == TESTER_FIXED_LINES, (
        "src/losslens/mt4/startfile.py: rule 3d: TESTER_FIXED_LINES changed"
    )
    valid = startfile.build_start_file("XAUUSD", date(2026, 3, 3), date(2026, 3, 4), 30)
    assert startfile.check_start_file(valid) == [], (
        "src/losslens/mt4/startfile.py: rule 3d: builder and checker disagree"
    )
    for bad_line in (
        "Login=1",
        "Server=ICMarketsSC-Demo04",
        "Expert=LossLensProbe",
        "Script=Test",
        "Symbol=XAUUSD",
        "Template=Default",
        "Profile=Default",
        "ExpertsTrades=true",
        "ProxyEnable=false",
    ):
        assert startfile.check_start_file(valid + bad_line + "\n"), (
            f"src/losslens/mt4/startfile.py: rule 3d: {bad_line} was not refused"
        )
    assert startfile.check_start_file(valid.replace("ExpertsTrades=false\n", "")), (
        "src/losslens/mt4/startfile.py: rule 3d: missing ExpertsTrades=false was not refused"
    )


def test_mt4_copy_file_list_and_setup(tmp_path):
    assert mt4_copy.MT4_COPY_FILES == MT4_COPY_FILES, (
        "src/losslens/mt4/copy.py: rule 3g: MT4_COPY_FILES changed"
    )
    source = tmp_path / "source"
    (source / "history" / "Server").mkdir(parents=True)
    for name in ("terminal.exe", "metaeditor.exe"):
        (source / name).write_bytes(b"program")
    for name in ("symbols.raw", "symgroups.raw"):
        (source / "history" / "Server" / name).write_bytes(b"symbols")
    forbidden = (
        "config/accounts.ini",
        "config/terminal.lic",
        "profiles/default/chart01.chr",
        "MQL4/Experts/Secret.ex4",
        "MQL4/Experts/Secret.mq4",
        "MQL4/Include/x.mqh",
        "logs/20261120.log",
    )
    for relative in forbidden:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"forbidden")

    target = tmp_path / "target"
    mt4_copy.setup_copy(source, "Server", target)

    copied = sorted(
        path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()
    )
    assert copied == [
        "history/default/symbols.raw",
        "history/default/symgroups.raw",
        "metaeditor.exe",
        "terminal.exe",
    ]


def test_program_starts_are_refused_before_any_run(tmp_path, monkeypatch):
    copy_root = tmp_path / "copy"
    (copy_root / "MQL4" / "Experts").mkdir(parents=True)
    (copy_root / "terminal.exe").write_bytes(b"terminal")
    (copy_root / "metaeditor.exe").write_bytes(b"editor")
    (copy_root / "MQL4" / "Experts" / "LossLensProbe.mq4").write_text("// probe", encoding="utf-8")
    valid = startfile.build_start_file("XAUUSD", date(2026, 3, 3), date(2026, 3, 4), 30)
    (copy_root / "losslens_start.ini").write_text(valid, encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "terminal.exe").write_bytes(b"terminal")
    (outside / "start.ini").write_text(valid, encoding="utf-8")
    (copy_root / "cmd.exe").write_bytes(b"cmd")
    calls = []

    def recorder(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("losslens.mt4.programs.subprocess.run", recorder)

    def refused(program, args):
        calls.clear()
        try:
            programs.run_program(program, args, copy_root=copy_root, timeout=1)
        except programs.UnsafeProgramError:
            pass
        else:
            raise AssertionError(
                "src/losslens/mt4/programs.py: rule 3e: unsafe program start was not refused"
            )
        assert calls == [], (
            "src/losslens/mt4/programs.py: rule 3e: unsafe start reached subprocess.run"
        )

    refused(outside / "terminal.exe", ["/portable", "losslens_start.ini"])
    refused(copy_root / "cmd.exe", ["/portable", "losslens_start.ini"])
    (copy_root / "losslens_start.ini").write_text(
        valid + "Expert=LossLensProbe\n", encoding="utf-8"
    )
    refused(copy_root / "terminal.exe", ["/portable", "losslens_start.ini"])
    (copy_root / "losslens_start.ini").write_text(valid, encoding="utf-8")
    refused(copy_root / "terminal.exe", ["/portable", str(outside / "start.ini")])
    refused(
        copy_root / "terminal.exe",
        ["/portable", "losslens_start.ini", "extra"],
    )
    refused(copy_root / "terminal.exe", ["losslens_start.ini"])

    calls.clear()
    programs.run_program(
        copy_root / "terminal.exe",
        ["/portable", "losslens_start.ini"],
        copy_root=copy_root,
        timeout=7,
    )
    assert len(calls) == 1
    assert calls[0][1]["stdin"] == subprocess.DEVNULL
    assert calls[0][1]["timeout"] == 7
