# inc-2 part B send-back 2 report

Builder · 2026-11-21 · code commit `94c7e9c` · account window untouched; no login typed; no `accounts.ini` opened.

## Summary (10 lines or fewer)

- **Done:** both code items are fixed; 87 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **1 Bare ini path:** `mt4 run` passes exactly `/portable` and the absolute `losslens_start.ini`; the test asserts two arguments and no `/config:`.
- **2 Empty probe:** an empty probe file now prints `RESULT: different`; a compared difference, extra probe ticks or extra store ticks are covered by unit tests.
- **3 Retry:** compile 0 errors (67 ms), HST 1,380 bars (0.436 s), run timed out at 180.055 s with no report, probe or `.fxt`.
- **No new numbers:** Q6/Q7 remain unmeasured because the copy still produced no tester file.
- **No account touched:** no click, no key, no login, no password, no `accounts.ini`; no week/month run.
- **Not verified:** Q6/Q7 and the FXT layout.

## Done-when checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
........................................................................ [ 82%]
...............                                                          [100%]
87 passed in 1.14s
exit=0

$ python -m ruff check .
All checks passed!
exit=0

$ python -m ruff format --check .
57 files already formatted
exit=0

$ python -m mypy
Success: no issues found in 17 source files
exit=0
```

The `pytest-current` atexit `PermissionError` is pytest's ignored temp cleanup; exit stays 0.

### 2. The run arguments

`src/losslens/mt4/run.py` now calls:

```text
terminal.exe /portable <absolute path of losslens_start.ini>
```

The test `test_run_starts_portable_with_the_absolute_ini_path` records the call
and asserts the argument list is exactly:

```text
["/portable", "C:\\...\\data\\mt4\\terminal\\losslens_start.ini"]
```

and that `/config:` is not present. It is part of the 87 passing tests.

### 3. Empty probe file

`check_probe_ticks` now requires at least one probe record for `identical`.
`test_empty_probe_is_not_identical` asserts an empty file is not identical; the
CLI's `RESULT:` line is driven by that flag. The other comparison tests cover a
bid difference, extra probe ticks and skipped start/end ticks.

### 4. The one retry

```text
$ python -m losslens mt4 compile
... LossLensProbe.mq4 : information: compiling 'LossLensProbe.mq4'
Result: 0 errors, 0 warnings, 67 msec elapsed
exit=0

$ python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --no-fxt
hst: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\history\default\XAUUSD1.hst
bars: 1380
export seconds: 0.436
exit=0

$ python -m losslens mt4 run --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --spread 30 --timeout 180
seconds: 180.055
ended by timeout: True
report files: []
probe info: None
probe ticks: None
exit=0
```

No tester report, probe file or non-empty `.fxt` appeared, so there was nothing
to inspect for Q6/Q7. The copy's "Open an Account"/login window was not clicked
or typed in; the timeout ended the run.

### 5. Account and scope

- No login or password was typed anywhere.
- `accounts.ini` was not opened.
- The user's own MT4 was not started.
- No week, month or three-month run was attempted.

## Not verified

- Q6/Q7 and the FXT layout: no tester file exists from the retry.
- The copy still cannot run a test without an account; that remains a user/Lead
  decision.

## Files changed

- `src/losslens/mt4/run.py` — bare absolute ini path.
- `src/losslens/mt4/check.py` — empty probe is not identical.
- `tests/test_mt4_run.py` — run-argument test.
- `tests/test_mt4_check.py` — empty-probe test.
