# Architecture (Lead-owned, one page)

Updated: 2026-11-20. Evidence words: measured (ran it), checked (read primary source), assumed.

## Flow

```text
Dukascopy / any CSV ──> Tick store ──> MT4 history export ──> MT4 Strategy Tester (the EA runs here)
                           │                                          │
                           │                        trades, journal (+ optional decision log)
                           ▼                                          ▼
                    Defect engine  <──────────────────────────────  Run store
                           │  reconcile, measure, run every detector
                           ▼
                      Local app  ── click ──> MT4 bridge (chart jumps to the trade)
```

## Parts

| Part | Job | Tech |
|---|---|---|
| Tick store | One Parquet file per UTC day, plus a manifest. Single read API `read_ticks(symbol, from_ms, to_ms)`. | Python, pyarrow, DuckDB |
| Downloader | Day-by-day sync from Dukascopy, resumable. | `dukascopy-node` 1.51.1 (pinned), called from Python |
| MT4 export | Writes two things from the tick store for the chosen date range: the chart history (M1 bars, `.hst`) and the tester's tick file (`.fxt`) holding the real ticks. See "MT4 export". | Python |
| Runner | Starts the MT4 tester from a config file, waits, collects the report and the journal. A seam: `mt4-native` first; `tick-data-suite`, `mt5` or `csv-import` can be added without touching the rest. Two modes, same machinery: **quick run** and **analysed run** (see "One software, two uses"). | Python + MT4 |
| Reference EA | Test EA with source, many trades a day, several rule gates, writes a decision log. Stands in until the expert's EA is plugged in. | MQL4 |
| EA profile | Small file where the expert states what the EA is meant to do (hours, max lot, max positions, risk per trade). Lets rule-breaking be detected even for compiled EAs. | TOML |
| Run store | Runs, trades, journal events, decisions, findings, notes. | DuckDB file |
| Defect engine | Reconciles the run with the ticks, computes per-trade measurements once, then runs every detector. | Python |
| Detectors | One file per defect, discovered automatically. Catalogue in `.teams/DEFECTS.md`. | Python |
| App | Defect list, filters, saved views, money ranking, calendar, tick replay with the evidence drawn on it, what-if, version compare. On open it tops up the tick store in the background (`ticks sync` up to now), shows how fresh the data is, and offers one button to run the EA over the new days. It never re-runs the EA by itself. Also holds the **Run** screen (pick EA, settings and any date range, then quick run or analysed run) and the **Data** tab (one package per year with Download and Top up buttons, see "Data tab"). | FastAPI + React/TypeScript; charts: lightweight-charts and uPlot (provisional, D-5) |
| MT4 bridge | An MT4 **indicator** (not an EA) on a chart that reads a command file, jumps to a time and draws the trade. MT4 does not let indicators place orders. | MQL4 |

## One software, two uses (D-16)

It is one program with one Run screen. The expert uses it in two ways: he lets it find the defects and jumps to them, or he picks a period and looks through it in MT4 with his own eyes. The second use must never force the first: no defect list, no analysis, nothing in his way.

- **Quick run.** The expert picks an EA, its settings and any date range (a day, three weeks, a month, a set of days, the year). The software checks the ticks for that range are stored, prepares MT4's history for exactly that range, starts the Strategy Tester on it, and leaves MT4 open with the result so he inspects it by hand, the way he does today. Visual mode is a tick box. No defect analysis runs.
- **Analysed run.** The same, followed by reconciliation and every detector.
- **A quick run can be analysed later** with one button, without running MT4 again, because its trades and journal are captured either way.
- **Both modes are Strategy Tester only** (D-14). Neither attaches an EA to a chart.
- **Missing ticks never pass silently.** If the chosen range has days that are not stored, the run does not start; it names the days and offers the download button.
- **Prepared history is reused.** A range that was prepared before starts without being rebuilt, so repeat runs are fast.
- To confirm in inc-2: that MT4 can be left open on the finished test, and that visual mode can be switched on, from the start file.

## MT4 export (D-18)

MT4 needs two different files, and they do different jobs.

- **Chart history, `.hst` (M1 bars).** This is what MT4 charts show, so it is what the click-to-chart jump lands on. Built by the method the user already used in another project (`C:\Users\yr471\OneDrive\Desktop\mt4-xasu-work\convert_to_mt4.py`, read-only reference): bid price, one bucket per minute, first / highest / lowest / last tick, volume = tick count, file named `<SYMBOL>1.hst`.
- **Tester tick file, `.fxt` (real ticks).** With only M1 bars, MT4's "Every tick" mode invents the path inside each minute. The EA would then be filled at prices and times that never happened, every finding would rest on made-up ticks, and reconciliation (D-9) would fail. So the tester is given the real ticks in its own `.fxt` file.
- **Two corrections to the reference method:**
  1. *Server time follows US daylight saving.* A fixed +2 hours is right only in winter. Measured in our ticks: the daily break starts at 20:59 UTC from 2026-03-09 and at 21:59 UTC from 2026-11-02, so the broker's clock is UTC+3 between those dates and UTC+2 outside them. The reference export covers 2026-10-29 and 2026-10-30 with +2, which puts those two days one hour off. The offset is computed per tick from the date, and confirmed against the installed terminal.
  2. *Prices are rounded to the broker's decimals before writing,* not only labelled. Dukascopy quotes gold to 3 decimals; IC Markets to 2 (from the user's note, to confirm on the terminal). The rounding (at most 0.005) is allowed for in reconciliation.
- **Not yet proven in a real MT4** (no MT4 on this PC yet; the reference files were checked as files only). inc-2 proves, in this order: MT4 shows our `.hst` correctly; the tester uses our `.fxt` instead of rebuilding its own; the largest `.fxt` it accepts; the modelling quality it reports. The `.hst` is written in MT4's current format (version 401) unless the terminal shows it needs the older version 400 the reference uses.
- The tester still applies one fixed spread to a run. Real spread is brought back by the defect engine, as before.

## Data tab (D-16, D-17)

One tab that shows what tick data is on this PC, as one package per year.

- **The list is what Dukascopy offers through `dukascopy-node`, and nothing else.** The first available year is read from the pinned package's own instrument record, not typed in by us. Measured 2026-11-20: gold ticks start on 2003-05-05, so the list runs from 2026 down to 2003.
- **One row per year,** newest first, with its state in words:
  - `Downloaded up to 2026-11-20` (the current year);
  - `Downloaded` (a complete past year);
  - `Downloaded, 3 days missing` (a year with gaps);
  - `Not downloaded`.
  Each row also shows the tick count and size on disk.
- **One button per row, matching the state:**
  - current year: **Top up**. It downloads every missing day of this year up to now, which includes everything from the last stored day to today;
  - a year with gaps: **Download missing**;
  - a year not downloaded: **Download**. Before it starts it shows the expected size and time, from the measured figures below.
- **Downloads run one at a time,** oldest day first, with a progress bar and a stop button. Stopping loses nothing; pressing the button again continues. Each button is `ticks sync` from inc-1 over that year's dates.
- **Opening a year** shows its days as a calendar: stored, partial (today), empty (weekend or holiday), missing.
- **Files the expert imported himself** (`ticks import`) are not mixed into this list. They appear in a separate "Imported files" section below it, only when there are any.
- The top-up on open (D-12) stays and does the same job as the Top up button, automatically.
- Sizes to quote (measured 2026-11-20 on the builder's store, to be re-checked in the inc-1 review): 2026-01-01 to 2026-11-20 is 84.0 million ticks in 277 day files, 0.5 GB on disk. A day takes about 7 seconds to download, so a full year is roughly 30 to 45 minutes.

## Detector contract (D-8)

Adding a defect must be a small, safe, self-contained job that the expert can hand to Claude Code in one sentence.

- **One file per defect:** `src/losslens/defects/<id>.py`. It declares `ID`, `TITLE`, `DESCRIPTION` (plain words), `LEVEL` (trade, basket or run), `NEEDS` (ticks, journal, profile, decision log, calendar), `PARAMS` (names, defaults, meaning) and one function `detect(ctx) -> list[Finding]`.
- **`ctx` gives everything ready-made:** the trade (or basket, or run), its precomputed measurements (R, MFE, MAE, spread at entry and exit, session, volatility, trend), and `ctx.ticks(from_ms, to_ms)`. A detector never opens files or talks to MT4.
- **A `Finding` carries its proof:** what it is attached to, a one-line explanation, the numbers that triggered it, and the time window to show. The app draws that proof on the tick replay, so the expert can check any finding by eye.
- **No detector without tests:** `tests/defects/test_<id>.py` must hold at least one case that must be flagged, one that must not, and one on the threshold edge. Cases are built with a small helper that makes synthetic ticks and trades, so tests need no downloads.
- **Discovered automatically:** a new file appears in the engine, the filters and the money ranking with no other change.
- **One command checks a new detector:** `python -m losslens defects check <id>` runs its tests, runs it on the latest stored run, and prints how many it found plus three examples.
- **Thresholds live in `defects.toml`,** overriding the defaults in the file. Changing a threshold needs no code.
- **The recipe is written down** in `docs/ADDING_A_DEFECT.md` and pointed to from `CLAUDE.md` and `AGENTS.md`, with a template file to copy.
- If the detector's `NEEDS` are not available for a run (no journal, no profile), it reports "not evaluated", never "no defects".

## Accuracy rules (D-9)

- **Reconcile first.** Before any detector runs, every MT4 trade is checked against the tick store: its entry and exit prices must exist in the ticks at those times within a small tolerance. If too many do not, the run is marked `RUN_NOT_RECONCILED` and the app says so at the top.
- **Measure once, in one place.** MFE, MAE, spread, session and the rest are computed by one tested module. Detectors read them; they do not recompute them.
- **Exit side is explicit.** Longs are measured on bid, shorts on ask. This is tested.
- **Every number is computed by code and stored with the finding.** Nothing is estimated.
- **Golden cases.** A small set of hand-checked real trades with known answers runs in the test suite and must not change without a decision.
- **Honest labels.** Findings that depend on thin or missing data carry `DATA_SUSPECT`. Things a backtest cannot know (real slippage, requotes, the broker's own feed) are stated in the app, not hidden.

## Safety: no live trading, ever (D-14)

The software only analyses. It must never place, change or close an order on any account, demo or real. This is enforced in layers, so no single mistake can break it:

1. **Tester only.** The runner starts MT4 only in Strategy Tester mode, where every order is simulated inside the tester and nothing is sent to a broker. The runner's start file may contain tester keys only; it never attaches an EA to a chart.
2. **No way to trade in our own code.** The Python side has no broker connection, no trading library and no account password. The price source (Dukascopy) is read-only.
3. **The bridge cannot trade.** It is an indicator, and MT4 refuses order functions inside indicators. Its source contains no order function at all.
4. **The reference EA refuses to run outside the tester.** Its first line of work is: if not `IsTesting()`, do nothing and remove itself. It is the only file allowed to contain order functions.
5. **A dedicated MT4 copy.** The runner uses its own MT4 folder (portable mode), separate from any terminal used for real trading. Before a run it checks that live trading is switched off in that copy and stops if it is not. (To confirm in inc-2: the tester still runs with live trading switched off.)
6. **A guard test that fails the build.** `tests/test_no_live_trading.py` scans the whole repository and fails if an order function appears anywhere except the reference EA, if the reference EA loses its tester check, if the runner writes a chart-attach key, or if a trading or broker library is added. It runs with the normal tests and on GitHub for every change.
7. **Written into the rules** for every AI that opens the repository (`AGENTS.md`, `CLAUDE.md`): refuse any request that would make this software trade, and never weaken the guard test.

Limit, stated plainly: these layers stop mistakes and careless changes. They cannot stop a person who deliberately rewrites the software and deletes the guards. And what the expert does with his own EA in his own MT4 is outside this software.

## Facts the design rests on

- measured: one trading day of XAUUSD ticks is about 0.55M rows and 21–27 MB as CSV (2026-03-03: 554,076 ticks). The first estimate of 130M ticks a year was too high: 2026-01-01 to 2026-11-20 is 84.0M ticks (measured on the builder's store, to be re-checked in the inc-1 review), so a full year is about 95M.
- measured: spread on 2026-03-03 had median 0.96, 99th percentile 2.69, max 13.74 (USD). Spread varies by more than 10x within a day.
- measured: no ticks in the 22:00 UTC hour on 2026-03-03 (daily break). Saturdays return an empty file with exit code 0.
- measured: the newest ticks are available within seconds; `-to` is exclusive.
- measured: on this PC, Node's own certificate store rejects every HTTPS host; `NODE_OPTIONS=--use-system-ca` fixes it. Dukascopy also sits behind a web firewall challenge that `dukascopy-node` solves with a headless browser (`--chrome-path`).
- checked (well known, re-test in inc-2): MT4's tester stores bid only and applies one fixed spread to a whole run. So spread-driven defects cannot appear in a native MT4 run. The defect engine re-checks every trade against real bid and ask to expose them.
- assumed (measure in inc-2): a full-year tick history file for MT4 would be around 5 GB (95M x 56 bytes), likely above what the 32-bit tester accepts, so runs are chunked by month with warm-up, or ticks are thinned. Decide after measuring.

## Storage contract

- `data/ticks/<SYMBOL>/<YYYY>/<YYYY-MM-DD>.parquet`: columns `ts_ms` int64 (UTC epoch ms), `bid` float64, `ask` float64, `bid_vol` float32, `ask_vol` float32; sorted by `ts_ms`, source order kept for equal timestamps; zstd.
- `data/ticks/<SYMBOL>/manifest.json`: one entry per day (status, tick count, first/last timestamp, source, fetch time).
- `data/lens.duckdb`: runs, trades, journal events, decisions, findings, notes (schema fixed in inc-2 and inc-3).
- `data/` is git-ignored.

## Increment sequence

1. Tick store (no MT4 needed).
2. MT4 run spike: one month end to end with the reference EA; measure MT4's limits. Quick run from the command line for any date range. The no-live-trading guard test and the tester-only runner arrive here, with the first MT4 code.
3. Full-year run, reconciliation, measurements, the detector contract and the first ten detectors.
4. The rest of catalogue v1, each with tests.
5. App v1: defect list, filters, saved views, money ranking, calendar, tick replay with evidence, tick top-up on open, the Run screen (quick and analysed runs) and the Data tab (year packages, Download and Top up).
6. MT4 jump.
7. Ship: private GitHub repository, one-step setup on the expert's PC, `CLAUDE.md`, the add-a-defect recipe proven by adding one through Claude Code.
8. What-if lab, version compare, review notes, team report, backtest-versus-demo comparison.
