# Builder handoff — after inc-1

Updated: 2026-11-20 · Increment: inc-1 (tick store) · Report: `work/report-inc-1.md`

## Goal

A local, validated store of XAUUSD 2026 ticks that one command fills and tops up, that any other tick CSV can be imported into, and that every later part reads through `read_ticks()`.

## State and how to check it

inc-1 is finished and reported. All nine checks in `.teams/increments/inc-1.md` pass on this PC.

```text
python -m pytest -q
python -m losslens ticks status --symbol XAUUSD
python -m losslens ticks verify --symbol XAUUSD
python -m losslens ticks query --symbol XAUUSD --from 2026-03-03T14:00:00Z --to 2026-03-03T14:10:00Z
```

Local data (not in git): 324 days, 2026-01-01..2026-11-20 — 276 complete, 47 empty, 1 partial (today), 0 failed. 277 Parquet files, 84,044,373 ticks, 516.84 MiB. Verify: 0 out-of-order, 0 `ask < bid`, 0 non-positive prices; only missing weekday is 2026-04-03 (Good Friday).

## Done (evidence in the report)

- `sync` day by day, atomic Parquet + manifest, retries, skip finished days, `--force`, Ctrl+C safe and resumable.
- Full sync completed; a Ctrl+C test stopped after 2026-01-09 with no `.tmp` and all files readable; the restart skipped those days and continued. A later server restart also lost nothing.
- `verify` writes `data/reports/quality-XAUUSD.json` and exits 1 on out-of-order rows.
- `query` reads only the day files in range; measured 14–51 ms for the 10-minute check (< 200 ms).
- `import` maps arbitrary CSV columns, applies `--utc-offset-minutes`, splits by UTC day, replaces those days, status `imported`.
- `status` prints coverage, counts, ticks and disk size.
- 21 tests pass; fixture CSV is under 1 KB.

## Ruled out / do not retry

- **MT4 installation:** D-13 and the amended inc-1 brief say the user installs IC Markets MT4. This PC has two MetaTrader 5 installs (`terminal64.exe`) and no MT4. Do not download from the IC client area.
- `pq.read_table` in the read path: ~250 ms first call per process on Windows; `pq.ParquetFile(path).read()` is ~14 ms. Do not switch back without measuring.
- ISO parsing of Dukascopy `timestamp`: it is already epoch milliseconds. Column mapping is by name, ask before bid.
- Installing formatters/linters or adding `losslens doctor` / the no-live-trading guard test during inc-1: not named in the inc-1 brief or dependency list.

## Open

- User: install IC Markets MT4 and open a demo account; the Lead then confirms it is MT4 and reads the gold symbol name and server time (D-13), needed for inc-2.
- Lead: name the formatter/linter if `QUALITY.md` §7 is to apply now; place `losslens doctor` and the per-run log (QUALITY §3); confirm `tests/test_no_live_trading.py` is inc-2, as ARCHITECTURE says.
- Tick data keeps topping up until 2026-12-31; run `python -m losslens ticks sync --symbol XAUUSD --from 2026-01-01` periodically (or from the last stored day) — finished days are skipped.
- `data/` is local to this PC and ignored by git, as required.

## Next step

Lead runs the nine checks in `.teams/increments/inc-1.md`, fills the Judgment, and briefs inc-2 (MT4 run spike with the reference EA, capturing the journal as well as the trades). The MT4 export that turns these ticks into MT4 tester history belongs to that increment.
