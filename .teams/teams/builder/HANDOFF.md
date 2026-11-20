# Builder handoff — after inc-1 send-back 2

Updated: 2026-11-20 · Increment: inc-1 send-back 2 · Report: `work/report-inc-1c.md`

## Goal

Fix exactly the three items in `.teams/increments/inc-1.md`, "Send-back 2", without changing the stored tick data.

## State and how to check it

The three items are fixed and committed locally (`ee21cfb` code; report in the next commit). The real store was not re-downloaded or written.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens ticks verify --symbol XAUUSD
```

Expected: 41 tests pass; all three tools exit 0; verify prints `Integrity problems: 0`, `Files not in manifest: none`, and exits 0. `ticks status` still shows 276 complete, 47 empty, 1 partial (324 days).

## Done (evidence in the report)

- **1 Ctrl+C path:** the downloader runs `node` directly with the script read from the `dukascopy-node` bin in `node_modules/dukascopy-node/package.json`, `stdin=DEVNULL`; a missing node or bin entry is a `SetupError`. The live node-path download of 2026-03-03 is exact (554,076 rows, first 1772496001086, last 1772582399247).
- **2 Stray files:** with no `--from`/`--to`, `ticks verify` scans every `*.parquet` under the symbol folder, including before the first manifest day and after the last. A copy with `2025/2025-12-30.parquet` lists `2025-12-30` and exits 1; an explicit range stays limited.
- **3 Report path:** `verify` stores `report_path` in the result and prints the actual file path. With `LOSSLENS_DATA` set, the printed path is under that folder (verified in the copy above).
- Stored data unchanged: 276 complete / 47 empty / 1 partial; 83,496,260 ticks in completed days; 2026-03-03 still 554,076 rows with the same first/last.

## Not verified

- The live Ctrl+C check (#2 of Done when). This non-interactive shell has no console that raises Python's `KeyboardInterrupt`; a console event kills the child with exit 1. The brief allows saying so. Tests cover the node command, `stdin=DEVNULL`, `main` returning 130, and temp-folder removal. The Lead should run the real 5-second Ctrl+C check.

## Ruled out / do not retry

- Going through `npx`/`cmd.exe`: it can sit at the hidden "Terminate batch job (Y/N)?" prompt. Run `node` directly.
- Hard-coding `./dist/cli/index.js`: read the `dukascopy-node` bin entry from `package.json`.
- Reporting `data/reports/...` blindly: use the path actually written.
- Limiting the default file scan to the manifest range: it must find stray files outside the range.
- Rewriting the real store to test: use an empty scratch `LOSSLENS_DATA` for live downloads.

## Open

- Lead: run the real Ctrl+C Done-when #2, then review inc-1c and brief inc-2.
- User: install IC Markets MT4 and open a demo account (D-13); no MT4 is installed on this PC.
- pytest still prints an ignored `pytest-current` Windows symlink `PermissionError` at atexit; exit code is 0. The locked `.pytest_tmp` folder remains ignored and excluded from ruff.

## Next step

Lead reviews inc-1c; if accepted, inc-2 starts once MT4 is installed.
