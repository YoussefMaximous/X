# inc-2 part A report — safety guards

Builder · 2026-11-20 · code commit `fad222c` · stored tick data untouched.

## Summary (10 lines or fewer)

- **Done:** both promises are now failing tests — `tests/test_no_network.py` (D-20) and `tests/test_no_live_trading.py` (D-14); 63 tests pass and `ruff`, `ruff format --check`, `mypy` exit 0.
- **Download command:** the stray `dukascopy-node` word is gone; the command is `node`, script, `-i`. The test asserts `cmd[2] == "-i"`, and a live one-day sync through the new path still gives 554,076 rows, first `1772496001086`, last `1772582399247`.
- **Twelve tamper checks:** each change, made alone in a copy of the repository and undone, made `pytest` exit 1; every message names the file and rule (full list below).
- **Network:** an autouse session fixture blocks `socket.connect`, `connect_ex`, `create_connection` and `getaddrinfo`; the required test gets `RuntimeError("network is blocked in tests")`.
- **Dependencies and Node:** pyproject must be exactly `pyarrow` plus dev `pytest/ruff/mypy`; the lock file pins `dukascopy-node` 1.51.1 with an integrity hash and no install scripts.
- **MQL / EA files:** MQL online calls and `#import` are rejected; `.ex4/.ex5/.mq4/.mq5/.mqh` outside `mql4/` are rejected with the exact required sentence; the `.gitignore` lines are added.
- **Setup:** README and both `SetupError` messages use `npm ci --ignore-scripts`; the README says it installs exactly the locked versions, checks checksums, and runs no install script.
- **SAFETY.md:** exact text match (2,152 characters); README links it on line 9, inside the first ten lines. CI has `permissions: contents: read` only.
- **Stored data:** untouched; no sync was run against `data/`. The live syncs used an empty scratch `LOSSLENS_DATA`.
- **Not verified:** the GitHub workflow itself (cannot push; the Lead checks it after pushing). `pytest` still prints the ignored `pytest-current` Windows symlink `PermissionError` at exit; exit code is 0.

## Done-when checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
...............................................................          [100%]
63 passed in 0.84s
pytest_exit=0

$ python -m ruff check .
All checks passed!
ruff_exit=0

$ python -m ruff format --check .
37 files already formatted
format_exit=0

$ python -m mypy
Success: no issues found in 8 source files
mypy_exit=0
```

The `pytest-current` `PermissionError` appears after the summary in pytest's atexit cleanup; it does not change the exit code.

### 2. Each tamper change makes pytest exit 1

Run in a copy of the repository (`guard-copy`), one change at a time, then undone. Every case `exit=1`.

| Change | Failure message (file and rule) |
|---|---|
| a. `import socket` in `src/losslens/cli.py` | `src/losslens/cli.py:399: rule 2a: import 'socket' is not approved` |
| b. `import urllib.request` in `src/losslens/ticks/store.py` | `src/losslens/ticks/store.py:250: rule 2a: import 'urllib.request' is not approved` |
| c. `import subprocess` in `src/losslens/ticks/quality.py` | `src/losslens/ticks/quality.py:206: rule 2a: import 'subprocess' is not approved` |
| d. `os.system("echo")` in `src/` | `src/losslens/ticks/store.py:252: rule 2b: call to os.system is not allowed` |
| e. `https://example.com` in `src/` | `src/losslens/ticks/store.py:250: rule 2c: web address 'https://' found` |
| f. `"requests>=2"` in pyproject dependencies | `pyproject.toml: rule 2d: project.dependencies must be exactly {'pyarrow'}, found ['pyarrow', 'requests']` |
| g. `"dukascopy-node": "^1.51.1"` | `package.json: rule 2e: dependencies must be exactly {"dukascopy-node": "1.51.1"}` |
| h. `"scripts": {}` in package.json | `package.json: rule 2e: scripts is not allowed` |
| i. `scratch/x.mq4` with `OrderSend(...)` | `scratch/x.mq4:1: rule 3a: order function 'OrderSend(' found` and `scratch/x.mq4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| j. `mql4/x.mqh` with `WebRequest(...)` | `mql4/x.mqh:1: rule 2h: MQL online call 'WebRequest' found` |
| k. `mql4/x.mq4` with `#import "user32.dll"` | `mql4/x.mq4:1: rule 2h: MQL #import found` |
| l. empty `my_ea.ex4` in the root | `my_ea.ex4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |

The tamper changes were made in a temporary copy; the real repository was not modified.

### 3. Network is blocked in tests

```text
$ python -m pytest -q tests/test_no_network.py::test_network_is_blocked_in_tests
.                                                                        [100%]
1 passed in 0.14s
exit=0
```

The test calls `socket.create_connection(("127.0.0.1", 9), timeout=1)` and asserts `RuntimeError("network is blocked in tests")`. The autouse session fixture also blocks `socket.socket.connect`, `connect_ex` and `socket.getaddrinfo` for every test.

### 4. Download command has no stray word; live sync is exact

`tests/test_temp.py::test_download_command_uses_node_and_the_package_bin` asserts the captured list is `[node, script, "-i", ...]`; it passes in the 63-test run.

Live one-day sync into an empty scratch store:

```text
$ $env:LOSSLENS_DATA="C:\Users\yr471\AppData\Local\Temp\opencode\inc2a-store"
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04 --force
2026-03-03  complete     554076     6.15s
Summary: 1 day(s), complete=1, empty=0, partial=0, imported=0, failed=0, 6.15s
exit=0
rows 554076
first 1772496001086
last 1772582399247
```

### 5. Fresh copy, `npm ci --ignore-scripts`, one-day sync

```text
$ npm ci --ignore-scripts
added 23 packages, and audited 24 packages in 11s
1 package is looking for funding
found 0 vulnerabilities

$ $env:PYTHONPATH="C:\Users\yr471\AppData\Local\Temp\opencode\inc2a-clean\src"
$ $env:LOSSLENS_DATA="C:\Users\yr471\AppData\Local\Temp\opencode\inc2a-clean-store"
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04 --force
2026-03-03  complete     554076    13.25s
Summary: 1 day(s), complete=1, empty=0, partial=0, imported=0, failed=0, 13.25s
exit=0
rows 554076
first 1772496001086
last 1772582399247
```

The copy was made without `node_modules`; `npm ci --ignore-scripts` installed the locked tree.

### 6. `SAFETY.md` and the README link

```text
$ python ... compare_safety.py
exact match: True
expected chars: 2152 actual chars: 2152
link lines: [9]
```

`SAFETY.md` is byte-for-byte the text in the brief (the comparison extracted the fenced block from `.teams/increments/inc-2.md`). `README.md` line 9 contains “What this software does, and what it never does” and links to it.

### 7. Git status and `.teams`

```text
$ git status --short
(no output)
```

The code commit `fad222c` changed `.github/workflows/ci.yml`, `.gitignore`, `README.md`, `SAFETY.md`, `src/losslens/ticks/dukascopy.py`, `tests/conftest.py`, `tests/test_temp.py` and the three new guard files; it changed nothing under `.teams/`. This report and the updated `HANDOFF.md` are the only later files, both in `.teams/teams/builder/`.

## What was not verified

- The GitHub workflow run itself: the builder cannot push; the Lead will see it after pushing.
- No stored data was re-downloaded or changed; the live syncs used empty scratch stores.

## Files changed

- `src/losslens/ticks/dukascopy.py` — command list, `npm ci --ignore-scripts` messages.
- `README.md`, `SAFETY.md`, `.gitignore`, `.github/workflows/ci.yml`.
- `tests/conftest.py`, `tests/_guard_scan.py`, `tests/test_no_network.py`, `tests/test_no_live_trading.py`, `tests/test_temp.py`.
