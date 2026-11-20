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
- `.teams/` written; inc-1 (tick store) briefed, not started by the builder as of this handoff.
- Check state with: `git log --oneline -10`, `git status --short`, then look for `.teams/teams/builder/work/report-inc-1.md`.

## Done (with evidence)
- measured: `dukascopy-node` 1.51.1 downloads XAUUSD ticks on this PC when `NODE_OPTIONS=--use-system-ca` is set and `--chrome-path` points at Chrome. One day takes about 7 s.
- measured: 2026-03-03 has 554,076 ticks, first ts 1772496001086, last ts 1772582399247; Saturday gives a 0-byte file with exit 0; today's ticks are current to within seconds.
- measured: this PC has two MetaTrader 5 installs and no MT4.
- Catalogue v1 of 58 defects written (`.teams/DEFECTS.md`); detector contract and accuracy rules in ARCHITECTURE.md.

## Decisions
D-1 to D-17 in `.teams/DECISIONS.md` (D-17: Data tab with one package per year, Download and Top up buttons). The ones that shape every review: D-9 (accuracy), D-10 (only the Lead pushes, after review), D-14 (no live trading, ever), D-15 (quality bar in `.teams/QUALITY.md`), D-16 (one software, two uses: quick run for manual inspection, and the "Download missing days" button).

As of 16:56 on 2026-11-20 the builder has five local commits for inc-1 and no report yet. Lead commits made after that sit on top of them, so `main` is not pushed until inc-1 is reviewed and accepted (D-10).

## Ruled out
- Re-implementing EA logic in our own engine (D-3).
- Committing tick data.
- A rule-builder screen as the way to add defects (D-8).

## Waiting on
- User: paste the builder kickoff (he added "install MT4" to it; the brief now tells the builder not to, D-13); install IC Markets' MT4 himself and open a demo account (the Lead then checks it is MetaTrader 4 and reads the gold symbol's name and server time); say whether the team owns Tick Data Suite.
- Not waiting on: the expert's review of the catalogue (after the software is finished, D-11).
- Builder: report for inc-1.

## Open
- MT4's real limits for a year of ticks (measure in inc-2), and the chunking or thinning choice that follows.
- Broker server-time offset (confirm in inc-2).
- Setup on the expert's PC (his MT4, his broker's symbol name and server time).

## Next step
When the builder reports, run the nine checks in `.teams/increments/inc-1.md` myself, fill in the Judgment, then brief inc-2 (MT4 run spike with the reference EA, capturing the journal as well as the trades).

## Files
`.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`, `.teams/DEFECTS.md`, `.teams/ROSTER.md`, `.teams/DECISIONS.md`, `.teams/KICKOFF.md`, `.teams/increments/inc-1.md`, `.teams/teams/builder/CHARTER.md`, `AGENTS.md`.
