from datetime import date
from pathlib import Path
from types import SimpleNamespace

from losslens.cli import build_parser
from losslens.mt4 import run, startfile


def _run_args(extra=()):
    return build_parser().parse_args(
        [
            "mt4",
            "run",
            "--symbol",
            "XAUUSD",
            "--from",
            "2026-03-03",
            "--to",
            "2026-03-03",
            *extra,
        ]
    )


def test_visual_is_off_by_default():
    args = _run_args()
    assert args.visual is False

    text = startfile.build_start_file("XAUUSD", date(2026, 3, 3), date(2026, 3, 4), 30)
    assert "TestVisualEnable=false" in text
    assert "TestVisualEnable=true" not in text
    assert startfile.check_start_file(text) == []


def test_visual_can_be_turned_on_and_off():
    assert _run_args(["--visual"]).visual is True
    assert _run_args(["--no-visual"]).visual is False

    text = startfile.build_start_file("XAUUSD", date(2026, 3, 3), date(2026, 3, 4), 30, visual=True)
    assert "TestVisualEnable=true" in text
    assert startfile.check_start_file(text) == []


def test_start_file_parameters_are_passed():
    text = startfile.build_start_file(
        "XAUUSD",
        date(2026, 3, 3),
        date(2026, 3, 4),
        30,
        parameters="losslens_trial.set",
    )

    assert "TestExpertParameters=losslens_trial.set" in text
    assert startfile.check_start_file(text) == []


def test_run_tester_writes_the_visual_setting(tmp_path, monkeypatch):
    copy_root = tmp_path / "copy"
    (copy_root / "MQL4" / "Experts").mkdir(parents=True)
    (copy_root / "terminal.exe").write_bytes(b"terminal")
    (copy_root / "MQL4" / "Experts" / "LossLensProbe.mq4").write_text("// probe", encoding="utf-8")
    calls = []

    def recorder(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("losslens.mt4.run.run_program", recorder)
    result = run.run_tester(
        copy_root,
        "XAUUSD",
        date(2026, 3, 3),
        date(2026, 3, 3),
        30,
        2,
        expert="MyEA",
        visual=True,
        parameters="trial.set",
    )

    text = (copy_root / "losslens_start.ini").read_text(encoding="utf-8")
    assert "TestExpert=MyEA" in text
    assert "TestVisualEnable=true" in text
    assert "TestExpertParameters=trial.set" in text
    assert calls
    assert result.timed_out is False
    assert result.report is None


def test_run_tester_parses_the_report(tmp_path, monkeypatch):
    copy_root = tmp_path / "copy"
    (copy_root / "MQL4" / "Experts").mkdir(parents=True)
    (copy_root / "terminal.exe").write_bytes(b"terminal")
    (copy_root / "MQL4" / "Experts" / "LossLensProbe.mq4").write_text("// probe", encoding="utf-8")
    (copy_root / "tester").mkdir()
    report_text = (Path(__file__).parent / "fixtures" / "mt4_report_probe.htm").read_text(
        encoding="utf-8"
    )

    def recorder(*args, **kwargs):
        (copy_root / "tester" / "losslens_report.htm").write_text(report_text, encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("losslens.mt4.run.run_program", recorder)
    result = run.run_tester(
        copy_root,
        "XAUUSD",
        date(2026, 3, 3),
        date(2026, 3, 3),
        30,
        2,
    )

    assert result.report is not None
    assert result.report.ticks_modelled == 471448
    assert result.report.bars == 1320
