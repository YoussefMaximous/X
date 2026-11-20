# Builder handoff — after inc-1 send-back 1

Updated: 2026-11-20 · Increment: inc-1 send-back 1 · Report: `work/report-inc-1b.md`

## Goal

Fix exactly the five items in `.teams/increments/inc-1.md`, "Send-back 1", without changing the storage contract or the stored tick data.

## State and how to check it

The five items are fixed and committed locally (`1488af3` code; report in the next commit). The real store was not re-downloaded or written.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens ticks verify --symbol XAUUSD
python -m losslens ticks status --symbol XAUUSD
```

Expected: 35 tests pass; all three tools exit 0; verify prints `Integrity problems: 0` and exits 0; status shows 276 complete, 47 empty, 1 partial (324 days).

## Done (evidence in the report)

- **1 Setup problems:** distinct `SetupError`; not retried, no next day, one `setup problem:` line, exit 2. With `node_modules` renamed, the real 4-day forced sync exited 2 in 0.85 s and the manifest hash did not change.
- **2 Temp folders:** `download_day` cleans in `finally` on failure and `KeyboardInterrupt`; `sync_days` cleans after conversion; stale `losslens-duka-*` folders older than one hour are removed at sync start with a temp root that tests can pass in.
- **3 Verify integrity:** per-day `problems` (`file_missing`, `unexpected_file`, `row_count_mismatch`, `first_last_mismatch`, `rows_outside_day`), plus `files_not_in_manifest`; prints `Integrity problems` and exits 1. Real store 0; deleted copy names the day and exits 1.
- **4 One store:** `LOSSLENS_DATA`, else `<repo>/data` found from the package folder; `read_ticks()` and `TickStore()` share it; `node_modules` and the downloader's working folder use the same repo root. From `C:\Users\yr471` the same 324 days show and no local `data` folder appears.
- **5 Quality:** `ruff` (line 100; E, F, I, B, UP), strict `mypy` on `src/losslens`, both in dev extras; `.github/workflows/ci.yml` for Windows, Python 3.11/3.13; the four commands are in the README.
- Stored data untouched: 276 complete / 47 empty / 1 partial; 83,496,260 ticks in completed days; 2026-03-03 still 554,076 rows with the same first/last.

## Ruled out / do not retry

- Treating setup problems as day failures: they now abort the sync with exit 2.
- Retrying a `SetupError`: tests assert exactly one call over a three-day range.
- `pq.read_table` for the hot read path: keep `ParquetFile.read` plus binary search.
- Adding formatter/linter exceptions: `mypy` skips only pyarrow internals; no bare type ignores.
- Running a real sync against the store to test the send-back: it would re-download data; the setup check and unit tests cover the code paths.

## Open

- Lead: run Done-when #5 (live Ctrl+C mid-download) and the GitHub workflow after pushing; the local CI file cannot run here.
- Lead: review the five fixes, then brief inc-2 (MT4 run spike, reference EA, journal capture).
- User: install IC Markets MT4 and open a demo account (D-13); no MT4 is installed on this PC.
- A locked `.pytest_tmp` folder from an earlier local pytest experiment remains ignored and excluded from ruff; it is not tracked and needs no action.

## Next step

Lead reviews inc-1b and, if accepted, starts inc-2 once MT4 is installed.
