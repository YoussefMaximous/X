# Defect catalogue, version 1 (Lead-owned)

Updated: 2026-11-20. Draft list of loss reasons. Each row can become one detector file (contract in `ARCHITECTURE.md`). Thresholds shown are defaults; every one is a parameter the expert can change. The list is not fixed (D-24).

A defect is a reason a losing trade lost (D-23). One loss can have several reasons, or none (D-24). The rows below are a draft list, not a fixed set.

**Loss types (D-24).** Classifying why a trade lost is the core of the product, and it is hard. A loss can match several reasons, or none. How the screen shows that is not settled; it is the subject of the Fable checkpoint `2026-11-20-loss-types-screen.md`. The expert reviews this draft list after the software works (D-11).

**Level:** trade, basket (a group of orders managed together, as in a grid), run (a pattern across the whole test).
**Needs:** T = trades and ticks (always available) · J = MT4 tester journal · P = EA profile (a small file where the expert states what the EA is supposed to do: hours, max lot, max positions, risk per trade) · D = decision log (EAs with source) · C = news calendar.
R = initial risk (entry to stop). MFE / MAE = best / worst price reached during the trade, measured on the side the trade exits on.

## A. Entry

| ID | Level | What it catches | Needs |
|---|---|---|---|
| NEVER_IN_PROFIT | trade | Loss whose MFE stayed below 0.1R: wrong from the first tick | T |
| COUNTER_TREND | trade | Loss taken against the higher-timeframe trend | T |
| LATE_ENTRY | trade | Entered after most of the move was done (price already travelled more than X of the recent range in the trade's direction) | T |
| ENTRY_AT_EXTREME | trade | Bought within X of the session high, or sold within X of the session low, then lost | T |
| ENTRY_IN_SPREAD_SPIKE | trade | Entered while spread was above 3x its rolling median | T |
| ENTRY_IN_THIN_MARKET | trade | Entered within 30 minutes of the daily break or the weekend close | T |
| ENTRY_BEFORE_NEWS | trade | Entered within X minutes before a high-impact event | T, C |
| REVENGE_REENTRY | trade | Same direction re-entered within N minutes of a stop-out, and lost again | T |
| DUPLICATE_ENTRY | trade | Two or more orders opened at nearly the same price and time without being a declared grid | T, P |
| ENTRY_IN_DEAD_MARKET | trade | Entered when volatility was below the level where the target is reachable in normal holding time | T |

## B. Exit

| ID | Level | What it catches | Needs |
|---|---|---|---|
| GAVE_BACK | trade | MFE reached at least 0.5R, closed at a loss | T |
| STOP_TOO_TIGHT | trade | Stopped out, then price reached the original target within N minutes without going a further 1R against | T |
| STOP_TOO_WIDE | trade | Loss larger than N times the run's average win | T |
| MISSED_TARGET_BY_A_HAIR | trade | MFE reached 90% or more of the target distance, then the trade lost or closed for much less | T |
| HELD_TOO_LONG | trade | Loss held far longer than the run's typical winner | T |
| BREAKEVEN_KILLED_WINNER | trade | Stop moved to break-even, hit, then price reached the original target | T, J |
| TRAIL_CHOKED | trade | Trailing stop closed the trade within X of a pullback low/high before the move continued | T, J |
| STOP_WIDENED | trade | Stop moved further away from entry during the trade | J |
| NO_STOP | trade | Order ran without a stop loss | T |
| CLOSED_AT_SESSION_END_LOSS | trade | Closed by time (end of day, weekend) at a loss while not near its stop | T |

## C. Costs and execution

| ID | Level | What it catches | Needs |
|---|---|---|---|
| HIDDEN_LOSS | trade | Backtest winner that would have hit its stop first with the real bid/ask ticks | T |
| SPREAD_SPIKE_STOPOUT | trade | Stop hit only because spread widened; the other side of the book never reached it | T |
| GAP_THROUGH_STOP | trade | Filled worse than the stop by more than Y (daily break, weekend, news gap) | T |
| COSTS_ONLY_LOSS | trade | Gross result not negative, net result negative after commission and swap | T |
| SWAP_EATEN | trade | Swap charges were more than X of the trade's gross result | T |
| TARGET_TOO_SMALL_FOR_SPREAD | trade | Target distance below N times the spread at entry, and the trade lost | T |

## D. Risk and sizing

| ID | Level | What it catches | Needs |
|---|---|---|---|
| OVERSIZED | trade | Lot above 2x the run's median lot | T |
| MARTINGALE_ESCALATION | basket | Lot size grows after losses | T |
| RISK_ABOVE_LIMIT | trade | Money at risk above the declared percent of balance | T, P |
| EXPOSURE_STACKING | basket | Total open lots in one direction above the declared limit | T, P |
| MARGIN_DANGER | run | Margin level fell below X% at any moment | T |
| BASKET_DRAWDOWN | basket | Floating loss of a basket went beyond X% of balance | T |
| OUTSIZED_LOSS | trade | A single loss wiped out the previous N winners | T |
| HEDGED_BOTH_WAYS | basket | Long and short open together, paying spread twice | T |

## E. Patterns across the run

| ID | Level | What it catches | Needs |
|---|---|---|---|
| LOSS_STREAK | run | N or more consecutive losses | T |
| WHIPSAW | run | Three or more losses in alternating directions within 30 minutes | T |
| OVERTRADING | run | More trades in an hour or a day than the run's normal by a wide margin | T |
| DRAWDOWN_EPISODE | run | Each drawdown beyond X%: depth, length, recovery time, the trades inside it | T |
| TIME_OF_DAY_LEAK | run | An hour of the day that loses consistently | T |
| DAY_OF_WEEK_LEAK | run | A weekday that loses consistently | T |
| SESSION_LEAK | run | A session (Asia, London, New York, overlap) that loses consistently | T |
| VOLATILITY_REGIME_LEAK | run | Losses concentrated in very high or very low volatility | T |
| DIRECTION_BIAS | run | Longs or shorts lose consistently while the other side makes the profit | T |

## F. A rule of the EA caused the loss

| ID | Level | What it catches | Needs |
|---|---|---|---|
| OUTSIDE_TRADING_HOURS | trade | A loss that opened outside the declared hours | T, P |
| MAX_POSITIONS_EXCEEDED | run | Losses taken while more positions were open than declared | T, P |
