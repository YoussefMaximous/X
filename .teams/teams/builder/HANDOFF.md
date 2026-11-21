# Builder handoff — Playground in the X style

Updated: 2026-11-22 · Part: Playground · Report: `work/report-playground.md`

## Goal

A local Playground that looks and feels like the X desktop app. It replays real Dukascopy ticks,
supports tick bars and time bars, mouse zoom/pan, freeze-time tickets, predictions scored by the
real ticks, scenario comparison, and an Expert tab for the project's `.set`/`.mq4` inputs and MT4
tester report. It also has a Draw ticks mode that lets the user paint a hypothetical future tape
and replay it.

## State and how to check it

Code: `src/losslens/playground/` (`page_body.py`, `page_script.py`, `page.py`, `build.py`) and
`tests/test_playground.py`. The command is wired in `src/losslens/cli.py`.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
```

Expected: 149 tests pass; all four tools exit 0; 16,498 ticks; first
`2026-03-03T14:00:00.003Z`; last `2026-03-03T14:29:59.817Z`; 698,081 bytes.

Open `data/playground/xauusd-2026-03-03-1400.html` by double-click. The Help tab opens first.
Try: wheel zoom, drag pan, Follow; Draw prediction and click ahead; Draw ticks and drag into the
future; step through the drawn tape; Clear ticks; add a scenario; Run to end; grid 0.25.

Expert build:

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 \
  --inputs expert.set --report tester.htm --out data/playground/expert.html
```

## Done

- X style: brand, Tahoma, `#f0f0f0`/`#e4e4e4`, raised/sunken buttons, timeframe buttons, black
  chart, 3-decimal prices, green/red candles, pink ask line, B/A/S overlay, grey last-price line,
  green last tag, 14 px candle bodies.
- Periods: Tick line, 1/10/100/500/1,000 ticks per bar, M1/M5/M15/M30/H1.
- Five-minute warm-up, auto-follow, wheel zoom, drag pan, Follow, double-click follow.
- Draw prediction with snapped live preview; Draw ticks / Clear ticks branch tape.
- Trade/History/Expert/Prediction/Scenarios/Session/Help Terminal tabs.
- Expert inputs/report with toggle and per-trade include/exclude; hidden while a drawn tape is
  active.
- No server, network, new dependency or MT4 change.

## Ruled out / do not retry

- A welcome overlay on the chart: it hid the data. The Help tab opens first.
- A full-window x-axis from tick zero: it looked zoomed out. Warm-up plus auto-follow.
- Editing MT4 files or the expert report format. Use `.set`/`.mq4` and the tester report as they
  are.
- A server, browser sub-app or external assets.

## Open

- User manual acceptance with their own browser and real expert files.
- Side-by-side pixel check against the running X desktop app.
- Entry markers need a journal/decision log; the tester report has closes only.
- `data/` is ignored; nothing generated is committed.

## Next step

Open the generated page and try the acceptance steps. For an expert, rebuild with `--inputs` and
`--report`; use the Expert tab; if you draw a tape, clear it to return to the real expert view.
