"""MT4 program starts: the only place that runs a program, and it is strict."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .startfile import check_start_file

TERMINAL_NAME = "terminal.exe"
METAEDITOR_NAME = "metaeditor.exe"
PROBE_NAME = "LossLensProbe.mq4"


class UnsafeProgramError(RuntimeError):
    """A program start was refused before anything ran."""


class ProgramTimeout(RuntimeError):
    """A started MT4 program did not finish before its timeout."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _check_terminal_args(copy_root: Path, args: list[str]) -> None:
    if not args or args[0] != "/portable":
        raise UnsafeProgramError("terminal.exe must start with /portable")
    if len(args) != 2:
        raise UnsafeProgramError("terminal.exe takes exactly /portable and one start file")
    start_arg = args[1]
    if start_arg.startswith("/config:"):
        start_text = start_arg[len("/config:") :]
    else:
        start_text = start_arg
    start_file = Path(start_text)
    if not start_file.is_absolute():
        start_file = copy_root / start_file
    if not _inside(start_file, copy_root):
        raise UnsafeProgramError("the start file must be inside the copy folder")
    if start_file.name != "losslens_start.ini":
        raise UnsafeProgramError("only losslens_start.ini may be used as a start file")
    if not start_file.is_file():
        raise UnsafeProgramError(f"start file not found: {start_file}")
    problems = check_start_file(start_file.read_text(encoding="utf-8", errors="replace"))
    if problems:
        raise UnsafeProgramError("start file refused: " + "; ".join(problems))


def _check_metaeditor_args(copy_root: Path, args: list[str]) -> None:
    if len(args) not in (1, 2):
        raise UnsafeProgramError("metaeditor.exe takes /compile and optional /log")
    if not args[0].startswith("/compile:"):
        raise UnsafeProgramError("metaeditor.exe takes a /compile: path")
    if len(args) == 2 and args[1] != "/log":
        raise UnsafeProgramError("only /log may follow the compile path")
    source = Path(args[0][len("/compile:") :].strip('"'))
    if not source.is_absolute():
        source = copy_root / source
    expected = copy_root / "MQL4" / "Experts" / PROBE_NAME
    if source.resolve() != expected.resolve():
        raise UnsafeProgramError("metaeditor.exe may compile only MQL4\\Experts\\LossLensProbe.mq4")
    if not _inside(source, copy_root):
        raise UnsafeProgramError("the compile file must be inside the copy folder")


def run_program(
    program: Path,
    args: list[str],
    *,
    copy_root: Path,
    timeout: float,
) -> Any:
    name = program.name.lower()
    if name not in {TERMINAL_NAME, METAEDITOR_NAME}:
        raise UnsafeProgramError(f"{program.name} is not an allowed MT4 program")
    if not _inside(program, copy_root) or not program.is_file():
        raise UnsafeProgramError("the program must be inside the copy folder")
    if name == TERMINAL_NAME:
        _check_terminal_args(copy_root, args)
    else:
        _check_metaeditor_args(copy_root, args)

    try:
        return subprocess.run(
            [str(program), *args],
            cwd=str(copy_root),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProgramTimeout(f"program did not finish within {timeout} seconds") from exc
