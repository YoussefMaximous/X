# inc-2 part B send-back 1 report

Builder · 2026-11-21 · code commit `5a97324` · no new file from the user's MT4; no account window touched.

## Summary (10 lines or fewer)

- **Done:** all four send-back items are fixed; 85 tests pass; `ruff check`, `ruff format --check` and `mypy` exit 0.
- **1 Headings:** `[Common]` then the ten fixed lines, `[Tester]` then the `Test*` lines. The checker accepts that file and refuses it with either heading missing or a fixed line under `[Tester]`.
- **2 Config switch:** `mt4 run` now starts `terminal.exe /portable /config:<absolute>\losslens_start.ini`; the bare form remains accepted by the guard but is not used.
- **3 Comparison:** `identical` now means every compared tick agrees in time and bid; skipped start/end ticks are printed and do not by themselves make it `different`; extra probe ticks do.
- **4 Inspector:** prints every 4-byte header slot to the end of the header; a 728-byte test header prints offsets 0 through 724.
- **Retry:** compile 0 errors, HST 1,380 bars in 0.460 s, then a 180 s run timed out with no tester report and no `.fxt`.
- **Not verified:** Q6/Q7; no FXT or report exists to inspect. No week or month run was tried.
- **Question:** none new; the copy still does not reach the tester.

## Done-when checks

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
........................................................................ [ 84%]
.............                                                            [100%]
85 passed in 1.20s
$ echo $LASTEXITCODE
0
```

`ruff check`, `ruff format --check` and `mypy` also exit 0 (checked in the same run).

### 2. Start file headings accepted and refused

```text
$ python -c "from datetime import date; from losslens.mt4.startfile import build_start_file, check_start_file; text=build_start_file('XAUUSD', date(2026,3,3), date(2026,3,4), 30); print('accepted:', check_start_file(text) == []); print('missing Common:', bool(check_start_file(text.replace('[Common]\n','')))); print('missing Tester:', bool(check_start_file(text.replace('[Tester]\n',''))))"
accepted: True
missing Common: True
missing Tester: True
```

The built file is:

```text
[Common]
ExpertsEnable=false
ExpertsTrades=false
ExpertsDllImport=false
ExpertsExpImport=false
EnableNews=false
EnableDDE=false
AutoConfiguration=false
ProxyEnable=true
ProxyServer=127.0.0.1:9
ProxyType=HTTP
[Tester]
TestExpert=LossLensProbe
TestSymbol=XAUUSD
TestPeriod=M1
TestModel=0
TestSpread=30
TestOptimization=false
TestDateEnable=true
TestFromDate=2026.03.03
TestToDate=2026.03.04
TestReport=tester\losslens_report
TestReplaceReport=true
TestShutdownTerminal=true
TestVisualEnable=false
```

A fixed line under `[Tester]` and an unknown `[Other]` section are refused by the test `test_start_file_constants_and_checker`.

### 3. The one retry

On the existing copy, in order:

```text
$ python -m losslens mt4 compile
... LossLensProbe.mq4 : information: compiling 'LossLensProbe.mq4'
Result: 0 errors, 0 warnings, 62 msec elapsed
compile_exit=0

$ python -m losslens mt4 export --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --no-fxt
hst: C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\history\default\XAUUSD1.hst
bars: 1380
export seconds: 0.460
export_exit=0

$ python -m losslens mt4 run --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --spread 30 --timeout 180
seconds: 180.061
ended by timeout: True
report files: []
probe info: None
probe ticks: None
run_exit=0
```

No tester report and no `.fxt` appeared, so there was nothing to inspect for Q6/Q7. The account window was not typed in, clicked, or otherwise touched. No week or month run was started.

### 4. Inspector header range

```text
$ python -c "from pathlib import Path; import tempfile; from losslens.mt4.fxt import inspect_fxt; p=Path(tempfile.gettempdir())/'header-check.fxt'; p.write_bytes(b'\0'*728+b'\0'*56); out=inspect_fxt(p); print('header 724 printed:', '724:' in out)"
header 724 printed: True
```

The inspector now prints 183 header slots (offsets 0 to 724), not only the first 64 bytes.

## Did not work

- The retry did not produce a tester report or a non-empty `.fxt`; it timed out at 180.061 s. Q6 and Q7 remain unanswered.
- The copy still does not reach the tester through the start file; the earlier “Open an Account” window remains the known blocker. Nothing was clicked or typed.
- No week, month or three-month run was attempted, as instructed.

## Files changed

- `src/losslens/mt4/startfile.py` — headings and ordered sections.
- `src/losslens/mt4/run.py` — `/config:` absolute path.
- `src/losslens/mt4/check.py` — comparison result definition.
- `src/losslens/mt4/fxt.py` — full header dump.
- `tests/test_no_live_trading.py`, `tests/test_mt4_check.py` — heading and comparison tests.
