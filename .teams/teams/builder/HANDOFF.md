# Builder handoff — local Playground (MT4-native)

Updated: 2026-11-21 · Part: Playground (separate from inc-2) · Report:
`work/report-playground.md`

## Goal

A local, self-contained Playground page for stepping through stored ticks, freezing time, opening
simulated tickets, drawing predicted moves, comparing scenarios on the same ticks and scoring them
on what really happened. It must feel native to MT4 users and match the app template, while doing a
different job and doing it better.

## State and how to check it

Code: `src/losslens/playground/` and `tests/test_playground.py`. The command is wired in
`src/losslens/cli.py` as `playground build` (already in HEAD).

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens playground build --symbol XAUUSD --day 2026-03-03 --from 14:00 --to 14:30 --out data/playground/xauusd-2026-03-03-1400.html
```

Expected: 126 tests pass; all four tools exit 0; the command reports 16,498 ticks, first
`2026-03-03T14:00:00.003Z`, last `2026-03-03T14:29:59.817Z`, 648,724 bytes.

Open `data/playground/xauusd-2026-03-03-1400.html` by double-click. Manual acceptance: step 20,
freeze and open a buy, draw an up path and a both-ways path, add a second tab, run to end, change the
grid to 0.25.

## Done (evidence in the report)

- One self-contained HTML file; ticks embedded as JSON in
  `<script id="tick-data" type="application/json">`.
- No server, network, new dependency, base64, external font/image/CDN, or MetaQuotes asset.
- Playback: Next tick / 10 / 100, Reset, Space, shared cursor; no auto-play.
- Freeze: Buy at ask, Sell at bid, 0.01 volume default, optional SL/TP, entry/floating/equity,
  $10,000 start, contract size 100, visible PAUSED; opening/closing never moves the cursor.
- Grid: 0.01, 0.05, 0.10, 0.25, 0.50, 1.00 and custom; drawing snaps to it.
- Prediction: click future ticks, polyline, Clear/Undo, both-ways mirror, fixed-move preview,
  scored MAE and direction hit rate.
- Scenarios: add/rename/duplicate/delete, own tickets and predictions, shared cursor, Run to end
  scoreboard sorted by final equity.
- localStorage keyed by dataset id; local JSON export/import.
- `file://` checked in headless Chrome; localStorage restore and JSON export/import checked.
- Visual system aligned to the app template: Tahoma 11px, `#f0f0f0` panels, `#e4e4e4` headers,
  `#a0a0a0` lines, `#2f6fb3` accent, black chart, `#00c000` bid/up, `#ff4040` ask/down.

## Ruled out / do not retry

- A server or any external asset: the page must open by double-click from `file://`.
- `fetch`, WebSocket, CDN links, web fonts or images; the guard tests cover the no-network rule.
- Random, Brownian or statistical path generation; the user draws, the real ticks judge.
- Changing MT4 code or `.teams/` outside this builder folder.
- Committing `data/`: the generated page is ignored.

## Open

- User manual acceptance in their own browser (double-click; download/upload dialogs).
- A side-by-side pixel comparison with the installed MT4; the skin follows the app template tokens.
- The main app (concurrent) may later reuse these exact tokens; this Playground is not integrated
  into the app's server/UI.
- Concurrent MT4 report/journal/reconciliation and app work landed in the same repo; not part of
  this part. One whitespace-only `ruff format` touched a line in the concurrent `cli.py` so the
  repo-wide format gate is green; no behavior changed.
- `data/` is ignored.

## Next step

User opens the generated page and runs the acceptance steps. Lead reviews `report-playground.md`
and decides whether the Playground is accepted; if accepted, the same MT4 tokens are the reference
for the next app screens.
