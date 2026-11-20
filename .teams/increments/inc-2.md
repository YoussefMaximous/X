# Increment inc-2, part A: Safety guards

Planned: 2026-11-20 · Status: with the builder · Phase: prototype

Part B (the MT4 run spike) will be added to this file after part A is accepted. Do not start it.

## Goal
The two promises in `AGENTS.md` become tests that fail the build: this software never trades (D-14) and nothing leaves the PC (D-20). They are in place before any MT4 code or app code exists, so every later change is checked by them.

## Done when
The Lead runs these on this PC. All commands run from the repository root.

1. `python -m pytest -q`, `python -m ruff check .`, `python -m ruff format --check .` and `python -m mypy` all exit 0.
2. Each change below, made alone and then undone, makes `python -m pytest -q` exit 1 with a message that names the file and the rule broken:
   a. `import socket` added to `src/losslens/cli.py`
   b. `import urllib.request` added to `src/losslens/ticks/store.py`
   c. `import subprocess` added to `src/losslens/ticks/quality.py`
   d. `os.system("echo")` added to any file in `src/`
   e. a string containing `https://example.com` added to any file in `src/`
   f. `"requests>=2"` added to `dependencies` in `pyproject.toml`
   g. `"dukascopy-node": "^1.51.1"` in `package.json`
   h. a `"scripts"` section added to `package.json`
   i. a new file `scratch/x.mq4` containing `OrderSend(Symbol(),0,0.1,Ask,3,0,0);`
   j. a new file `mql4/x.mqh` containing `WebRequest("GET","x",h,5000,d,r,rh);`
   k. a new file `mql4/x.mq4` containing `#import "user32.dll"`
   l. a new empty file `my_ea.ex4` in the repository root
3. A test that tries `socket.create_connection(("127.0.0.1", 9), timeout=1)` gets the "network is blocked in tests" error, not a connection error.
4. The download command list has no word between the script path and `-i`. A forced sync of 2026-03-03 into an empty scratch store (`LOSSLENS_DATA`) still gives 554076 rows, first `ts_ms` 1772496001086, last `ts_ms` 1772582399247.
5. In a fresh copy of the repository without `node_modules`, `npm ci --ignore-scripts` followed by that same one-day sync works.
6. `SAFETY.md` exists with exactly the text given below, and `README.md` links to it in its first ten lines.
7. `git status` is clean after your commits, and nothing under `.teams/` outside `.teams/teams/builder/` was changed.

## Owners and contributions
| Area | Owner | Others contribute |
|---|---|---|
| everything outside `.teams/` (except `AGENTS.md`) | builder | lead: review |

## Brief

### builder

**Your area:** every file outside `.teams/` except `AGENTS.md`; plus `.teams/teams/builder/`.

**Inputs:** `AGENTS.md`; `.teams/ARCHITECTURE.md`, sections "Safety" and "Privacy"; decisions D-14 and D-20.

**No new dependencies.** Do not touch the stored data in `data/`.

**Bias reminder:** these tests exist to catch a careless change by a person or an AI later. Make them strict and their failure messages plain. Do not make them clever.

#### Item 1. Remove the stray word from the download command
In `src/losslens/ticks/dukascopy.py` the command list is `[node, script, "dukascopy-node", "-i", ...]`. The third item is left over from the `npx` form. Remove it. Extend `test_download_command_uses_node_and_the_package_bin` to assert that the item after the script path is `"-i"`.

#### Item 2. `tests/test_no_network.py`
The lists below are constants at the top of the file, under this comment, word for word:

```python
# SAFETY GUARD (D-20). Only the Lead changes these lists, through a brief.
# If this test fails, do not edit the lists: change your code, or stop and ask.
```

Rules to check, each as its own test function with a failure message that names the file, the line and the rule:

**2a. Imports in `src/` come from an approved list.** Parse every `.py` file under `src/` with `ast`. For `import a.b` the name checked is `a.b`. For `from a.b import c` the name checked is `a.b`. Relative imports (`from . import x`, `from .store import y`) and anything starting with `losslens` are allowed. Every other name must be exactly one of:

```text
__future__ abc argparse bisect collections collections.abc contextlib csv dataclasses
datetime decimal enum functools hashlib io itertools json math os pathlib re shutil
statistics struct sys tempfile time tomllib typing zoneinfo
pyarrow pyarrow.compute pyarrow.csv pyarrow.parquet
```

`subprocess` is allowed only in the files in this list: `src/losslens/ticks/dukascopy.py`.

**2b. No hidden ways around 2a.** In `src/`, fail on: a call to the bare name `eval`, `exec`, `compile` or `__import__` (a method such as `re.compile` is fine); any use of `os.system`, `os.popen`, `os.startfile`, or an `os` attribute whose name starts with `exec` or `spawn`.

**2c. No web address in `src/`.** Fail if any `.py` file under `src/` contains `http://`, `https://`, `ftp://` or `ws://` anywhere, including comments.

**2d. Dependencies are exactly the approved ones.** Read `pyproject.toml` with `tomllib`. The package names in `project.dependencies` must be exactly `{pyarrow}`. The names in `project.optional-dependencies.dev` must be exactly `{pytest, ruff, mypy}`. There must be no other optional-dependency group. (Compare names only, lower-case, without version parts.)

**2e. The Node side is pinned.** `package.json`: `dependencies` must be exactly `{"dukascopy-node": "1.51.1"}`; there must be no `devDependencies`, `optionalDependencies` or `scripts` key. `package-lock.json`: the entry `packages["node_modules/dukascopy-node"]` has `version` `1.51.1` and a non-empty `integrity`; no entry in `packages` has `hasInstallScript`.

**2f. Only `ticks sync` can start another program.** A test that replaces `subprocess.run` and `subprocess.Popen` with functions that raise, then runs `ticks status`, `ticks verify`, `ticks query` and `ticks import` (the fixture CSV) through `main()` on a store in `tmp_path`, and all four still succeed.

**2g. The network is blocked while tests run.** In `tests/conftest.py` add an autouse, session-wide fixture that replaces `socket.socket.connect`, `socket.socket.connect_ex`, `socket.create_connection` and `socket.getaddrinfo` with functions that raise `RuntimeError("network is blocked in tests")`. Add the test described in "Done when" 3.

**2h. Our MT4 files cannot go online.** For every `.mq4`, `.mq5` and `.mqh` file in the repository: fail if it contains `WebRequest`, `SendMail`, `SendFTP`, `SendNotification`, `InternetOpen`, `InternetConnect`, `HttpOpenRequest`, `URLDownloadToFile` or `socket` (case-insensitive for the last), or a line that starts with `#import` after leading spaces. There are no such files today; see "Proving the scanners work" below.

**2i. No EA files in the repository folder.** Fail if any `.ex4`, `.ex5`, `.mq4`, `.mq5` or `.mqh` file exists in the repository outside the folder `mql4/` (which does not exist yet and will hold our own MT4 files). The message must say: "EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy." Also add these lines to `.gitignore`:

```text
*.ex4
*.ex5
*.mq4
*.mq5
*.mqh
!mql4/**
```

#### Item 3. `tests/test_no_live_trading.py`
Same comment block at the top, with `(D-14)` in place of `(D-20)`.

**3a. No order function anywhere.** Walk every text file in the repository (see "Which files are scanned"). Fail if any file contains a match for the regular expression `\bOrder(Send|Close|CloseBy|Modify|Delete)\s*\(`. The list of files allowed to contain one is a constant, `ORDER_FUNCTION_ALLOWED: frozenset[str] = frozenset()`, empty today. The test file itself is skipped by name.

**3b. No trading or broker library.** Covered for `src/` by 2a and 2d. In this file add one test that fails if any of these names appears as a dependency in `pyproject.toml` or `package.json`: `MetaTrader5`, `metaapi`, `ccxt`, `oandapyV20`, `ib_insync`, `ibapi`, `alpaca`, `binance`, `fxcmpy`, `pymt5`, `zmq`, `pyzmq`.

**3c. No stored login.** Fail if any scanned text file contains a match for `(?i)\b(password|passwd|investor[_ ]?password)\s*[=:]\s*\S`.

#### Which files are scanned (items 2h, 2i, 3a, 3c)
Walk the repository root found by `repository_root()`. Skip these folders entirely: `.teams` (planning text, which names these functions in order to forbid them), `.git`, `node_modules`, `data`, `.venv`, `.pytest_cache`, `.pytest_tmp`, `.ruff_cache`, `.mypy_cache`, `__pycache__`, `build`, `dist`, and any folder ending in `.egg-info`. A file is "text" if its first 4096 bytes contain no zero byte; read it as UTF-8 with `errors="replace"`. Put the walking and scanning helpers in `tests/_guard_scan.py` so both test files share them.

#### Proving the scanners work
A guard that passes because it looks at nothing is worthless. For every rule in items 2 and 3, the helper that does the checking must be a function that takes text (or a parsed structure) and returns the list of problems, and there must be a test that calls it with a bad sample and asserts a problem is returned, and with a clean sample and asserts none is. Bad samples are built inside the test from pieces (for example `"Order" + "Send("`) so the samples themselves do not trip the repository scan.

#### Item 4. Setup uses the lock file exactly
Change the setup command in `README.md`, and in the two `SetupError` messages in `dukascopy.py`, from `npm install` to `npm ci --ignore-scripts`. Add one sentence to the README: it installs exactly the versions in `package-lock.json`, checks their checksums, and runs no install script.

#### Item 5. `SAFETY.md`
Create `SAFETY.md` in the repository root with exactly this text, and link to it from the first ten lines of `README.md` with the words "What this software does, and what it never does".

```markdown
# What this software does, and what it never does

loss-lens tests MT4 expert advisors (EAs) against stored price history, on your own PC. This page lists everything it touches. Each line can be checked against the code.

## It never trades
- It contains no code that can place, change or close an order on any account, demo or real.
- It never asks for, reads or stores an account number or a password.

## It never sends anything out
- No telemetry, no analytics, no crash reports, no update checks, no accounts, no cloud.
- It goes online for one thing only: downloading public price history from Dukascopy, and only when you run the download yourself. The request names a symbol and a date. It carries nothing about you, your EAs or your results.
- Nothing is downloaded when the software starts, in the background, or on a timer.

## It leaves your EAs alone
- It does not upload, send or copy an EA anywhere.
- EA files (`.ex4`, `.mq4`, `.mqh`) do not belong in this folder and are never added to this repository. Keep them in MT4's own folder.

## What it writes
- Only its own `data` folder (or the folder named in `LOSSLENS_DATA`), and a temporary folder that is deleted after each download.

## How this is enforced
- `tests/test_no_network.py` fails if network code, a web address, an unapproved dependency or an EA file appears.
- `tests/test_no_live_trading.py` fails if an order function, a trading library or a stored password appears.
- Both run with the normal tests on every change. The tests themselves run with the network blocked.

## Limits, said plainly
- The download is done by `dukascopy-node` 1.51.1, an open-source tool by another author, pinned to that exact version and checked by checksum. It starts Chrome or Edge in the background to fetch the price files.
- Setting up the software downloads its building blocks once from PyPI and npm.
- If you open this folder with an AI assistant, that assistant sends the files it reads to its own provider. That is the assistant, not this software. Keep your EAs out of this folder.
- This covers the official repository. A copy changed by someone else is that person's software.
```

#### Item 6. Continuous integration
In `.github/workflows/ci.yml` add, at the top level under `on:`:

```yaml
permissions:
  contents: read
```

Change nothing else in that file.

#### Not in this increment
The server address check, the check for outside addresses in app screens, the tester start-file check and the reference EA arrive with the code they guard. A Python lock file with checksums arrives with the ship step. Do not build them now.

**Return:** `.teams/teams/builder/work/report-inc-2a.md` in the same form as your earlier reports (summary of 10 lines or fewer, then each "Done when" check with the command and its real output; for check 2, the failure message each of the twelve changes produced), and an updated `HANDOFF.md`. List anything you could not verify under "not verified". If a rule above cannot be met without changing an approved list, stop and say so in the report; do not change the list.
