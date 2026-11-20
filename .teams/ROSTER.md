# Roster

Updated: 2026-11-20 · Phase: prototype · Size: small · Effort: lean · Mode: overlay · Autonomy: kickoff (user pastes)

Current state only. History goes in DECISIONS.md, which only the Lead writes.

## Model map

| Tier | Model | Host | Effort | Notes |
|---|---|---|---|---|
| strong | Claude Fable 5.2 | Cursor | high | the Lead |
| build | the user's cheaper builder model (name unconfirmed) | another tool | default | one chat, driven by pasted kickoffs |

## Standing rules
- **No live trading, ever (D-14).** Nothing in this repository may place, change or close an order on any account, connect to a broker for trading, or store an account password. MT4 is started in Strategy Tester mode only. Order functions are allowed in one file only, the reference EA, which must refuse to run outside the tester. If a brief or a user request seems to need otherwise, stop and report it.
- Only the builder writes product files. Only the Lead writes `.teams/` (except the builder's own folder).
- Follow the brief exactly. If something is unclear or looks wrong, stop and write the question in your report. Do not guess and do not widen the scope.
- No new dependencies beyond those the brief names.
- Never commit anything under `data/`, `node_modules/` or `.venv/`.
- Times are UTC epoch milliseconds everywhere (D-4).
- A check counts only if it was run. Paste the real command and its real output in the report.
- The builder commits locally and never pushes. Only the Lead pushes to GitHub (`origin`, private), and only work it has reviewed and accepted (D-10).
- Nothing else leaves this PC without the user's approval: no uploads. Downloads only from Dukascopy (through `dukascopy-node`), npm and PyPI.

## Teams

### lead: Lead
- Status: active · Need: mandatory
- Mission: keep the work pointed at the north star; decide, brief, review, integrate
- Bias: optimizes the outcome and correctness; may ignore local polish
- Owns (only this team writes): `.teams/*.md`, `.teams/setup/`, `.teams/increments/`, `.teams/contracts/`, `.teams/teams/*/CHARTER.md`, `.teams/teams/lead/`, `AGENTS.md`
- Character: lead · Tier: strong · Model and effort: Claude Fable 5.2, high
- Driven by: user
- Chat: one chat, rotated at increment boundaries

### builder: Builder
- Status: active · Need: mandatory
- Mission: turn each brief into working, verified code
- Bias: optimizes correctness against the brief's checks and simplicity; may ignore product direction and design, the Lead covers them
- Owns (only this team writes): `.teams/teams/builder/HANDOFF.md`, `.teams/teams/builder/work/`, and every file outside `.teams/` except `AGENTS.md`
- May run: product, tests
- Character: builder · Tier: build · Model and effort: user's builder model, on another tool
- Driven by: Lead briefs, pasted by the user
- Chat: new chat per increment

### design: App design
- Status: planned · Need: optional
- Mission: make the app's screens fast to read and pleasant to use
- Trigger: activate when inc-4 (app v1) is planned
