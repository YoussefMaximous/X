# Report — Playground merged into X

Updated: 2026-11-22 · Builder · Native window plus the HTML build.

**Summary.** The Playground now runs inside the X desktop app as a native Tk window. Open it
from X's **File > Playground** menu or the **Playground** toolbar button. It loads the real
Dukascopy ticks for X's symbol and day, opens at the 14:00 UTC session (falling back to the
last 30 minutes when that session is missing), reveals five minutes of warm-up, and follows
the cursor. The HTML build remains available and unchanged.

## Files

- `src/losslens/desktop/playground_model.py` — pure replay, tickets, predictions, scenarios,
  and the drawn future tape.
- `src/losslens/desktop/playground.py` — the native window.
- `src/losslens/desktop/app.py` — X menu/toolbar entry and single-window reuse.
- `tests/test_desktop_playground.py` — nine model tests.

## Native behaviour

- Periods: Tick, 1T, 10T, 100T, 500T, 1K, M1, M5, M15, M30, H1.
- Wheel zoom around the pointer, drag to pan, End follows the cursor, Space reveals one tick.
- The toolbar time field defaults to `14:00`; press Go or Return to jump to any UTC time.
- Trade: Buy at ask, Sell at bid, optional S/L and T/P checked on every revealed tick.
- Draw prediction: click ahead of the cursor; the path is blue, scored points turn green/red.
- Draw ticks: drag a light-grey path into the future; step through it with the normal replay,
  tickets, stops, and prediction scoring. Clear ticks restores the real tape at the branch.
- Scenarios, duplicate/delete, Run to end, scoreboard, max drawdown, prediction MAE/hit rate.
- Expert tab lists the `.set`/`.mq4` inputs X loaded; it never runs MT4.
- X style: Tahoma, `#f0f0f0` panels, raised/sunken Tk buttons, black chart, 3-decimal prices,
  green/red candles, pink ask line, B/A/S overlay, grey last-price line, green last tag.

The browser page still adds the MT4 tester report overlay, include/exclude what-if, and the
saved-session behaviour. The native window does not port the report overlay yet.

## Launch

```text
python -m losslens desktop --symbol XAUUSD --day 2026-03-03
```

Then open **File > Playground** or click **Playground**. Add expert inputs with `--inputs`.
The browser page remains at `data/playground/xauusd-2026-03-03-1400.html`.

## Evidence

```text
python -m pytest -q                 158 passed
python -m ruff check .              All checks passed
python -m ruff format --check .     95 files already formatted
python -m mypy                      Success: no issues found in 35 source files
```

Native smoke on 2026-03-03: 554,076 ticks; opened at 14:04:59 UTC; 90 bars in view; Market
Watch 5158.875 / 5160.095, spread 1.220; Data Window and Replay populated; chart rendered
candles, pink ask line, B/A/S, last-price tag; toolbar fits at 1400 px.

## Not verified / open

- The user's own browser-free acceptance run and their real `.set`/report files.
- A native MT4 report overlay: the HTML build still owns that path.
- `data/` is ignored; generated pages are not committed.
