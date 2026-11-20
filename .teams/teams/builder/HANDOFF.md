# Builder handoff — after inc-2 part A

Updated: 2026-11-20 · Increment: inc-2 part A (safety guards) · Report: `work/report-inc-2a.md`

## Goal

Make the two promises in `AGENTS.md` fail the build: this software never trades (D-14) and nothing leaves the PC (D-20), before any MT4 or app code exists.

## State and how to check it

Part A is fixed and committed locally (`fad222c` code; report in the next commit). The real tick store was not re-downloaded or written.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest -q tests/test_no_network.py::test_network_is_blocked_in_tests
```

Expected: 63 tests pass; all tools exit 0; the network test passes with `RuntimeError("network is blocked in tests")`. `git status` is clean after the report commit.

## Done (evidence in the report)

- `tests/test_no_network.py` enforces (2a) approved imports in `src/`, `subprocess` only in the downloader; (2b) no `eval`/`exec`/`compile`/`__import__`, no `os.system`/`popen`/`startfile`/`exec*`/`spawn*`; (2c) no web address in `src/`; (2d) exact pyproject dependencies; (2e) exact Node pin and lock integrity, no install scripts; (2f) only `ticks sync` may start a process; (2g) network blocked in all tests; (2h) no MQL online calls/`#import`; (2i) no EA files outside `mql4/`.
- `tests/test_no_live_trading.py` enforces (3a) no order function anywhere (test file itself skipped; allowed set empty); (3b) no trading/broker library; (3c) no stored login. Proving tests for every scanner use bad samples built from pieces.
- `tests/_guard_scan.py` holds the shared scanners; the required comment blocks are at the top of both guard files.
- Twelve tamper changes in a copy, one at a time, all made `pytest` exit 1 with a file-and-rule message (table in the report).
- Download command: `[node, script, "-i", ...]`; test asserts `cmd[2] == "-i"`. Live scratch sync: 554,076 rows, first `1772496001086`, last `1772582399247`.
- Fresh copy with no `node_modules`: `npm ci --ignore-scripts` installed 23 packages; one-day sync gave the same exact result.
- `SAFETY.md` is byte-for-byte the brief's text; README links it on line 9. CI has `permissions: contents: read`.
- Stored data untouched: no sync against `data/`; live syncs used empty scratch `LOSSLENS_DATA`.

## Ruled out / do not retry

- Editing the approved import/dependency lists to make a test pass: the guard header says change the code or ask the Lead.
- Scanning `.teams` for order/network words: it is planning text and is skipped, as the brief says.
- Using `npx` or `cmd.exe` for downloads: run `node` directly; the command list is now `[node, script, "-i", ...]`.
- Putting test sample strings in the repository literally: bad samples are built from pieces so the guard scans do not trip on their own test file.

## Open

- Lead: push and run the GitHub workflow; it cannot be run locally.
- Lead: review inc-2 part A, then add part B (the MT4 run spike) when ready.
- User: install IC Markets MT4 and open a demo account (D-13); no MT4 is installed on this PC.
- `pytest` still prints the ignored `pytest-current` Windows symlink `PermissionError` at atexit; exit code is 0.

## Next step

Lead reviews the safety guards; if accepted, inc-2 part B can start once MT4 is installed.
