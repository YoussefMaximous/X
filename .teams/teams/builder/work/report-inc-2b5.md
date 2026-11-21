# inc-2 part B send-back 4 report

Builder · 2026-11-21 · code commit `6b8bdc5` · no MT4 started; no `accounts.ini` opened; no login typed.

## Summary (10 lines or fewer)

- **Done:** FXT header bytes 472 and 476 now hold 00:00 UTC on `--from` and on the day after `--to`.
- **Measured export:** 2026-03-03 gives 554,076 records, 31,028,984 bytes, and header values 472=1772496000, 476=1772582400.
- **Unchanged:** bar count 1,380, bar times 1772503200/1772589540, spread 30.
- **Test:** the five-tick FXT test now checks 472=1772496000 and 476=1772582400, and every unpatched header byte.
- **Tools:** 88 tests pass; ruff, ruff format and mypy exit 0.
- **Repo state:** the other agent's one edit was already reverted; the job started from a clean tree at `ef4597b`.
- **Not verified:** whether MT4 accepts the corrected file; the Lead runs it.

## Done-when checks

### 1. Four tools

```text
$ python -m pytest -q
........................................................................ [ 81%]
................                                                         [100%]
88 passed in 1.09s
exit=0

$ python -m ruff check .
All checks passed!
exit=0

$ python -m ruff format --check .
59 files already formatted
exit=0

$ python -m mypy
Success: no issues found in 17 source files
exit=0
```

The `pytest-current` atexit `PermissionError` is pytest's ignored temp cleanup; exit stays 0.

### 2. Export of 2026-03-03

```text
$ python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
hst: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\history\default\XAUUSD1.hst
bars: 1380
fxt: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\tester\history\XAUUSD1_0.fxt
fxt records: 554076
export seconds: 2.151
exit=0
```

Header values:

```text
$ python -c "from pathlib import Path; import struct; p=Path(r'data/mt4/terminal/tester/history/XAUUSD1_0.fxt'); b=p.read_bytes(); print('size', len(b)); print('ints', [(o, struct.unpack_from('<i', b, o)[0]) for o in (216,220,224,252,472,476)]); print('records', (len(b)-728)//56)"
size 31028984
ints [(216, 1380), (220, 1772503200), (224, 1772589540), (252, 30), (472, 1772496000), (476, 1772582400)]
records 554076
```

- 472 = 1772496000 = 2026-03-03 00:00 UTC.
- 476 = 1772582400 = 2026-03-04 00:00 UTC (day after `--to`).
- Size = 728 + 554,076 × 56 = 31,028,984 bytes; file is read-only.

### 3. Five-tick test

`test_fxt_bytes_for_five_ticks_across_two_minutes` builds two minutes with a
template of `0xAA` bytes and checks:

- 472 = 1772496000 and 476 = 1772582400;
- 216 = 2, 220/224 = the two bar times, 252 = 30;
- every byte outside the six patched fields is unchanged;
- all five 56-byte records equal bytes written by hand.

It passes in the 88-test run.

## Not verified

- MT4 opening this corrected `.fxt`: the Lead runs it.
- Q6/Q7 numbers from this file: not measured here.

## Files changed

- `src/losslens/mt4/export.py` — UTC date bounds in header fields 472/476.
- `tests/test_mt4_export.py` — date-field assertions.
- `docs/MT4_FILES.md` — corrected field description.
