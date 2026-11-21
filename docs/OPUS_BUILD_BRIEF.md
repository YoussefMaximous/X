# Build brief for Opus — the loss-lens app after the MT4 spike

Read first: `AGENTS.md`, `.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`,
`.teams/QUALITY.md`, `.teams/LOSSES.md`, `docs/OPTIMIZE.md`.

## Scope change

**MT4 execution and the EA run are out of scope for this build.** The app is
independent of MT4: it reads the local tick store and imported trade files. Keep
the existing MT4 modules (`src/losslens/mt4/`) as legacy tools, but do not build
the app on them, do not launch MT4, and do not require `.fxt`/`.hst` for any app
feature.

The user's words: “we are independent of it; remove these 2.” The two removed
items are (1) the EA run and (2) MT4.

## Current state

- Tick store: `data/ticks/<SYMBOL>/<YEAR>/<DAY>.parquet`, columns `ts_ms`
  (UTC epoch ms, int64), `bid`, `ask` (float64, 3 decimals for XAUUSD),
  `bid_vol`, `ask_vol`. `TickStore.read_ticks(from_ms, to_ms)` is the one read
  function. `python -m losslens ticks status|verify|query|import|sync`.
- Chart page: `python -m losslens app build --symbol XAUUSD --day YYYY-MM-DD
  [--inputs expert.set]` writes a self-contained MT4-style HTML page with 3
  decimals, real ask line/spread, timeframes, pan/zoom, Market Watch, Terminal
  tabs and an Expert Inputs editor that saves a `.set`.
- AI-native optimizer: `python -m losslens optimize plan|run|status|shortlist|
  decide|winner|best`, engines `random` and `smac`, JSON outputs, a chosen
  “winner” that need not be the top score, `docs/OPTIMIZE.md` is the AI protocol.
- Legacy MT4 readers: report/journal/reconcile/check tools. Useful only as
  import formats; do not launch MT4.

## What to build

### 1. The app shell — native to an MT4 user

- FastAPI backend on `127.0.0.1` only, React/TypeScript frontend, bundled
  assets, no internet on load. (The Lead must add the approved dependencies and
  server bind to the safety guard; do not weaken the guard yourself.)
- Window layout: menu bar and toolbars on top, Market Watch and Navigator on the
  left, chart in the middle, Terminal-style tabs at the bottom, status bar.
- MT4 habits, not a reskin: right-click menus, F-keys, drag/drop, double-click,
  timeframe buttons, crosshair, auto-scroll, chart shift, templates, colours.
- Use our own code, icons, text and colours. Never copy MetaQuotes code, name,
  logo, icons or assets.
- 60 fps chart, instant panel switches, no layout jank, no spinner on local data.

### 2. Runs and trades — the data the app needs without MT4

Define a run/trade model and an import path. No EA run is performed.

```text
Run: id, symbol, period, from_day, to_day, source, imported_at, notes
Trade: id, run_id, ticket, side (buy/sell), lots,
       open_time_utc_ms, open_price, close_time_utc_ms, close_price,
       stop_loss, take_profit, profit, commission, swap, comment
```

- Import an MT4 Strategy Tester report and journal as **files** (reuse
  `src/losslens/mt4/report.py` and `journal.py`; do not launch MT4). The report
  gives closed trades; the journal can add entries where present.
- Import a generic CSV/JSON with the `Trade` columns. This is the primary path
  when the expert has no MT4 output.
- Store runs in a local file the app reads. DuckDB is the planned store; if the
  dependency is not approved, use Parquet/JSONL and keep the interface.
- Every imported trade is reconciled against the ticks: its open and close
  prices must exist in our bid/ask at those times within a stated tolerance.
  Unreconciled runs are shown as `RUN_NOT_RECONCILED`, never silently trusted.

### 3. Chart with trade markers

- Candles/line with M1 to MN, 3 decimals, real bid/ask and a spread readout.
- Draw every trade: entry and exit arrows, a dashed line between them, SL and TP
  lines, profit/loss label. Hover shows the trade; click opens its detail.
- Clicking a trade/reason moves the chart to that exact moment and starts tick
  replay. Play/pause, step, speed, jump to entry/exit.
- Drawing tools: horizontal, vertical and trend lines, channels, Fibonacci,
  text, arrows; templates and chart properties.
- Standard indicators checked against the real MT4 where possible; custom EA
  indicators are out of scope (state that plainly).
- Optional “Open in real MT4” bridge is out of scope in this build.

### 4. Results (the losses screen)

- Open on the biggest loss and work down; money at stake is always visible.
- Show the reason/type, the proof numbers, and the total money per reason across
  the run. A loss can have several reasons or none; never invent one.
- Filters and saved views: side, symbol, date, reason, size, session, duration,
  spread, tags. Toggle reasons on/off; hide rather than delete.
- One click opens the trade on the chart at the right moment with replay.
- If no classification data exists, show “Unclassified” and allow manual tags;
  do not fabricate reasons.
- Keep the title neutral if the user prefers not to name it “losses”; the
  internal concept stays.

### 5. Data tab

- List tick coverage per symbol/year, missing weekdays, disk size.
- Download/Top up only on an explicit click; the only online source is
  Dukascopy. No automatic download, no timer, no telemetry.
- Import another tick CSV through the existing importer.
- Show the freshness of the store and a button to run the EA only if that path
  is ever re-enabled; otherwise show “Import a run”.

### 6. Optimization lab

- Read `data/optimize/<run>/results.jsonl`, `decision.json`, `config.json`.
- Table of every trial: values, metrics, objective, eligible, error.
- Chart of the improvement curve; mark the best score and the chosen winner
  separately; show the decision reason and the stop advice.
- One click opens the winner’s `.set` and the trial table; no hidden trials.
- The AI-native commands stay the source of truth; the lab is a view.

### 7. Quality and performance

- `python -m pytest -q`, `python -m ruff check .`,
  `python -m ruff format --check .`, `python -m mypy` all exit 0.
- Every screen has tests for its data logic; no TODO, stub, mock or sample data
  in a shipped path.
- Performance budgets: chart at 60 fps with 50k visible bars; a 1M-tick day
  loads without freezing; panel switches under 100 ms; no network on load.
- Side-by-side check against the installed MT4 for layout and habits; the user
  signs it off.

### 8. Packaging

- One setup step on Windows; no admin if possible; the app runs from the repo or
  a packaged build; local data stays under `data/`.
- Never commit `data/`, tick files, `.set` files, EA files or account data.

## Safety rules that stay

- No live trading, ever. Nothing places, changes or closes an order on any
  account.
- Nothing leaves the PC. The only online action is the Dukascopy download when
  the user asks. The app listens on `127.0.0.1` only.
- Never copy, upload or commit an EA file; do not open an EA source unless the
  user asks.
- No MetaQuotes assets, name, logo or code. Our look is our own implementation.
- The safety guard (`tests/test_no_network.py`, `tests/test_no_live_trading.py`)
  must stay green. Only the Lead extends its approved lists.

## Acceptance for the first app increment

1. App starts on `127.0.0.1`, no network requests on load.
2. Imports a run CSV and shows its trades on the chart with entry/exit markers.
3. Clicking a loss opens the chart at its entry and replays the ticks.
4. Results list sorts by loss size and shows total money per reason.
5. Data tab shows coverage and the store’s freshness.
6. Optimization lab shows all trials, best vs chosen winner, and the stop reason.
7. The four tools exit 0; no stub/mock data in the shipped path.
8. A side-by-side MT4-look review is signed off by the user.

## Out of scope for this build

- Running an EA or MT4 Strategy Tester.
- Re-implementing EA logic.
- Live/demo trading, broker connections, account credentials.
- Copying MetaQuotes assets, icons, name or code.
- Cloud, accounts, telemetry, uploads.

## Decisions for the Lead

- Approve the app dependencies and the `127.0.0.1` server bind in the guard.
- Confirm the trade import format the expert can provide (CSV, MT4 report, or
  both).
- Confirm the neutral label for the Results/losses screen.
- Confirm whether the optional MT4 bridge is dropped permanently (recommended
  for this build).
