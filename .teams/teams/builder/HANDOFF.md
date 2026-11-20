# Builder handoff — after inc-2 part B send-back 1

Updated: 2026-11-21 · Increment: inc-2 part B send-back 1 · Report: `work/report-inc-2b2.md`

## Goal

Fix the four part B send-back items, then make the one allowed retry of the 2026-03-03 tester run.

## State and how to check it

The four code fixes are committed locally (`5a97324` code; report in the next commit). The retry compiled and exported, but the tester run still timed out with no report or `.fxt`.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Expected: 85 tests pass; all tools exit 0.

## Done (evidence in the report)

- **Start file:** `[Common]`, the ten fixed lines, `[Tester]`, the `Test*` lines; accepted by the checker, refused missing either heading, refused a fixed line under `[Tester]`, refused any other bracket section.
- **Run:** `terminal.exe /portable /config:<absolute>\losslens_start.ini`; the guard still accepts the bare path form but `mt4 run` uses `/config:`.
- **Comparison:** `identical` requires every compared tick to agree in time and bid; skipped start/end ticks are reported but do not make it different; extra probe ticks make it different.
- **Inspector:** prints every 4-byte slot to the end of the header (728-byte test header printed offset 724).
- **Retry:** compile 0 errors, export 1,380 bars in 0.460 s, run timed out at 180.061 s with no report, probe or `.fxt`.
- No account window was touched; no week/month run was started.

## Ruled out / do not retry

- Clicking or typing in "Open an Account": forbidden; the retry was left to timeout.
- `--replace` on the existing copy: forbidden in the send-back.
- Inventing the FXT layout without a measured file: not done.
- Starting week/month/three-month runs: not done.

## Open

- Q6/Q7 still have no measured answer: no FXT or report exists.
- The copy still does not reach the tester through `/config:`; the Lead/user must decide the next step for the account window.
- `data/` (including the copy) is ignored; no program, `.ex4`, `.fxt` or `.hst` is tracked.

## Next step

Lead reviews the four fixes and the retry output; a working tester path is still needed for Q6/Q7.
