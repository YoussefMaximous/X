# Why did this trade lose? The design of loss classification (Lead-owned)

Updated: 2026-11-20. Decision D-26. This answers the checkpoint `teams/lead/work/checkpoints/2026-11-20-loss-types-screen.md`.

Nobody has seen the expert's trades yet. Every number in an example below is invented to show how the screen reads. Every threshold marked **(guess)** is a starting value to be tuned on real runs.

## 1. The one idea everything rests on

A rule that matches a loss is not yet a reason for it. A reason has to be worth money.

So every loss type must answer one question with a number: **"If this one thing had not happened, how much smaller would this loss have been?"** The answer is measured on the real ticks, not estimated. That number, as a share of the loss, is the score. The gate is a minimum score. This is what stops a reason from appearing "just because its rule matched".

## 2. The screen, top to bottom

It is laid out like the terminal the team already knows: chart on top, a tabbed panel at the bottom.

1. **The chart** (MT4 style, D-21). It shows the loss that is selected below: entry and exit arrows, the dashed line between them, stop and target lines, the bid and the real ask.
2. **One summary line** under the chart, always visible, never changed by any switch:
   `Losses 412 · -18,340.50 · Reason found for 64% of the money · Partly 9% · No reason found 27% · Not judged 0`
3. **Bottom panel, tab "Losses"**, in two parts side by side:
   - **Left: Loss types.** One row per type, biggest money first, each with a tick box. The row starts with what the losses have in common (the pattern), then the name.
   - **Right: Losses.** Every losing trade of the run, biggest loss first, in the same columns as MT4's account history, plus three of ours: Shape, Main reason, Other reasons.
4. **The "Why" box** beside the chart (where MT4 keeps its Data Window). For the selected loss it lists every reason that matched, with its score, whether it counted, and a "Show" button that draws the proof on the chart.

What he does in the first minute: reads the summary line, looks at the top row of Loss types, clicks it, and the Losses list shows only those; clicks the first loss, the chart jumps there; presses the replay key and watches it happen tick by tick.

## 3. How a reason is decided

### Step 0. Can this loss be judged at all?
If the run did not match the stored ticks (D-9), or ticks are missing during the trade, the loss is **Not judged**, with the cause stated. It still appears in the list with its money. It never gets a reason.

### Step 1. The shape: how the loss unfolded
Every judged loss gets exactly one shape. A shape is a description, not a reason. It is always provable from the ticks and it is never "unknown". First match in this order:

| Shape | Meaning |
|---|---|
| Costs only | In profit before commission and swap, a loss after them |
| Jumped through the stop | Closed by its stop at a price clearly worse than the stop (a gap) |
| Won first, then lost | Was at least half-way to its target (or +0.5 of its risk), still closed at a loss |
| Stopped, then went to target | Closed by its stop; afterwards price reached the target before going a further full risk against |
| Slow bleed | Closed by the EA, not by the stop, after an unusually long hold, never half-way to target |
| Cut by the EA | Closed by the EA at a loss, anything else |
| Straight to the stop | Closed by its stop without ever getting half-way to target |

"Risk" is the distance from entry to the first stop, times the size. The thresholds (half-way, "unusually long", how long "afterwards" lasts) are **(guess)**.

### Step 2. Each loss type gives a what-if and a money figure
A loss type is one file (D-8). Besides its rule it must state **one what-if, fixed in advance, in one sentence**, and compute what the trade's result would have been under it, on the real ticks. Two kinds:

- **Proved on this trade.** The what-if changes only the one thing the type names and replays this trade. Example: "the same trade, with the spread at its 10-minute median". Stop, target, size and entry time stay as they were. If the trade would have stayed open longer, the stop and target stay where the EA last put them, and the screen says so.
- **Proved over the run.** Some reasons are circumstances (entered just before the daily break, entered again right after a stop). For one trade these can be shown as a fact but not as a cause. Their money figure comes from the whole run: the average result of all trades in that circumstance against all trades outside it, winners included. If trades in the circumstance do worse by 0.4 of their risk on average, the type is credited with 0.4 of this trade's risk. It only counts when there are at least 30 trades on each side **(guess)** and the gap shows in both halves of the run. Otherwise the circumstance is shown as a grey fact and is not a reason.

`saved` = result under the what-if minus the real result, in money. If it is zero or negative, the type is not a reason for this loss.

### Step 3. The score
`score = saved ÷ size of the loss`, capped at 100%. If the what-if turns the loss into a win, the score is 100% and the Why box adds "would have closed at +X".

### Step 4. The gate
A reason **counts** only if its score is at least **25%** **(guess)** and `saved` is more than a small floor in money (a tenth of the run's typical loss, **guess**), so tiny losses do not produce reasons out of rounding. Both are settings.

### Step 5. The main reason
The counted reason with the highest score. If a "proved over the run" reason leads a "proved on this trade" reason by fewer than 10 points, the one proved on this trade is the main reason, because its evidence is on this chart. Up to five reasons are shown on the row; all are in the Why box.

Each counted reason carries a word: **strong** (75% and up), **clear** (50 to 74%), **partial** (25 to 49%).

### Step 6. No reason
If nothing counts, the loss goes to **No reason found**. This is a normal, honest result: a sound trade can simply lose. It is a row like any other, it cannot be switched off, and its size is on the summary line. If it is large, the list of types is missing something, which is what "add a loss type in one sentence" is for.

### A worked number
A sell loses 100.00. Its risk was 100.00. Four types match:

| Type | What-if | Result under it | Saved | Score | Counts? |
|---|---|---|---|---|---|
| Stopped by the spread | spread at its 10-minute median | not stopped, later closes at +150 | 100 (capped) | 100% | yes, main, strong |
| Stop inside normal noise | stop at the usual one-minute swing | -60 | 40 | 40% | yes, partial |
| Entered just before the daily break | (over the run) such trades do 0.18 of risk worse | | 18 | 18% | no, below the gate |
| Commission and swap | none charged | -94 | 6 | 6% | no |

The row reads: Loss -100.00 · Main: Stopped by the spread (100%) · Also: Stop inside normal noise (40%). The Why box shows all four, the last two in grey with "matched, below the gate". The scores are not added together: they overlap, because fixing either of the first two alone would have helped.

## 4. Money is shown once

- A loss's money appears once on its own row, and in totals it is counted once, under its **main** reason.
- In the Loss types table the columns "Losses" and "Money" count main reasons only. Together with "No reason found" and "Not judged" they add up to the run's total loss, to the cent. A test checks this on every run.
- A separate grey column "Also in" says in how many other losses the type counted as an extra reason. It has no money total, and it is never added to anything.
- There is no chart that adds reasons together, and no pie of reasons inside one loss.
- In the Why box each reason reads "explains 40% of this loss on its own (40.00 of 100.00)", followed by the line "These overlap. They are not added."

## 5. Switches

Two different actions, because he may mean either:

- **The tick box on a type = "count this type as a reason".** Off: the type no longer exists for this view. On every loss where it was an extra reason, it disappears from the row. On every loss where it was the main reason, the next counted reason becomes the main one; if there is none, the loss moves to "No reason found". No loss leaves the list and no total changes. It is instant, because every score is already stored; nothing is run again. In the Why box the switched-off reason stays visible in grey, marked "switched off", so nothing is silently ignored.
- **Hide (right-click a type or a loss, as in MT4's symbol list).** Those losses leave the list and the chart marks. A status line at the bottom of the list always says `Hidden: 37 losses, -4,210.00 · Show all`. The summary line under the chart does not change.

A set of switches can be saved under a name and picked again later.

## 6. The pattern first, the name second

A type's row starts with what its losses have in common, in plain words with this run's numbers. The name comes after. Clicking the row opens three things: the list of those losses, the **overlay** (all of them drawn on one small chart, lined up at the entry, in units of risk, so the common shape is visible at a glance and the odd one out stands apart), and the proof.

### Worked example (invented numbers)

**The pattern.** 12 losses. All were closed by their stop. In all 12, at the tick that hit the stop, the spread was at least three times its 10-minute median, and the middle price (half-way between bid and ask) was still short of the stop. In 11 of 12 the spread was back to normal within 20 seconds.

**The name.** Stopped by the spread.

**The proof a sceptical EA maker would accept:**
1. Each of the 12 opens on the chart at the stop tick. He sees the ask line jump to the stop while the bid barely moves, and the two lines closing again seconds later.
2. For each: the stop price, the ask at that tick, the middle price at that tick, the spread at that tick and its 10-minute median, side by side.
3. The what-if, trade by trade, replayed on the same ticks with the spread at its median: 9 would have reached their target, 2 would have been stopped later anyway, 1 would have closed near zero.
4. The check against winners: during the same run 31 trades were open during such a jump; 12 were stopped by it and 19 were not.
5. The same 12 trades in "MT4 says" (fixed spread): none of them was stopped at that tick. This is the difference the software exists to show.

If point 2 did not hold (the middle price itself reached the stop), the tool would not use this name: the price hit the stop, the spread did not.

### Groups without a name (later)
For losses under "No reason found", the tool may point out a group that shares circumstances ("23 of these opened within five minutes after the daily break") **without naming it**. The expert decides whether it is a type and names it; one sentence to his AI assistant turns it into a file. To avoid seeing patterns in noise, a group is shown only if it has at least 15 losses, appears in both halves of the run, and trades in that circumstance really do worse than the rest, winners included **(all guesses)**.

## 7. The numbers on each type

| Column | Meaning |
|---|---|
| Losses | How many losses have this type as the main reason |
| Money | Their total |
| % of loss | Share of the run's total loss |
| Typical | The middle loss (median) |
| Usual range | The middle half of the losses, from smaller to larger |
| Worst | The biggest single loss |
| Top 3 | Share of the type's money that comes from its three biggest losses |
| Days | On how many different days it happened |
| Both halves | "Steady" if it shows in both halves of the run, otherwise which half |
| Also in | Grey. Other losses where it counted as an extra reason |
| With the fix | For types proved on the trade: the total these same trades would have made under the what-if. Labelled "these trades only" |
| Same situation | For types proved over the run: all trades in that circumstance, how many won, and their net result |
| By month | A small bar per month |

Standard deviation is available as an optional column, off by default. It is a poor fit here: losses pile up near the stop size with a few far out, so the figure is mostly those few, and it assumes a symmetry losses do not have.

**Numbers that lie when a type has few losses, and what the screen does:**
- Under 5 losses: only Losses and Money are shown; the losses themselves are the summary. Everything else is blank, with "too few".
- 5 to 19 losses: Typical, smallest and largest, Days. No Usual range, no Top 3, no By month, no Both halves.
- 20 and more: everything.
- The numbers that mislead most on few losses: the average (one big loss moves it), standard deviation, any percentage or month-by-month trend, and "how many won in the same situation". The count is always printed beside them.

## 8. What the tool refuses to call a reason

- Anything known only afterwards: "price went against it", "wrong direction", "bought the top".
- A circumstance that winners share just as much. If trades at that hour win as often as others, the hour is not a reason.
- A rule that matched but is not worth money (below the gate).
- Anything the data cannot show: intent ("the broker hunted the stop": we show the jump, not a motive), real slippage or requotes (not in a backtest), news with no calendar loaded.
- What the EA "meant", unless the EA says so in a decision log or the expert states it in the EA's profile.
- A feeling. Types are named by what happened ("opened again within 3 minutes after a stop"), not "revenge" or "greed".
- A pattern from a handful of trades, or one that appears in only half the run.
- Any reason at all when the run did not match the ticks.

## 9. Ideas added by the Lead (all inside this problem)

1. **Shape on every loss**, so even "No reason found" says something true.
2. **The overlay** of all losses of a type on one small chart.
3. **The check against winners** on every type.
4. **"Only on real spreads" mark** on losses that MT4's fixed-spread run shows as a win or a smaller loss.
5. **Agree / Not this.** Two buttons in the Why box. The expert's verdict is stored on his PC only, shown on the row, and counted per type ("agreed 41 of 46"). A type he often rejects is flagged as needing work. This is how the thresholds get tuned and how the tool earns trust.
6. **Both halves** check on every type.
7. **Groups without a name**, as in section 6.

## 10. Spec

**Loss types table (left).** Rows: one per type that is switched on or has losses, then "No reason found", then "Not judged" (only if not zero), then a total row. Types with no losses sit at the bottom in grey with 0, so he knows they were checked. A type that could not be checked says why ("needs the EA's journal", "needs a calendar"). Columns: tick box · Pattern · Name · Losses · Money · % of loss · Typical · Usual range · Worst · Top 3 · Days · Both halves · Also in · With the fix / Same situation · By month. Default sort: Money, biggest first. Click a header to sort, as in MT4.

**Losses table (right).** Rows: every losing trade (result after costs below zero) of the run, or of the selected type. Columns: Ticket · Open time · Type · Size · Open price · S/L · T/P · Close time · Close price · Commission · Swap · Loss · In risk units · Shape · Main reason (score) · Other reasons (scores) · marks (only on real spreads, 1 switched off, agreed/rejected). Default sort: Loss, biggest first. A total line at the bottom, as in account history.

**Which result:** "with real spreads" by default, switchable to "MT4 says" (D-19).

**Keys and mouse** (final keys are set against the real MT4 at design time): click a loss, the chart goes to it; up and down move through losses with the chart following; double-click starts replay shortly before the entry; one key for next loss of the same type; space toggles the selected type; right-click menus hold Hide, Show all, Save view.

**Empty states.**
- No losing trades: "No losing trades in this run (N trades)."
- Run did not match the ticks: the list shows every loss with its money, all "Not judged", with the cause on top.
- All types switched off: every loss is under "No reason found", with the line "All loss types are switched off."
- Everything hidden: "All N losses are hidden. Show all."

## 11. What this changes in the build

- The detector contract (D-8) gains two required parts for a loss type: the one-sentence what-if, and the money it saves, with its own test (a hand-computed case).
- Stored per loss: its shape, and every matched type with `saved`, `score` and kind, so switches work without a new run.
- Order of building: (1) the list of losses with money and shape, which is always right; (2) five types proved on the trade, with their what-ifs; (3) types proved over the run; (4) switches, saved views and the numbers; (5) the overlay; (6) Agree / Not this; (7) groups without a name.

## 12. What we are not seeing

- **No real trades yet.** Every threshold here is a guess until the reference EA's run, and then the expert's, are on the screen.
- **Baskets.** If an EA manages several orders as one position (grid, averaging, martingale), "a loss" is the basket, not the ticket. This design is per trade. Question for the expert: does any of his EAs do this?
- **What-ifs that need the EA to decide again.** If the trade would have continued, we assume its stop and target stay put. For an EA with a trailing stop that is only approximately true; the screen says so, and layer 2 (D-19) is what makes it exact.
- **"With the fix" covers the losing trades only.** A wider stop also changes other trades. The honest whole-run figure comes with the what-if lab; until then the column is labelled "these trades only".
- **Sizing.** If the size changes from trade to trade, money ranks by size as much as by fault. The "In risk units" column is there for that.
- **The risk of looking smarter than we are.** The measure of this feature is not how few losses are under "No reason found". It is how often the expert agrees.

## 13. Next

1. Build in the order of section 11, starting with the reference EA's run.
2. **A blind test with the expert** on his first real run: he labels 50 to 100 losses by hand before seeing ours; then the two are compared. Disagreements tune the gate and show which types are missing or wrong.
