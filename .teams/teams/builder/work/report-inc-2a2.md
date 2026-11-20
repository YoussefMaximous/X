# inc-2 part A send-back 1 report

Builder · 2026-11-20 · code commit `a1bfc46` · stored tick data and `src/` untouched.

## Summary (10 lines or fewer)

- **Done:** all nine send-back items are closed; 66 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **2b:** catches `from os import system`/`*`, `import os as ...`, every `os.<forbidden>` access even without a call, and `getattr(os, ...)`; clean code passes.
- **2a:** checks the imported submodule too; `from pyarrow import flight` and `fs` fail, `from pyarrow import compute` passes; only exact `losslens`/`losslens.*` counts as ours.
- **2j:** new rule rejects `fs`, `flight` attributes and any name ending `FileSystem`.
- **2c:** any `scheme://` is rejected and the message names the scheme (`s3`, `wss`, `gs`, `file`, ...).
- **2h:** `socket` is found inside words in any case (`SocketCreate` fails).
- **Folders:** root-only `.teams`, `data`, `build`, `dist`; other skip names at any depth; EA files in `.teams` fail.
- **2d/2e:** build tools are pinned to setuptools; every lock package must resolve from registry.npmjs.org with an integrity hash.
- **Checks:** P1–P12 and P14, the six extra changes and the original a–l all exit 1 with file-and-rule messages; the unchanged repository passes.
- **Not verified:** nothing in this send-back; the GitHub workflow is not part of it.

## Done-when checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
..................................................................       [100%]
66 passed in 0.85s
pytest_exit=0

$ python -m ruff check .
All checks passed!
ruff_exit=0

$ python -m ruff format --check .
38 files already formatted
format_exit=0

$ python -m mypy
Success: no issues found in 8 source files
mypy_exit=0
```

The `pytest-current` `PermissionError` still appears after the summary from pytest's atexit cleanup; the exit code is 0.

### 2. Bypasses P1–P12 and P14

Each change was made alone in a copy of the repository (`guard-copy-2`), `pytest` ran, the change was undone. Every case exited 1.

| # | Failure message |
|---|---|
| P1 | `src/losslens/ticks/store.py:250: rule 2b: from os import system is not allowed` |
| P2 | `src/losslens/ticks/store.py:250: rule 2b: import os as another name is not allowed` |
| P3 | `src/losslens/ticks/store.py:250: rule 2b: access to os.system is not allowed` |
| P4 | `src/losslens/ticks/store.py:250: rule 2a: import 'pyarrow.flight' is not approved` |
| P5 | `src/losslens/ticks/store.py:250: rule 2a: import 'pyarrow.fs' is not approved` |
| P6 | `src/losslens/ticks/store.py:250: rule 2c: address scheme 's3' found` |
| P7 | `src/losslens/ticks/store.py:250: rule 2c: address scheme 'wss' found` |
| P8 | `mql4/x.mq4:1: rule 2h: MQL socket found` |
| P9 | `src/losslens/data/x.py:1: rule 3a: order function 'OrderSend(' found` |
| P10 | `docs/build/my_ea.ex4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| P11 | `pyproject.toml: rule 2d: build-system.requires must be exactly {'setuptools'}, found ['setuptools', 'wheel']` |
| P12 | `package-lock.json: rule 2e: node_modules/ansi-regex must resolve from https://registry.npmjs.org/` |
| P14 | `src/losslens/dist/x.txt:1: rule 3c: stored password or investor password found` |

### 3. The six extra changes

All made alone in the same copy and undone; all exited 1.

| Change | Failure message |
|---|---|
| `x = getattr(os, "system")` in `src/` | `src/losslens/ticks/store.py:250: rule 2b: getattr(os, ...) is not allowed` |
| `from os import *` in `src/` | `src/losslens/ticks/store.py:250: rule 2b: from os import * is not allowed` |
| `pa.fs.S3FileSystem()` in `src/` | `src/losslens/ticks/store.py:250: rule 2j: remote filesystem name 'S3FileSystem' found` (also `'fs'`) |
| `.ex4` inside `.teams/teams/builder/work/` | `.teams/teams/builder/work/extra.ex4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| `build-backend` changed | `pyproject.toml: rule 2d: build-system.build-backend must be 'setuptools.build_meta'` |
| lock entry integrity removed | `package-lock.json: rule 2e: node_modules/ansi-regex needs an integrity hash` |

### 4. The original twelve changes still fail

Made alone in a copy and undone; all exited 1.

| Change | Failure message |
|---|---|
| a | `src/losslens/cli.py:399: rule 2a: import 'socket' is not approved` |
| b | `src/losslens/ticks/store.py:250: rule 2a: import 'urllib.request' is not approved` |
| c | `src/losslens/ticks/quality.py:206: rule 2a: import 'subprocess' is not approved` |
| d | `src/losslens/ticks/store.py:252: rule 2b: access to os.system is not allowed` |
| e | `src/losslens/ticks/store.py:250: rule 2c: address scheme 'https' found` |
| f | `pyproject.toml: rule 2d: project.dependencies must be exactly {'pyarrow'}, found ['pyarrow', 'requests']` |
| g | `package.json: rule 2e: dependencies must be exactly {"dukascopy-node": "1.51.1"}` |
| h | `package.json: rule 2e: scripts is not allowed` |
| i | `scratch/x.mq4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| j | `mql4/x.mqh:1: rule 2h: MQL online call 'WebRequest' found` |
| k | `mql4/x.mq4:1: rule 2h: MQL #import found` |
| l | `my_ea.ex4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |

The order-function part of case i also fails rule 3a: `scratch/x.mq4:1: rule 3a: order function 'OrderSend(' found`.

### 5. The repository as it is still passes

The unchanged repository passes all 66 tests; `git diff --stat fad222c..HEAD -- src pyproject.toml package.json` has no output. No production file was edited.

### 6. Only the allowed files changed

The literal `fad222c..HEAD` range also contains the Lead's review commit and the earlier part-A report, so it is not the send-back diff. The code commit is:

```text
$ git show --stat --oneline a1bfc46
a1bfc46 Close guard bypasses: ...
 tests/_guard_scan.py     | 201 ++++++++++++++++++++++++++++++++++++---------
 tests/test_no_network.py | 130 ++++++++++++++++++++++++++++++++---
 2 files changed, 279 insertions(+), 52 deletions(-)
```

The report/handoff commit adds only this report and `HANDOFF.md` (shown in the complete diff below).

From the Lead's review commit (`15f2320`) to HEAD, the complete change list is exactly the two guard test files, this report and `HANDOFF.md`:

```text
$ git diff --name-only 15f2320..HEAD
.teams/teams/builder/HANDOFF.md
.teams/teams/builder/work/report-inc-2a2.md
tests/_guard_scan.py
tests/test_no_network.py
```

No production file changed since `fad222c`; this command has no output:

```text
$ git diff --name-only fad222c..HEAD -- src pyproject.toml package.json README.md .github .gitignore
(no output)
```

## Not verified

Nothing in this send-back. The GitHub workflow is not part of it and cannot be run locally.

## Files changed

- `tests/_guard_scan.py` — expanded 2a, 2b, 2c, 2d, 2e, 2h, 2i, 2j and folder-place scanning.
- `tests/test_no_network.py` — must-flag / must-not-flag samples for every changed rule.
- `tests/test_no_live_trading.py` — unchanged; it inherits the corrected scanners.
