# Lead handoff

Updated: 2026-11-20 (after the user's second message)

## Goal
Lead loss-lens to the north star in `.teams/PROJECT.md`. The Lead plans, briefs, reviews and decides; the builder (a cheaper model in another tool, kickoffs pasted by the user) implements.

## Constraints (user's words)
- "you are the lead and orchestrator you do not build, i have a cheap AI that build and you review and do all the thinking"
- "we have a very expert person is who im shipping this tool to, he makes the EA and starts to open the live demo to try it on ... why dont i make him a software that spots for him the defects, like literally any type of defect"
- "make it easy to add any type of defect he wants if he put this github repo to his claude code and told him i want to add (example) as a defect to be spotted"
- "first i should add everything that could be needed, and be extremely accuracte, and easy to use, and doesnt make mistakes"
- "when I want to inspect one of them i click on it and it should take me to my MT4 on the exact day and it should show me the thing that happend there"
- Test EA: the Lead's choice; "enough rules so it wouldn't have losses everywhere", "many tickets a day".
- The user reads little: keep messages to him short and plain.

## State and how to check it
- Repository `C:\Users\yr471\Projects\loss-lens`, branch `main`, remote `origin` = https://github.com/YoussefMaximous/loss-lens (private). Only the Lead pushes, after accepting an increment (D-10).
- inc-1 (tick store) was reviewed on 2026-11-20 and sent back once with five small items ("Send-back 1" at the end of `.teams/increments/inc-1.md`). The tick data is accepted: 2026-01-01 to 2026-11-20, 84M ticks, 0.5 GB, in `data/` (not in git).
- `main` is ahead of `origin` and must not be pushed until the send-back is accepted (D-10).
- Check state with: `git log --oneline origin/main..main`, `git status --short`, then look for `.teams/teams/builder/work/report-inc-1b.md`.

## Done (with evidence)
- measured: `dukascopy-node` 1.51.1 downloads XAUUSD ticks on this PC when `NODE_OPTIONS=--use-system-ca` is set and `--chrome-path` points at Chrome. One day takes about 7 s.
- measured: 2026-03-03 has 554,076 ticks, first ts 1772496001086, last ts 1772582399247; Saturday gives a 0-byte file with exit 0; today's ticks are current to within seconds.
- measured: this PC has two MetaTrader 5 installs and no MT4.
- Catalogue v1 of 58 defects written (`.teams/DEFECTS.md`); detector contract and accuracy rules in ARCHITECTURE.md.
- measured (inc-1 review): all nine checks pass; two days re-downloaded outside the builder's code are identical to the store; a hard kill mid-sync breaks nothing; manifest and files agree; every gap over 300 s is a daily break, a US-holiday early close, or one 469 s quiet spell. Details in the Judgment in `inc-1.md`.
- measured: the daily break starts at 20:59 UTC from 2026-03-09 and at 21:59 UTC from 2026-11-02 (US daylight saving), which fixes the server-time rule for the MT4 export (D-18).
- The user's other project (`C:\Users\yr471\OneDrive\Desktop\mt4-xasu-work`, read-only) holds a working ticks-to-`.hst` converter and a handoff note; it is the reference for the chart-history half of the MT4 export. It was never loaded into a real MT4.

## Decisions
D-1 to D-18 in `.teams/DECISIONS.md` (D-17: Data tab with one package per year, Download and Top up buttons; D-18: MT4 export writes `.hst` for charts and `.fxt` with real ticks for the tester). The ones that shape every review: D-9 (accuracy), D-10 (only the Lead pushes, after review), D-14 (no live trading, ever), D-15 (quality bar in `.teams/QUALITY.md`), D-16 (one software, two uses: quick run for manual inspection, and the "Download missing days" button).

## Ruled out
- Re-implementing EA logic in our own engine (D-3).
- Committing tick data.
- A rule-builder screen as the way to add defects (D-8).

## Waiting on
- User: paste the builder kickoff (he added "install MT4" to it; the brief now tells the builder not to, D-13); install IC Markets' MT4 himself and open a demo account (the Lead then checks it is MetaTrader 4 and reads the gold symbol's name and server time); say whether the team owns Tick Data Suite.
- Not waiting on: the expert's review of the catalogue (after the software is finished, D-11).
- Builder: report for the send-back, `report-inc-1b.md`.

## Open
- MT4's real limits for a year of ticks (measure in inc-2), and the chunking or thinning choice that follows.
- Broker server-time offset (confirm in inc-2).
- Setup on the expert's PC (his MT4, his broker's symbol name and server time).

## Next step
When the builder reports the send-back, run its six "Done when" checks myself. If they pass: accept inc-1, push `main`, confirm the GitHub checks run green, then brief inc-2 (MT4 run spike: prove `.hst` and `.fxt` in a real MT4, reference EA, quick run from the command line, journal capture, guard test, `losslens doctor`, per-run log). inc-2 cannot be verified until the user has installed MT4.

## Files
`.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`, `.teams/DEFECTS.md`, `.teams/ROSTER.md`, `.teams/DECISIONS.md`, `.teams/KICKOFF.md`, `.teams/increments/inc-1.md`, `.teams/teams/builder/CHARTER.md`, `AGENTS.md`.
