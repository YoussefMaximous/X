# inc-2 part A send-back 2 report

Builder · 2026-11-20 · code commit `e33bfb0` · `src/`, stored data and dependency files untouched.

## Summary (10 lines or fewer)

- **Done:** rules 2k and 2l are in place; 70 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **2k:** code files are only `.py` under `src/` or `tests/`; the walker includes `.teams`; every other code suffix or place fails with the exact required message.
- **2l:** `SUBPROCESS_ALLOWED` is now `{"src/losslens/ticks/dukascopy.py": 1}`; aliased/from imports fail, `Popen`/`call`/other attributes fail, and the number of `subprocess.run` accesses must be exactly one.
- **N probes:** N1, N2, N3, N10, N11, N12 and N13 each exit 1 with a file-and-rule message.
- **Extra probes:** `import subprocess as sp`, `from subprocess import run`, `notes/run.bat` and `.teams/.../helper.py` each exit 1.
- **Earlier probes:** all 31 changes from the two earlier briefs (P1–P12, P14, E1–E6, a–l) still exit 1; the unchanged repository passes.
- **Changed files:** only `tests/_guard_scan.py`, `tests/test_no_network.py`, this report and `HANDOFF.md`; no `src/`, package, README or data changes.
- **Not verified:** nothing in this send-back; GitHub Actions is not part of it.
- Note: `pytest` still prints the ignored `pytest-current` Windows symlink `PermissionError` at atexit; exit code is 0.

## Done-when checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
......................................................................   [100%]
70 passed in 0.90s
pytest_exit=0

$ python -m ruff check .
All checks passed!
ruff_exit=0

$ python -m ruff format --check .
39 files already formatted
format_exit=0

$ python -m mypy
Success: no issues found in 8 source files
mypy_exit=0
```

### 2. N1–N13

Each change was made alone in a copy of the repository, `pytest` ran, and the change was undone. Every case exited 1.

| # | Failure message |
|---|---|
| N1 | `scripts/upload.py: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |
| N2 | `setup.py: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |
| N3 | `tools/send.ps1: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |
| N10 | `src/losslens/x.pyw: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |
| N11 | `src/losslens/ticks/dukascopy.py: rule 2l: found 2 subprocess.run accesses, allowed 1` |
| N12 | `src/losslens/ticks/dukascopy.py:237: rule 2l: subprocess.Popen is not allowed` |
| N13 | `conftest.py: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |

### 3. Four extra changes

| Change | Failure message |
|---|---|
| `import subprocess as sp` in `dukascopy.py` | `src/losslens/ticks/dukascopy.py:235: rule 2l: import subprocess as another name is not allowed` |
| `from subprocess import run` in `dukascopy.py` | `src/losslens/ticks/dukascopy.py:235: rule 2l: from subprocess import ... is not allowed` |
| `notes/run.bat` | `notes/run.bat: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |
| `.teams/teams/builder/work/helper.py` | `.teams/teams/builder/work/helper.py: rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else.` |

### 4. Earlier probes and the unchanged repository

All 31 earlier probes still exit 1 in a copy, with the same rules as before:

- P1–P3 rule 2b; P4–P5 rule 2a; P6–P7 rule 2c; P8 rule 2h; P9 rule 3a; P10 rule 2i; P11 rule 2d; P12 rule 2e; P14 rule 3c.
- E1–E2 rule 2b; E3 rule 2j; E4 rule 2i; E5 rule 2d; E6 rule 2e.
- a–c rule 2a; d rule 2b; e rule 2c; f rule 2d; g–h rule 2e; i rule 2i (and 3a); j–k rule 2h; l rule 2i.

The repository as it is passes: 70 tests, all four tools exit 0. A source scan of the unchanged tree finds no 2k or 2l problem.

### 5. Only the allowed files changed

```text
$ git diff --name-only 38b358e..HEAD
.teams/teams/builder/HANDOFF.md
.teams/teams/builder/work/report-inc-2a3.md
tests/_guard_scan.py
tests/test_no_network.py
```

No `src/`, `pyproject.toml`, `package.json`, README, workflow or data file changed. `git status --short` is clean after the commits.

## Not verified

Nothing in this send-back. GitHub Actions is not part of it and cannot be run locally.

## Files changed

- `tests/_guard_scan.py` — `check_code_files` (2k) and `check_subprocess_use` (2l).
- `tests/test_no_network.py` — `CODE_SUFFIXES`, `CODE_ALLOWED_PREFIXES`, `SUBPROCESS_ALLOWED` mapping, must-flag/must-not-flag tests for 2k and 2l.
