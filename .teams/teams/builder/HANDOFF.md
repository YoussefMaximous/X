# Builder handoff — after inc-2 part A send-back 2

Updated: 2026-11-20 · Increment: inc-2 part A send-back 2 · Report: `work/report-inc-2a3.md`

## Goal

Close the two remaining guard gaps: code files outside the guarded places, and the single allowed program start.

## State and how to check it

Rules 2k and 2l are in place and committed locally (`e33bfb0` code; report in the next commit). `src/`, the stored data and dependency files were not changed.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Expected: 70 tests pass; all tools exit 0. The new guard scans are clean on the repository, and every N probe and earlier probe fails in a copy.

## Done (evidence in the report)

- **2k code-place:** only `.py` files under `src/` or `tests/` are allowed; the walker includes `.teams`; all other suffixes/places fail with the exact message. `scripts/upload.py`, `setup.py`, `tools/send.ps1`, `src/losslens/x.pyw`, root `conftest.py`, `notes/run.bat` and `.teams/.../helper.py` each fail.
- **2l subprocess:** `SUBPROCESS_ALLOWED = {"src/losslens/ticks/dukascopy.py": 1}`. Aliased `subprocess` imports and any `from subprocess import ...` fail; `Popen`/`call`/other attributes fail; the file must contain exactly one `subprocess.run` access. N11 and N12 fail as required.
- **Earlier probes:** all 31 from the two earlier briefs (P1–P12, P14, E1–E6, a–l) still exit 1; the repository passes.
- **Changed files:** only `tests/_guard_scan.py`, `tests/test_no_network.py`, this report and `HANDOFF.md`; `git status` is clean after the commits.
- No stored data was touched.

## Ruled out / do not retry

- Checking only `src/*.py`: Python files in the root, scripts, powershell, batch and `.pyw` stayed hidden; 2k now walks the repository and checks suffixes.
- Allowing `subprocess` anywhere in `dukascopy.py`: the file may start exactly one program; 2l counts `subprocess.run` and rejects other attributes/import forms.
- Editing `src/` to satisfy the guards: no production code was changed.
- Literal bad samples in the test files: samples are built from pieces so the scans do not trip on their own tests.

## Open

- Lead: review this send-back and probe again; then inc-2 part B (MT4 run spike) can be added once MT4 is installed.
- User: install IC Markets MT4 and open a demo account (D-13); no MT4 is installed on this PC.
- `pytest` still prints the ignored `pytest-current` Windows symlink `PermissionError` at atexit; exit code is 0.

## Next step

Lead reviews inc-2 part A send-back 2; if accepted, part B starts once MT4 is installed.
