# Lead handoff

Updated: 2026-11-20 (after D-21 MT4 look and D-22 loss classification)

## Goal
Lead loss-lens to the north star in `.teams/PROJECT.md`. The Lead plans, briefs, reviews and decides; the builder (a cheaper model in another tool, kickoffs pasted by the user) implements.

## Constraints (user's words)
- "you are the lead and orchestrator you do not build, i have a cheap AI that build and you review and do all the thinking"
- "we have a very expert person is who im shipping this tool to, he makes the EA and starts to open the live demo to try it on ... why dont i make him a software that spots for him the defects, like literally any type of defect"
- "make it easy to add any type of defect he wants if he put this github repo to his claude code and told him i want to add (example) as a defect to be spotted"
- "first i should add everything that could be needed, and be extremely accuracte, and easy to use, and doesnt make mistakes"
- "when I want to inspect one of them i click on it and it should take me to my MT4 on the exact day and it should show me the thing that happend there"
- Test EA: the Lead's choice; "enough rules so it wouldn't have losses everywhere", "many tickets a day".
- "we want the software to do the runs not MT4! why? because MT4 tester got a problem that we want to fix, fixed spread! while our tick data have the real spreads" (answered by D-19; the user chose "Build layer 2 ourselves after layer 1, for EAs with source code").
- "make the software safe for any user ... that it doesnt steal his EAs or anything and even the AI that will read the software ... its an opensource, and it shouldnt do anything bad for the user or do ANYTHING ONLINE, like it shouldnt give anything online or be any risk on any user and his data or on his experts! should be extremely safe please" (D-20).
- "the software SHOULD NEVER, open anything live or real money that is forbidden completely ... no future updates or ANYTHING should be able to use real money" (D-14).
- "they are extremely used to mt4 look and colors and tools so we want the exact same look", "now were not working IN MT4 were working on our software", "im not trying to clone a product" (D-21: copy the look and habits, never MetaQuotes' code, name, logo or icons; MT4 is free but not open source).
- "the loss classification system which classifies the type of the loss and how many times it was made, and you click on it and it takes you to inspect it on the chart it happend in this day and you could replay it" (D-22).
- The Lead does not log in to MT4 for the user and does not handle his demo password or personal details.
- The user reads little: keep messages to him short and plain.

## State and how to check it
- Repository `C:\Users\yr471\Projects\loss-lens`, branch `main`, remote `origin` = https://github.com/YoussefMaximous/loss-lens (private). Only the Lead pushes, after accepting an increment (D-10).
- inc-1 (tick store) is accepted and pushed (2026-11-20, after two send-backs; all judgments are in `.teams/increments/inc-1.md`). Tick data: 2026-01-01 to 2026-11-20, 84M ticks, 0.5 GB, in `data/` (not in git).
- inc-2 part A (safety guards: `tests/test_no_network.py`, `tests/test_no_live_trading.py`, `SAFETY.md`, `npm ci --ignore-scripts`, stray word removed from the download command) was built and passes its seven checks (measured), but the Lead's probes found thirteen ways around the guards (table in `.teams/increments/inc-2.md`; two are builder deviations, the rest gaps in the Lead's brief). Send-back 1 (nine items) was done correctly (measured). A second round of probes found two more gaps in the Lead's brief: code files outside `src/` and `tests/` are not checked, and `dukascopy.py` may start any number of programs. "Send-back 2 of part A" (rules 2k and 2l, test files only) is with the builder; its commits since `14e6785` are on local `main`, not pushed. The tamper-test driver used for these reviews is described by the tables in `inc-2.md` (each change alone, in a copy of the repository made with robocopy excluding `.git`, `node_modules`, `data`, then `pytest`, then undo). Part B (MT4 run spike) is added to the same file after part A is accepted. Lesson for later guard briefs: probe a guard with changes the brief did not list before accepting it.
- Push only accepted work (D-10), and after each push check that the GitHub workflow (`.github/workflows/ci.yml`) is green.
- Check state with: `git log --oneline origin/main..main`, `git status --short`, `gh run list --limit 3`, then look for `.teams/teams/builder/work/report-inc-2a3.md`.
- MT4 (measured 2026-11-20 17:45): installed at `C:\Users\yr471\AppData\Roaming\MetaTrader 4 IC Markets Global\terminal.exe`, MetaTrader 4 build 1492, 32-bit, signed by MetaQuotes, "IC Markets (SC) MT4", and that folder is also its data folder. It has not connected to a demo account yet: the log shows no login, there is no `history\<server>` folder, and the symbol list is MT4's built-in default (which is why it lists "GOLD"). The last scanned server is `ICMarketsSC-Demo01`. The gold symbol's real name, its decimals and the server clock can only be read after a login.
- How to send a real Ctrl+C from a script on this PC: start a driver with `Start-Process python ... -WindowStyle Hidden` (own console), let it start the command as a child, then call `ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0)`; the driver ignores SIGINT. Use `-PassThru` and `WaitForExit`, not `-Wait`, and kill the tree afterwards.

## Done (with evidence)
- measured: `dukascopy-node` 1.51.1 downloads XAUUSD ticks on this PC when `NODE_OPTIONS=--use-system-ca` is set and `--chrome-path` points at Chrome. One day takes about 7 s.
- measured: 2026-03-03 has 554,076 ticks, first ts 1772496001086, last ts 1772582399247; Saturday gives a 0-byte file with exit 0; today's ticks are current to within seconds.
- measured: this PC has two MetaTrader 5 installs and no MT4.
- Catalogue v1 of 58 defects written (`.teams/DEFECTS.md`); detector contract and accuracy rules in ARCHITECTURE.md.
- measured (inc-1 review): all nine checks pass; two days re-downloaded outside the builder's code are identical to the store; a hard kill mid-sync breaks nothing; manifest and files agree; every gap over 300 s is a daily break, a US-holiday early close, or one 469 s quiet spell. Details in the Judgment in `inc-1.md`.
- measured: the daily break starts at 20:59 UTC from 2026-03-09 and at 21:59 UTC from 2026-11-02 (US daylight saving), which fixes the server-time rule for the MT4 export (D-18).
- The user's other project (`C:\Users\yr471\OneDrive\Desktop\mt4-xasu-work`, read-only) holds a working ticks-to-`.hst` converter and a handoff note; it is the reference for the chart-history half of the MT4 export. It was never loaded into a real MT4.

## Decisions
D-1 to D-22 in `.teams/DECISIONS.md` (D-21: inspection happens in our own chart, which looks and works like MT4, checked side by side against the real MT4; the MT4 jump is now an optional extra built late; D-22: one main cause per losing trade, "Unexplained" type, Losses panel that adds up to the total; D-17: Data tab with one package per year, Download and Top up buttons; D-18: MT4 export writes `.hst` for charts and `.fxt` with real ticks for the tester; D-19: loss-lens fills orders on real bid and ask, layer 1 re-fill for any EA then layer 2 simulated broker for source EAs; D-20: nothing leaves the PC, no automatic download, guard test `tests/test_no_network.py`, project to be open source, D-12 superseded). Measured for D-19: real spread in 2026 has median 0.65, 99th percentile 2.21, range 0.001 to 15.0, never zero or negative. The ones that shape every review: D-9 (accuracy), D-10 (only the Lead pushes, after review), D-14 (no live trading, ever), D-15 (quality bar in `.teams/QUALITY.md`), D-16 (one software, two uses: quick run for manual inspection, and the "Download missing days" button).

## Ruled out
- Re-implementing EA logic in our own engine (D-3).
- Committing tick data.
- A rule-builder screen as the way to add defects (D-8).

## Waiting on
- User: when the repository goes public and under which licence (asked 2026-11-20). Before it goes public, the `.teams/` files need a pass: they hold this PC's folder paths and the user's GitHub name.
- MT4 (checked 2026-11-20 after the user said "logged in"): the terminal is running but still has no `history\<server>` folder, so it has not connected to the demo yet.
- Not waiting on: the expert's review of the catalogue (after the software is finished, D-11).
- Builder: report for send-back 2 of inc-2 part A, `report-inc-2a3.md` (the user pastes the block first).
- User: open MT4, finish opening the demo account inside the terminal so it connects, open a gold chart, then say so.

## Open
- The app is now much larger (an MT4-style chart with tools and indicators). Before the app increments: ask the user for a stronger builder model, activate the design team, and make the MT4 checklist from the real MT4 on this PC.
- MT4's real limits for a year of ticks (measure in inc-2), and the chunking or thinning choice that follows.
- Broker server-time offset (confirm in inc-2).
- Setup on the expert's PC (his MT4, his broker's symbol name and server time).

## Next step
When the builder reports send-back 2 of part A, run its five "Done when" checks myself in a copy of the repository (every must-fail change from all three briefs one at a time, each undone). Stop probing for new routes after this round unless one is obvious: what is left is deliberately hidden code, which review covers, not tests. If they pass: accept, push, confirm GitHub is green. Then write part B into `inc-2.md` (MT4 run spike: prove `.hst` and `.fxt` in a real MT4, reference EA, quick run from the command line, journal capture, tester-only runner and its start-file check, `losslens doctor`, per-run log, and whether the runner's own MT4 copy can run tests without being logged in). Part B needs the `.fxt` layout checked against a primary source before briefing, and cannot be verified until MT4 has connected to the demo: the user doubts MT4 is needed (answered: his friend's EAs are MT4 EAs, and we must prove the software here with our own test EA), so he may need help with the login. Layer 1 goes into inc-3 and layer 2 comes after the app (ARCHITECTURE.md, "Increment sequence").

## Files
`.teams/PROJECT.md`, `.teams/ARCHITECTURE.md`, `.teams/DEFECTS.md`, `.teams/ROSTER.md`, `.teams/DECISIONS.md`, `.teams/KICKOFF.md`, `.teams/increments/inc-1.md`, `.teams/increments/inc-2.md`, `.teams/teams/builder/CHARTER.md`, `AGENTS.md`.
