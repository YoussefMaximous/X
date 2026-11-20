# Increment inc-2, part A: Safety guards

Planned: 2026-11-20 · Status: part A accepted and pushed 2026-11-20, after two send-backs (judgments below); part B not yet written · Phase: prototype

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

## Judgment on part A (filled in by the Lead, 2026-11-20)

**builder: all seven checks pass, and the work follows the brief. Not accepted yet: the Lead probed the guards and found ways around them. Two are places where the code is looser than the brief; the rest are gaps in the Lead's own brief. Sent back once with eight items.**

What the Lead ran (measured, code at `fad222c`):
- Check 1: 63 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0; no `type: ignore`, `noqa`, skip or xfail.
- Check 2: in a copy of the repository, each of the twelve changes made alone and undone gives `pytest` exit 1 with a message naming the file and the rule. After all were undone: exit 0.
- Check 3: a test that opens a socket fails with "network is blocked in tests".
- Check 4: no word between the script path and `-i`; a forced sync of 2026-03-03 into a scratch store gives 554076 rows, first 1772496001086, last 1772582399247, identical to the stored day in every column.
- Check 5: in the copy without `node_modules`, `npm ci --ignore-scripts` exits 0 and the same sync, run from the copy's code, gives the identical day.
- Check 6: `SAFETY.md` matches the brief's text exactly; the README links to it on line 9.
- Check 7: `git status` clean; nothing under `.teams/` outside the builder's folder was changed; no stored day file was touched.

Ways around the guards (each one measured: the change was made in the copy and `pytest` still exited 0):

| # | Change that was not caught | Whose gap |
|---|---|---|
| P1 | `from os import system` then `system("echo")` in `src/` | builder (brief said "any use") |
| P2 | `import os as o` then `o.system("echo")` | builder |
| P3 | `f = os.system` (no call) | builder |
| P4 | `from pyarrow import flight` | Lead's brief |
| P5 | `from pyarrow import fs` (and `pa.fs` is reachable once `pyarrow.parquet` is imported) | Lead's brief |
| P6 | a string `s3://bucket/ticks` in `src/` | Lead's brief |
| P7 | a string `wss://example.com` in `src/` | Lead's brief |
| P8 | `SocketCreate();` in `mql4/x.mq4` | builder (brief said contains `socket`, not the whole word) |
| P9 | an order call in `src/losslens/data/x.py` (any folder named `data`, `build` or `dist` is skipped at every depth) | Lead's brief was unclear |
| P10 | `docs/build/my_ea.ex4` | same |
| P11 | an extra package in `build-system.requires` | Lead's brief |
| P12 | a `resolved` address in `package-lock.json` pointing away from npm | Lead's brief |
| P14 | a stored password in `src/losslens/dist/x.txt` | same as P9 |

## Send-back 1 of part A: brief for the builder

Close the ways around the guards. Change only `tests/_guard_scan.py`, `tests/test_no_network.py` and `tests/test_no_live_trading.py`. No new dependencies. Do not touch `src/`, the stored data, or the approved lists except where an item below says so. Every item gets a must-flag and a must-not-flag sample test, built from pieces as before.

**1. Rule 2b covers every way of reaching the forbidden `os` functions.** The forbidden names are `system`, `popen`, `startfile`, and any name starting with `exec` or `spawn`. In `src/`, fail on:
- any attribute access `os.<forbidden name>`, called or not (`f = os.system` fails);
- `from os import <forbidden name>` and `from os import *`;
- `import os as <anything>` (the module must keep its own name so the check above sees it);
- a call to the bare name `getattr` whose first argument is the name `os`.

**2. Rule 2a checks what is imported, not only where from.** For `from X import Y` (not relative, not our own package): `X` must be approved as today, and if `X.Y` is itself a module, `X.Y` must be approved too. "Is a module" means `importlib.util.find_spec(f"{X}.{Y}")` returns something; if it raises, treat it as not a module. `from pyarrow import compute` passes; `from pyarrow import flight` and `from pyarrow import fs` fail.

**3. New rule 2j: no remote file systems through pyarrow.** In `src/`, fail on any attribute access whose attribute name is `fs` or `flight`, and on any name or attribute name that ends with `FileSystem`.

**4. Rule 2c catches every address scheme.** Replace the four fixed markers with the regular expression `[A-Za-z][A-Za-z0-9+.\-]*://`. The message names the scheme found. `s3://`, `wss://`, `gs://` and `file://` all fail.

**5. Rule 2h finds `socket` anywhere in a word,** in any letter case: `SocketCreate` fails. No word boundaries.

**6. Folders are skipped by place, not by name alone.**
- Skipped only when they sit directly in the repository root: `.teams`, `data`, `build`, `dist`.
- Skipped at any depth: `.git`, `node_modules`, `.venv`, `.pytest_cache`, `.pytest_tmp`, `.ruff_cache`, `.mypy_cache`, `__pycache__`, and folders ending in `.egg-info`.
- Rule 2i (EA files) does not skip `.teams`: an EA file there fails too.

**7. Rule 2d also fixes the build tools.** In `pyproject.toml`, the names in `build-system.requires` must be exactly `{setuptools}` and `build-system.build-backend` must be exactly `setuptools.build_meta`.

**8. Rule 2e checks where every Node package comes from.** In `package-lock.json`, every entry in `packages` except the root entry `""` must have a `resolved` that starts with `https://registry.npmjs.org/` and a non-empty `integrity`.

**9. Rule 2a, own package.** A name counts as ours only if it is exactly `losslens` or starts with `losslens.`.

**Done when** (the Lead runs these):
1. `python -m pytest -q`, `python -m ruff check .`, `python -m ruff format --check .` and `python -m mypy` all exit 0.
2. Each change P1 to P12 and P14 in the table above, made alone in a copy of the repository and undone, makes `python -m pytest -q` exit 1 with a message that names the file and the rule.
3. Also failing, each alone: `x = getattr(os, "system")` in `src/`; `from os import *` in `src/`; `pa.fs.S3FileSystem()` in `src/`; an `.ex4` file inside `.teams/teams/builder/work/`; `build-backend` changed to another value; a `packages` entry in the lock with its `integrity` removed.
4. The twelve changes of the first brief (a to l) still fail.
5. Still passing with no change to `src/`: the repository as it is.
6. `git diff --stat` between `fad222c` and your new commit shows changes only in the three test files named above, your report and your `HANDOFF.md`.

**Return:** `.teams/teams/builder/work/report-inc-2a2.md` in the same form, with the failure message for every change in checks 2 and 3, and an updated `HANDOFF.md`.

## Judgment on send-back 1 of part A (filled in by the Lead, 2026-11-20)

**builder: all nine items done correctly, all six checks pass. Not accepted yet for a reason that is not the builder's: a second round of probes by the Lead found two more ways around the guards, both gaps in the Lead's briefs. Sent back with two items.**

What the Lead ran (measured, code at `a1bfc46`, in a copy of the repository, each change alone and undone):
- Check 1: 66 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0; no suppression.
- Checks 2, 3 and 4: P1 to P12 and P14, the six extra changes, and the first brief's twelve (a to l) each give `pytest` exit 1 with a message naming the file and the rule. After all were undone: exit 0.
- Check 5 and 6: the repository as it is passes; only `tests/_guard_scan.py`, `tests/test_no_network.py`, the report and the builder's `HANDOFF.md` changed.
- New probes that were caught: `from os import system as s`; an import inside a function; `importlib`, `asyncio`, `ctypes`, `webbrowser`; `from subprocess import run` outside the allowed file; `import os, socket` on one line; `MY.EX4` in capitals; a tab-indented `#import` in `mql4/sub/`; an investor password and an order call in the README.

New probes that were **not** caught (`pytest` still exited 0):

| # | Change | Why it gets through |
|---|---|---|
| N1 | `scripts/upload.py` containing `import requests` | Python files are only checked under `src/` |
| N2 | `setup.py` in the root containing `import urllib.request` | same |
| N13 | `conftest.py` in the root containing `import socket` | same |
| N10 | `src/losslens/x.pyw` containing `import socket` | only `*.py` is read |
| N3 | `tools/send.ps1` that posts a file to a web address | no rule about other kinds of script |
| N11 | a second `subprocess.run([...])` added to `dukascopy.py` | the file is allowed to use `subprocess` without limit |
| N12 | `subprocess.Popen([...])` added to `dukascopy.py` | same |

What a text scan cannot catch, stated once: code written to hide on purpose (for example reaching `os` through `sys.modules`). The guards are for mistakes and careless changes; the Lead's review of every change covers the rest.

## Send-back 2 of part A: brief for the builder

Two new rules. Change only `tests/_guard_scan.py` and `tests/test_no_network.py`. No new dependencies. Do not touch `src/` or the stored data. Each rule gets a must-flag and a must-not-flag sample test.

**1. New rule 2k: code lives only where the guards look.**
- Walk the repository with the existing walker, with `.teams` included (as rule 2i does).
- A file is a "code file" if its suffix, lower-cased, is one of:

```text
.py .pyw .pyi .pyc .pyd .ipynb
.js .mjs .cjs .ts .tsx .jsx
.ps1 .psm1 .bat .cmd .sh .vbs .wsf
.exe .dll .msi .scr .com .jar .lnk
```

- The only code files allowed are `.py` files whose path starts with `src/` or `tests/`. Every other code file fails, with this message after the file name: "rule 2k: code files are allowed only as .py under src/ or tests/. Ask the Lead before adding code anywhere else."
- The two lists (suffixes, allowed places) are constants in `tests/test_no_network.py` under the SAFETY GUARD comment. MQL files stay under rule 2i.

**2. New rule 2l: the one file that may start a program starts exactly one.**
- Change `SUBPROCESS_ALLOWED` from a set into a mapping from file to the number of program starts allowed: `{"src/losslens/ticks/dukascopy.py": 1}`. Rule 2a keeps using its keys.
- In each file of that mapping, fail on:
  - `import subprocess as <anything>` and any `from subprocess import ...`;
  - any attribute of the name `subprocess` other than `run`, `DEVNULL` and `TimeoutExpired` (so `subprocess.Popen`, `subprocess.call`, `subprocess.check_output` fail);
  - a number of `subprocess.run` accesses different from the number in the mapping. The message says how many were found and how many are allowed.

**Done when** (the Lead runs these):
1. `python -m pytest -q`, `python -m ruff check .`, `python -m ruff format --check .` and `python -m mypy` all exit 0.
2. Each change N1, N2, N3, N10, N11, N12 and N13 in the table above, made alone in a copy of the repository and undone, makes `python -m pytest -q` exit 1 with a message that names the file and the rule.
3. Also failing, each alone: `import subprocess as sp` in `dukascopy.py`; `from subprocess import run` in `dukascopy.py`; a file `notes/run.bat`; a file `.teams/teams/builder/work/helper.py`.
4. Every change from the two earlier briefs still fails; the repository as it is still passes.
5. Only `tests/_guard_scan.py`, `tests/test_no_network.py`, your report and your `HANDOFF.md` changed.

**Return:** `.teams/teams/builder/work/report-inc-2a3.md` in the same form, and an updated `HANDOFF.md`.

## Judgment on send-back 2 of part A (filled in by the Lead, 2026-11-20)

**builder: accepted. inc-2 part A (safety guards) is accepted and pushed.**

What the Lead ran (measured, code at `e33bfb0`, in a copy of the repository, each change alone and undone):
- Check 1: 70 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0; no suppression.
- Checks 2, 3 and 4: 45 changes, each caught with `pytest` exit 1 and the expected rule named: the first brief's twelve and the socket test; P1 to P12 and P14; the six extras of send-back 1; N1, N2, N3, N10, N11, N12, N13; the four extras of send-back 2; plus `tests/tool.js` (2k) and `subprocess.check_output` in `dukascopy.py` (2l). After all were undone: exit 0.
- Check 5: only `tests/_guard_scan.py`, `tests/test_no_network.py`, the report and the builder's `HANDOFF.md` changed; no production file changed since `fad222c`.

The guard rules now in force: 2a approved imports (and imported submodules), 2b no hidden execution through `os`, 2c no address of any scheme in `src/`, 2d exact Python dependencies and build tools, 2e pinned Node side with npm-registry sources and checksums, 2f only `ticks sync` starts a program, 2g network blocked in tests, 2h no online call or DLL import in MQL files, 2i no EA files outside `mql4/`, 2j no remote file systems, 2k code only as `.py` under `src/` or `tests/`, 2l exactly one program start in the one allowed file, 3a no order function, 3b no trading library, 3c no stored password.

Known limit, accepted: code written to hide on purpose is outside what these scans can see. Review of every change covers that.

When later parts add code in new places (`mql4/`, the app), the Lead extends the approved lists in the brief for that part, and adds the guards those parts need (tester-only start file, reference EA allowed to hold order functions and required to check `IsTesting()`, server bound to `127.0.0.1`, no outside address in app screens).
