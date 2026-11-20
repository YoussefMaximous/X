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
- Quick run: the expert picks any date range and the software opens that range in the MT4 Strategy Tester on our ticks for manual inspection, with no defect analysis (D-16). It can be analysed afterwards with one button.
- A Data tab lists every year Dukascopy offers as a package, says how far each is downloaded, and has a Download button per year and a Top up button for the current year (D-17).
- Orders are filled by loss-lens on real bid and ask, not by MT4's fixed spread: every run shows "MT4 says" beside "with real spreads" (layer 1, any EA), and EAs with source can run wholly on real spreads through one include line (layer 2), proven first to match MT4 at a fixed spread (D-19).
- Every detector in `.teams/DEFECTS.md` (catalogue v1) runs automatically on the result. Every finding stores the numbers that triggered it.
- A new defect is added by creating one file plus its tests, following `docs/ADDING_A_DEFECT.md`. Proven by adding one through Claude Code with a one-sentence request.
- A fast local app lists defects, filters them any way the expert likes (saved views), ranks defect types by money, and replays the ticks of any trade with the proof drawn on it.
- Clicking a defect moves the MT4 chart to that moment and draws entry, exit, stop, target and the defect.
- The expert can install and run it on his own PC from the GitHub repository with one setup step.
- Time-bound duties: until 2026-12-31: tick sync keeps topping up, owner builder (tooling), expert or user (running it).

## Hard constraints
- **Nothing leaves the PC.** The only online action is downloading public price ticks when the user asks. No telemetry, no uploads, no accounts. EAs are never copied out, uploaded or added to git (ARCHITECTURE.md, "Privacy", D-20). The project is open source.
- **No live trading, ever.** The software only analyses. It never places, changes or closes an order on any account, demo or real, now or in any later version. Enforced in layers (ARCHITECTURE.md, "Safety", D-14).
- **Professional grade, as defined in `.teams/QUALITY.md`.** Every increment is judged against that page as well as its brief (D-15).
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
- Rules: GitHub repository https://github.com/YoussefMaximous/loss-lens, private for now and to become open source (D-20); only the Lead pushes, after review (D-10). Nothing else leaves the machine without the user's approval.

## Assumptions
- The expert's EAs are MT4 EAs and he has MT4 on his own Windows PC. Confirm with: user.
- A purpose-built reference EA is used for development until the expert's EA is plugged in (D-6).
- MT4 server time is UTC+2 in winter and UTC+3 in summer (New York close). Confirm with: test on the installed terminal in inc-2.
- The builder can open and edit `C:\Users\yr471\Projects\loss-lens`. Confirm with: user.

## Open questions
- MT4 from IC Markets is installed here (build 1492, in `C:\Users\yr471\AppData\Roaming\MetaTrader 4 IC Markets Global`, measured 2026-11-20) but has not yet connected to a demo account (D-13). The exact gold symbol name (standard is XAUUSD; brokers may use GOLD or add a suffix) is read by the Lead from the installed terminal, not asked of the user.
- Real limits of MT4's tester on this build (history file size, speed for ~130M ticks), owner: builder, measured in inc-2.
- When the repository goes public, under which licence, and whether the `.teams/` planning files (which hold this PC's folder paths and the user's GitHub name) go public with it, owner: user.
- Defects the expert wants that are missing from catalogue v1, owner: user, asked after the software is finished (D-11).
