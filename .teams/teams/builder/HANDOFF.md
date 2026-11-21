# Builder handoff — after inc-2 part B send-back 5 and the MT4 report tools

Updated: 2026-11-21 · Report: `work/report-inc-2b6.md` · Latest code: `c3c60e5`

## Goal

Accurate runs: MT4 executes the EA on our real ticks, and the software proves from MT4's own report that it used them.

## State and how to check it

Local commits: `0394ace` (broker-midnight cutoff), `3cac3fb` (send-back 5 report), `9c44513` (visual toggle), `4f90fc4` (report parser + check-report), `6428f07` (run parses its report), `270b55e` (journal parser), `c3c60e5` (reconcile report trades).

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens mt4 check-report --report tests\fixtures\mt4_report_probe.htm --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
python -m losslens mt4 parse-journal tests\fixtures\mt4_tester.log --tail 3
python -m losslens mt4 reconcile --report <report.htm> --symbol XAUUSD
```

Expected: 116 tests pass; tools exit 0; the probe report check says `report ticks: 471448`, `store ticks: 542939`, `RESULT: different`; the journal prints 8 lines; reconcile prints `RESULT: reconciled` for a report whose trades exist in the store.

## Done

- FXT stops at broker midnight after `--to`; verified byte-for-byte on 2026-03-03, 03-09, 07-15 and 11-10.
- `mt4 run --visual/--no-visual` controls MT4's tester chart, default off (fast).
- `mt4 parse-report` reads the summary and closed trades from MT4's report.
- `mt4 check-report` compares the report's tick and bar counts to the FXT we export.
- `mt4 run` parses its own report and prints that comparison.
- `mt4 parse-journal` reads the tab-separated tester journal.
- `mt4 reconcile` checks each reported close against the store's bid (buy) or ask (sell), using the +2/+3 server-time rule.
- The old probe report is correctly `different`: 471,448 MT4-generated ticks vs our 542,939.

## Ruled out / do not retry

- Date fields 472/476 as the rebuild trigger.
- Matching all six header numbers and making our file newer than the bars.
- Writing the 1,380 UTC-day bars; MT4 keeps the 1,320 before broker midnight.

## Open

- Whether MT4 now keeps the file: the Lead's run.
- The copy has no account, so its tester still stops at "Open an Account". Automated runs need either a one-time login in the copy or a Lead decision to drive the logged-in terminal directly.
- The report's trade table has close time and price only; entries need the journal or the reference EA's decision log.
- Part C is not briefed until MT4 keeps our ticks.
- The app (server/UI) needs the Lead to extend the safety guard's approved import lists first; the builder must not edit them.
- The parallel playground files stay untracked and untouched.
- `data/` is ignored.

## Next step

Lead runs the new FXT in the logged-in terminal, then runs `mt4 check-report` on the produced report. If it says `identical`, brief part C.
