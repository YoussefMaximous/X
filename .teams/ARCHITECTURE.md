# Architecture (Lead-owned, one page)

Updated: 2026-11-20. Evidence words: measured (ran it), checked (read primary source), assumed.

## Flow

```text
Dukascopy / any CSV ──> Tick store ──> MT4 history export ──> MT4 Strategy Tester (the EA runs here)
                           │                                          │
                           │                                 trades (+ optional decision log)
                           ▼                                          ▼
                     Loss engine  <───────────────────────────────  Run store
                           │  metrics, loss tags, hidden losses
                           ▼
                      Local app  ── click ──> MT4 bridge (chart jumps to the trade)
```

## Parts

| Part | Job | Tech |
|---|---|---|
| Tick store | One Parquet file per UTC day, plus a manifest. Single read API `read_ticks(symbol, from_ms, to_ms)`. | Python, pyarrow, DuckDB |
| Downloader | Day-by-day sync from Dukascopy, resumable. | `dukascopy-node` 1.51.1 (pinned), called from Python |
| MT4 export | Writes MT4 history from the tick store with the broker's server-time offset. | Python |
| Runner | Starts the MT4 tester from a config file, waits, collects the report. A seam: `mt4-native` first; `tick-data-suite`, `mt5` or `csv-import` can be added without touching the rest. | Python + MT4 |
| Reference EA | Test EA with source, many trades a day, several rule gates, writes a decision log. Stands in until the team's EA is plugged in. | MQL4 |
| Run store | Runs, trades, decisions, tags, notes. | DuckDB file |
| Loss engine | Per-trade metrics from ticks, loss tags, hidden-loss re-check, baskets, streaks. Deterministic rules with thresholds in one config file. | Python |
| App | Loss list, filters, saved views, money ranking, calendar, tick replay, what-if, version compare. | FastAPI + React/TypeScript; charts: lightweight-charts and uPlot (provisional, D-5) |
| MT4 bridge | Small EA on an MT4 chart that reads a command file and jumps to a time, then draws the trade. | MQL4 |

## Facts the design rests on

- measured: one trading day of XAUUSD ticks is about 0.55M rows and 21–27 MB as CSV (2026-03-03: 554,076 ticks). A year is roughly 130M ticks.
- measured: spread on 2026-03-03 had median 0.96, 99th percentile 2.69, max 13.74 (USD). Spread varies by more than 10x within a day.
- measured: no ticks in the 22:00 UTC hour on 2026-03-03 (daily break). Saturdays return an empty file with exit code 0.
- measured: the newest ticks are available within seconds; `-to` is exclusive.
- measured: on this PC, Node's own certificate store rejects every HTTPS host; `NODE_OPTIONS=--use-system-ca` fixes it. Dukascopy also sits behind a web firewall challenge that `dukascopy-node` solves with a headless browser (`--chrome-path`).
- checked (well known, re-test in inc-2): MT4's tester stores bid only and applies one fixed spread to a whole run. So spread-driven losses cannot appear in a native MT4 run. The loss engine re-checks every trade against real bid and ask to expose them.
- assumed (measure in inc-2): a full-year tick history file for MT4 would be around 7 GB (130M x 56 bytes), likely above what the 32-bit tester accepts, so runs are chunked by month with warm-up, or ticks are thinned. Decide after measuring.

## Storage contract

- `data/ticks/<SYMBOL>/<YYYY>/<YYYY-MM-DD>.parquet`: columns `ts_ms` int64 (UTC epoch ms), `bid` float64, `ask` float64, `bid_vol` float32, `ask_vol` float32; sorted by `ts_ms`, source order kept for equal timestamps; zstd.
- `data/ticks/<SYMBOL>/manifest.json`: one entry per day (status, tick count, first/last timestamp, source, fetch time).
- `data/lens.duckdb`: runs, trades, decisions, tags, notes (schema fixed in inc-2 and inc-3).
- `data/` is git-ignored.

## Loss tags, version 0 (multi-label, thresholds configurable)

R = initial risk (entry to stop). MFE / MAE = best / worst excursion measured on the side the trade exits on.

| Tag | Rule sketch |
|---|---|
| NEVER_IN_PROFIT | MFE below 0.1R |
| GAVE_BACK | MFE at least 0.5R, then closed at a loss |
| STOP_TOO_TIGHT | after the stop, price reached the original target within N minutes without a further 1R against |
| SPREAD_SPIKE | exit happened while spread was above 3x its rolling median and the other side of the book had not reached the stop |
| NEWS_SPIKE | entry or exit within X minutes of a high-impact event (needs a calendar) |
| GAP_THROUGH_STOP | fill worse than the stop by more than Y |
| COUNTER_TREND | against the higher-timeframe trend |
| WHIPSAW | three or more losses in alternating directions inside 30 minutes |
| OVERSIZED | lot above 2x the run's median lot |
| COSTS_ONLY | gross result not negative, net result negative |
| THIN_MARKET | within 30 minutes of the daily break |
| STREAK | part of a run of consecutive losses or a drawdown episode |
| DATA_SUSPECT | a tick gap above threshold during the trade |
| HIDDEN_LOSS (winners) | with real bid/ask the stop is hit before the target |

Grid or martingale EAs: trades are grouped into baskets and judged per basket as well as per order.

## Increment sequence

1. Tick store (no MT4 needed).
2. MT4 run spike: one month end to end with the reference EA; measure MT4's limits.
3. Full-year run and loss engine.
4. App v1: list, filters, saved views, money ranking, calendar, tick replay.
5. MT4 jump.
6. What-if lab, version compare, review notes, team report, news calendar.
