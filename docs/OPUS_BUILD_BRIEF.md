# Build brief for Opus — X, the desktop app

Read first: `AGENTS.md`, `.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`,
`.teams/QUALITY.md`, `.teams/LOSSES.md`, `docs/OPTIMIZE.md`.

## Scope change

**The product is a native desktop app named X, not a browser application.**
There is no web server and no `127.0.0.1` page to open. One Windows window holds
the menus, toolbars, Market Watch, chart, Terminal tabs and status bar. The app
reads the local tick store and imported trade files. MT4 is allowed only as a
**hidden EA host**: tester-only, no chart, no MT4 UI, closed after each run; X
owns every screen and all analysis. Keep the existing MT4 modules
(`src/losslens/mt4/`); the app never shows MT4. The 2-vs-3-decimals and
source-vs-compiled questions are listed at the end.

## Current state

- Tick store: `data/ticks/<SYMBOL>/<YEAR>/<DAY>.parquet`, columns `ts_ms`
  (UTC epoch ms, int64), `bid`, `ask` (float64, 3 decimals for XAUUSD),
  `bid_vol`, `ask_vol`. `TickStore.read_ticks(from_ms, to_ms)` is the one read
  function. `python -m losslens ticks status|verify|query|import|sync`.
- HTML chart prototype: `python -m losslens app build --symbol XAUUSD --day
  YYYY-MM-DD [--inputs expert.set]` writes a self-contained page. Keep it as a
  reference for the visuals; it is not the product.
- Desktop shell: `x desktop --symbol XAUUSD --day YYYY-MM-DD [--inputs
  expert.set]` opens a native Tkinter window named **X** with the MT4 layout,
  3-decimal bid/ask, timeframes, pan/zoom, Market Watch, Terminal, status and an
  Expert Inputs editor. This is the base Opus extends.
- AI-native optimizer: `python -m losslens optimize plan|run|status|shortlist|
  decide|winner|best`, engines `random` and `smac`, JSON outputs, a chosen
  “winner” that need not be the top score, `docs/OPTIMIZE.md` is the AI protocol.
- Hidden host runner: `LOSSLENS_MT4_HOST=<logged-in MT4 data folder>` switches
  runs from the copy to the live terminal; `mt4 run --expert MyEA --parameters
  expert.set` writes `TestExpert`/`TestExpertParameters`, runs tester-only and
  reads the report. Code ready, not yet run end-to-end.
- Legacy MT4 readers: report/journal/reconcile/check tools. Useful as import
  formats; the hidden host is the only place MT4 is launched.

## What to build

### 1. The app shell — native to an MT4 user

- Native Windows desktop app in Python. The current `x desktop` shell uses
  Tkinter (stdlib, no browser, no server). Opus may move to PySide6 for a richer
  look, but there must be **no web server and no browser window**.
- Window layout: menu bar and toolbars on top, Market Watch and Navigator on the
  left, chart in the middle, Terminal-style tabs at the bottom, status bar.
- MT4 habits, not a reskin: right-click menus, F-keys, drag/drop, double-click,
  timeframe buttons, crosshair, auto-scroll, chart shift, templates, colours.
- Use our own code, icons, text and colours. Never copy MetaQuotes code, name,
  logo, icons or assets.
- 60 fps chart, instant panel switches, no layout jank, no spinner on local data.
- One process, one window; no localhost server, no bundled webview, no tab.

### 1b. Run and Optimization screens inside X

- **Run panel:** pick the EA/expert name, its `.set`, the date range, spread and
  timeout; press **Run hidden**. Show a progress log and a summary from the
  report (ticks, bars, trades, net profit, drawdown, profit factor). No MT4
  window, no MT4 chart, no MT4 tabs.
- The host is the logged-in terminal selected by `LOSSLENS_MT4_HOST`; if it is
  not set, use the isolated copy. MT4 is tester-only, closed after the run. Never
  type a login or password.
- Back up an existing `history/default/<SYMBOL>1.hst` and
  `tester/history/<SYMBOL>1_0.fxt` before replacing them; leave a timestamped
  copy beside them.
- **Optimization panel:** list the run folders; edit the goal/budget/constraints;
  run `random` or `smac`; show `status` advice, `shortlist`, and the chosen
  winner beside the top score. The CLI stays the source of truth; the panel
  calls the same core.
- **Accuracy split:** compiled EAs are re-priced after the run (layer 1) and later
  orders that depended on a corrected fill are marked; source EAs can use the
  layer-2 include so every fill is ours inside the tester.

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
- Dukascopy catalog: `docs/DUKASCOPY_DATA.md`; fork
  `YoussefMaximous/dukascopy-node` (MIT, 1,499 instruments, 10 timeframes).
  Show the years available and one Download/Top up button per year.
- Download/Top up only on an explicit click; the only online source is
  Dukascopy. No automatic download, no timer, no telemetry.
- Import another tick CSV through the existing importer.
- Show the freshness of the store and both actions: **Run hidden** (the MT4 host)
  and **Import a run**.

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

- One setup step on Windows; no admin if possible. Ship a shortcut or a
  PyInstaller build named **X** that opens the window without a console; local
  data stays under `data/`.
- Never commit `data/`, tick files, `.set` files, EA files or account data.

## Safety rules that stay

- No live trading, ever. Nothing places, changes or closes an order on any
  account.
- The hidden host is Strategy Tester only. Never type a login or password. Back
  up an existing HST/FXT before replacing it, and close MT4 after each run.
- Nothing leaves the PC. The only online action is the Dukascopy download when
  the user asks. X is one desktop process; no server listens at all.
- Never copy, upload or commit an EA file; do not open an EA source unless the
  user asks.
- No MetaQuotes assets, name, logo or code. Our look is our own implementation.
- The safety guard (`tests/test_no_network.py`, `tests/test_no_live_trading.py`)
  must stay green. Only the Lead extends its approved lists.

## Acceptance for the first app increment

1. X opens as a native Windows window; no browser, no server, no network on load.
2. Imports a run CSV and shows its trades on the chart with entry/exit markers.
3. Clicking a loss opens the chart at its entry and replays the ticks.
4. Results list sorts by loss size and shows total money per reason.
5. Data tab shows coverage and the store’s freshness.
6. Optimization lab shows all trials, best vs chosen winner, and the stop reason.
7. The four tools exit 0; no stub/mock data in the shipped path.
8. A side-by-side MT4-look review is signed off by the user.
9. The Run panel starts a hidden tester run and shows its report; no MT4 window
   or MT4 chart appears.
10. The Optimization panel shows every trial, the best score, the chosen winner
    and the stop reason.

## Out of scope for this build

- Showing MT4's window, chart or tester UI. MT4 is the hidden host only; X is
  the only screen.
- Re-implementing EA logic.
- Live/demo trading, broker connections, account credentials.
- Copying MetaQuotes assets, icons, name or code.
- Cloud, accounts, telemetry, uploads.

## Decisions for the Lead

- Approve PySide6 if Opus chooses it over Tkinter. Tkinter needs no new
  dependency. There is no server bind to approve.
- Confirm the trade import format the expert can provide (CSV, MT4 report, or
  both).
- Confirm the neutral label for the Results/losses screen.
- Confirm the hidden host path: the already logged-in terminal
  (`LOSSLENS_MT4_HOST`) or a one-time login in the isolated copy.

## Open questions for Opus

1. **2 or 3 decimals.** Our data is 3; MT4’s symbol/files are 2; compiled EAs
   see 2 inside the tester. Choose the product rule with the expert.
2. **Source or compiled EAs.** Source enables layer 2 and full real-spread
   fills; compiled gets layer-1 correction only.
3. **Layer 2 include.** Scope and proof that it matches MT4 at a fixed spread
   before switching to real spreads.
4. **Tkinter or PySide6** for the fuller X UI.
5. **Trade import format** and the run/trade store schema.
6. **The big one:** how to make X the best environment for testing, optimizing
   and improving the Expert. Leave this open; explore it with the expert and
   measure it.
