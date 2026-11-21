# Report — local Playground (MT4-native, matches the app's template)

Updated: 2026-11-21 · Builder · Separate part; not an inc-2 change.

**Summary.** Added `src/losslens/playground/` and `playground build`. It reads the window with
`TickStore.read_ticks` (UTC epoch ms), stops above `--max-ticks`, and writes one self-contained
HTML page with inline CSS/JS and the ticks embedded as JSON. The page is a black Canvas 2D chart
with a lime bid line, red ask line, MT4 price/time axes, playback, freeze-time simulated tickets,
price grid, prediction drawing, both ways, fixed-move preview, scenario tabs, localStorage and
local JSON export/import. The visual system now uses the same tokens as the app template being
built beside it: Tahoma 11px, `#f0f0f0` panels, `#e4e4e4` headers, `#a0a0a0` lines, `#2f6fb3`
accent, black chart, `#00c000` up and `#ff4040` down. No server, network, new dependency, base64,
external font/image/CDN, MT4 code change, or MetaQuotes asset.

## Files

- `src/losslens/playground/__init__.py`
- `src/losslens/playground/build.py`
- `src/losslens/playground/page.py`
- `tests/test_playground.py`
- CLI wiring in `src/losslens/cli.py` (`playground build`)
- Generated and ignored: `data/playground/xauusd-2026-03-03-1400.html`

## 1. Command

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
playground: data\playground\xauusd-2026-03-03-1400.html
ticks: 16498
first tick: 2026-03-03T14:00:00.003Z
last tick: 2026-03-03T14:29:59.817Z
bytes: 648724
```

`tests/test_playground.py` also checks the cap: a 6-tick window with `--max-ticks 2` exits 2 and
prints `the window has 6 ticks, more than --max-ticks 2` plus `choose a shorter --from/--to window`.

## 2. Page checks

- Data: `<script id="tick-data" type="application/json">` parses to `tickCount = 16498`,
  `len(ticks) = 16498`, first `[1772546400003, 5156.405, 5157.432]`,
  last `[1772548199817, 5145.685, 5146.755]`.
- Static: no `://`, no `fetch(`, no `<script src=`, no `WebSocket`.
- Required text: `Next tick`, `Next 10`, `Next 100`, `Reset`, `Buy`, `Sell`, `Both ways`,
  `Run to end`, `PAUSED`, `FUTURE HIDDEN`; grid control `id="grid-step"` with
  `0.01 / 0.05 / 0.10 / 0.25 / 0.50 / 1.00 / custom`.
- JavaScript: `node --check` on the extracted inline script exits 0.
- `file://` in headless Chrome: loads, no JS error, and the acceptance harness produced:

```text
initial:            Tick 1 / 16498
after Next 10 x2:   Tick 21 / 16498
after Buy:          cursor still Tick 21 / 16498
ticket:             14:00:01 buy 0.01 5157.12 - - -$1.10 Close
equity:             $9,998.90
prediction:         Points 3 · reached 0 · MAE - · direction -
Both ways:          active
tabs:               Scenario 1, Scenario 2
grid after change:  0.25
Run to end:         scoreboard visible
score rows:         Scenario 2 | $10,000.00 | $0.00 | 0 | - | - | -
                    Scenario 1 | $9,988.56 | $50.36 | 1 | - | 14.93 | 33.3%
cursor after end:   Tick 16498 / 16498
```

- localStorage: reload of the same file restored `Tick 21 / 16498` and the ticket row.
- Export/import: export captured a `losslens.playground` JSON with 1 tab, 1 ticket, cursor 20;
  feeding it back through the file input produced `Scenario file imported.`
- SL/TP: a stop on a revealed tick closes at the stop price; manual close uses current bid/ask and
  leaves the cursor unchanged.

## 3. Tools

Verified on the committed tree `a096cc1` in a clean worktree, so the concurrent work-in-progress
in the main tree does not affect this evidence.

```text
python -m pytest -q
126 passed in 1.97s
PYTEST_EXIT=0
```

One pytest atexit cleanup warning about `pytest-current` permissions is printed after the result;
it is pytest's temporary-folder cleanup, not a test, and the exit code is 0.

```text
python -m ruff check .
All checks passed!
RUFF_CHECK_EXIT=0

python -m ruff format --check .
78 files already formatted
RUFF_FORMAT_EXIT=0

python -m mypy
Success: no issues found in 26 source files
MYPY_EXIT=0
```

The same clean worktree builds the page with the same result:

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out <temp>.html
ticks: 16498
first tick: 2026-03-03T14:00:00.003Z
last tick: 2026-03-03T14:29:59.817Z
bytes: 648724
BUILD_EXIT=0
```

Focused: `python -m pytest -q tests/test_playground.py` → `3 passed`.

Current main tree note: a concurrent agent is mid-write on `src/losslens/optimize/` and
`src/losslens/cli.py`. A repo-wide run there currently fails at `cli.py:125` with
`cmd_optimize_plan` undefined, and the optimize files have their own lint issues. That work is not
part of this commit and has not been changed. The clean-worktree result above is the Playground's
evidence; re-run the four tools after the concurrent work settles.

## MT4 look

The user asked the Playground to feel native to MT4 and to match the rest of the software. The
chart is the MT4 default: black, lime bid, red ask, gray grid, right price scale, bottom time
scale, filled bid/ask price tags, and a blue `NOW` marker. The chrome is the app template's MT4
language: Tahoma, light panels, beveled buttons, white terminal table and inputs, blue active
buttons, and a light status bar. The Playground's own tools (scenario tabs, prediction, both ways,
scoreboard) are styled in the same language. No MetaQuotes code, name, logo, icon or font file is
used; Tahoma is a Windows system font.

## Not verified / open

- A side-by-side pixel check against the installed MT4 was not made; the skin follows the app
  template's tokens and MT4's documented default layout. The user's manual acceptance is the final
  visual check.
- The user's own browser download/upload dialogs were not exercised; export/import was verified
  in-process with Blob/FileReader in headless Chrome.
- `data/` is ignored; nothing generated is committed.
- Concurrent MT4 report/journal/reconciliation and app work landed in the same repository during
  this session. It is not part of this report and was not changed, except a whitespace-only
  `ruff format` on one unformatted line in the concurrent `cli.py` so the repo-wide format gate is
  green.
