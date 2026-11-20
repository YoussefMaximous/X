"""Compile the probe EA inside the MT4 copy."""

from __future__ import annotations

import shutil
from pathlib import Path

from losslens.ticks.store import repository_root

from .programs import PROBE_NAME, ProgramTimeout, UnsafeProgramError, run_program


class CompileError(RuntimeError):
    """The probe did not compile."""


def compile_probe(copy_root: Path, timeout: float = 120) -> str:
    source = repository_root() / "mql4" / "Experts" / PROBE_NAME
    if not source.is_file():
        raise CompileError(f"probe source not found: {source}")
    experts = copy_root / "MQL4" / "Experts"
    experts.mkdir(parents=True, exist_ok=True)
    target = experts / PROBE_NAME
    shutil.copy2(source, target)
    exe = copy_root / "metaeditor.exe"
    try:
        result = run_program(
            exe,
            [f"/compile:{target}", "/log"],
            copy_root=copy_root,
            timeout=timeout,
        )
    except (UnsafeProgramError, ProgramTimeout) as exc:
        raise CompileError(f"metaeditor did not run safely: {exc}") from exc

    log_path = target.with_suffix(".log")
    log = ""
    if log_path.is_file():
        raw_log = log_path.read_bytes()
        if raw_log.startswith(b"\xff\xfe"):
            log = raw_log.decode("utf-16", errors="replace")
        elif raw_log.count(b"\x00") > len(raw_log) // 4:
            log = raw_log.decode("utf-16-le", errors="replace")
        else:
            log = raw_log.decode("utf-8", errors="replace")
    output = "\n".join(part for part in (result.stdout, result.stderr, log) if part)
    compiled = experts / "LossLensProbe.ex4"
    if not compiled.is_file():
        raise CompileError("LossLensProbe.ex4 was not produced\n" + output)
    if "0 errors" not in output:
        raise CompileError("metaeditor did not report 0 errors\n" + output)
    return output
