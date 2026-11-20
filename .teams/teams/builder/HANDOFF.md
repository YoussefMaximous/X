# Builder handoff — after inc-2 part A send-back 1

Updated: 2026-11-20 · Increment: inc-2 part A send-back 1 · Report: `work/report-inc-2a2.md`

## Goal

Close the ways around the network and no-live-trading guards found by the Lead, changing only the three guard test files, the report and this handoff.

## State and how to check it

All nine send-back items are closed and committed locally (`a1bfc46` code; report in the next commit). `src/`, the stored data, `pyproject.toml` and `package.json` were not changed.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Expected: 66 tests pass; all tools exit 0. The expanded guard tests catch every P1–P12/P14 case, the six extra cases and the original a–l cases; the unchanged repository passes.

## Done (evidence in the report)

- **2b:** `from os import system|*`, `import os as ...`, any `os.<forbidden>` attribute access (called or not), and `getattr(os, ...)` fail. `from os import path`, `import os`, `os.path` and `getattr(other, ...)` pass.
- **2a:** for `from X import Y`, `X` must be approved and `X.Y` must be approved when it is a module. `pyarrow.flight` and `pyarrow.fs` fail; `pyarrow.compute` passes. Only exact `losslens` or `losslens.*` is ours.
- **2j:** `fs`, `flight` attributes and names ending `FileSystem` fail.
- **2c:** any `<scheme>://` fails and names the scheme.
- **2h:** `socket` is found inside any word, any case.
- **Folders:** skip `.teams`, `data`, `build`, `dist` only at the repository root; other skip names at any depth. Rule 2i includes `.teams`.
- **2d:** `build-system.requires` exactly `{setuptools}`, backend exactly `setuptools.build_meta`.
- **2e:** every lock package except the root must resolve from `https://registry.npmjs.org/` and carry an integrity hash.
- No production file changed; the stored tick data was not touched.

## Ruled out / do not retry

- Editing the approved lists: their header still says the Lead changes them through a brief.
- Name-based folder skipping at every depth: it hid `src/losslens/data`, `docs/build` and `src/losslens/dist`; skip by place instead.
- Checking only the top-level module in `from X import Y`: it missed `pyarrow.flight` and `pyarrow.fs`; check the submodule when it is a module.
- Treating `losslens_evil` as ours: only exact `losslens` or `losslens.*` counts.
- Literal bad samples in the test files: they are built from pieces so the repository scan does not trip on its own tests.

## Open

- Lead: review this send-back and run the guard probes again; then inc-2 part B (MT4 run spike) can be added once MT4 is installed.
- User: install IC Markets MT4 and open a demo account (D-13); no MT4 is installed on this PC.
- `pytest` still prints the ignored `pytest-current` Windows symlink `PermissionError` at atexit; exit code is 0.

## Next step

Lead reviews inc-2 part A send-back 1; if accepted, part B starts once MT4 is installed.
