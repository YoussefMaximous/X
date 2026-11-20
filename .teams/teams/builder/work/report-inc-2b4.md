# inc-2 part B send-back 3 report

Builder · 2026-11-21 · code commit `a6e54f1` · no MT4 started; no `accounts.ini` opened; no login typed.

## Summary (10 lines or fewer)

- **Done:** `mt4 export` now writes the measured 728-byte FXT header plus one 56-byte record per stored tick, from the tick store.
- **Header:** the 728-byte template is exactly the header MT4 build 1492 wrote; only bytes 216, 220, 224, 252, 472 and 476 change.
- **Records:** 554,076 records for 2026-03-03, each holding the minute state and that tick's server second; the file ends read-only.
- **File size:** 31,028,984 bytes = 728 + 554,076 × 56.
- **Tests:** 88 pass; ruff, ruff format and mypy exit 0; the five-tick test compares the changed header bytes and all five records with bytes written by hand.
- **Not verified:** whether MT4 accepts this file; that is the Lead's run. No MT4 was started here.
- Q6/Q7 are not re-measured; this send-back only writes the file.

## Done-when checks

### 1. Four tools

```text
$ python -m pytest -q
........................................................................ [ 81%]
................                                                         [100%]
88 passed in 1.24s
exit=0

$ python -m ruff check .
All checks passed!
exit=0

$ python -m ruff format --check .
58 files already formatted
exit=0

$ python -m mypy
Success: no issues found in 17 source files
exit=0
```

The `pytest-current` atexit `PermissionError` is pytest's ignored temp cleanup; exit stays 0.

### 2. The measured header is the template

```text
$ python -c "from pathlib import Path; from losslens.mt4.export import FXT_HEADER_TEMPLATE; m=Path(r'data/mt4/measured/XAUUSD1_0.fxt').read_bytes()[:728]; print('template equals measured:', FXT_HEADER_TEMPLATE == m); print('template bytes:', len(FXT_HEADER_TEMPLATE))"
template equals measured: True
template bytes: 728
```

The only bytes changed are the six fields in the brief:

| Offset | Field | Source |
|---:|---|---|
| 216 | number of minute bars | 1,380 for 2026-03-03 |
| 220 | first bar server time | 2026-03-03 02:00 server |
| 224 | last bar server time | 2026-03-03 23:59 server |
| 252 | spread | 30 |
| 472 | first tick server second | first stored tick |
| 476 | last tick server second + 1 | last stored tick |

### 3. Export of 2026-03-03

```text
$ python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03
hst: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\history\default\XAUUSD1.hst
bars: 1380
fxt: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\tester\history\XAUUSD1_0.fxt
fxt records: 554076
export seconds: 2.302
exit=0

$ Get-Item data\mt4\terminal\tester\history\XAUUSD1_0.fxt | Select-Object Length,IsReadOnly
Length     : 31028984
IsReadOnly : True
```

31,028,984 = 728 + 554,076 × 56. `--no-fxt` still writes only the HST.

### 4. Five-tick unit case

`test_fxt_bytes_for_five_ticks_across_two_minutes` builds five ticks across two
minutes with a template of `0xAA` bytes, checks every unpatched header byte stays
`0xAA`, checks the six patched integers, and compares the five 56-byte records
with hand-built `struct.pack` bytes. It passes in the 88-test run.

## Not verified

- MT4 opening and running this `.fxt`: the Lead will run it; the builder did not
  start MT4.
- Q6/Q7 numbers from this file: not measured here.

## Files changed

- `src/losslens/mt4/export.py` — measured FXT header template, record writer,
  read-only output, correct record count.
- `src/losslens/cli.py` — print the FXT path and record count.
- `tests/test_mt4_export.py` — five-tick FXT byte test.
