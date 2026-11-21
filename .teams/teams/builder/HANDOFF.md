# Builder handoff — after inc-2 part B send-back 5

Updated: 2026-11-21 · Increment: inc-2 part B send-back 5 · Report: `work/report-inc-2b6.md`

## Goal

Write the FXT only up to broker midnight after `--to`, so MT4 keeps the file instead of rebuilding it.

## State and how to check it

The cutoff is committed locally (`0394ace`; report `3cac3fb`). No MT4 was started in this job.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
```

Expected: 95 tests pass; tools exit 0; export reports 1,320 FXT bars, 542,939 records and a 30,405,312-byte read-only file.

## Done (evidence in the report)

- FXT drops every tick whose server time is at or after 1772582400, which is field 476 = broker midnight after `--to`.
- 2026-03-03: 216 = 1320, 220 = 1772503200, 224 = 1772582340, 252 = 30, 472 = 1772496000, 476 = 1772582400.
- 542,939 records; last tick second 1772582399; zero records at or after the cutoff.
- 11,137 late ticks dropped; file 30,405,312 bytes; read-only.
- New test: one second before the cutoff is present, at the cutoff and after are absent.
- HST unchanged at 1,380 bars.
- The cutoff was re-checked byte-for-byte on four dates (2026-03-03, 03-09, 07-15, 11-10): header, every record and file size matched a hand-built expectation.
- `mt4 run` now takes `--visual / --no-visual` (default off) and writes `TestVisualEnable` from it; three tests cover the default, both flags and the generated start file.

## Ruled out / do not retry

- Changing the date fields 472/476 as the rebuild trigger: fixed, MT4 still rebuilt (Lead's run).
- Matching all six header numbers to MT4's values, and making our file newer than the minute bars: both still rebuilt (Lead's runs).
- Writing all 1,380 UTC-day bars: MT4 keeps only the 1,320 before broker midnight.

## Open

- Whether MT4 now keeps the file is the Lead's run.
- Part C is not briefed until MT4 keeps our ticks.
- `data/` (including the copy and measured file) is ignored; no `.fxt`/`.hst`/program is tracked.

## Next step

Lead runs the new export in the logged-in MT4. If MT4 keeps it, brief part C.
