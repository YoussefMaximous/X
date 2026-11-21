# Report — Playground rebuild (MT4-native, tick bars, expert inspection)

Updated: 2026-11-21 · Builder · Separate part.

**Summary.** Rebuilt the Playground after the feedback that the first view was too zoomed out,
had no period choice, did not make the ticks visible, and did not let the expert be loaded. The page
now uses the app template's MT4 layout: menubar, toolbar, Market Watch, chart, Terminal and status
bar. It has a period picker (Tick line, 1/10/100/500/1,000 ticks per bar, M1/M5/M15/M30/H1), candles
built from the stored Dukascopy ticks, a five-minute warm-up, auto-follow, wheel zoom, drag pan,
a Data Window, and a first-run Help tab. The Expert tab loads the project's `.set`/`.mq4` inputs and
an MT4 Strategy Tester report, shows the report's closes on the chart, toggles the overlay, and
lets each trade be unchecked from the what-if. The Playground never runs MT4; the run still comes
from the existing runner. No server, network, new dependency, base64, external asset or MT4 change.

## Files

- `src/losslens/playground/page_body.py` — MT4 layout, CSS and page markup
- `src/losslens/playground/page_script.py` — chart, replay, tickets, prediction, scenarios, expert
- `src/losslens/playground/page.py` — assembles the single HTML file
- `src/losslens/playground/build.py` — ticks, period data, expert inputs/report, atomic write
- `tests/test_playground.py` — page, cap, window and expert tests
- `src/losslens/cli.py` — `--inputs` and `--report` on `playground build`
- Generated and ignored: `data/playground/xauusd-2026-03-03-1400.html`

## Command

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
playground: data\playground\xauusd-2026-03-03-1400.html
ticks: 16498
first tick: 2026-03-03T14:00:00.003Z
last tick: 2026-03-03T14:29:59.817Z
bytes: 683343
BUILD_EXIT=0
```

The command also accepts `--inputs expert.set` (or `.mq4`) and `--report tester.htm`. It prints the
expert input count and how many report trades close in the window.

## What changed after the feedback

- **Zoomed out / empty first view:** the first five minutes are revealed at load, the x-axis fits the
  revealed series plus a small future margin, and the view auto-follows the cursor. `Follow` brings
  it back after a pan or zoom.
- **Period picker:** Tick line, 1/10/100/500/1,000 ticks per bar, and M1/M5/M15/M30/H1. The default
  is 100 ticks per bar; the Help explains how to switch to M1.
- **Ticks are drawn:** tick bars are OHLC candles built from the real Dukascopy ticks; the Tick line
  mode draws the raw bid line (and spread marks when zoomed in). The Data Window shows the current
  bar's O/H/L/C, change, tick count, and how full a tick bar is (`44 / 100`).
- **Cognitively clearer:** MT4 layout and tokens, first-run Help tab (not an overlay on the chart),
  Data Window, replay bar with tick progress, status messages, no tooltip for future prices.
- **Expert inspection:** the Expert tab uses the project's existing `.set`/`.mq4` reader and MT4
  report reader/reconcile path. It shows the report's in-window closes, a chart toggle, a per-trade
  `Use` checkbox, the window start balance, and a what-if final. Unchecking a trade removes its
  P&L from the what-if and hides its marker; the raw ticks stay untouched. The scoreboard adds a
  normalized `$10,000` expert row. The Playground does not execute the EA.

## Evidence

Page data: `tickCount = 16498`, `len(ticks) = 16498`, first
`[1772546400003, 5156.405, 5157.432]`, last `[1772548199817, 5145.685, 5146.755]`.
Static checks: no `://`, no `fetch(`, no `<script src=`, no `WebSocket`; required labels and the
period/grid controls are present. `node --check` on the inline script exits 0.

Final acceptance harness (headless Chrome, `file://`):

```text
initial: Help tab active, Tick 3,244 / 16,498, 100 ticks / bar, 44 / 100
+20 ticks: Tick 3,264 / 16,498, 64 / 100
switch to M1: 1 minute, 14:05 UTC, 20 ticks in the bar
Buy: 14:05:01 buy 0.01 5159.87, cursor still Tick 3,264, equity $9,998.80
2 prediction points; Both ways active
Scenarios: Scenario 1, Scenario 2
Grid: 0.25
Run to end: scoreboard visible
Scenario 2 | $10,000.00 | $0.00 | 0 | — | — | —
Scenario 1 | $9,985.81 | $50.36 | 1 | — | 3.46 | 50.0%
end: Tick 16,498 / 16,498
```

Period harness: all eleven periods switch and report the right Data Window values, including
Tick line (3,244 ticks), 1 tick/bar (3,244 bars), 10 ticks/bar (325 bars), 100 ticks/bar (33 bars),
M1 (5 bars), and the larger time bars (1 bar while only the first five minutes are revealed).

Expert harness (synthetic `expert.set` and tester report, same stored ticks):

```text
Expert: TestExpert · expert.set · report.htm
Report: 1 trade · net $1.00; window: 1 close · 1 placed; window start $10,000.00
Trade: 1 · 14:00:23 UTC · buy · 0.01 · 5156.40 · $1.00 · $10,001.00
What-if: 1 included · $1.00 · final $10,001.00
Uncheck the trade: 0 included · $0.00 · final $10,000.00
Re-check: 1 included · $1.00 · final $10,001.00
Overlay toggle: off
Scoreboard: Expert report (window, $10k) | $10,001.00 | — | 1 | 100.0% | — | —
```

## Tools

Verified in the shared working tree after the concurrent optimizer work settled:

```text
python -m pytest -q
142 passed in 5.26s
PYTEST_EXIT=0

python -m ruff check .
All checks passed!
RUFF=0

python -m ruff format --check .
85 files already formatted
FMT=0

python -m mypy
Success: no issues found in 30 source files
MYPY=0

python -m pytest -q tests/test_playground.py
4 passed
```

The pytest atexit warning about `pytest-current` permissions is pytest's temporary-folder cleanup;
the exit code is 0.

## Research and rationale

The rebuild follows MT4's visual-mode habits (step, chart through time, tester-style controls) and
TradingView/MotiveWave replay habits (a replay bar, step-forward, auto-follow, zoom/pan, a clear
cursor). Tick charts are useful for activity and spread detail but noisy alone, so the default is
100 ticks per bar and time bars are one click away. The first view shows the first five minutes so
the chart has shape; the Help tab opens first so the controls are explained without covering the
chart. The app template's exact tokens (Tahoma, `#f0f0f0`, `#e4e4e4`, `#2f6fb3`, black chart,
`#00c000`/`#ff4040`) keep the Playground in the same product.

## Not verified / open

- The user's own browser and their real expert report; the Expert path was tested with a synthetic
  report whose close matches a stored tick. The Playground does not run MT4; the runner produces
  the report.
- A side-by-side pixel check against the installed MT4; the layout follows the app template and
  MT4's documented visual mode.
- `data/` is ignored; nothing generated is committed.
