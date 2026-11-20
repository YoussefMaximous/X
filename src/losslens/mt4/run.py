"""Run the probe in the MT4 Strategy Tester."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .programs import ProgramTimeout, UnsafeProgramError, run_program
from .startfile import build_start_file

START_FILE = "losslens_start.ini"
PROBE_INFO = "losslens_probe_info.txt"
PROBE_TICKS = "losslens_probe_ticks.bin"


class RunError(RuntimeError):
    """The tester could not be started safely."""


@dataclass
class RunResult:
    timed_out: bool
    seconds: float
    report_files: list[Path]
    probe_info: Path | None
    probe_ticks: Path | None
    output: str


def run_tester(
    copy_root: Path,
    symbol: str,
    from_day: date,
    to_day: date,
    spread: int,
    timeout: float,
) -> RunResult:
    start_text = build_start_file(symbol, from_day, to_day + timedelta(days=1), spread)
    start_file = copy_root / START_FILE
    start_file.write_text(start_text, encoding="utf-8", newline="\n")

    files = copy_root / "tester" / "files"
    info = files / PROBE_INFO
    ticks = files / PROBE_TICKS
    for path in (info, ticks):
        if path.exists():
            path.unlink()

    started = time.perf_counter()
    timed_out = False
    output = ""
    try:
        result = run_program(
            copy_root / "terminal.exe",
            ["/portable", f"/config:{start_file.resolve()}"],
            copy_root=copy_root,
            timeout=timeout,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    except ProgramTimeout:
        timed_out = True
        output = ""
    except UnsafeProgramError as exc:
        raise RunError(str(exc)) from exc
    seconds = time.perf_counter() - started
    tester = copy_root / "tester"
    report_files = sorted(tester.glob("losslens_report*")) if tester.is_dir() else []
    return RunResult(
        timed_out=timed_out,
        seconds=seconds,
        report_files=report_files,
        probe_info=info if info.is_file() else None,
        probe_ticks=ticks if ticks.is_file() else None,
        output=output,
    )
