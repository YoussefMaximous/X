# MT4 history files

Measured/checked on MT4 build 1492 on this PC on 2026-11-20. The tester run itself
did not work in this session because the copy opened an "Open an Account" window
and the hard rules forbid interacting with it; the run timed out. Everything
below is therefore marked **not confirmed**.

## HST — `history/default/XAUUSD1.hst`

Status: not confirmed in MT4. The layout is taken from MetaQuotes'
`PeriodConverter.mq4` on this PC, but no successful tester run confirmed it.

Header, 148 bytes:

| Offset | Size | Type | Field | Status |
|---:|---:|---|---|---|
| 0 | 4 | int32 | version = 401 | not confirmed |
| 4 | 64 | char[64] | copyright, zero padded | not confirmed |
| 68 | 12 | char[12] | symbol, zero padded | not confirmed |
| 80 | 4 | int32 | period in minutes = 1 | not confirmed |
| 84 | 4 | int32 | digits = 2 | not confirmed |
| 88 | 4 | int32 | zero | not confirmed |
| 92 | 4 | int32 | zero | not confirmed |
| 96 | 52 | int32[13] | unused, all zero | not confirmed |

Record, 60 bytes:

| Offset | Size | Type | Field | Status |
|---:|---:|---|---|---|
| 0 | 8 | int64 | bar time, server time, seconds | not confirmed |
| 8 | 8 | double | open bid | not confirmed |
| 16 | 8 | double | high bid | not confirmed |
| 24 | 8 | double | low bid | not confirmed |
| 32 | 8 | double | close bid | not confirmed |
| 40 | 8 | int64 | tick volume | not confirmed |
| 48 | 4 | int32 | spread = 0 | not confirmed |
| 52 | 8 | int64 | real volume = 0 | not confirmed |

Our file has one record per minute that has ticks; open is the first rounded
bid, high/low the running extremes, close the last rounded bid, and tick volume
the number of stored ticks in that minute.

## FXT — tester history

Status: not confirmed. MT4 created `tester/history/XAUUSD1_0.fxt` with size 0
during the one tester start that got past the window; it did not build a test.
The expected layout from the brief is below and is not confirmed; the file MT4
itself writes in a working run decides, not this table.

Expected header: 728 bytes. Expected record: 56 bytes.

| Offset | Size | Type | Field | Status |
|---:|---:|---|---|---|
| 0 | 8 | int64 | bar time, server time, seconds | not confirmed |
| 8 | 8 | double | open | not confirmed |
| 16 | 8 | double | high | not confirmed |
| 24 | 8 | double | low | not confirmed |
| 32 | 8 | double | close | not confirmed |
| 40 | 8 | int64 | volume so far in the minute | not confirmed |
| 48 | 4 | int32 | current tick time, server time, seconds | not confirmed |
| 52 | 4 | int32 | flag | not confirmed |

Our `mt4 export` writes only the HST until the FXT layout has been measured in
a real run; it refuses to write an invented FXT header and says to use
`--no-fxt`.

## What blocked the measurement

The copy's `terminal.exe` started and opened a visible window titled
"Open an Account". The hard rules say type nothing and click nothing. The run
was left to time out. A later clean start stopped at the same window. Therefore
no tester result, probe file, report or run-time FXT exists to measure.
