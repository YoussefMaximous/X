# Report — Playground rebuilt in the X style

Updated: 2026-11-22 · Builder · Separate part.

**Summary.** Rebuilt the Playground to match the X desktop app (`src/losslens/desktop/app.py`):
X branding, Tahoma, `#f0f0f0` panels, raised/sunken Tk-style buttons, the X timeframe buttons
(Tick, 1T, 10T, 100T, 500T, 1K, M1, M5, M15, M30, H1), black chart, 3-decimal prices, green/red
candles, the pink ask line, the B/A/S overlay, the grey last-price line and the green last-price
tag. The chart starts with the first five minutes revealed, follows the cursor, and supports
mouse-wheel zoom and drag-to-pan. The replay bar, Market Watch, Data Window, Terminal tabs and
status bar follow the X layout. Added **Draw prediction** with a live snapped preview, and
**Draw ticks** / **Clear ticks**: drag a light-grey future tape from the freeze point, step through
it with the normal tickets/predictions, and clear it to restore the real tape. The Expert tab still
loads the project's `.set`/`.mq4` inputs and an MT4 tester report; while a drawn tape is active the
real report is hidden, because the expert report belongs to the real tape. No server, network, new
dependency, base64, external asset or MT4 change.

## Output

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
playground: data\playground\xauusd-2026-03-03-1400.html
ticks: 16498
first tick: 2026-03-03T14:00:00.003Z
last tick: 2026-03-03T14:29:59.817Z
bytes: 698081
BUILD=0
```

The file is ignored by git. It is one self-contained HTML page: inline CSS/JS, ticks as JSON in
`<script id="tick-data" type="application/json">`, no external address, font, image, CDN, `fetch`,
`<script src=` or `WebSocket`.

## X style alignment

- Brand `X` with a muted `Playground`, window title `X — Playground`.
- Timeframe buttons in the toolbar, active button sunken; all toolbar/replay buttons raised and
  sunken like Tk.
- Chart colours from X: `#000` background, `#1a1a1a` grid, `#d0d0d0` text, `#a8a8a8` axes,
  `#00c000` up/bid, `#ff4040` down, `#ff9090` ask, grey `#707070` last-price line, green bid tag.
- Candles are bid OHLC with a body capped at 14 px; the pink ask close line runs over them.
- Chart overlay: `XAUUSD, <period>`, O/H/L/C/V, and `B/A/S` in ask pink, as in X.
- 3-decimal prices throughout (chart, Market Watch, Data Window, tickets).

## Playback and drawing

- First five minutes revealed; auto-follow; wheel zoom; drag pan; `Follow`; double-click follows.
  Status shows the view size so zoom is visible.
- **Draw prediction**: click future points, snapped to the price grid; a live blue preview shows
  the point and its snapped price. Undo/Clear in the Prediction tab or Tools menu.
- **Draw ticks**: drag a light-grey path into the future from the current freeze point. The path
  becomes a synthetic tape: custom bid/ask ticks replace the real future, the pink ask line and
  candles follow, and the normal replay, tickets, SL/TP and prediction scoring work on it.
  `Clear ticks` restores the real tape and clears tickets/prediction. The tape is saved in
  localStorage and the scenario JSON.
- Expert: `--inputs` and `--report`; the Expert tab shows inputs, report summary/closes, the chart
  toggle and per-trade include/exclude. It is hidden while a drawn tape is active; the report is
  tied to the real tape.

## Evidence

```text
python -m pytest -q
149 passed in 9.33s
PYTEST=0

python -m ruff check .
All checks passed!
RUFF=0

python -m ruff format --check .
92 files already formatted
FMT=0

python -m mypy
Success: no issues found in 33 source files
MYPY=0

python -m pytest -q tests/test_playground.py
4 passed
```

Final headless `file://` acceptance harness:

```text
initial: X Playground, 100T active, view 42 bars, real ticks, FUTURE
wheel: view 42 bars -> 34 bars
M1 button: 1 minute, active M1
Draw prediction: 2 points
Draw ticks: 53 custom ticks, status "16,498 real + 53 drawn", tape "Drawn · 53 ticks",
            clear enabled, replay 3,244 / 3,297
after Next 10: tick 3,254 / 3,297, status "drawn"
After Clear ticks: FUTURE, "16,498 Dukascopy ticks", tape "Real ticks", clear disabled
Run to end: scoreboard visible
```

The expert harness (synthetic `.set` + tester report on the same stored ticks) showed
`TestExpert`, the input row, one in-window close at 14:00:23 UTC (buy 0.01, close 5156.400,
profit $1.00), and unchecking it changed the what-if from $10,001.00 to $10,000.00; rechecking
restored it. The scoreboard expert row was `Expert report (window, $10k) | $10,001.00 | — | 1 |
100.0% | — | —`.

Period harness: all eleven periods switch, including Tick line (3,244 ticks), 1 tick/bar
(3,244 bars), 10 ticks/bar (325 bars), 100 ticks/bar (33 bars), M1 (5 bars), and the larger time
bars while only the first five minutes are revealed.

## Not verified / open

- The user's own browser and their real expert `.set`/report; the expert path was tested with a
  synthetic report whose close matches a stored tick.
- A side-by-side pixel check against the running X desktop window; the style follows its constants
  and layout.
- The report gives close times/prices only; entry markers need a journal or decision log.
- `data/` is ignored; nothing generated is committed.
