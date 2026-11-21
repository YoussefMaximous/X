# Optimize an EA — for the AI and the user

This page is for an AI assistant working in this repository. The user does not
need to learn SMAC or the optimizer's internals; you drive it and explain it.

## What is real today

- `mt4 inputs` reads a `.set` preset or an `.mq4` source.
- `optimize plan` turns the `.set` ranges into `config.json` and lists the
  questions to ask the user.
- `optimize run --dry-run` validates the loop without MT4.
- `optimize status`, `shortlist`, `decide`, `winner` and `best` work on a run.
- `engine=random` and `engine=smac` both run. SMAC is installed and drives the
  same trial loop; `--dry-run` validates it.
- The **real MT4 evaluator** is enabled: each trial `.set` is copied to the
  copy's `tester/` folder and passed with `TestExpertParameters`. It still needs
  a logged-in MT4 copy (this PC's copy has no account) and a working tester run.
- `config.json` has an `engine` field: `random` or `smac`.

## The conversation you must have

Before spending a single trial, ask the user:

1. What are we optimizing for: net profit, profit factor, drawdown, or a mix?
2. What is the largest drawdown you accept?
3. What is the minimum number of trades?
4. Is this period representative, or should we validate on another?
5. How many trials may I spend?

Show the plan (`optimize plan --json`) and its `questions` list. Do not start a
run until the user answers. Write the answers into `config.json` (objective,
constraints, budget) before running.

## Commands

```text
python -m losslens mt4 inputs expert.set
python -m losslens optimize plan --set expert.set --expert MyEA --symbol XAUUSD \
    --from 2026-03-03 --to 2026-03-03 --budget 50 --engine smac \
    --out data/optimize/run1 --json
python -m losslens optimize run --config data/optimize/run1/config.json --dry-run --json
python -m losslens optimize run --config data/optimize/run1/config.json --json
python -m losslens optimize status --run data/optimize/run1 --json
python -m losslens optimize shortlist --run data/optimize/run1 --limit 5 --json
python -m losslens optimize decide --run data/optimize/run1 --trial 7 \
    --reason "flatter neighbourhood, drawdown inside the limit" --json
python -m losslens optimize winner --run data/optimize/run1 --json
python -m losslens optimize best --run data/optimize/run1 --json
```

Every command takes `--json`; use it. The plain output is for the user, the JSON
is for you.

A real run launches MT4 once per trial, so it is slow. Use `--dry-run` to check
the loop first. `--visual` shows MT4's tester chart (slower); `--timeout` sets
the per-trial limit.

## Stop rule

`optimize status --json` returns `advice.recommended_stop` and `advice.reason`.
The advice is not a command. You decide, then tell the user:

- how many trials ran, and how many failed;
- the best score and whether it is still improving;
- whether the budget is spent or the search has plateaued;
- why you stopped, or why you want more trials.

Stop when the budget is spent, the best has not improved for a meaningful
window, or the candidates are unstable. Never stop silently.

## The winner is not always the best

`optimize best` writes the highest score. The winner is a separate, recorded
decision:

- read `shortlist`: the top eligible trials plus the candidate most different
  from the best;
- look at the neighbourhood: a good winner should not fall apart when a
  parameter moves one step;
- check the constraints and the failed trials;
- ask the user which trade-off they prefer;
- record it with `optimize decide --trial N --reason "..."`;
- write it with `optimize winner`.

Every trial, every metric, every failure and the decision reason stay in the run
folder. Never hide a failed trial, a rejected candidate or the reason for
stopping. If the top score is fragile, say so and pick the steadier candidate.

## Run folder

```text
data/optimize/run1/
  config.json      the goal, constraints, budget and parameter space
  results.jsonl    one line per trial: values, metrics, objective, eligible, error
  trials/0001.set  the exact MT4 preset used for that trial
  decision.json    the chosen trial, its record and the reason
  winner.set       the chosen preset
  best.set         the highest-scoring preset, when different
```

## Safety

No live trading, no network, no account details. The evaluator runs the MT4
Strategy Tester only. Never type a login or a password.
