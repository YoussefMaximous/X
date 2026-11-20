# Project: loss-lens

Updated: 2026-11-20 · Phase: prototype · Source: intent (user, 2026-11-20)

## North star
An EA team runs any MT4 expert advisor over a full year of real ticks, and the software finds every loss by itself, names its type, ranks what it costs, and takes the user to that exact moment on the MT4 chart in one click.

## Who it is for
A member of an EA-making team (the user). The team backtests on Dukascopy ticks and has a small in-house tool today; this replaces it at a higher level. The user is not the programmer: the app must be usable without reading code.

## Done for this phase
- One command syncs XAUUSD 2026 ticks from Dukascopy (year to date, topped up through 31 Dec 2026) into a validated local store. Any other tick file can be imported.
- One action runs an EA in the MT4 Strategy Tester over the whole period and captures every trade (winners and losers).
- Every loss is tagged automatically with one or more loss types; winners are re-checked against real bid/ask for hidden losses.
- A fast local app lists losses, filters them any way the user likes (saved views), ranks loss types by money, and replays the ticks of any trade.
- Clicking a loss moves the MT4 chart to that moment and draws entry, exit, stop, target and loss type.
- Time-bound duties: until 2026-12-31: tick sync keeps topping up, owner builder (tooling), user (running it).

## Hard constraints
- Windows. MT4 (32-bit), installed on this PC by the user. The EA runs only inside MT4; we never re-implement an EA's logic.
- EA-agnostic. Works with a compiled `.ex4` (trades only) and with source `.mq4` (optional decision log).
- Tick data never goes into git.
- All times stored as UTC epoch milliseconds. Broker server time is applied only when writing MT4 files.
- The Lead does not build. One builder (a cheaper model in another tool) implements; the user pastes briefs to it.

## Non-goals
- Not a trading platform, not a strategy optimizer, not a live-trading monitor (for now).
- No cloud service, no accounts, no data leaving this PC.
- No MT5 runner in this phase (kept possible by the runner seam in ARCHITECTURE.md).

## Existing setup and conventions to preserve
- Chats and roles: this Cursor chat is the Lead. The builder is a separate chat in another tool, driven by the user pasting kickoffs.
- Records: `.teams/` is the only record. The builder's earlier draft prompt (CLI first, 12-question interview) is superseded by this file; the user said to ignore it.
- Rules: nothing leaves the machine without the user's approval (no GitHub push yet).

## Assumptions
- The team's real EA is an MT4 EA; a purpose-built reference EA is used until they plug theirs in. Confirm with: user.
- MT4 server time is UTC+2 in winter and UTC+3 in summer (New York close). Confirm with: test on the installed terminal in inc-2.
- The builder can open and edit `C:\Users\yr471\Projects\loss-lens`. Confirm with: user.

## Open questions
- Which broker's MT4 will be installed, and the exact name of its gold symbol (XAUUSD, GOLD, XAUUSD.m ...), owner: user.
- Real limits of MT4's tester on this build (history file size, speed for ~130M ticks), owner: builder, measured in inc-2.
- Whether the team owns Tick Data Suite (would give real variable spread inside MT4), owner: user.
