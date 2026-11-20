# loss-lens

Runs an MT4 expert advisor over real ticks, finds defects in how it traded, and
shows the proof. This repository is being built increment by increment. **This
increment is the tick store only**: it downloads XAUUSD ticks from Dukascopy,
keeps one Parquet file per UTC day, imports other tick CSVs, checks the data and
answers range queries.

## What you need

- Windows.
- Python 3.11 or newer.
- Node.js 18 or newer (for the pinned Dukascopy downloader).
- Google Chrome or Microsoft Edge, for the download site's browser check.

## Setup

Run these once, from the repository root:

```text
python -m pip install -e .
npm install
```

`npm install` installs `dukascopy-node` at exactly 1.51.1. The commands below
also assume you run them from the repository root.

## Commands

### Download and top up ticks

```text
python -m losslens ticks sync --symbol XAUUSD --from 2026-01-01
python -m losslens ticks sync --symbol XAUUSD --from 2026-03-03 --to 2026-03-04
```

`--to` is exclusive. Without it, sync runs through today (UTC). The command goes
one UTC day at a time, oldest first. Finished days (`complete`, `empty`,
`imported`) are skipped, so running it again is cheap. `--force` re-downloads
everything in the range except imported days. A failed day is retried, then left
unrecorded and reported at the end (exit code 1); it is never saved as empty.
Stopping with Ctrl+C is safe: every file is written atomically, and the next run
continues with whatever is not finished.

### Check the store

```text
python -m losslens ticks verify --symbol XAUUSD
python -m losslens ticks verify --symbol XAUUSD --from 2026-03-01 --to 2026-03-31
```

Per day it prints status, tick count, largest gap, out-of-order rows, rows where
ask is below bid, and spread median / 99th percentile / maximum. The summary
lists weekdays with no data and the largest bid jump between two days. The full
report is written to `data/reports/quality-<SYMBOL>.json`. The command exits 1 if
any day has out-of-order rows.

### Read a range

```text
python -m losslens ticks query --symbol XAUUSD --from 2026-03-03T14:00:00Z --to 2026-03-03T14:10:00Z
```

This is the same `read_ticks(symbol, from_ms, to_ms)` function later parts use.
`from` is inclusive, `to` is exclusive. It prints the row count, first and last
row, and the read time.

### Import another tick CSV

```text
python -m losslens ticks import --symbol XAUUSD --file ticks.csv --ts-col time --bid-col bid --ask-col ask --ts-format iso --utc-offset-minutes 120
```

- `--ts-format` is `epoch_ms`, `epoch_s` or `iso`.
- `--utc-offset-minutes` says how far the file's clock is ahead of UTC; it is
  subtracted. ISO values that already carry a time zone are converted to UTC and
  ignore this offset.
- Optional `--bid-vol-col` and `--ask-vol-col`; missing volumes become 0.
- Rows are sorted, split by UTC day, and every UTC day present in the file is
  replaced. Imported days have status `imported` and are never downloaded over.

### Show coverage

```text
python -m losslens ticks status --symbol XAUUSD
```

## Where the data lives

```text
data/ticks/<SYMBOL>/<YYYY>/<YYYY-MM-DD>.parquet
data/ticks/<SYMBOL>/manifest.json
data/reports/quality-<SYMBOL>.json
```

Each Parquet file is one UTC day, zstd-compressed, with columns `ts_ms` (int64,
UTC epoch milliseconds), `bid`, `ask` (float64), `bid_vol`, `ask_vol` (float32),
sorted by `ts_ms`. `data/` is git-ignored: tick data never goes into git.

Manifest statuses:

- `complete`: downloaded at least 6 hours after that UTC day ended, with ticks.
- `empty`: downloaded at least 6 hours after that day ended, no ticks (weekend or
  holiday). No Parquet file.
- `partial`: downloaded sooner than that (today or a day that just ended).
- `imported`: written by `ticks import`.

## Tests

```text
python -m pytest -q
```

The tests use only local fixtures and make no network calls.
