# X — wrap-up for Opus

Updated: 2026-11-22 · Repo: `https://github.com/YoussefMaximous/X` (private)
Build spec: `docs/OPUS_BUILD_BRIEF.md`

## What X is

A native Windows desktop app. One window, no browser, no web server, no
localhost page. The chart, Market Watch, Terminal, inputs, menus and status bar
are ours. MT4, when used, is only a hidden EA host: tester-only, no chart, no
UI, closed after the run.

## Run it

```text
python -m pip install -e .
x desktop --symbol XAUUSD --day 2026-03-03
x desktop --symbol XAUUSD --day 2026-03-03 --inputs expert.set
```

The X window opens with the day’s ticks. Drag to pan, wheel to zoom, arrows to
move, End to jump. Timeframes M1–D1, real ask line, spread, 3 decimals, Expert
Inputs with Save `.set`.

## What works today

- **Tick store:** `data/ticks/<SYMBOL>/<YEAR>/<DAY>.parquet`; UTC ms, bid/ask,
  3 decimals for XAUUSD. `ticks status|verify|query|import|sync`.
- **X desktop:** native Tkinter shell; chart, Market Watch, Terminal, status,
  timeframes, crosshair, 3-decimal bid/ask/spread, Expert Inputs editor.
- **Optimizer, AI-native:** `x optimize plan|run|status|shortlist|decide|winner|
  best`; JSON; goal questions; stop advice; top + diverse candidates; a chosen
  winner that need not be the top score; no hidden trials.
- **SMAC:** installed (`smac==2.4.1`, `ConfigSpace==1.2.2`) and enabled as
  `engine=smac`; dry runs work. It writes the same trial `.set` files.
- **Hidden host runner:** `LOSSLENS_MT4_HOST=<logged-in MT4 data folder>` switches
  runs from the copy to the logged-in terminal. `mt4 run --expert MyEA
  --parameters expert.set` writes `TestExpert` and `TestExpertParameters`, runs
  tester-only, and reads the report. The code is ready; it has **not** been run
  end-to-end against the live terminal yet.
- **Legacy MT4 readers:** report/journal/reconcile/check tools; useful as import
  formats, never launched by X.

## What is not built yet

- Run and Optimization panels inside X (they are CLI now).
- Trade/run import (CSV or MT4 report/journal files) and the local run store.
- Trade markers on the X chart (entry/exit, SL/TP, click → replay).
- Results/losses screen (biggest first, money per reason, filters, saved views).
- Data tab and the optimization lab.
- Layer 2: the `LossLens.mqh` fill engine on real bid/ask for source EAs.
- Installer / `.exe` packaging.
- The 2-vs-3-decimals decision is deliberately open for Opus.

## Accuracy split

- **Compiled EA:** MT4’s fixed spread and 2-digit symbol shape the EA’s own
  decisions. X re-prices every trade on our 3-decimal ticks after the run and
  marks later orders that depended on a corrected fill.
- **Source EA:** layer 2 puts our fill engine in charge of every order inside the
  tester — real spread, 3 decimals. This is the full-accuracy path.
- The tick store, X chart, fills and analysis use **3 decimals**. MT4’s
  `.hst`/`.fxt` round to 2 only at the file boundary because the symbol says 2.

## Open questions for Opus / the Lead

1. **2 or 3 decimals.** Our data is 3; MT4’s symbol/files are 2; compiled EAs see
   2 inside the tester. Choose the product rule with the expert.
2. **Source or compiled EAs.** Source enables layer 2 and full real-spread fills;
   compiled gets layer-1 correction only.
3. **Trade import format.** CSV, MT4 report/journal files, or both.
4. **Tkinter or PySide6** for the fuller X UI.
5. **Hidden host:** use the logged-in terminal (env path) or log into the copy
   once.
6. **Layer 2 include:** scope and proof against MT4 at a fixed spread.

## Verify

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
x desktop --symbol XAUUSD --day 2026-03-03
x optimize plan --set expert.set --expert MyEA --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --budget 6 --engine smac --out data/optimize/demo --json
x optimize run --config data/optimize/demo/config.json --dry-run --json
x optimize status --run data/optimize/demo --json
```

The previous clean-tree run was 141 tests; the current changes add desktop and
host tests. Re-run all four tools before accepting.

## For Opus

Read `docs/OPUS_BUILD_BRIEF.md` first. It contains the full app, trade import,
chart markers, losses screen, Data tab, optimization lab, performance budgets
and safety rules. Do not add a browser, a web server or a localhost page. Do not
weaken the safety guards. Keep everything local.

## The open question for Opus

**How do we make X the best environment in the world for testing, optimizing and
improving the Expert?**

Leave this open. Do not assume the answer. Explore it with the expert and measure
it.

Starting points, not answers:

- What must he see to trust a run: real fills, spread at entry/exit, the tick
  path, the proof, the difference from MT4?
- What does “better” mean for him: money, robustness across periods, fewer big
  losses, fewer rule breaks, faster decisions?
- How should optimization choose a winner: top score, stability across
  neighbouring parameters, out-of-sample, drawdown, trade count, simplicity?
- How do we shorten the loop from a new idea to a validated improvement?
- Which parts belong in the app, which in a batch run, and what should be one
  click?
- What can we remove so the environment stays fast and clear?
- What would make him stop using the live demo as his first test?

