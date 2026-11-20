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
                      Local app  ── click ──> our MT4-style chart at that trade (optional: the same moment in real MT4)
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
| App | Looks and works like MT4 (D-21). MT4-style chart with tools, indicators and tick replay; the Losses panel (D-22); defect list, filters, saved views, money ranking, calendar, the evidence drawn on the chart, what-if, version compare. On open it goes online for nothing: it reads the local manifest, shows how old the stored data is, and offers the Top up button and a button to run the EA over the new days (D-20). It never downloads and never re-runs the EA by itself. Results are shown two ways side by side: "MT4 says" and "with real spreads" (D-19). Also holds the **Run** screen (pick EA, settings and any date range, then quick run or analysed run) and the **Data** tab (one package per year with Download and Top up buttons, see "Data tab"). | FastAPI + React/TypeScript; charts: lightweight-charts and uPlot (provisional, D-5) |
| MT4 bridge | Optional extra, "Open in real MT4" (D-21); the main place to inspect is our own MT4-style chart. An MT4 **indicator** (not an EA) on a chart that reads a command file, jumps to a time and draws the trade. MT4 does not let indicators place orders. | MQL4 |

## One software, two uses (D-16)

It is one program with one Run screen. The expert uses it in two ways: he lets it find the defects and jumps to them, or he picks a period and looks through it with his own eyes on our MT4-style chart (D-21). The second use must never force the first: no defect list, no analysis, nothing in his way.

- **Quick run.** The expert picks an EA, its settings and any date range (a day, three weeks, a month, a set of days, the year). The software checks the ticks for that range are stored, prepares MT4's history for exactly that range, runs the Strategy Tester on it in the background, and opens the result on our chart with every trade drawn, so he inspects it by hand the way he does today. "Open in real MT4" stays available. No defect analysis runs.
- **Analysed run.** The same, followed by reconciliation and every detector.
- **A quick run can be analysed later** with one button, without running MT4 again, because its trades and journal are captured either way.
- **Both modes are Strategy Tester only** (D-14). Neither attaches an EA to a chart.
- **Missing ticks never pass silently.** If the chosen range has days that are not stored, the run does not start; it names the days and offers the download button.
- **Prepared history is reused.** A range that was prepared before starts without being rebuilt, so repeat runs are fast.
- To confirm in inc-2: that MT4 can run a test from the start file without its window getting in the user's way, and close itself when the test ends.

## MT4 export (D-18)

MT4 needs two different files, and they do different jobs.

- **Chart history, `.hst` (M1 bars).** This is what MT4 charts show, so it is what the click-to-chart jump lands on. Built by the method the user already used in another project (`C:\Users\yr471\OneDrive\Desktop\mt4-xasu-work\convert_to_mt4.py`, read-only reference): bid price, one bucket per minute, first / highest / lowest / last tick, volume = tick count, file named `<SYMBOL>1.hst`.
- **Tester tick file, `.fxt` (real ticks).** With only M1 bars, MT4's "Every tick" mode invents the path inside each minute. The EA would then be filled at prices and times that never happened, every finding would rest on made-up ticks, and reconciliation (D-9) would fail. So the tester is given the real ticks in its own `.fxt` file.
- **Two corrections to the reference method:**
  1. *Server time follows US daylight saving.* A fixed +2 hours is right only in winter. Measured in our ticks: the daily break starts at 20:59 UTC from 2026-03-09 and at 21:59 UTC from 2026-11-02, so the broker's clock is UTC+3 between those dates and UTC+2 outside them. The reference export covers 2026-10-29 and 2026-10-30 with +2, which puts those two days one hour off. The offset is computed per tick from the date, and confirmed against the installed terminal.
  2. *Prices are rounded to the broker's decimals before writing,* not only labelled. Dukascopy quotes gold to 3 decimals; IC Markets to 2 (from the user's note, to confirm on the terminal). The rounding (at most 0.005) is allowed for in reconciliation.
- **Not yet proven in a real MT4** (no MT4 on this PC yet; the reference files were checked as files only). inc-2 proves, in this order: MT4 shows our `.hst` correctly; the tester uses our `.fxt` instead of rebuilding its own; the largest `.fxt` it accepts; the modelling quality it reports. The `.hst` is written in MT4's current format (version 401) unless the terminal shows it needs the older version 400 the reference uses.
- The tester still applies one fixed spread to a run. Real spread is brought back by the defect engine, as before.

## Real-spread execution (D-19)

MT4's tester fills orders from one price line plus one fixed spread. Our ticks hold the real bid and the real ask. So MT4 keeps the one job only it can do, executing the EA's code, and loss-lens takes over the filling of orders. An MT4 EA cannot run anywhere but MT4, so a fully separate engine is not an option (D-3 stands).

**Layer 1: real-spread re-fill (any EA, compiled or with source).**
- MT4 runs the EA on the real bid ticks. loss-lens then replays every order the EA placed, tick by tick, on the real bid and ask: entry price, stop and target triggers (longs exit on bid, shorts on ask), close price, profit.
- Every order and the whole run are reported twice: "MT4 says" and "with real spreads", with the difference and the tick that caused it.
- Its limit, shown in the app and never hidden: the EA took its later decisions inside MT4's fixed-spread world. Where a corrected result would have changed what the EA did next (a re-entry after a stop, a lot size taken from the balance, a grid step), the orders after that point are marked "depends on an earlier corrected order".
- Stops and targets: by default they keep their distance from the entry (so they move with the corrected entry price); the other reading (keep the absolute price) is a setting. With a decision log the EA's own rule is used.

**Layer 2: real-spread broker inside the test (EAs with source).**
- The expert adds one line to his EA, an include of `LossLens.mqh`. During a tester run every order call in his EA goes to our simulated broker instead of MT4's, and `Ask`, the spread and the account figures it reads come from the real ticks. Decisions and fills are then both on real spreads, for the whole run.
- MT4 still executes the EA's code and its indicators. Nothing else of MT4's order handling is used.
- The library is plain, short, readable source. It reads the tick file and writes its log on this PC and does nothing else: no network function, no DLL, no real order function (see "Privacy" and "Safety"). An EA compiled with the line in cannot place a real order anywhere, because its order calls no longer reach MT4.
- **Proof before trust:** with the spread forced to a constant, a layer-2 run must match MT4's own tester order for order (same tickets, times, prices, profit) on the reference EA across a full month. Only then is the real spread switched on. This check stays in the test suite.
- Simulating MT4's whole order interface is the riskiest piece of the project. It gets a second independent review, and anything the library does not support makes the run stop with a plain message, never a silent guess.

**What we may claim, and what we may not.** More accurate than MT4's tester on spread (real, per tick, not one fixed number) and on ticks (real, not invented inside each minute), with proof per order. Not claimed: real slippage, requotes, or the broker's own price feed; those appear only on a live demo.

## Privacy: nothing leaves the PC (D-20)

The software is open source and must be safe for any user, his data and his EAs. This is enforced the same way as the no-trading rule: in layers, with a guard test.

1. **One online action, and only when asked.** The only thing the software ever does online is download public price ticks from Dukascopy, and only when the user presses Download or Top up (or runs `ticks sync`). Nothing happens online on start, in the background, or on a timer.
2. **Nothing is ever sent out.** No telemetry, no analytics, no crash reports, no update checks, no accounts, no cloud. The download asks for a symbol and a date; it carries nothing about the user, his EAs or his results.
3. **EAs stay where they are.** The software never uploads, emails or copies an EA out of the PC. It does not need to read EA source at all: it works from the compiled file in MT4's own folder and records only its name and a fingerprint (hash) so a run can be repeated. No EA file is ever added to git (`*.ex4`, `*.mq4`, `*.mqh` outside our own are git-ignored).
4. **The app is local.** It listens on `127.0.0.1` only, so no other device can reach it. Its screens load no fonts, scripts or images from the internet; everything is bundled.
5. **Our MT4 files cannot go online.** The bridge indicator, `LossLens.mqh` and the reference EA contain no `WebRequest`, `SendMail`, `SendFTP` or `SendNotification`, and import no DLL, so MT4's "Allow DLL imports" and "Allow WebRequest" stay off.
6. **Few, pinned dependencies.** Every dependency is named in a brief, pinned, and locked with checksums. The one piece that goes online, `dukascopy-node`, is pinned to an exact version.
7. **A guard test that fails the build.** `tests/test_no_network.py` fails if network code (`socket`, `urllib`, `http.client`, `requests`, `httpx`, `aiohttp`, `websockets`, `ftplib`, `smtplib` and the like) appears anywhere except the one downloader module; if the server binds to anything but `127.0.0.1`; if a screen references an outside address; if an MQL4 file of ours contains an online function or a DLL import; or if a dependency outside the approved list is added. The test suite itself runs with the network blocked.
8. **Written into the rules** for every AI that opens the repository (`AGENTS.md`, `CLAUDE.md`): never add anything that sends data out, never copy or upload EA files, do not open the user's EA source unless he asks, never weaken the guard test.
9. **A plain-words page at the top of the repository** ("What this software does and does not do") so any user, or his AI, can check these claims against the code in minutes.

Limits, stated plainly:
- MT4 is its own program. When logged in it talks to its broker, as it always does. The runner uses its own separate MT4 copy; inc-2 checks whether that copy can run tests without being logged in at all.
- The downloader is third-party code (`dukascopy-node`) that opens a hidden browser to pass the site's check. It is pinned, but it is not ours.
- An AI assistant such as Claude Code sends the files it reads to its provider. That is outside this software. The expert's EA source does not need to be in this repository's folder, and the rules tell the AI not to open it.
- These layers stop mistakes and careless changes. Open source means anyone can read the code and see it is so; it also means a person can make his own changed copy.

## MT4 look and feel (D-21)

The team works inside loss-lens. MT4 runs in the background to execute the EA and is not where anyone looks. So our chart has to feel like the chart they have used for years.

**What matches MT4** (each item is checked against the real MT4 on this PC, side by side, on the same symbol and period):
- Window layout: toolbars on top, chart in the middle, Market Watch and Navigator style panels on the left, a Terminal style panel at the bottom with tabs, a status bar. Panels open and close with MT4's keys.
- The chart: MT4's default colours (black background, green bars, grid, bid line), bars, candles and line types, timeframes M1 to MN, zoom steps, auto-scroll and chart shift, crosshair with distance read-out, period separators, the price and time scales, the top-left symbol and OHLC text, the Data Window.
- Tools: horizontal, vertical and trend lines, channels, Fibonacci, text and arrows, drawn and edited the way MT4 does it. Templates and chart properties (colours) can be changed and saved.
- Standard indicators (moving averages, RSI, MACD, Bollinger Bands, ATR, Stochastic and the rest of MT4's built-in list). Each one is tested against values exported from MT4 itself; one that does not match MT4 is not shipped.
- Trades drawn the way the tester draws them: entry and exit arrows, the dashed line between them, stop and target lines.
- Replay controls in the style of the tester's visual mode: speed slider, pause, step, skip to a time. Ours goes tick by tick.
- MT4's keyboard keys and mouse habits wherever we have the same function.

**What is added, without changing a habit:** the real ask line and spread, the defect's proof drawn on the chart, the Losses panel, "MT4 says" beside "with real spreads", next and previous defect keys.

**Limits, stated plainly:**
- An EA's own custom indicators can only be computed by MT4. They are not drawn on our chart. For those, "Open in real MT4" (the bridge) shows the same moment in MT4.
- We copy how it looks and behaves. We do not use MetaQuotes' code, name, logo or icon pictures; our icons are our own drawings in the same places. (MT4 is free to use but it is not open source.)
- MT4 has hundreds of small behaviours. "Like MT4" is held by a written checklist made from the real MT4 and signed off by the team before the screens are built, not by impression.

**Chart engine:** chosen by a short trial at the start of the app increment, between `lightweight-charts` with our own additions and our own canvas chart. It must pass three checks: looks like MT4 side by side, supports the drawing tools, and plays a day of ticks at 60 frames per second.

## Loss classification (D-24)

Classifying why a trade lost is the core of the product, and it is the hard part. A loss can have several reasons, or none. When several fit, one is the main reason, the one that accounts for the most of the loss, and each further reason must pass a gate: a score high enough against that loss (D-25). How the score and the gate work is not settled. The screen (types on and off, every loss listed from the biggest, the pattern shown before the name, the money and the spread of each type) is being designed; the brief is `.teams/teams/lead/work/checkpoints/2026-11-20-loss-types-screen.md`.

What already stands:
- A defect is a reason a loss happened (D-23). The draft reasons are in `.teams/DEFECTS.md`.
- Clicking a loss opens our chart at that moment, with replay.
- Results can be read as "MT4 says" or "with real spreads" (D-19).

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
- Nothing is downloaded automatically. The tab shows how many days behind the current year is, and the user presses Top up (D-20, which replaces the automatic top-up of D-12).
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
6. **A guard test that fails the build.** `tests/test_no_live_trading.py` scans the whole repository and fails if an order function appears anywhere except the reference EA (and, in `LossLens.mqh`, the lines that redirect those names to the simulated broker), if the reference EA loses its tester check, if the runner writes a chart-attach key, or if a trading or broker library is added. It runs with the normal tests and on GitHub for every change.
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
2. MT4 run spike: one month end to end with the reference EA; measure MT4's limits. Quick run from the command line for any date range. The two guard tests (no live trading, no network) come first, as part A, before any MT4 code; the tester-only runner arrives with the first MT4 code, as part B.
3. Full-year run, reconciliation, measurements, the real-spread re-fill (layer 1), the detector contract, the first ten detectors and the one-main-cause loss classification (D-22).
4. The rest of catalogue v1, each with tests.
5. App, part 1: the MT4-style chart (D-21). The MT4 checklist and designs signed off by the team, the chart-engine trial, then chart, timeframes, tools, standard indicators checked against MT4, trades drawn, tick replay.
6. App, part 2: the Losses panel (D-22), defect list, filters, saved views, calendar, proof drawn on the chart, "MT4 says" beside "with real spreads", the Run screen (quick and analysed runs) and the Data tab (year packages, Download and Top up).
7. Real-spread broker inside the test (layer 2): `LossLens.mqh`, the match-MT4-at-fixed-spread proof, then real spreads. "Open in real MT4" (the bridge) is built here too.
8. Ship: public open-source repository with a licence, the plain-words safety page, one-step setup on the expert's PC, `CLAUDE.md`, the add-a-defect recipe proven by adding one through Claude Code.
9. What-if lab, version compare, review notes, team report, backtest-versus-demo comparison.
