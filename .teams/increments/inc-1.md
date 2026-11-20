# Increment inc-1: Tick store

Planned: 2026-11-20 · Status: planned · Phase: prototype

## Goal
A local, validated store of XAUUSD 2026 ticks that one command fills and tops up, that any other tick CSV can be imported into, and that every later part reads through one function.

## Done when
The Lead runs these on this PC and each one passes. All commands run from the repository root.

1. `python -m pytest -q` passes with no network access.
2. `python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04` creates `data/ticks/XAUUSD/2026/2026-03-03.parquet` with exactly **554076** rows, first `ts_ms` **1772496001086**, last `ts_ms` **1772582399247**, and the first row has `bid` 5345.755 and `ask` 5346.605.
3. `python -m losslens ticks sync --symbol XAUUSD --from 2026-03-07 --to 2026-03-08` (a Saturday) writes no Parquet file and records the day as `empty` in the manifest.
4. Running command 2 a second time downloads nothing and finishes in under 5 seconds.
5. `python -m losslens ticks sync --symbol XAUUSD --from 2026-01-01` (no `--to` means up to now) completes. If it is stopped with Ctrl+C halfway and started again, it continues from where it stopped and no `.tmp` file or broken Parquet file is left behind.
6. `python -m losslens ticks verify --symbol XAUUSD` prints a summary, writes `data/reports/quality-XAUUSD.json`, reports zero out-of-order rows, and lists no missing weekday between 2026-01-02 and yesterday other than real market holidays (list them in your report).
7. `python -m losslens ticks query --symbol XAUUSD --from 2026-03-03T14:00:00Z --to 2026-03-03T14:10:00Z` prints the row count and a read time under 200 ms (time measured inside the program around the read only).
8. `python -m losslens ticks import ...` on the fixture CSV in `tests/fixtures/` creates the expected day files (covered by a test).
9. `git status` shows nothing under `data/`, `node_modules/` or `.venv/` as tracked or untracked-but-not-ignored.

## Owners and contributions
| Area | Owner | Others contribute |
|---|---|---|
| everything outside `.teams/` (except `AGENTS.md`) | builder | lead: review |

Contracts needed: none (the storage contract is in `.teams/ARCHITECTURE.md` and repeated below).
Idle this increment: none.

## Briefs

### builder

**Your area (you alone write here):** every file outside `.teams/` except `AGENTS.md`; plus `.teams/teams/builder/`.

**Inputs:** `.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`, decisions D-3 to D-5.

**Bias reminder:** optimize passing the checks above with simple code. Ignore the app, MT4 and the loss engine: they are later increments.

**Allowed dependencies.** Python: `pyarrow`, `duckdb`, `pytest`. Node: `dukascopy-node` pinned to exactly `1.51.1` in `package.json`. Command line parsing: `argparse` from the standard library. Nothing else without asking.

**Layout to create**

```text
pyproject.toml            package name "losslens", Python >= 3.11, src layout
package.json              only dependency: "dukascopy-node": "1.51.1"
.gitignore                data/  node_modules/  .venv/  __pycache__/  *.tmp  .dukascopy-cache/  .pytest_cache/
README.md                 setup steps and the five commands, in plain words
src/losslens/__main__.py  entry point for "python -m losslens"
src/losslens/cli.py       argparse commands
src/losslens/ticks/dukascopy.py   download one UTC day to a temporary CSV
src/losslens/ticks/store.py       Parquet day files, manifest, read_ticks()
src/losslens/ticks/quality.py     verify
src/losslens/ticks/importer.py    generic CSV import
tests/                    pytest tests and tests/fixtures/ (small CSV files only, under 50 KB each)
```

**Storage contract (do not change it)**

- Day file: `data/ticks/<SYMBOL>/<YYYY>/<YYYY-MM-DD>.parquet`, one file per UTC day, zstd compression.
- Columns, in this order: `ts_ms` int64 (UTC epoch milliseconds), `bid` float64, `ask` float64, `bid_vol` float32, `ask_vol` float32.
- Rows sorted by `ts_ms` ascending. Rows with equal `ts_ms` keep the order they had in the source. Do not remove duplicates.
- Manifest: `data/ticks/<SYMBOL>/manifest.json`, one entry per day: `date`, `status`, `ticks`, `first_ts_ms`, `last_ts_ms`, `source`, `fetched_at_utc`, `tool_version`.
- `status` values:
  - `complete`: fetched at least 6 hours after that UTC day ended, and has ticks;
  - `empty`: fetched at least 6 hours after that UTC day ended, download succeeded, zero ticks (weekends, holidays). No Parquet file;
  - `partial`: fetched earlier than that (today, or a day that just ended). Has a Parquet file if there are ticks;
  - `imported`: written by `ticks import`.
- Every file write is atomic: write `<name>.tmp` in the same folder, then `os.replace` onto the final name. Update the manifest (also atomically) after each day.
- The one read function everything else will use: `read_ticks(symbol: str, from_ms: int, to_ms: int) -> pyarrow.Table` in `store.py`. It returns rows with `from_ms <= ts_ms < to_ms`, opens only the day files the range touches, and returns an empty table with the right schema when there is no data.

**Commands**

1. `ticks sync --symbol XAUUSD --from YYYY-MM-DD [--to YYYY-MM-DD] [--force]`
   - `--to` is exclusive; without it, sync up to and including today (UTC).
   - Go day by day, oldest first, one day at a time (no parallel downloads: the source rate-limits).
   - Skip days whose status is `complete`, `empty` or `imported`. Re-download days that are `partial` or absent. `--force` re-downloads everything in the range except `imported` days.
   - Print one line per day (date, status, tick count, seconds) and a final summary.
   - If a day fails, retry it up to 3 times with a pause, then record nothing for that day, carry on with the next day, and at the end print the failed days and exit with code 1. A failed download must never be recorded as `empty`.
2. `ticks verify --symbol XAUUSD [--from] [--to]`
   - Per day: status, tick count, first and last time, largest gap in seconds, every gap longer than 300 seconds (start and end time), out-of-order row count, rows where `ask < bid`, rows with a price `<= 0`, spread median / 99th percentile / max, first and last bid.
   - Summary: days per status, total ticks, weekdays (Mon–Fri) in the range with no data, largest bid change between one day's last tick and the next day's first tick.
   - Write it all to `data/reports/quality-<SYMBOL>.json` and print a short table. Exit code 1 if any day has out-of-order rows; otherwise 0.
3. `ticks query --symbol XAUUSD --from <ISO time> --to <ISO time>`: calls `read_ticks`, prints row count, first and last row, and the read time in milliseconds.
4. `ticks import --symbol <SYMBOL> --file <csv> --ts-col <name> --bid-col <name> --ask-col <name> [--bid-vol-col <name>] [--ask-vol-col <name>] --ts-format epoch_ms|epoch_s|iso [--utc-offset-minutes N]`
   - Converts timestamps to UTC epoch ms (`--utc-offset-minutes` says how far the file's clock is ahead of UTC; default 0), sorts, splits by UTC day, and replaces the day files for every day present in the CSV. Missing volume columns become 0. Status `imported`, `source` = `import:<file name>`.
5. `ticks status --symbol XAUUSD`: date range covered, days per status, total ticks, disk size.

**How to download one day (measured by the Lead on this PC, 2026-11-20)**

This exact command works and takes about 7 seconds for a trading day:

```text
npx dukascopy-node -i xauusd -from 2026-03-03 -to 2026-03-04 -t tick -f csv -v -vu units -r 3 -rp 1500 -s --chrome-path "C:\Program Files\Google\Chrome\Application\chrome.exe" -dir <temp folder>
```

Things you must respect:

- **Set `NODE_OPTIONS=--use-system-ca` in the environment of the child process only.** Without it every download fails on this PC with `fetch failed` (certificate error `UNABLE_TO_VERIFY_LEAF_SIGNATURE`).
- The source is behind a web firewall challenge that the tool solves with a browser. Pass `--chrome-path` when Chrome or Edge exists in its standard install folder (check Chrome first, then Edge). If neither exists, stop with a message telling the user to run `npx dukascopy-node --install-browser`.
- Run `npm install` once so the pinned version is used; call it through `npx` found with `shutil.which("npx")` (on Windows this is `npx.cmd`).
- `-to` is exclusive: `-from 2026-03-03 -to 2026-03-04` returns only 3 March.
- The output file is named like `xauusd-tick-2026-03-03-2026-03-04.csv`. When `-to` is in the future the name ends with a time instead (for example `xauusd-tick-2026-11-20-2026-11-20T13-16.csv`), so find the file by listing the temp folder, not by guessing its name.
- CSV header is `timestamp,askPrice,bidPrice,askVolume,bidVolume`. **Ask comes before bid.** Map by column name, never by position.
- A day with no ticks (Saturday) gives exit code 0 and a 0-byte file. That is `empty`, not an error.
- Download each day into a fresh temporary folder outside `data/ticks/`, convert, then delete the CSV.
- Symbol mapping for this increment: `XAUUSD` -> instrument `xauusd`. Keep the mapping in one small dictionary so more symbols can be added.

**Tests (no network).** At least: column mapping with ask before bid; split at UTC midnight; `read_ticks` range edges (`from` inclusive, `to` exclusive) across two days; atomic write leaves no `.tmp`; status rule (`complete` / `partial` / `empty`) from the fetch time; a failed download is not recorded; verify detects an out-of-order row, an `ask < bid` row and a 400-second gap; import with `iso` timestamps and a UTC offset. One optional real-download test may exist, marked `network`, skipped by default.

**Do not:** build any UI; touch MT4; create a GitHub repository or push; add dependencies; change the storage contract; commit tick data; edit `.teams/` outside your own folder.

**If something here is wrong or impossible:** stop, write what you found in your report, and wait. Do not work around it silently.

**Return:** write `.teams/teams/builder/work/report-inc-1.md` with:
- a summary of 10 lines or fewer: done, not verified, questions for the Lead;
- for each of the 9 checks: the exact command you ran and its real output (trimmed to the relevant lines);
- from the full sync: number of days per status, total ticks, total size of `data/ticks`, total time taken, and the list of weekdays with no data.

Then overwrite `.teams/teams/builder/HANDOFF.md` and tell the user in one line that the report is ready.

## Judgment (filled in by the Lead)
- builder: pending
