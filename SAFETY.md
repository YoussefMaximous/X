# What this software does, and what it never does

loss-lens tests MT4 expert advisors (EAs) against stored price history, on your own PC. This page lists everything it touches. Each line can be checked against the code.

## It never trades
- It contains no code that can place, change or close an order on any account, demo or real.
- It never asks for, reads or stores an account number or a password.

## It never sends anything out
- No telemetry, no analytics, no crash reports, no update checks, no accounts, no cloud.
- It goes online for one thing only: downloading public price history from Dukascopy, and only when you run the download yourself. The request names a symbol and a date. It carries nothing about you, your EAs or your results.
- Nothing is downloaded when the software starts, in the background, or on a timer.

## It leaves your EAs alone
- It does not upload, send or copy an EA anywhere.
- EA files (`.ex4`, `.mq4`, `.mqh`) do not belong in this folder and are never added to this repository. Keep them in MT4's own folder.

## What it writes
- Only its own `data` folder (or the folder named in `LOSSLENS_DATA`), and a temporary folder that is deleted after each download.

## How this is enforced
- `tests/test_no_network.py` fails if network code, a web address, an unapproved dependency or an EA file appears.
- `tests/test_no_live_trading.py` fails if an order function, a trading library or a stored password appears.
- Both run with the normal tests on every change. The tests themselves run with the network blocked.

## Limits, said plainly
- The download is done by `dukascopy-node` 1.51.1, an open-source tool by another author, pinned to that exact version and checked by checksum. It starts Chrome or Edge in the background to fetch the price files.
- Setting up the software downloads its building blocks once from PyPI and npm.
- If you open this folder with an AI assistant, that assistant sends the files it reads to its own provider. That is the assistant, not this software. Keep your EAs out of this folder.
- This covers the official repository. A copy changed by someone else is that person's software.
