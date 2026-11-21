# Main software handoff — after send-back 5, the chart, expert inputs and the optimizer

Updated: 2026-11-21 · Latest code: `d8942ae` · The parallel Playground has its own section in `../HANDOFF.md`.

## Goal

Accurate runs on our real ticks, then the parts around them: the MT4-style chart, the expert's inputs, and an AI-native optimization loop (random and SMAC). The product is not finished; the blockers are listed below.

## State and how to check it

138 tests pass in a clean worktree at `d8942ae`; ruff, ruff format and mypy exit 0. The live tree currently has an uncommitted Playground refactor beside this work; its own test is mid-write, so repo-wide runs are temporarily red until that session commits.

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
python -m losslens mt4 check-report --report <report.htm> --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
python -m losslens mt4 parse-journal <tester.log> --tail 20
python -m losslens mt4 reconcile --report <report.htm> --symbol XAUUSD
```

## Done

- FXT stops at broker midnight after `--to`; byte-checked on 2026-03-03, 03-09, 07-15 and 11-10.
- `mt4 run --visual/--no-visual` controls MT4's tester chart, default off.
- `mt4 parse-report`, `check-report`, `parse-journal` and `reconcile` read MT4's own output and verify the ticks.
- `mt4 run` parses its report and prints whether MT4 counted our ticks or its own.
- `app build` writes one self-contained MT4-style page: menu, Market Watch, chart, Terminal tabs, timeframes, pan/zoom, crosshair, and an Expert Inputs dialog that saves a real MT4 `.set`.
- `mt4 inputs` reads a `.set` or `.mq4`; the `.set` writer keeps the MT4 optimization range format.
- `optimize` is the AI-native interface: plan asks the user the goal/risk/trades questions, `run --dry-run` validates the loop, `status` gives stop advice, `shortlist` gives candidates, `decide` records a winner that need not be the top score, `winner` writes it, `best` keeps the top score separate.
- SMAC is installed (`smac==2.4.1`, `ConfigSpace==1.2.2`) and enabled as `engine=smac`; the smoke run did 6 trials on the dry objective and found 98.3333 at `Lots 0.04, StopLoss 40`.
- The guard allowlists now include `smac`/`ConfigSpace` and the exact dependency set; the guard tests still pass.
- `docs/OPTIMIZE.md` tells an AI how to run the conversation, when to stop and how to keep every trial visible.

## Ruled out / do not retry

Date fields 472/476, matching all six header numbers, making our file newer than the bars, and writing all 1,380 UTC-day bars: none made MT4 keep the file.

## Open

- Whether MT4 now keeps the 30,405,312-byte tick file: the Lead's run.
- The **real** optimizer evaluator needs `TestExpertParameters` in the start file; the safety guard's tester-key list must allow it. Then a trial can pass a `.set` to MT4. SMAC itself is now enabled; only the MT4 side is missing.
- The copy has no account; automated runs need a one-time login in the copy or a decision to drive the logged-in terminal.
- The full app and the losses screen are not built; `app build` is a static page, not the server UI.
- The parallel Playground is committed and has its own handoff/report; leave it alone.

## Next step

The Lead allows `TestExpertParameters` and runs the new FXT once. Then the real evaluator connects to the SMAC interface that is already in place.
