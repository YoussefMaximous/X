# Builder handoff — after inc-2 part B send-back 3

Updated: 2026-11-21 · Increment: inc-2 part B send-back 3 · Report: `work/report-inc-2b4.md`

## Goal

Write our stored ticks into the measured MT4 FXT layout, using the header MT4 itself wrote.

## State and how to check it

The FXT writer is committed locally (`a6e54f1`; report commit next). No MT4 was started in this job.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
```

Expected: 88 tests pass; tools exit 0; export reports 1,380 bars, 554,076 FXT records and a 31,028,984-byte read-only file.

## Done (evidence in the report)

- FXT header template is exactly the measured 728-byte header; only the six specified integers are changed.
- One 56-byte record per stored tick: minute bar time, OHLC state so far, volume so far, tick server second, zero flag.
- 2026-03-03 export: 554,076 records; 31,028,984 bytes; file read-only.
- Five-tick test checks all six header fields and all five records against hand-built bytes.
- `--no-fxt` still writes only the HST.
- No MT4 started, no `accounts.ini` opened, no login typed.

## Ruled out / do not retry

- Inventing a header: the measured header is embedded byte-for-byte.
- Writing records for minutes rather than ticks: the count is 554,076, not 1,380.
- Starting MT4 to test the file: the Lead runs that.

## Open

- Whether MT4 accepts and uses this FXT is the Lead's run; Q6/Q7 are not re-measured here.
- The copy still has no account; the user/Lead decides if it gets one.
- `data/` (including the copy and measured file) is ignored; no `.fxt`/`.hst`/program is tracked.

## Next step

Lead runs the FXT through MT4 and answers Q6/Q7 from that run.
