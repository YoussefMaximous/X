# Builder handoff — Playground rebuild (MT4-native, tick bars, expert inspection)

Updated: 2026-11-21 · Part: Playground · Report: `work/report-playground.md`

## Goal

A local Playground that feels native to MT4, uses the real Dukascopy ticks as the edge, lets the
expert replay with tick bars or time bars, freeze a ticket, draw predictions, compare scenarios,
and load their expert inputs plus a Strategy Tester report to inspect the expert's closes and
exclude individual trades from a what-if.

## State and how to check it

Code: `src/losslens/playground/` (`page_body.py`, `page_script.py`, `page.py`, `build.py`) and
`tests/test_playground.py`. The command is wired in `src/losslens/cli.py` as `playground build`.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
```

Expected: 142 tests pass; all four tools exit 0; the command reports 16,498 ticks, first
`2026-03-03T14:00:00.003Z`, last `2026-03-03T14:29:59.817Z`, 683,343 bytes.

With an expert:

```text
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 \
  --inputs expert.set --report tester.htm --out data/playground/expert.html
```

Open `data/playground/xauusd-2026-03-03-1400.html` by double-click. The Help tab opens first.
Manual acceptance: step 20 ticks, switch to M1, open the Trade tab and buy, draw an up path and a
both-ways path, add a second scenario, run to end, change the grid to 0.25. For the expert, build
with `--inputs`/`--report`, open Expert, toggle the closes, and uncheck a trade.

## Done (evidence in the report)

- MT4 layout: menubar, toolbar, Market Watch, black chart, Terminal tabs, status bar; app template
  tokens.
- Period picker: Tick line, 1/10/100/500/1,000 ticks per bar, M1/M5/M15/M30/H1. Default 100T.
- Candles and raw tick line built from the stored Dukascopy ticks; Data Window O/H/L/C, change,
  tick count and `used / per bar`.
- Five-minute warm-up; auto-follow; wheel zoom; drag pan; Follow; replay bar with progress; Space.
- Trade, History, Prediction, Scenarios, Session and Help tabs; no overlay covering the chart.
- Expert tab: `.set`/`.mq4` inputs, tester report summary and in-window closes, chart toggle,
  per-trade `Use` checkbox, window start balance, what-if, scoreboard row.
- No MT4 execution, server, network, new dependency, base64, external asset or MT4 source change.
- Tests: 4 in `tests/test_playground.py`, including the expert input/report path.

## Ruled out / do not retry

- A welcome card over the chart: it hid the early bars and the expert markers. The Help tab opens
  first instead.
- A full-window x-axis from tick zero: it looked zoomed out and empty. The chart now warms up with
  five minutes and follows the cursor.
- An empty side panel as the main layout: it hid the MT4 habits. The Terminal/Data Window layout is
  the reference.
- Running MT4 or the EA from the Playground: it is a static local page. Use `mt4 run` and pass the
  report with `--report`.

## Open

- User manual acceptance in their browser, with their own expert `.set`/`.mq4` and tester report.
- A side-by-side pixel check against the installed MT4.
- The report gives close times/prices only; entry markers need a journal or a decision log, which
  this build does not have.
- `data/` is ignored; nothing generated is committed.

## Next step

User opens the generated page and runs the acceptance steps. For an expert, rebuild with
`--inputs` and `--report`, then use the Expert tab to inspect closes and test trade exclusion.
