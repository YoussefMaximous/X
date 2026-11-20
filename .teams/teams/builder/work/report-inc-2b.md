# inc-2 part B report — our ticks through MT4's Strategy Tester

Builder · 2026-11-20/21 · code commit `d8f0265` · no stored tick data changed.

## Summary (12 lines or fewer)

- **Built:** the guarded MT4 copy, probe EA, start file, programs seam, HST export, FXT inspector, run command and tick comparison; 81 tests pass and `ruff`/`mypy` exit 0.
- **Measured:** the copy holds exactly four files after `mt4 setup`; the probe compiles with 0 errors; the HST for 2026-03-03 has 1,380 minute bars and the hand-built five-tick unit case is byte-exact.
- **Blocked:** the copy's `terminal.exe` opened a visible **“Open an Account”** window. The hard rules forbid typing or clicking; the run was left to time out. No tester result, report, probe file or run-time `.fxt` exists.
- **Guards:** all 45 earlier probes still fail; the 14 new tamper changes (a–n) also fail with file-and-rule messages; the repository passes.
- **Q1:** no test ran; the window appeared; run timed out at 180.060 s; no report or probe files.
- **Q5:** the measured compile command works: `metaeditor.exe /compile:<copy>\MQL4\Experts\LossLensProbe.mq4 /log` → 0 errors, 56 ms.
- **Q6:** HST layout is taken from `PeriodConverter.mq4`, not confirmed in MT4; FXT layout (728-byte header, 56-byte records) is not confirmed; `docs/MT4_FILES.md` marks every field **not confirmed**.
- **Q7–Q10:** not measured; there was no probe run.
- **Q11:** connection sampling for 75 s saw **0** addresses outside this PC; the copy's log had only LiveUpdate lines in the last run; an earlier run showed `MQL5.community: authorization failed`.
- **Q12:** the unexpected thing is the “Open an Account” window itself; it also appeared on a clean copy.
- **Not verified:** Q2, Q3, Q4, Q7, Q8, Q9, Q10 and the item 6/7 measurements; the item 5 rerun cannot give numbers without a working tester.
- **Question for the Lead/user:** the copy has no account by design; how should the “Open an Account” window be handled without breaking the hard rules?

## Q1–Q12

### Q1. Does a copy with no account and no `config` folder start, run a test from the start file, and close by itself? What appeared on screen?

**No — did not work.** Command:

```text
$ python -m losslens mt4 run --symbol XAUUSD --from 2026-03-03 --to 2026-03-03 --spread 30 --timeout 180
seconds: 180.060
ended by timeout: True
report files: []
probe info: None
probe ticks: None
```

While it ran, the copy's windows were listed (read-only):

```text
329856 True 'Open an Account'
852578 True 'MetaTrader 4'
```

Nothing was typed or clicked. The copy started, opened the account window, and the
run was ended by its timeout. It did not run a test or close by itself.

### Q2. Does the test run with all four `Experts...=false` lines?

**Not verified.** No tester run reached a test; the start file contains the four
lines and the checker accepts them, but MT4 never got past the account window.

### Q3. Which history folder does the copy use, and does it know `XAUUSD` from the two copied files?

**Not verified.** The copy has `history/default/symbols.raw` and
`symgroups.raw`; `setup` printed four files. No successful tester run confirmed
which folder it uses.

### Q4. What does the probe's info file say?

**Not verified.** `tester/files/losslens_probe_info.txt` was not created.

### Q5. The exact command line that compiles an EA.

**Measured.** The command is built by `programs.run_program` as:

```text
metaeditor.exe /compile:C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\MQL4\Experts\LossLensProbe.mq4 /log
```

Output from `python -m losslens mt4 compile`:

```text
C:\Users\yr471\Projects\loss-lens\data\mt4\terminal\MQL4\Experts\LossLensProbe.mq4 : information: compiling 'LossLensProbe.mq4'
Result: 0 errors, 0 warnings, 56 msec elapsed
exit=0
```

### Q6. The measured `.fxt` layout and the `.hst` layout MT4 accepted.

**Not confirmed.** No tester run completed. The HST layout in
`docs/MT4_FILES.md` comes from `PeriodConverter.mq4`; the expected FXT layout is
from the brief. Both are marked **not confirmed**. MT4 created
`tester/history/XAUUSD1_0.fxt` at size 0 during the one start that got past the
window, then stopped.

### Q7. Left alone, how many ticks does MT4 make up for that day, against 554,076 real ones? What modelling quality does it report?

**Not verified.** No test ran; the FXT is 0 bytes and no report was written.

### Q8. With our read-only `.fxt`: did the EA get our ticks?

**Not verified.** The FXT writer is not enabled because the layout was not
measured; no probe file exists. `mt4 export` refuses to write an invented header
and asks for `--no-fxt`.

### Q9. Is `Ask - Bid` the same fixed amount on every tick?

**Not verified.** No probe records exist.

### Q10. Sizes and times for a day, a week, a month and three months, and where it stopped working.

**Not verified.** No tester run completed; only the one-day HST export was
measured (1,380 bars, 0.42 s).

### Q11. Did the copy connect to anything outside this PC? What did MT4 create in its own folder?

**Checked by sampling, not proof.** A 75-second sampler over the copy's
`terminal.exe` saw 0 connections to addresses outside this PC. The copy's last
log had only LiveUpdate lines. An earlier run's log (before the clean copy) had:

```text
1  MQL Base: failed write to base
1  MQL5.community: authorization failed
```

The copy created `config`, `logs`, `history`, `MQL4`, `profiles`, `templates` and
`tester` folders. No account was entered.

### Q12. Anything you saw that this brief did not expect.

The **“Open an Account”** window appeared even with no `config` and no account.
That is the blocker. `terminal.exe` also spent about five minutes before the
first tester start, apparently on community authorisation, and then started the
tester; a later clean copy did not reach the tester either, but its windows were
not enumerated.

## Done when

### 1. Tests, linter, formatter, type checker

```text
$ python -m pytest -q
........................................................................ [ 88%]
.........                                                                [100%]
81 passed in 1.07s
pytest_exit=0

$ python -m ruff check .
All checks passed!
ruff_exit=0

$ python -m ruff format --check .
53 files already formatted
format_exit=0

$ python -m mypy
Success: no issues found in 17 source files
mypy_exit=0
```

### 2. Every earlier guard probe still fails

All 45 probes from part A's three briefs were rerun in a copy, each alone and
undone. All made `pytest` exit 1 with the expected rule:

- a–l (12): 2a, 2a, 2a, 2b, 2c, 2d, 2e, 2e, 2i, 2h, 2h, 2i.
- Network-block test: passes (the socket test).
- P1–P12 and P14 (13): 2b, 2b, 2b, 2a, 2a, 2c, 2c, 2h, 3a, 2i, 2d, 2e, 3c.
- E1–E6 (6): 2b, 2b, 2j, 2i, 2d, 2e.
- N1, N2, N3, N10, N11, N12, N13 (7): 2k, 2k, 2k, 2k, 2l, 2l, 2k.
- X1–X4 (4): 2l, 2l, 2k, 2k.
- `tests/tool.js`: 2k; `subprocess.check_output` in `dukascopy.py`: 2l.

The repository as it is passes 81 tests.

### 3. New tamper changes a–n

Each was made alone in a copy and undone; every one exited 1.

| # | Failure message |
|---|---|
| a | `src/losslens/mt4/startfile.py: rule 3d: builder and checker disagree` |
| b | `src/losslens/mt4/startfile.py: rule 3d: TESTER_FIXED_LINES changed` |
| c | `src/losslens/mt4/startfile.py: rule 3d: TESTER_FIXED_LINES changed` |
| d | `src/losslens/mt4/startfile.py: rule 3d: TESTER_KEYS changed` |
| e | `mql4/Experts/LossLensProbe.mq4: rule 3f: missing the IsTesting() refusal line` |
| f | `mql4/Experts/LossLensProbe.mq4:11: rule 2m: MQL account name 'AccountNumber' found` |
| g | `mql4/Experts/LossLensProbe.mq4:79: rule 3a: order function 'OrderSend(' found` |
| h | `mql4/Experts/Other.mq4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| i | `mql4/Experts/LossLensProbe.ex4: rule 2i: EA files do not belong in this folder. Keep them in MT4's own folder; loss-lens never needs a copy.` |
| j | `src/losslens/mt4/copy.py: rule 3g: MT4_COPY_FILES changed` |
| k | `src/losslens/mt4/programs.py: rule 2l: found 2 subprocess.run accesses, allowed 1` |
| l | `src/losslens/mt4/check.py:101: rule 2a: import 'subprocess' is not approved` |
| m | `src/losslens/mt4/programs.py: rule 3e: unsafe program start was not refused` |
| n | `src/losslens/mt4/programs.py: rule 3e: unsafe program start was not refused` |

### 4. Setup into an empty data folder

```text
$ $env:LOSSLENS_DATA="C:\Users\yr471\AppData\Local\Temp\opencode\mt4-copy-check"
$ python -m losslens mt4 setup --from "<user MT4 folder>" --server ICMarketsSC-Demo04
terminal.exe  45725928 bytes
metaeditor.exe  16658336 bytes
history/default/symbols.raw  453024 bytes
history/default/symgroups.raw  2560 bytes
copy: ...\mt4\terminal
```

The target contained exactly those four files; no `config`, `profiles`, `MQL4`
or `logs` file was copied.

### 5. Compile, and the item 6/7 numbers

`mt4 compile` gives 0 errors (Q5 above). The item 6/7 commands do not give the
same numbers because the tester never ran: `mt4 run` timed out at the “Open an
Account” window, and `mt4 export --no-fxt` is the only export mode that works.
This is a **did not work**, not a number to compare.

### 6. `docs/MT4_FILES.md`

```text
$ Test-Path docs/MT4_FILES.md
True
```

The file has both layouts field by field with byte positions; every status is
marked **not confirmed**. No field is claimed as measured on build 1492.

### 7. The report

This file answers Q1–Q12 with commands and output, or marks them not verified.

### 8. Git and forbidden files

`git status --short` is clean after the commits. No `.ex4`, `.ex5`, `.fxt`,
`.hst`, `terminal.exe` or `metaeditor.exe` is tracked or untracked outside the
ignored `data/` folder, and no file from the user's MT4 folder is in the
repository.

## Did not work

- The MT4 tester run: the copy's “Open an Account” window blocked it. Hard rules
  forbid interacting with it.
- FXT layout measurement, FXT writer, item 6 and item 7 measurements, and the
  day/week/month/three-month runs.
- Probe info/ticks, report and `check-ticks`: no probe run exists.
- The offline measurement could not confirm the item 6/7 numbers; only the
  75-second connection sampling was checked.

## Files changed

- `src/losslens/mt4/` — setup copy, start file, programs seam, compile, HST export,
  FXT inspector, run and tick comparison.
- `mql4/Experts/LossLensProbe.mq4`, `docs/MT4_FILES.md`.
- `src/losslens/cli.py`, `tests/_guard_scan.py`, `tests/test_no_network.py`,
  `tests/test_no_live_trading.py`, `tests/test_mt4_export.py`.
