from datetime import date
from types import SimpleNamespace

from losslens.mt4 import run as mt4_run


def test_run_starts_portable_with_the_absolute_ini_path(tmp_path, monkeypatch):
    copy_root = tmp_path / "copy"
    copy_root.mkdir()
    captured = {}

    def fake(program, args, *, copy_root, timeout):
        captured["program"] = program
        captured["args"] = args
        captured["timeout"] = timeout
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr("losslens.mt4.run.run_program", fake)

    mt4_run.run_tester(copy_root, "XAUUSD", date(2026, 3, 3), date(2026, 3, 3), 30, 180)

    assert captured["args"] == [
        "/portable",
        str((copy_root / "losslens_start.ini").resolve()),
    ]
    assert len(captured["args"]) == 2
    assert "/config:" not in " ".join(captured["args"])
