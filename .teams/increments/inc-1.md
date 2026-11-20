# Increment inc-1: Tick store

Planned: 2026-11-20 · Status: sent back twice (2026-11-20), current brief is "Send-back 2" at the end · Phase: prototype

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

**MT4 is not your job in this increment.** If your kickoff message asks you to install MT4, do not: the installer sits behind the broker's client area and a demo account needs the user's personal details, so the user installs it himself (D-13). Never install any MetaTrader build from another site. Say this in your first reply and carry on with the tick store, which needs no MT4.

**Do not:** build any UI; touch MT4; create a GitHub repository or push; add dependencies; change the storage contract; commit tick data; edit `.teams/` outside your own folder.

**If something here is wrong or impossible:** stop, write what you found in your report, and wait. Do not work around it silently.

**Return:** write `.teams/teams/builder/work/report-inc-1.md` with:
- a summary of 10 lines or fewer: done, not verified, questions for the Lead;
- for each of the 9 checks: the exact command you ran and its real output (trimmed to the relevant lines);
- from the full sync: number of days per status, total ticks, total size of `data/ticks`, total time taken, and the list of weekdays with no data.

Then overwrite `.teams/teams/builder/HANDOFF.md` and tell the user in one line that the report is ready.

## Judgment (filled in by the Lead, 2026-11-20)

**builder: send back, five small items. The tick data itself is accepted and does not need downloading again.**

What the Lead ran on this PC (measured):
- All nine checks pass: 21 tests; forced re-download of 2026-03-03 gives 554,076 rows with the expected first and last timestamps, `bid_vol` 90 and `ask_vol` 120 in the right columns, zstd; Saturday recorded `empty` with no file; second run 1.0 s; full sync tops up today in 13 s; verify exit 0; query 15–27 ms; nothing under `data/` visible to git.
- Independent of the builder's code: 2026-06-16 and 2026-10-27 downloaded again with plain `dukascopy-node` are identical to the stored files in every column (288,894 and 217,126 rows).
- Hard kill (not Ctrl+C) in a scratch store at 15 s: no `.tmp`, manifest readable, finished day intact; the restart skipped it and finished; the four days are identical to the main store.
- Manifest against files: 324 entries, 277 files, every row count and first/last timestamp agrees, no row outside its UTC day, no file without an entry.
- All 184 gaps longer than 300 s are explained: 179 are the daily one-hour break, 4 are US-holiday early closes (19 Jan, 16 Feb, 25 May, 7 Sep), 1 is a 469 s quiet spell at 23:01 UTC on 12 Feb. No hour is silently missing.

What is wrong (measured):
1. A setup problem is treated as a failed day and retried. With `dukascopy-node` not installed, a 3-day sync took 45.9 s and printed the same message three times; a year would take over an hour to fail. The brief said to stop with a message.
2. Download temp folders are left behind after an interruption (3 `losslens-duka-*` folders found in the temp folder).
3. `ticks verify` does not compare the manifest with the files, so a deleted or truncated day file would go unnoticed.
4. The store location depends on the folder the command is run from. Run from anywhere else, it silently starts a second, empty store.
5. No formatter, linter or type checker yet (the builder's question 1; `QUALITY.md` section 7 was written after this brief).

Answers to the builder's questions:
- Question 1: `ruff` and `mypy`, now, in this send-back (item 5).
- Question 2: confirmed, `tests/test_no_live_trading.py` arrives in inc-2 with the first MT4 code.
- Question 3: `losslens doctor` and the per-run log arrive in inc-2 with the runner.

Decisions logged: D-18.

## Send-back 1: brief for the builder

Fix exactly these five items. Do not change the storage contract, the stored data, or anything else. Same rules as the inc-1 brief.

**Allowed new dependencies (dev only):** `ruff`, `mypy`. Nothing else.

**1. Setup problems stop the sync at once.**
- These are setup problems, not failed days: no Dukascopy mapping for the symbol, `npx` not found, `dukascopy-node` not installed, no Chrome or Edge.
- Raise a distinct `SetupError` for them. `sync_days` must not retry it and must not carry on to the next day. `ticks sync` prints one line, `setup problem: <what is wrong and what to do>`, to stderr and exits with code 2. No day is recorded.
- Tests: a fake download that raises `SetupError` is called exactly once for a three-day range, and the error reaches the caller; an ordinary download error is still retried and reported as before.

**2. No temp folders left behind.**
- If a download is interrupted (including Ctrl+C), that day's temp folder is removed before the interruption carries on.
- When a sync starts, it removes `losslens-duka-*` folders in the temp folder that are more than one hour old. Newer ones are left alone, in case another sync is running.
- Tests for both, using a temp root passed in by the test.

**3. `ticks verify` checks the manifest against the files.**
- Per day, a `problems` list with any of: `file_missing` (status says there are ticks, no file), `unexpected_file` (status `empty`, file exists), `row_count_mismatch`, `first_last_mismatch`, `rows_outside_day`.
- Summary: `integrity_problems` (count) and `files_not_in_manifest` (list of day files with no manifest entry). Print both.
- Exit code 1 if there are out-of-order rows, or any integrity problem, or any file not in the manifest.
- Tests: one per problem type, plus one clean store that exits 0.

**4. One store, wherever the command is run from.**
- The data folder is: the `LOSSLENS_DATA` environment variable if set; otherwise `<repository root>/data`, where the repository root is found by walking up from the `losslens` package folder to the folder that holds `pyproject.toml`; only if that fails, `data` under the current folder.
- `node_modules` is looked for under the same repository root, and `dukascopy-node` is run with that root as its working folder.
- `read_ticks(symbol, from_ms, to_ms)` keeps its signature and uses the same rule.
- Remove the "run from the repository root" requirement from the README.
- Tests: `LOSSLENS_DATA` is honoured; the repository root is found from the package location.

**5. Formatter, linter, type checker, and tests on GitHub.**
- `pyproject.toml`: add `ruff` and `mypy` to the `dev` extras. Ruff: line length 100, rules `E`, `F`, `I`, `B`, `UP`. Mypy: `strict = true` on `src/losslens`; `ignore_missing_imports` for `pyarrow.*` only.
- No bare `# type: ignore`: each one names its error code. If more than ten are needed, stop and report instead of adding them.
- Add `.github/workflows/ci.yml`: on push and pull request, `windows-latest`, Python 3.11 and 3.13, `pip install -e .[dev]`, then `ruff check .`, `ruff format --check .`, `mypy`, `pytest -q`. You cannot push, so you cannot run it; the Lead checks it after pushing.
- Add these four commands to the README under "Tests".

**Done when** (the Lead runs these):
1. `python -m pytest -q`, `python -m ruff check .`, `python -m ruff format --check .` and `python -m mypy` all exit 0.
2. With `node_modules` renamed away, `python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-06 --force` exits 2 in under 5 seconds with one `setup problem:` line, and the manifest is unchanged. (Rename it back afterwards.)
3. From `C:\Users\yr471`, `python -m losslens ticks status --symbol XAUUSD` shows the same store as from the repository root (324 days or more), and no `data` folder appears in `C:\Users\yr471`.
4. `python -m losslens ticks verify --symbol XAUUSD` exits 0 and prints `Integrity problems: 0`. After the Lead deletes one day file in a copy of the store, it exits 1 and names that day.
5. After a sync is stopped with Ctrl+C mid-download, no `losslens-duka-*` folder from that run remains.
6. The stored data is untouched: `ticks status` still shows the same completed days and tick counts for them.

**Return:** `.teams/teams/builder/work/report-inc-1b.md` in the same form as before (summary of 10 lines or fewer, then each check with its real command and output), and an updated `HANDOFF.md`.

## Judgment on send-back 1 (filled in by the Lead, 2026-11-20)

**builder: four of the five items accepted. One fails, and two small gaps were found. Sent back a second time with three items.**

What the Lead ran (measured):
- Check 1: 35 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0; no `type: ignore` and no `noqa` anywhere.
- Check 2: with `node_modules` renamed, the forced sync exits 2 in 0.64 s with one `setup problem:` line; manifest hash unchanged.
- Check 3: from `C:\Users\yr471` the same store is shown (324 days); no `data` folder appears there.
- Check 4: real store exits 0 with `Integrity problems: 0`. In a tampered copy (one file deleted, one copied onto an empty day, one overwritten by its neighbour) all three days are named with the right problem types and the exit code is 1.
- Check 6: no day file was modified since the first review.
- Check 5 fails. A real Ctrl+C sent 5 s into a download: the sync had not exited after 40 s and printed nothing. `node` had stopped, but the `cmd.exe` that runs `npx.cmd` was still alive with no child: it was waiting at its hidden "Terminate batch job (Y/N)?" prompt, and Python cannot raise the interruption until that process ends. The unit test passes because it fakes the interruption inside Python.
- The same Ctrl+C against `node <repo>\node_modules\dukascopy-node\dist\cli\index.js` run directly with `stdin=DEVNULL` (the Lead's own test script): interrupted in 0.1 s, no process left behind.
- A stray day file placed at `2025/2025-12-30.parquet` (before the manifest's first day) was not reported by `ticks verify`.
- `ticks verify` prints `Quality report: data/reports/...` even when `LOSSLENS_DATA` sends the report somewhere else.

## Send-back 2: brief for the builder

Fix exactly these three items. No new dependencies. Do not touch the stored data.

**1. Ctrl+C during a download must stop the sync within seconds.**
- Do not go through `npx` (on Windows it is a batch file, and `cmd.exe` holds the process open at a hidden prompt). Run the downloader with `node` directly: find `node` with `shutil.which("node")`, and take the script path from the `bin` entry named `dukascopy-node` in `<repository root>/node_modules/dukascopy-node/package.json` (today it is `./dist/cli/index.js`; read it, do not hard-code it).
- Pass `stdin=subprocess.DEVNULL` to the child.
- `node` not found, or the `bin` entry missing, is a `SetupError`.
- All the arguments, `NODE_OPTIONS`, the working folder, the timeout and the temp-folder cleanup stay as they are.
- Update the README and the setup messages where they mention `npx`.
- Tests: the command list starts with the `node` path and the script path read from `package.json`; a missing `bin` entry raises `SetupError`.

**2. `ticks verify` with no `--from` and no `--to` checks every day file under the symbol folder,** including files dated before the first manifest day or after the last. With a range given, it stays limited to that range. Test: a day file dated before the first manifest entry is listed in `files_not_in_manifest` and the exit code is 1.

**3. `ticks verify` prints the path the report was really written to.** Test: with `LOSSLENS_DATA` set, the printed path is under that folder.

**Done when** (the Lead runs these):
1. `python -m pytest -q`, `python -m ruff check .`, `python -m ruff format --check .` and `python -m mypy` all exit 0.
2. A real Ctrl+C sent 5 seconds into `python -m losslens ticks sync --symbol XAUUSD --from 2026-03-02 --to 2026-03-06` (with `LOSSLENS_DATA` pointing at an empty scratch folder) ends the command with exit code 130 within 5 seconds; no `losslens-duka-*` folder from that run remains; no `node.exe` or `cmd.exe` from that run is still alive.
3. `python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04 --force` still gives 554076 rows with first `ts_ms` 1772496001086 and last `ts_ms` 1772582399247.
4. In a copy of the store with a stray `2025/2025-12-30.parquet`, `ticks verify` lists 2025-12-30 under "Files not in manifest" and exits 1; the printed report path is inside the copy.
5. `ticks verify` on the real store still exits 0.

**Return:** `.teams/teams/builder/work/report-inc-1c.md` in the same form, and an updated `HANDOFF.md`. You do not need to produce a real Ctrl+C yourself; say so under "not verified" if you did not.

## Judgment on send-back 2 (filled in by the Lead, 2026-11-20)

**builder: accepted. inc-1 (tick store) is accepted and pushed.**

What the Lead ran (measured, code at `ee21cfb`):
- Check 1: 41 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0; no `type: ignore`, no `noqa`, no skipped test.
- Check 2: a real Ctrl+C sent 5 s into `ticks sync --from 2026-03-02 --to 2026-03-06` on an empty scratch store: exit code 130 after 0.1 s, the line "interrupted; finished days are safe, run the command again", no `losslens-duka-*` folder left, no new `node.exe` or `cmd.exe` left, nothing half-written in the store. (The builder could not produce a real Ctrl+C and said so.)
- Check 3: forced sync of 2026-03-03 into a scratch store: 554076 rows, first 1772496001086, last 1772582399247, and the file is identical to the one in the real store in every column.
- Check 4: in a full copy of the store with a stray `2025/2025-12-30.parquet`, verify lists 2025-12-30 under "Files not in manifest" and exits 1; the printed report path is inside the copy and the real report was not touched. With `--from 2026-03-01 --to 2026-03-31` the stray file is not listed and the exit code is 0. A stray file after the last day (2026-12-25), run from another folder, is listed too.
- Check 5: real store verify exits 0: 83,496,260 ticks in completed days, 0 integrity problems, no file outside the manifest. No day file changed since the first review; status still 276 complete, 47 empty, 1 partial.
- The builder changed nothing under `.teams/` outside its own folder. No secret, data file or EA file is tracked.

One tidy-up carried into the next brief (not a fault in behaviour): the command line still contains the word `dukascopy-node` after the script path, left over from the `npx` form. Measured: a download with and without that word gives a byte-identical file (same SHA-256), exit 0 both times. It is removed, with a test, as item 1 of inc-2.
