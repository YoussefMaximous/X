# Lead handoff

Updated: 2026-11-20

## Goal
Lead loss-lens to the north star in `.teams/PROJECT.md`. The Lead plans, briefs, reviews and decides; the builder (a cheaper model in another tool, kickoffs pasted by the user) implements.

## Constraints (user's words)
- "you are the lead and orchestrator you do not build, i have a cheap AI that build and you review and do all the thinking"
- "the software should be extremely smooth and have the types of losses identified and filtered as I like and I can put any type of ticks data I want in it"
- "when I want to inspect one of them i click on it and it should take me to my MT4 on the exact day and it should show me the thing that happend there"
- Test EA: the Lead's choice; "enough rules so it wouldn't have losses everywhere", "many tickets a day".
- The builder's earlier draft prompt may be ignored.

## State and how to check it
- Repository `C:\Users\yr471\Projects\loss-lens`, branch `main`, local only (no remote).
- `.teams/` written; inc-1 (tick store) briefed, not started.
- Check state with: `git log --oneline -10`, `git status --short`, then look for `.teams/teams/builder/work/report-inc-1.md`.

## Done (with evidence)
- measured: `dukascopy-node` 1.51.1 downloads XAUUSD ticks on this PC when `NODE_OPTIONS=--use-system-ca` is set and `--chrome-path` points at Chrome. One day takes about 7 s.
- measured: 2026-03-03 has 554,076 ticks, first ts 1772496001086, last ts 1772582399247; Saturday gives a 0-byte file with exit 0; today's ticks are current to within seconds.
- measured: this PC has two MetaTrader 5 installs and no MT4.

## Decisions
D-1 to D-6 in `.teams/DECISIONS.md`.

## Ruled out
- Re-implementing EA logic in our own engine (D-3).
- Committing tick data.

## Waiting on
- User: paste the builder kickoff; install MT4 from the team's broker and say the gold symbol's exact name; say whether the team owns Tick Data Suite; confirm the builder can open the project folder.
- Builder: report for inc-1.

## Open
- MT4's real limits for a year of ticks (measure in inc-2), and the chunking or thinning choice that follows.
- Broker server-time offset (confirm in inc-2).
- GitHub remote: offered to the user, not created.

## Next step
When the builder reports, run the nine checks in `.teams/increments/inc-1.md` myself, fill in the Judgment, then brief inc-2 (MT4 run spike with the reference EA).

## Files
`.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`, `.teams/ROSTER.md`, `.teams/DECISIONS.md`, `.teams/KICKOFF.md`, `.teams/increments/inc-1.md`, `.teams/teams/builder/CHARTER.md`, `AGENTS.md`.
