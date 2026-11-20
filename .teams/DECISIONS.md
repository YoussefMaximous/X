# Decisions

Append-only, newest at the bottom. Only the Lead writes here. Never edit an old entry; supersede it with a new one.

Tags: team ids, `ALL` (every team must read it) or `SETUP`.

## D-1 · 2026-11-20 · SETUP
Decision: Team setup: small, overlay mode; active `lead`, `builder`. No proposer competition was run.
Why: The user fixed the roster up front (a Lead that thinks and reviews, one cheaper builder that implements, kickoffs pasted by the user). Existing setups win.
Alternatives rejected: extra teams (design, domain science) now: one implementing chat cannot absorb their output yet; revisit at inc-4 (app design).
Supersedes: none
Decided by: user

## D-2 · 2026-11-20 · ALL
Decision: The app is the product. The builder's earlier draft prompt (CLI first, dashboard later, 12-question interview) is superseded by `.teams/PROJECT.md` and `.teams/ARCHITECTURE.md`.
Why: The user asked for a smooth loss-inspection tool and told the Lead to ignore the draft.
Alternatives rejected: CLI-only tool with reports: does not meet the north star.
Supersedes: none
Decided by: user

## D-3 · 2026-11-20 · ALL
Decision: The EA always runs inside MetaTrader. loss-lens never re-implements strategy logic. The runner is a seam; first runner is native MT4 Strategy Tester.
Why: EA-agnostic, works with compiled EAs, and matches what the team will trade.
Alternatives rejected: own tick-replay engine executing the strategy: cannot run `.ex4`, and diverges from MT4 behaviour. MT5 runner: user specified MT4; kept possible for later.
Supersedes: none
Decided by: Lead

## D-4 · 2026-11-20 · ALL
Decision: Ticks are stored as one Parquet file per UTC day with the schema in ARCHITECTURE.md; times are UTC epoch milliseconds everywhere; broker time is applied only at MT4 export. `data/` is never committed.
Why: Per-day files make sync resumable and updates cheap; one time convention removes a whole class of bugs.
Alternatives rejected: one big CSV or one database file: slow to update, easy to corrupt, hard to verify.
Supersedes: none
Decided by: Lead

## D-5 · 2026-11-20 · ALL
Decision: Stack: Python 3.11+ (pyarrow, DuckDB) for data, runner and loss engine; Node only to run `dukascopy-node` pinned at 1.51.1; app as FastAPI + React/TypeScript (provisional until inc-4). The builder may not add dependencies beyond those a brief names without asking.
Why: Common, well-documented tools a cheaper model handles reliably; both runtimes are already installed (Python 3.13, Node 24, measured).
Alternatives rejected: C#/.NET desktop app: slower to build with the available builder. All-TypeScript: weaker for the numeric loss engine.
Supersedes: none
Decided by: Lead

## D-6 · 2026-11-20 · ALL
Decision: The test EA is a purpose-built reference EA in MQL4 with source (built in inc-2): gold scalper, many trades a day, several rule gates, decision log with rule ids. The team's real EA plugs in later through the same runner.
Why: The user left the choice to the Lead. A reference EA we control exercises every loss type and the decision-log path, and needs no download from unknown hosts.
Alternatives rejected: MT4's bundled sample EAs: too few rules and trades. A downloaded third-party EA: unknown quality and licence.
Supersedes: none
Decided by: Lead

## D-7 · 2026-11-20 · ALL
Decision: The end user is the team's EA expert, and the subject is defects, not only losses: any nameable problem in how the EA traded, including fragile winners, risk and sizing problems, patterns across the run, broken rules and order errors. Catalogue v1 is `.teams/DEFECTS.md`. The tool ships to the expert through a private GitHub repository.
Why: The user clarified the purpose: replace weeks of live-demo watching with a tick-data run that spots "literally any type of defect".
Alternatives rejected: keeping the scope at losing trades: misses defects hidden inside winners and across the run.
Supersedes: none (widens the loss-tag list in the first ARCHITECTURE.md)
Decided by: user

## D-8 · 2026-11-20 · ALL
Decision: Detectors are plug-ins: one file per defect with declared parameters and a `detect(ctx)` function, mandatory tests, automatic discovery, a one-command check, thresholds in `defects.toml`, and a written recipe for Claude Code. Contract in ARCHITECTURE.md.
Why: The user requires that the expert can add any defect by asking Claude Code in one sentence. That only works if a detector touches one file and cannot break the others.
Alternatives rejected: a rule-builder screen in the app: cannot express arbitrary defects. One large rules module: every addition risks breaking the rest.
Supersedes: none
Decided by: Lead

## D-9 · 2026-11-20 · ALL
Decision: Accuracy rules are binding: reconcile each run with the ticks before analysis; compute measurements once in one tested module; every finding stores its proof; no detector without a must-flag, must-not-flag and threshold-edge test; hand-checked golden cases in the test suite; "not evaluated" is never shown as "no defects".
Why: The user requires the tool to be extremely accurate. An expert who catches one wrong finding stops trusting the rest.
Alternatives rejected: trusting the MT4 report as-is; statistical or model-judged tagging: not checkable by eye.
Supersedes: none
Decided by: Lead

## D-10 · 2026-11-20 · ALL
Decision: The project lives in a private GitHub repository, https://github.com/YoussefMaximous/loss-lens. The builder commits locally and never pushes. The Lead pushes `main` after accepting an increment, so GitHub only ever holds reviewed work.
Why: The user asked for a GitHub repository; the expert will open it in Claude Code. Pushing only after review keeps unreviewed code from reaching him.
Alternatives rejected: public repository: the tool is the team's own. Builder pushes directly: unreviewed work would reach the expert.
Supersedes: none
Decided by: user (repository), Lead (push rule)

## D-11 · 2026-11-20 · SETUP
Decision: The expert reviews the defect catalogue after the software is finished, not before. Until then catalogue v1 stands as the Lead wrote it.
Why: The user's choice.
Alternatives rejected: asking the expert now.
Supersedes: none
Decided by: user

## D-12 · 2026-11-20 · ALL
Decision: When the app opens it tops up the tick store to the present in the background and shows the data's freshness. Running the EA over the new days is one button, never automatic. Built in the app increment; inc-1's `ticks sync` already provides the top-up.
Why: The user wants the data current whenever the tool opens. Measured 2026-11-20: today's ticks were available to within 5 seconds of the present. An MT4 run takes real time and should not start unasked.
Alternatives rejected: re-running the EA on every open: slow, and surprising. A live streaming feed into the app: not a live monitor (non-goal).
Supersedes: none
Decided by: user (top-up on open), Lead (EA run stays manual)

## D-13 · 2026-11-20 · ALL
Decision: The MT4 used for development is IC Markets' (the site now trades as "IC", https://www.ic.com). The user installs it and opens a demo account; the builder does not install MetaTrader. The Lead then confirms the program is MetaTrader 4 and reads the gold symbol's name and the server time from it.
Why: The user chose IC Markets. Observed 2026-11-20: the page's "Download MetaTrader 4" link goes to the client area (`secure.ic.com/Downloads`) and the site refuses automated requests (403), so a builder would have to guess a link or use another site; whether the download needs a login was not confirmed. A demo account needs personal details. This PC's `C:\Program Files\MetaTrader` folder holds MetaTrader 5, so a wrong installer is a real risk.
Alternatives rejected: builder installs MT4 during inc-1: contradicts its download rule, and it would have to guess the installer. MetaQuotes' generic installer: known to install MT5.
Supersedes: none
Decided by: user (broker), Lead (who installs)

## D-14 · 2026-11-20 · ALL
Decision: The software never trades: no order is placed, changed or closed on any account, demo or real, in this or any later version. Enforced by the seven layers in ARCHITECTURE.md ("Safety"): tester-only runner, no broker connection or passwords in our code, the MT4 bridge is an indicator, the reference EA refuses to run outside the tester, a dedicated MT4 copy with live trading off, a guard test that fails the build, and a written rule for every AI that opens the repository.
Why: The user forbids any live or real-money action, including through future updates. The expert will change the repository with Claude Code, so the rule must be enforced by checks, not by intention.
Alternatives rejected: relying on the tester being a simulation alone: the bridge and future changes are outside the tester. Making the bridge an EA: an EA is able to trade; an indicator is not.
Supersedes: the "small EA" wording for the MT4 bridge in earlier ARCHITECTURE.md
Decided by: user (the rule), Lead (how it is enforced)

## D-15 · 2026-11-20 · ALL
Decision: The product must ship at professional grade. The bar is `.teams/QUALITY.md`: provable findings, repeatable runs, plain failure messages and a self-check command, measured speed budgets, tick replay as a first-class feature, screens designed before they are built, and code kept like a product (types, linting, tests on GitHub, releases, clean-PC install). An increment with a known defect is sent back. Risky steps get a second independent review.
Why: The user requires that the tool does not look or behave like something generated in one go; it goes to an expert whose trust depends on it.
Alternatives rejected: leaving quality to each brief: the bar drifts. Polishing at the end: structure and speed cannot be added afterwards.
Supersedes: none
Decided by: user (the requirement), Lead (the bar)

## D-16 · 2026-11-20 · ALL
Decision: One software, two uses. Besides finding defects, the expert can pick any date range (a day, weeks, a month, a set of days, the year) and have that range opened in the MT4 Strategy Tester on our ticks to inspect by eye, with no defect analysis ("quick run"). A quick run can be analysed afterwards with one button. A Data screen shows which days are stored, and a "Download missing days" button fetches the gaps from Dukascopy through `dukascopy-node`. Details in ARCHITECTURE.md.
Why: The user's requirement: the expert sometimes wants to run a few weeks and detect things visually, as he does today, and wants a manual button for missing data. Both reuse the runner and `ticks sync`, so they cost little.
Alternatives rejected: a separate tool for manual runs: two programs to install and keep in step. Always analysing: gets in his way when he only wants to look.
Supersedes: none (D-12's top-up on open stays; D-14 applies to both uses: Strategy Tester only)
Decided by: user

## D-17 · 2026-11-20 · ALL
Decision: The Data tab shows tick data as one package per year, listing only what Dukascopy offers through `dukascopy-node` (first year read from the pinned package's instrument record; gold starts 2003-05-05, measured). Each year shows how far it is downloaded. A year not downloaded has a Download button; the current year has a Top up button that fetches every missing day up to now; a past year with gaps has Download missing. Imported files are listed separately. Details in ARCHITECTURE.md, "Data tab".
Why: The user's requirement, in his words: show "2026 package is downloaded until the date of 2026-11-20 and 2025 and 2024 and so on is not downloaded", with a download button each and a top-up for the current year.
Alternatives rejected: only a day-by-day calendar: does not answer "which years do I have" at a glance. A typed-in list of years: goes wrong when the source changes.
Supersedes: the "Data screen" wording in D-16
Decided by: user

## D-18 · 2026-11-20 · ALL
Decision: The MT4 export writes both a chart history file (`.hst`, M1 bars, by the method from the user's other project) and a tester tick file (`.fxt`, the real ticks). Two corrections to that method: the server-time offset follows US daylight saving instead of a fixed +2 hours, and prices are rounded to the broker's decimals before writing. Details in ARCHITECTURE.md, "MT4 export". inc-2 proves both files in a real MT4 before anything is built on them.
Why: The user supplied his working `.hst` method. It is right for charts. For testing, M1 bars alone make MT4 invent the ticks inside each minute, which would make findings wrong and break D-9. Measured in our ticks: the daily break moves from 20:59 to 21:59 UTC on 2026-11-02 (and back on 2026-03-09), so a fixed offset is an hour off for part of the year, including the first two days of the reference export.
Alternatives rejected: `.hst` only: interpolated ticks. Tick Data Suite: paid, and the user has not said the team owns it; the runner seam keeps it possible.
Supersedes: none
Decided by: Lead, on the user's input

## D-19 · 2026-11-20 · ALL
Decision: loss-lens does the order filling on real bid and ask; MT4 only executes the EA's code. Two layers, both built by us. Layer 1 (any EA): after an MT4 run, every order is re-filled tick by tick on real bid and ask, and results are shown as "MT4 says" beside "with real spreads", with later orders that depend on a corrected one marked. Layer 2 (EAs with source, one include line): a simulated broker inside the tester run, so decisions and fills are both on real spreads; it must first match MT4 order for order at a fixed spread. Details in ARCHITECTURE.md, "Real-spread execution".
Why: The user and the expert want runs that use the real spreads in our ticks, because MT4's tester applies one fixed spread (measured on the 84.0M ticks of 2026 so far: the real spread has a median of 0.65, is above 2.21 for 1% of ticks, and ranges from 0.001 to 15.0). The user chose to build layer 2 rather than buy it; the expert has his EAs' source.
Alternatives rejected: a fully separate engine that runs the strategy: an MT4 EA can only be executed by MT4, so it would test a rewrite, not the EA. Tick Data Suite: the user chose to build; the runner seam still allows it. MT5's tester (real spreads natively): the EAs are MT4.
Supersedes: none (D-3 stands: the EA's logic still runs only in MT4; what changes is who fills the orders)
Decided by: user

## D-20 · 2026-11-20 · ALL
Decision: Nothing leaves the PC. The software's only online action is downloading public price ticks from Dukascopy, and only when the user asks for it. No telemetry, analytics, update checks, accounts or cloud. EA files are never uploaded, copied out or added to git; the software records only an EA's name and fingerprint. The app listens on `127.0.0.1` only and loads nothing from the internet. Our MT4 files contain no online function and no DLL import. Enforced by `tests/test_no_network.py`, a dependency allow-list, rules for AI agents, and a plain-words page in the repository. The project is to be open source. Details in ARCHITECTURE.md, "Privacy".
Why: The user's requirement, in his words: "it shouldnt do anything bad for the user or do ANYTHING ONLINE ... or be any risk on any user and his data or on his experts", "its an opensource".
Alternatives rejected: keeping the automatic top-up when the app opens: it is online activity the user did not start. Reading EA source to give richer analysis by default: not needed, and it is the user's most sensitive file.
Supersedes: D-12 (no automatic top-up; the app shows how old the data is and offers the Top up button). Changes D-10's "private" to "open source", with the date of going public and the licence still to be chosen by the user.
Decided by: user (the rule), Lead (how it is enforced)

## D-21 · 2026-11-20 · ALL
Decision: The team works inside loss-lens, not inside MT4. The chart and inspection tools in loss-lens look and work the way MT4's do: same layout, colours, chart types, timeframes, zoom and scroll, keyboard keys, drawing tools, standard indicators, trade marks and tester-style replay controls. MT4 runs in the background only to execute the EA. What the look must match is taken from the real MT4 on this PC, side by side, at design time. We copy the look and the habits, never MetaQuotes' code, name, logo or icon pictures. Details in ARCHITECTURE.md, "MT4 look and feel".
Why: The user, in his words: "they are extremely used to mt4 look and colors and tools so we want the exact same look", "now were not working IN MT4 were working on our software". MT4 cannot show what loss-lens adds (real ask, tick replay, proof, loss types), so the team needs one place that feels like home.
Alternatives rejected: a modern look of our own: the team would have to relearn it. Sending the expert to the real MT4 for every inspection (the earlier plan): slower, and MT4 cannot draw the proof or replay ticks.
Supersedes: the part of D-16 that leaves MT4 open as the place to inspect a quick run (the result now opens in our chart). The MT4 jump becomes an optional extra, "Open in real MT4", built late; it stays useful for an EA's own custom indicators, which only MT4 can draw.
Decided by: user

## D-22 · 2026-11-20 · ALL
Decision: Every losing trade is classified. It gets exactly one main cause from the catalogue (so the counts and the money of all types add up to the total losses, with nothing counted twice), and keeps its other defects as tags. A loss with no cause found goes to "Unexplained", which is shown like any other type. The Losses panel lists each type with how many times it happened, the money it cost, its share, and its trend over the run; clicking a type lists its trades; clicking a trade opens the chart at that moment with the proof drawn and replay ready. Details in ARCHITECTURE.md, "Loss classification".
Why: The user asked for "the loss classification system which classifies the type of the loss and how many times it was made, and you click on it and it takes you to inspect it on the chart ... and you could replay it".
Alternatives rejected: counting a trade under every defect it carries: the totals would exceed the real loss and mislead. Hiding losses that fit no type: it would make the software look more certain than it is.
Supersedes: none (adds to D-7 and D-8)
Decided by: user (the feature), Lead (one main cause, the "Unexplained" type)

## D-23 · 2026-11-20 · ALL
Decision: A defect is the reason a losing trade lost. Every loss is classified into exactly one type (D-22): how many times that reason happened, what it cost, and one click opens that loss on the chart. Catalogue v1 holds only loss reasons. A winning trade, a missed trade, a broken rule that did not cause a loss, and a warning about the data are not defects and are not in the first release. The check that a run matches the ticks (D-9) stays; it is a trust check, not a defect type.
Why: The user, in his words: "defects are the reasons of the loss classified into different types".
Alternatives rejected: keeping the wider list (fragile winners, order errors, trust flags): that is a different product from the one the user described.
Supersedes: the widening in D-7 ("not only losses"). The rest of D-7 stands: the end user is the expert, and the catalogue is `.teams/DEFECTS.md`.
Decided by: user

## D-24 · 2026-11-20 · ALL
Decision: Classifying the reason of a loss is the core of the product, and it is hard. A loss can carry more than one reason, or none. Nothing about how those reasons are counted, named or switched off is locked. The earlier rule of exactly one main cause per loss is withdrawn. The screen for this is an open design, sent to Fable in `.teams/teams/lead/work/checkpoints/2026-11-20-loss-types-screen.md`.
Why: The user, in his words: "knowing the type of the loss as in classifying it is extremely challenging and hard but it is the core of our product", and "a loss can be multiple reasons or not there are no locked rules".
Alternatives rejected: keeping one forced cause so the counts add up to the number of losses. That was the Lead's rule, and the user rejected it.
Supersedes: the "exactly one main cause" rule in D-22. The rest of D-22 stands: click a loss and the chart opens on it with replay.
Decided by: user

## D-25 · 2026-11-20 · ALL
Decision: A loss can carry more than one reason. One of them is the main reason: the one that accounts for the most of that loss. Any other reason counts only if it passes a gate, a score high enough against the size of the loss. A reason that fails the gate is not listed. How the score is calculated and where the gate sits are not settled; Fable is asked to design them in the losses-screen checkpoint.
Why: The user, in his words: "if multiple reasons of loss it should have 1 main reason which is the most and maybe put a gate that says if it actually can count as 2 or 3 or all 5 or only 1 there should be gates or something like a score enough to the loss total".
Alternatives rejected: listing every weak match as a reason. Forcing exactly one reason in every case.
Supersedes: none (narrows D-24: several reasons are allowed, but only the main one is automatic, and the rest must clear a gate)
Decided by: user (the rule), Lead (the score itself stays open)
