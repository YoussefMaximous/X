# inc-1c report — send-back 2

Builder · 2026-11-20 · code commit `ee21cfb` · real tick store not modified.

## Summary (10 lines or fewer)

- **Done:** all three send-back items are fixed; 41 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **1 Ctrl+C path:** the downloader now runs `node <package bin>` directly, not through the `npx.cmd` batch file, with `stdin=subprocess.DEVNULL`. A missing `node` or missing `dukascopy-node` bin entry is a `SetupError`.
- **Live download:** a real March 3 download through the new `node` path wrote 554,076 rows with first `1772496001086` and last `1772582399247` (run against an empty scratch store, not the reviewed data).
- **2 Stray files:** with no `--from`/`--to`, verify scans every `*.parquet` under the symbol folder, before the first manifest day and after the last; with a range it stays limited.
- **3 Report path:** verify now stores and prints the exact path it wrote. With `LOSSLENS_DATA` set, the printed path is under that folder.
- **Stored data:** unchanged — 276 complete, 47 empty, 1 partial; 2026-03-03 still 554,076 rows; completed-day ticks still 83,496,260. No real sync was run.
- **Not verified:** the live Ctrl+C check (#2 of Done when). This non-interactive shell has no console that raises Python's `KeyboardInterrupt`; control events kill the child with exit 1. The brief says this may be listed as not verified.
- **Covered instead:** tests assert the command starts with the `node` path and the bin script from `package.json`, that `stdin` is `DEVNULL`, that `main` returns 130 on `KeyboardInterrupt`, and that the temp folder is removed.
- **Note:** `pytest` exits 0 but still prints the ignored `pytest-current` symlink `PermissionError` from pytest's own Windows temp cleanup.
- **No questions.**

## Checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
.........................................                                [100%]
41 passed in 0.77s
pytest_exit=0

$ python -m ruff check .
All checks passed!
ruff_exit=0

$ python -m ruff format --check .
31 files already formatted
format_exit=0

$ python -m mypy
Success: no issues found in 8 source files
mypy_exit=0
```

The `pytest-current` `PermissionError` is printed after the test summary by pytest's atexit cleanup; the exit code is 0.

### 2. A real Ctrl+C five seconds into a download

**Not verified.** The send-back brief allows this. This shell is non-interactive: sending a console control event to a child in a new console terminates it with exit 1 instead of raising `KeyboardInterrupt`, so it cannot demonstrate the 130 exit path. The Lead's real-console check remains.

What is verified instead:

- `test_download_command_uses_node_and_the_package_bin` — the captured command list starts with the fake `node` path and the script path read from `node_modules/dukascopy-node/package.json` (`./dist/cli/index.js`), and `stdin == subprocess.DEVNULL`.
- `test_missing_bin_entry_is_a_setup_error` — `{"bin": {}}` raises `SetupError`.
- `test_missing_node_is_a_setup_error` — no `node` on PATH raises `SetupError`.
- `test_interrupted_download_removes_its_temp_folder` — a `KeyboardInterrupt` raised inside `download_day` leaves no `losslens-duka-*` folder.
- `test_sync_keyboard_interrupt_returns_130` — `main()` returns 130 and prints the interruption line when the sync raises `KeyboardInterrupt`.

The live download in check 3 below also proves the new `node` invocation works end to end (the old code's `cmd.exe`/`npx` path is gone; `rg npx` finds no mention in the repository).

### 3. Forced March 3 download still exact

Run against an empty scratch store so the reviewed store was not rewritten:

```text
$ $env:LOSSLENS_DATA="C:\Users\yr471\AppData\Local\Temp\opencode\sb2-store"
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04 --force
2026-03-03  complete     554076    13.08s
Summary: 1 day(s), complete=1, empty=0, partial=0, imported=0, failed=0, 13.08s
exit=0
rows 554076
first 1772496001086
last 1772582399247
```

The real store's existing 2026-03-03 file was not touched and reads the same values.

### 4. Stray file before the first manifest day

A copy of the store with only the 2026-03-03 manifest entry and file plus a stray `2025/2025-12-30.parquet`:

```text
$ $env:LOSSLENS_DATA="C:\Users\yr471\AppData\Local\Temp\opencode\sb2-integrity"
$ python -m losslens ticks verify --symbol XAUUSD
Integrity problems: 0
Files not in manifest: 2025-12-30
Quality report: C:\Users\yr471\AppData\Local\Temp\opencode\sb2-integrity\reports\quality-XAUUSD.json
exit=1
```

The stray file is found because the default verify has no range and scans every day file under the symbol folder. With an explicit range (`--from 2026-03-03 --to 2026-03-03`), the 2025 file is not in range and is not listed; the test `test_default_verify_finds_a_file_before_the_first_manifest_day` covers both cases.

### 5. Real store still clean

```text
$ python -m losslens ticks verify --symbol XAUUSD
Total ticks: 83496260
Out-of-order rows: 0
Integrity problems: 0
Files not in manifest: none
Weekdays with no data: 2026-04-03
Largest bid change between days: -111.937 (2026-04-10 -> 2026-04-12)
Quality report: C:\Users\yr471\Projects\loss-lens\data\reports\quality-XAUUSD.json
exit=0
```

The stored data is unchanged: `ticks status` shows 276 complete, 47 empty, 1 partial (324 days), 84,050,530 total ticks; completed days 83,496,260; 2026-03-03 still 554,076 rows with first `1772496001086` and last `1772582399247`.

## Files changed

- `src/losslens/ticks/dukascopy.py` — read the `dukascopy-node` bin from `package.json`, run `node` directly with `stdin=DEVNULL`, `SetupError` for missing node/bin/script.
- `src/losslens/ticks/quality.py` — default scan of all day files; explicit-range limit; `report_path` in the result; no changes to stored data.
- `src/losslens/cli.py` — print `report["report_path"]`.
- `README.md` — setup problem wording no longer mentions `npx`.
- Tests: `test_temp.py`, `test_quality.py`, `test_sync.py` for the new paths.
