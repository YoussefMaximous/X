# Builder handoff — after inc-2 part B send-back 4

Updated: 2026-11-21 · Increment: inc-2 part B send-back 4 · Report: `work/report-inc-2b5.md`

## Goal

Write the two FXT date fields correctly: 00:00 UTC on `--from` and on the day after `--to`.

## State and how to check it

The fix is committed locally (`6b8bdc5`; report commit next). The other agent's earlier edit was already reverted before this job; the tree was clean at `ef4597b`.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
```

Expected: 88 tests pass; tools exit 0; export reports 554,076 records and a 31,028,984-byte file.

## Done (evidence in the report)

- Header 472 = 1772496000 (2026-03-03 00:00 UTC).
- Header 476 = 1772582400 (2026-03-04 00:00 UTC, day after `--to`).
- Bar count 1,380, bar times 1772503200/1772589540, spread 30 unchanged.
- File size 31,028,984 = 728 + 554,076 × 56; read-only.
- Five-tick test checks the two date fields and every unpatched header byte.
- No MT4 started, no `accounts.ini` opened, no login typed.

## Ruled out / do not retry

- Using server time or the first/last tick for 472/476: both were wrong; MT4 restored UTC date bounds.
- Changing bar count or bar times in this send-back: not done.
- Starting MT4 to test: the Lead runs it.

## Open

- Whether MT4 accepts the corrected file is the Lead's run.
- `data/` (including the copy and measured file) is ignored; no `.fxt`/`.hst`/program is tracked.

## Next step

Do "Send-back 5 of part B" in `.teams/increments/inc-2.md`. Stop the tick file at broker midnight. Do not start either MT4. Tell the user "Report inc-2b6 is ready".
