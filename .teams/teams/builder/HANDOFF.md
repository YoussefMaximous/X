# Builder handoff — after inc-2 part B send-back 2

Updated: 2026-11-21 · Increment: inc-2 part B send-back 2 · Report: `work/report-inc-2b3.md`

## Goal

Fix the two remaining part B items and make the one retry of the 2026-03-03 tester run on the copy.

## State and how to check it

The code fixes are committed locally (`94c7e9c`; report in the next commit). The retry still produced no tester file.

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Expected: 87 tests pass; all tools exit 0.

## Done (evidence in the report)

- **Bare ini path:** `mt4 run` passes `/portable` and the absolute `losslens_start.ini`; test asserts exactly two arguments and no `/config:`.
- **Empty probe:** `check_probe_ticks` returns `different` for no records; unit test added.
- **Retry:** compile 0 errors (67 ms), export 1,380 bars (0.436 s), run timed out at 180.055 s with no report, probe or `.fxt`.
- **No account action:** no click, key, login, password or `accounts.ini`; no user MT4; no week/month run.
- The copy still cannot reach the tester; Q6/Q7 remain unmeasured.

## Ruled out / do not retry

- Clicking or typing in the account/login window: forbidden.
- Opening `accounts.ini` or writing a password: forbidden.
- Using the user's own MT4: forbidden; only the copy is started through `losslens`.
- `--replace`: not used in this send-back.
- Week/month runs: not started.

## Open

- Q6/Q7 still have no measured answer from the copy; the Lead's logged-in run was a separate measurement outside this copy.
- The user must decide whether to log the copy in once; the software will not do it.
- `data/` (including the copy) is ignored; no `.ex4`, `.fxt`, `.hst` or MT4 program is tracked.

## When you finish

The last thing you do, after the report file is written, is run this from the loss-lens folder. It is how the Lead hears you. The id stays as written. The sentence in quotes is the one the brief names.

```text
agent --resume d074dc17-1115-46e0-b57c-867454a73cdc -p --trust --workspace C:\Users\yr471\Projects\loss-lens "Report inc-2b4 is ready"
```

## Next step

Send-back 2's code is accepted. Do "Send-back 3 of part B" in `.teams/increments/inc-2.md`: write our ticks into the `.fxt` using the measured header. Do not start either MT4. End by running the command above.
