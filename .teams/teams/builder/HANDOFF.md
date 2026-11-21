# Builder handoff — Playground inside X

Updated: 2026-11-22 · Part: Playground · Report: `work/report-playground.md`

## Goal

A local Playground that lives inside the X desktop app: real Dukascopy ticks, tick and time
bars, mouse zoom/pan, freeze-time tickets, predictions, scenarios, and a drawn future tape.
The standalone HTML build remains available for the expert report overlay.

## State and how to check it

Native code: `src/losslens/desktop/playground_model.py`, `playground.py`, and the menu/toolbar
hook in `app.py`. Tests: `tests/test_desktop_playground.py`.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens desktop --symbol XAUUSD --day 2026-03-03
```

Expected: 158 tests pass; all four tools exit 0. In X, click **Playground** or use
**File > Playground**. The window opens at 14:04:59 UTC on 2026-03-03 with 90 bars in view.

Try: wheel zoom, drag pan, End; Draw prediction and click ahead; Draw ticks and drag right;
Next tick/+10/+100/Next bar; Clear ticks; Buy/Sell with S/L and T/P; Scenarios > Run to end;
the Go field (`14:00` + Return).

## Done

- Native Playground window launched from X, single instance reused.
- X styling and layout: toolbar, Market Watch, Data Window, Replay, trade terminal, status.
- 14:00 UTC opening session with five-minute warm-up; Go jumps anywhere in the day.
- Draw prediction (click) and Draw ticks (drag), snap to the price grid.
- Clear ticks restores the real tape at the branch and clears tickets/predictions.
- Tickets, stops, prediction scoring, scenarios, scoreboard, max drawdown.
- Expert tab shows the inputs loaded by X; no MT4 execution.
- 9 model tests; 158 total pass.

## Ruled out / do not retry

- A separate browser sub-app or server. The native window and the one-file HTML build are enough.
- Replacing X's main chart. The Playground is its own window inside X.
- Starting at midnight: the first minutes are thin and the chart looks empty. Start at 14:00
  UTC with the last-30-minutes fallback.
- Editing MT4 files or the tester report format.

## Open

- Native MT4 report overlay / include-exclude what-if; the HTML Playground still owns it.
- User acceptance with their real expert `.set` and report.
- `data/` is ignored; generated pages are not committed.

## Next step

Open X, launch the Playground, and run the acceptance steps above. For the report overlay,
build/open `data/playground/xauusd-2026-03-03-1400.html` with `--inputs` and `--report`.
