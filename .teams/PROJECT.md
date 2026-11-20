# Project: loss-lens

Updated: 2026-11-20 · Phase: prototype · Source: intent (user, 2026-11-20, two messages)

## North star
The team's EA expert runs any MT4 expert advisor over a full year of real ticks, and in minutes the software shows every defect in how it traded, each with its proof, ranked by what it costs, one click from the exact moment on the MT4 chart. He stops finding these defects the slow way, on a live demo. Adding a new kind of defect takes him one sentence to Claude Code.

## Who it is for
- **End user: the team's EA expert.** He writes the EAs and today tests them on a live demo account. He is highly skilled in trading and EAs; he should never need to read this tool's code. He has Claude Code and will use it on the repository to add defects.
- **Sponsor: the user.** Ships the tool to the expert, directs the Lead, pastes briefs to the builder. Not the programmer.

## Done for this phase
- One command syncs XAUUSD 2026 ticks from Dukascopy (year to date, topped up through 31 Dec 2026) into a validated local store. Any other tick file can be imported.
- One action runs an EA in the MT4 Strategy Tester over the whole period and captures every trade and the tester journal.
- Every detector in `.teams/DEFECTS.md` (catalogue v1) runs automatically on the result. Every finding stores the numbers that triggered it.
- A new defect is added by creating one file plus its tests, following `docs/ADDING_A_DEFECT.md`. Proven by adding one through Claude Code with a one-sentence request.
- A fast local app lists defects, filters them any way the expert likes (saved views), ranks defect types by money, and replays the ticks of any trade with the proof drawn on it.
- Clicking a defect moves the MT4 chart to that moment and draws entry, exit, stop, target and the defect.
- The expert can install and run it on his own PC from a private GitHub repository with one setup step.
- Time-bound duties: until 2026-12-31: tick sync keeps topping up, owner builder (tooling), expert or user (running it).

## Hard constraints
- **Accuracy before features.** A wrong finding costs the expert's trust in all of them. No detector ships without tests; no run is analysed before it is reconciled with the ticks (ARCHITECTURE.md, "Accuracy rules").
- Windows. MT4 (32-bit). The EA runs only inside MT4; we never re-implement an EA's logic.
- EA-agnostic. Works with a compiled `.ex4` (trades and journal) and with source `.mq4` (adds an optional decision log).
- Tick data never goes into git.
- All times stored as UTC epoch milliseconds. Broker server time is applied only when writing MT4 files.
- The Lead does not build. One builder (a cheaper model in another tool) implements; the user pastes briefs to it.

## Non-goals
- Not a trading platform, not a strategy optimizer, not a live-trading monitor.
- It does not replace the demo entirely: real slippage, requotes and the broker's own price feed can only be seen live. It removes the weeks of demo time spent finding defects that ticks can already show. Comparing a demo's trade history against the backtest is planned for a later increment.
- No cloud service, no accounts, no data leaving the PC it runs on.
- No MT5 runner in this phase (kept possible by the runner seam).

## Existing setup and conventions to preserve
- Chats and roles: this Cursor chat is the Lead. The builder is a separate chat in another tool, driven by the user pasting kickoffs.
- Records: `.teams/` is the only record. The builder's earlier draft prompt is superseded (D-2).
- Rules: nothing leaves the machine without the user's approval (no GitHub push until the user says so).

## Assumptions
- The expert's EAs are MT4 EAs and he has MT4 on his own Windows PC. Confirm with: user.
- A purpose-built reference EA is used for development until the expert's EA is plugged in (D-6).
- MT4 server time is UTC+2 in winter and UTC+3 in summer (New York close). Confirm with: test on the installed terminal in inc-2.
- The builder can open and edit `C:\Users\yr471\Projects\loss-lens`. Confirm with: user.

## Open questions
- Which broker's MT4 will be installed here, and the exact name of its gold symbol, owner: user.
- Real limits of MT4's tester on this build (history file size, speed for ~130M ticks), owner: builder, measured in inc-2.
- Whether the team owns Tick Data Suite (would give real variable spread inside MT4), owner: user.
- Defects the expert already knows he wants that are missing from catalogue v1, owner: user (ask the expert).
