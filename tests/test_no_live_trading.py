# SAFETY GUARD (D-14). Only the Lead changes these lists, through a brief.
# If this test fails, do not edit the lists: change your code, or stop and ask.

import json
import tomllib
from pathlib import Path

import _guard_scan as guard

ROOT = Path(__file__).resolve().parents[1]
ORDER_FUNCTION_ALLOWED: frozenset[str] = frozenset()


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
