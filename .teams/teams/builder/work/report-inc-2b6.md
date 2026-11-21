# inc-2 part B send-back 5 report

Builder · 2026-11-21 · code commit `0394ace` · no MT4 started; no `accounts.ini` opened; no login typed.

## Summary (10 lines or fewer)

- **Done:** `mt4 export` now writes no FXT tick at or after broker midnight following `--to`; the cutoff is header field 476.
- **Export 2026-03-03:** 1,320 bars, first 1772503200, last 1772582340; 472/476 unchanged; no record at or after 1772582400.
- **Records:** 542,939 (11,137 late ticks dropped), file 30,405,312 bytes = 728 + 542,939 × 56, read-only.
- **Last record:** tick second 1772582399, one second before the cutoff.
- **Tests:** 89 pass; the new test proves a tick at the cutoff and one after are absent while one second earlier is present.
- **Tools:** ruff, ruff format and mypy exit 0.
- **HST:** unchanged at 1,380 bars, as the brief asked.
- **Not verified:** whether MT4 now keeps the file; the Lead runs it.

## Done-when checks

### 1. Four tools

```text
$ python -m pytest -q
........................................................................ [ 80%]
.................                                                        [100%]
89 passed in 1.13s
exit=0

$ python -m ruff check .
All checks passed!
exit=0

$ python -m ruff format --check .
60 files already formatted
exit=0

$ python -m mypy
Success: no issues found in 17 source files
exit=0
```

The `pytest-current` atexit `PermissionError` is pytest's ignored temp cleanup; exit stays 0.

### 2. Fresh export of 2026-03-03

```text
$ python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
hst: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\history\default\XAUUSD1.hst
bars: 1380
fxt: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\tester\history\XAUUSD1_0.fxt
fxt records: 542939
export seconds: 1.993
exit=0
```

### 3. Header and cutoff

The check decoded every 56-byte record with `struct.iter_unpack`:

```text
$ python C:\Users\yr471\AppData\Local\Temp\opencode\check_inc2b6.py
size 30405312
ints [(216, 1320), (220, 1772503200), (224, 1772582340), (252, 30), (472, 1772496000), (476, 1772582400)]
records 542939
records with bar time at/after cutoff 0
records with tick second at/after cutoff 0
last records [(1772582340, 5087.75, 5088.89, 5086.25, 5087.87, 378, 1772582399, 0), (1772582340, 5087.75, 5088.89, 5086.25, 5087.93, 379, 1772582399, 0), (1772582340, 5087.75, 5088.89, 5084.87, 5084.87, 380, 1772582399, 0)]
```

- 216 = 1,320 bars, 220 = 1772503200, 224 = 1772582340.
- 472 = 1772496000 and 476 = 1772582400 are unchanged.
- The last tick second is 1772582399; the cutoff 1772582400 is broker midnight
  after 2026-03-03, written as a server-clock timestamp.
- File size = 728 + 542,939 × 56 = 30,405,312 bytes; `IsReadOnly` is `True`.
- 554,076 − 542,939 = 11,137 ticks at or after the cutoff were dropped.

### 4. New test

`test_fxt_records_stop_at_broker_midnight` builds four ticks: 21:59:58 and
21:59:59 UTC (server 1772582398 and 1772582399) and 22:00:00 and 22:00:01 UTC
(server 1772582400 and 1772582401). It asserts:

- the two ticks before the cutoff are the only two records;
- their bar time is 1772582340 and their tick seconds are 1772582398/1772582399;
- 216 = 1, 220 = 224 = 1772582340, 472 = 1772496000, 476 = 1772582400;
- no record has a bar time or tick second at or after the cutoff.

The five-tick test still passes unchanged.

## Not verified

- MT4 opening this file and keeping it instead of rebuilding: the Lead runs it.
- Q6/Q7 numbers from this file: not measured here.

## Files changed

- `src/losslens/mt4/export.py` — cutoff filtering and cutoff passed from the date range.
- `tests/test_mt4_export.py` — broker-midnight test.
- `docs/MT4_FILES.md` — cutoff note.
