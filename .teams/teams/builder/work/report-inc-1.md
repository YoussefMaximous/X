# inc-1 report — tick store

Builder · 2026-11-20 · code commits `54dc30e..5124f27` · data stays local and git-ignored.

## Summary (10 lines or fewer)

- **Done:** the tick store is built and all nine checks below pass on this PC; 21 tests pass with no network.
- **Full sync:** 2026-01-01 to 2026-11-20 — 324 days, 276 complete, 47 empty, 1 partial (today), 0 failed; 277 Parquet files, 84,044,373 ticks, 516.84 MiB.
- **Verify:** 0 out-of-order rows, 0 `ask < bid` rows, 0 non-positive prices; the only missing weekday is 2026-04-03 (Good Friday).
- **Resume:** stopped the full sync with a Ctrl+C event after 45 s; no `.tmp`, every stored file readable; the restart skipped the finished days and continued. A server restart later stopped it again with no loss; the same command finished it.
- **MT4:** not installed, per D-13 and the amended inc-1 brief. The user installs IC Markets MT4 himself. Confirmed this PC has two MetaTrader 5 installs (`terminal64.exe` in `C:\Program Files\MetaTrader` and `C:\Program Files\MetaTrader 5`) and no MT4.
- **Not verified:** nothing in the brief's nine checks is unrun. `QUALITY.md` tooling (formatter/linter, `doctor`, per-run log) and D-14's guard test are not in inc-1's brief or dependency list.
- **Question 1:** `QUALITY.md` §7 requires a formatter and linter per language; inc-1 names no such dependency and the standing rules forbid adding one unasked. Name `ruff`/`mypy` (or defer) in a brief.
- **Question 2:** D-14 says `tests/test_no_live_trading.py` fails the build; AGENTS.md already names it, but ARCHITECTURE puts it in inc-2 with the first MT4 code. Confirm it is not expected in inc-1.
- **Question 3:** `QUALITY.md` §3 names `losslens doctor`, and §3 also asks for a log file per run; neither is in inc-1's brief. Which increment should carry them?
- **No other questions.** The storage contract was implemented as written; the manifest JSON envelope (unspecified) is `{"symbol": ..., "days": {"YYYY-MM-DD": entry}}` and is documented in the README.

## Checks

### 1. `python -m pytest -q`

```text
$ python -m pytest -q
.....................                                                    [100%]
21 passed in 1.26s
$ echo $LASTEXITCODE
0
```

No network is touched: the tests build synthetic ticks/trades in `tmp_path`; the only CSV fixture is `tests/fixtures/import_sample.csv`, and no test calls `download_day`.

Covered, as the brief requires: ask-before-bid mapping, UTC-midnight split, `read_ticks` edges across two days, atomic write (no `.tmp`), status rule (`complete`/`partial`/`empty`), failed download not recorded, verify catching out-of-order / `ask < bid` / a 400 s gap, and ISO import with a UTC offset.

### 2. Sync 2026-03-03

```text
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04
2026-03-03  complete     554076     6.88s
Summary: 1 day(s), complete=1, empty=0, partial=0, imported=0, failed=0, 6.88s
```

The file readback:

```text
$ python -c "import pyarrow.parquet as pq; t=pq.read_table('data/ticks/XAUUSD/2026/2026-03-03.parquet'); print('rows', t.num_rows); print('first', t['ts_ms'][0].as_py(), t['bid'][0].as_py(), t['ask'][0].as_py()); print('last', t['ts_ms'][-1].as_py())"
rows 554076
first 1772496001086 5345.755 5346.605
last 1772582399247
```

A later rerun correctly skips it (`0.00s (skipped)`) because the manifest says `complete`.

### 3. Saturday 2026-03-07

```text
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-03-07 --to 2026-03-08
2026-03-07  empty             0     3.39s
Summary: 1 day(s), complete=0, empty=1, partial=0, imported=0, failed=0, 3.39s
$ Test-Path data/ticks/XAUUSD/2026/2026-03-07.parquet
False
```

Manifest entry:

```json
{"date": "2026-03-07", "status": "empty", "ticks": 0, "first_ts_ms": null,
 "last_ts_ms": null, "source": "dukascopy:xauusd",
 "fetched_at_utc": "2026-11-20T13:56:50Z", "tool_version": "0.1.0"}
```

### 4. Second run downloads nothing, under 5 seconds

```text
$ Measure-Command { python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04 | Out-Host } | Select-Object TotalSeconds

2026-03-03  complete     554076     0.00s  (skipped)
Summary: 1 day(s), complete=1, empty=0, partial=0, imported=0, failed=0, 0.00s

TotalSeconds
------------
        1.67
```

The sync work is 0.00 s; 1.67 s is Python import and process startup.

### 5. Full-year sync, and stop/continue

```text
$ python -m losslens ticks sync --symbol XAUUSD --from 2026-01-01
...
2026-11-12  complete     527096     0.00s  (skipped)
2026-11-13  complete     461864     9.42s
2026-11-14  empty             0     4.46s
2026-11-15  complete      19902     8.38s
2026-11-16  complete     650503    25.12s
2026-11-17  complete     601145     8.96s
2026-11-18  complete     685579    14.26s
2026-11-19  complete     690073    10.44s
2026-11-20  partial      548113     9.65s
Summary: 324 day(s), complete=276, empty=47, partial=1, imported=0, failed=0, 90.71s
```

That summary is the final resumed run: it skipped 316 finished days and downloaded the remaining eight. The full wall-clock span from the first fetch of 2026-01-01 to the fetch of 2026-11-20 is 3158 s = **52.6 minutes**, including the interruptions below.

Interruption test: I started the same command, sent `CTRL_C_EVENT` after 45 s, then inspected the store:

```text
$ Get-ChildItem data/ticks/XAUUSD -Recurse -Filter *.tmp
no .tmp files

$ python -c "import pyarrow.parquet as pq, pathlib; files=sorted(pathlib.Path('data/ticks/XAUUSD').rglob('*.parquet')); print('parquet files', len(files)); [print(p.name, pq.ParquetFile(p).metadata.num_rows) for p in files]"
parquet files 10
2026-01-01.parquet 7245
2026-01-02.parquet 336704
2026-01-04.parquet 13649
2026-01-05.parquet 404125
2026-01-06.parquet 389627
2026-01-07.parquet 391382
2026-01-08.parquet 388478
2026-01-09.parquet 342891
2026-01-11.parquet 12470
2026-03-03.parquet 554076
```

The restart log begins with the finished days skipped and continues at 2026-01-10:

```text
2026-01-01  complete       7245     0.00s  (skipped)
2026-01-02  complete     336704     0.00s  (skipped)
...
2026-01-09  complete     342891     0.00s  (skipped)
2026-01-10  empty             0     9.23s
2026-01-11  complete      12470     6.95s
```

The agent server later restarted and killed the background process at 2026-11-11; the same command again skipped everything stored and finished the remaining days. No `.tmp` file and no broken Parquet file was found at either stop.

Full-sync totals:

| Item | Value |
|---|---|
| Days | 324 (2026-01-01 .. 2026-11-20) |
| Statuses | complete 276, empty 47, partial 1, imported 0, failed 0 |
| Parquet day files | 277 (today is the partial one) |
| Ticks in manifest | 84,044,373 |
| Ticks in complete days through 2026-11-19 | 83,496,260 |
| Size of `data/ticks` | 541,950,826 bytes = 516.84 MiB |
| Wall-clock span | 3158 s = 52.6 minutes (four interrupted/resumed sessions) |
| Final resumed run | 90.71 s for the last eight days |
| `.tmp` files | none |

### 6. `ticks verify`

```text
$ python -m losslens ticks verify --symbol XAUUSD
date       status        ticks    gap_s  ooo ask<bid   sp_p50   sp_p99   sp_max
2026-01-01 complete       7245     17.5    0       0    1.160    3.930    5.580
2026-01-02 complete     336704     16.1    0       0    0.727    1.160    2.540
2026-01-03 empty             0        -    0       0        -        -        -
...
2026-11-18 complete     685579   3602.4    0       0    0.495    0.695    4.810
2026-11-19 complete     690073   3601.8    0       0    0.420    0.702    6.172
Statuses: complete=276, empty=47
Total ticks: 83496260
Out-of-order rows: 0
Weekdays with no data: 2026-04-03
Largest bid change between days: -111.937 (2026-04-10 -> 2026-04-12)
Quality report: data/reports/quality-XAUUSD.json
```

Today's partial day is excluded by the default `--to` = yesterday; that is why this summary has 323 days and 83,496,260 ticks while the manifest has 324 and 84,044,373.

The JSON holds the full per-day detail, including every gap longer than 300 s (184 of them) with start and end times, for example:

```json
{"from_ts_ms": 1767650399018, "from_utc": "2026-01-05T21:59:59.018Z",
 "to_ts_ms": 1767654008149, "to_utc": "2026-01-05T23:00:08.149Z", "seconds": 3609.131}
```

Across all 323 verified days: out-of-order 0, `ask < bid` 0, non-positive prices 0, 184 gaps >300 s. The only weekday with no data at all is Good Friday, 2026-04-03. The largest overnight bid change is -111.937 (2026-04-10 last bid 4746.935 to 2026-04-12 first bid 4634.998); it is a weekend gap, stored as measured.

### 7. `ticks query`

```text
$ python -m losslens ticks query --symbol XAUUSD --from 2026-03-03T14:00:00Z --to 2026-03-03T14:10:00Z
symbol: XAUUSD
range: 2026-03-03T14:00:00Z .. 2026-03-03T14:10:00Z (from inclusive, to exclusive)
rows: 5998
first: ts_ms=1772546400003, bid=5156.405, ask=5157.432, bid_vol=90.0, ask_vol=270.0
last: ts_ms=1772546999982, bid=5166.345, ask=5167.485, bid_vol=120.0, ask_vol=120.0
read_ms: 50.59
```

`read_ms` is measured only around `read_ticks`, and 50.59 < 200. Repeated runs are 14–51 ms. (`ParquetFile.read` plus a binary search avoids the ~250 ms one-time `pq.read_table`/dataset setup on Windows.)

### 8. `ticks import` on the fixture CSV

Run from a temporary working directory so the demo rows did not touch the real XAUUSD store:

```text
$ python -m losslens ticks import --symbol XAUUSD --file C:\Users\yr471\Projects\loss-lens\tests\fixtures\import_sample.csv --ts-col time --bid-col bid --ask-col ask --ts-format iso --utc-offset-minutes 120
2026-03-02  imported          1
2026-03-03  imported          2
Imported 3 ticks from import_sample.csv
```

Readback of the expected day files:

```text
data/ticks/XAUUSD/2026/2026-03-02.parquet  1 row
data/ticks/XAUUSD/2026/2026-03-03.parquet  2 rows  ts_ms [1772497800000, 1772497801000]
                                           bid [5345.5, 5345.6] ask [5346.3, 5346.4]
```

The fixture's local clock is 120 minutes ahead of UTC, so 01:30 and 02:30 split across UTC midnight as expected. Also covered by `tests/test_import.py`.

### 9. Git excludes data, node_modules and .venv

```text
$ git status --short -- data node_modules .venv
(no output)

$ git ls-files data node_modules .venv
(no output)
```

Full `git status --short` was clean at the end (the Lead committed its `.teams` edits concurrently). Nothing under `data/`, `node_modules/` or `.venv/` is tracked or untracked-but-not-ignored. `data/` is ignored at `.gitignore:1`.

## What was ruled out

- Installing MT4 (D-13): the user installs IC Markets MT4; the builder does not. I did not open the IC page or download an installer.
- `pq.read_table` for the hot read path: its first call in a fresh process costs ~250 ms here (dataset/filesystem setup); `pq.ParquetFile(path).read()` is ~14 ms. Recorded in code comments.
- Parsing Dukascopy timestamps as ISO: the downloaded CSV's `timestamp` column is already UTC epoch milliseconds (`1772496001086`), so it is read as int64. The brief's column names are respected (ask before bid).
- Adding a formatter/linter, `losslens doctor`, a per-run log, or `tests/test_no_live_trading.py` in inc-1: none is named in the inc-1 brief or its allowed dependencies; the questions above ask the Lead to place them.
