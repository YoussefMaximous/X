# Main software handoff — the app is handed to Opus

Updated: 2026-11-21 · Latest code: `8e2ba52` · CI green · Brief for Opus: `docs/OPUS_BUILD_BRIEF.md`

## Goal

The app, independent of MT4: the tick store, imported trades, the native chart
with trade markers, the results/losses screen, the Data tab and the optimization
lab. MT4 and the EA run are out of scope for this build. The full brief is
`docs/OPUS_BUILD_BRIEF.md`.

## State and how to check it

The repository is pushed to `https://github.com/YoussefMaximous/loss-lens`
(private), CI green at `8e2ba52`. 141 tests passed in a clean worktree at
`bf33a11`; ruff, ruff format and mypy exit 0. The Playground rebuild is
committed as `2bf658d` with its own handoff/report.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens app build --symbol XAUUSD --day 2026-03-03
python -m losslens app build --symbol XAUUSD --day 2026-03-03 --inputs expert.set
python -m losslens mt4 inputs expert.set
python -m losslens optimize plan --set expert.set --expert MyEA --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --budget 50 --engine smac --out data/optimize/run1 --json
python -m losslens optimize run --config data/optimize/run1/config.json --dry-run --json
python -m losslens optimize status --run data/optimize/run1 --json
python -m losslens optimize shortlist --run data/optimize/run1 --limit 5 --json
python -m losslens optimize decide --run data/optimize/run1 --trial 7 --reason "steadier neighbourhood" --json
python -m losslens optimize winner --run data/optimize/run1 --json
```

## Done

- Tick store, validated, one read function.
- `app build` writes one self-contained MT4-style page: menu, Market Watch,
  chart, Terminal tabs, timeframes, pan/zoom, crosshair, Expert Inputs with Save
  `.set`. The chart keeps **3 decimals** and draws the real ask line/spread;
  MT4's `.hst`/`.fxt` still round to 2 only at the export boundary.
- AI-native optimizer: goal questions, stop advice, shortlist, winner that need
  not be the best score, random + SMAC, JSON for the AI.
- SMAC is installed (`smac==2.4.1`, `ConfigSpace==1.2.2`); guard allowlists
  updated; `TestExpertParameters` is allowed and the tester can receive a trial
  `.set`.
- Legacy MT4 readers/tools (report, journal, reconcile, export) remain for
  importing and verifying old files; they are not part of the app build.

## Ruled out / do not retry

Date fields 472/476, matching all six header numbers, making our file newer than
the bars, and writing all 1,380 UTC-day bars: none made MT4 keep the file. MT4's
EA run is removed from scope.

## Open

- The app shell, trade import, chart trade markers, results/losses screen, Data
  tab, optimization lab and installer are **not built**. Opus builds them from
  `docs/OPUS_BUILD_BRIEF.md`.
- The app dependencies and the `127.0.0.1` server bind need the Lead's guard
  approval; the brief says so.
- The parallel Playground is committed and has its own handoff/report; leave it
  alone.

## Next step

Hand `docs/OPUS_BUILD_BRIEF.md` to Opus. Do not wait on MT4 or an EA run.
