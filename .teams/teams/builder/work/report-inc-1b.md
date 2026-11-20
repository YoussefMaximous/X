# inc-1b report — send-back 1

Builder · 2026-11-20 · code commit `1488af3` · stored tick data not re-downloaded or changed.

## Summary (10 lines or fewer)

- **Done:** all five send-back items are fixed; 35 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **1 Setup problems** now raise `SetupError`: not retried, one `setup problem:` line, exit 2. Real 4-day forced sync with `node_modules` renamed: exit 2 in 0.85 s, manifest SHA-256 unchanged.
- **2 Temp folders** are removed on interruption and at download failure; stale `losslens-duka-*` folders older than one hour are removed at sync start, newer ones kept.
- **3 Verify** compares each manifest entry with its file: `file_missing`, `unexpected_file`, `row_count_mismatch`, `first_last_mismatch`, `rows_outside_day`, plus `files_not_in_manifest`; prints `Integrity problems` and exits 1. Real store: 0. Deleted copy: names the day, exits 1.
- **4 One store** from anywhere: `LOSSLENS_DATA`, else `<repo>/data` found from the package; `node_modules` and the downloader use the same repo root. From `C:\Users\yr471` the same 324 days show; no local `data` folder appears.
- **5 Quality:** `ruff` (E,F,I,B,UP; line 100), strict `mypy` on `src/losslens`, `ruff`/`mypy` in the dev extras, `.github/workflows/ci.yml` (Windows, Python 3.11 and 3.13), and the four commands in the README.
- **Stored data:** unchanged — 276 complete, 47 empty, 1 partial; 83,496,260 ticks in completed days; no `ticks sync` was run against the real store.
- **Not verified here:** the live Ctrl+C check (#5 of Done when) and the GitHub workflow; the Lead runs both. The Ctrl+C cleanup path is covered by passing tests.
- **Note:** `pytest` exits 0 but prints an ignored `PermissionError` from its global `pytest-current` symlink during atexit cleanup on this PC; it is pytest's temp-dir handling, not a test failure.
- **No questions.**

## Checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
...................................                                      [100%]
35 passed in 0.74s
$ echo $LASTEXITCODE
0
```

The atexit `PermissionError` on `...\Temp\pytest-of-yr471\pytest-current` appears after that summary; it does not change the exit code. It is the same Windows symlink issue the Lead saw before.

```text
$ python -m ruff check .
All checks passed!

$ python -m ruff format --check .
30 files already formatted

$ python -m mypy
Success: no issues found in 8 source files
```

All four exit 0. `mypy` is strict on `src/losslens`; pyarrow's incomplete type information is skipped for `pyarrow` and `pyarrow.*` only. There is no bare `# type: ignore` in the code.

### 2. Setup problem stops at once

Real store, `node_modules` renamed, then restored:

```text
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-06 --force
setup problem: dukascopy-node is not installed; run 'npm install' in the repository folder
exit=2 seconds=0.85
manifest unchanged: True
```

The manifest hash was taken before and after the command (SHA-256); it is identical. `setup problem:` is the only output line, on stderr. The four setup cases (no mapping, no `npx`, no local `dukascopy-node`, no Chrome/Edge) raise `SetupError`; `sync_days` re-raises it and does not try the next day.

Tests:

- `test_setup_error_is_not_retried`: a fake `SetupError` over a three-day range is called exactly once and reaches the caller.
- `test_ordinary_error_is_still_retried`: an ordinary `DownloadError` is tried three times and reported as failed.

### 3. No temp folders left behind

```text
$ python -m pytest -q -k "temp" --basetemp="C:\Users\yr471\AppData\Local\Temp\opencode\pt-temp"
....                                                                     [100%]
4 passed, 31 deselected in 0.21s
exit=0
```

The tests are:

- `test_old_temp_folders_are_removed_and_new_ones_kept` — with a temp root passed in, an old `losslens-duka-*` folder is removed and a new one is kept.
- `test_sync_cleans_stale_temp_folders_when_it_starts` — `sync_days(..., temp_root=...)` removes the stale folder before the first day.
- `test_interrupted_download_removes_its_temp_folder` — a `KeyboardInterrupt` inside the downloader leaves no `losslens-duka-*` folder.
- `test_successful_download_is_converted_and_temp_folder_removed` — the normal path also removes it.

`download_day` cleans in a `finally` that runs for `KeyboardInterrupt` too; `sync_days` has a second `finally` around the day's conversion. A live Ctrl+C run is the Lead's Done-when #5; I did not re-download a day for it.

### 4. `ticks verify` checks manifest against files

Real store:

```text
$ python -m losslens ticks verify --symbol XAUUSD
...
Statuses: complete=276, empty=47
Total ticks: 83496260
Out-of-order rows: 0
Integrity problems: 0
Files not in manifest: none
Weekdays with no data: 2026-04-03
Largest bid change between days: -111.937 (2026-04-10 -> 2026-04-12)
Quality report: data/reports/quality-XAUUSD.json
$ echo $LASTEXITCODE
0
```

Copy of the real manifest with only 2026-03-03 and its file, run with `LOSSLENS_DATA` pointing at the copy:

```text
clean exit=0
2026-03-03: file_missing
Integrity problems: 1
deleted exit=1
```

The output names 2026-03-03. Tests cover one case per problem type: `file_missing`, `unexpected_file`, `row_count_mismatch`, `first_last_mismatch`, `rows_outside_day`, and a file with no manifest entry; the clean store test asserts exit 0. Exit 1 is returned for out-of-order rows, any integrity problem, or any file not in the manifest.

### 5. One store wherever the command is run from

From `C:\Users\yr471` (outside the repository):

```text
$ python -m losslens ticks status --symbol XAUUSD
symbol: XAUUSD
range: 2026-01-01 .. 2026-11-20
days: complete=276, empty=47, partial=1
total ticks: 84050530
disk size: 516.79 MB
local data dir exists: False
```

This is the same store as from the repository root; no `C:\Users\yr471\data` folder was created. `resolve_data_root()` uses `LOSSLENS_DATA` when set, otherwise walks from the `losslens` package to the folder with `pyproject.toml`; only then falls back to `./data`. `read_ticks()` and `TickStore()` use the same rule. `dukascopy` looks for `node_modules` under that repository root and runs with it as its working folder.

Tests: `test_losslens_data_env_is_honoured`, `test_repository_root_is_found_from_the_package`, `test_read_ticks_uses_the_same_data_root`.

### 6. Stored data untouched

```text
days: complete=276, empty=47, partial=1
completed ticks: 83496260
2026-03-03: 554076 rows, first 1772496001086, last 1772582399247
2026-11-19: 690073 rows
```

The completed days and their tick counts are unchanged. I ran `status` and `verify` only (verify writes `data/reports/quality-XAUUSD.json`, not tick files). No `ticks sync` was run against the real store; the setup check used the real manifest only after a hash was recorded and it was never written.

## Files changed

- `src/losslens/ticks/dukascopy.py` — `SetupError`, temp cleanup, repo-relative `node_modules` and working folder.
- `src/losslens/cli.py` — setup error handling, per-day cleanup `finally`, store resolution.
- `src/losslens/ticks/store.py` — `LOSSLENS_DATA`/repo-root resolution, `TickStore` default and `read_ticks`.
- `src/losslens/ticks/quality.py` — manifest/file integrity checks and summary.
- `pyproject.toml`, `.github/workflows/ci.yml`, `README.md` — dev tools, configuration, CI, commands.
- Tests: `test_sync.py`, `test_temp.py`, `test_paths.py`, `test_quality.py`, `test_dukascopy.py`, plus existing suites.
