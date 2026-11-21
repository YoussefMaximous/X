"""Pure data and rules for the native X Playground."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

PERIODS: dict[str, dict[str, int | str]] = {
    "tick": {"kind": "tick", "label": "Tick line"},
    "t1": {"kind": "tickbar", "count": 1, "label": "1 tick / bar"},
    "t10": {"kind": "tickbar", "count": 10, "label": "10 ticks / bar"},
    "t100": {"kind": "tickbar", "count": 100, "label": "100 ticks / bar"},
    "t500": {"kind": "tickbar", "count": 500, "label": "500 ticks / bar"},
    "t1000": {"kind": "tickbar", "count": 1000, "label": "1,000 ticks / bar"},
    "m1": {"kind": "timebar", "ms": 60_000, "label": "1 minute"},
    "m5": {"kind": "timebar", "ms": 300_000, "label": "5 minutes"},
    "m15": {"kind": "timebar", "ms": 900_000, "label": "15 minutes"},
    "m30": {"kind": "timebar", "ms": 1_800_000, "label": "30 minutes"},
    "h1": {"kind": "timebar", "ms": 3_600_000, "label": "1 hour"},
}
PERIOD_ORDER = ("tick", "t1", "t10", "t100", "t500", "t1000", "m1", "m5", "m15", "m30", "h1")
START_BALANCE = 10_000.0
CONTRACT_SIZE = 100.0
DEFAULT_WARMUP_MS = 5 * 60 * 1000
MAX_CUSTOM_TICKS = 5_000


@dataclass(frozen=True)
class Tick:
    ts_ms: int
    bid: float
    ask: float


@dataclass(frozen=True)
class Bar:
    t: int
    o: float
    h: float
    lo: float
    c: float
    ac: float
    v: int
    first: int
    last: int


@dataclass
class Ticket:
    id: int
    side: str
    lots: float
    entry: float
    sl: float | None
    tp: float | None
    open_index: int
    status: str = "open"
    close_index: int | None = None
    close_price: float | None = None
    close_reason: str | None = None
    realized: float = 0.0


@dataclass
class Prediction:
    points: list[tuple[int, float]] = field(default_factory=list)
    anchor_index: int | None = None
    anchor_price: float | None = None


@dataclass
class Scenario:
    name: str
    tickets: list[Ticket] = field(default_factory=list)
    prediction: Prediction = field(default_factory=Prediction)


@dataclass(frozen=True)
class PredictionScore:
    point: tuple[int, float]
    actual: float
    error: float
    hit: bool


@dataclass(frozen=True)
class PredictionSummary:
    count: int
    mae: float | None
    hit_rate: float | None


@dataclass(frozen=True)
class ScenarioSummary:
    name: str
    equity: float
    max_drawdown: float
    tickets: int
    win_rate: float | None
    mae: float | None
    hit_rate: float | None


class PlaygroundModel:
    """Tick replay, tickets, predictions and the drawn future tape."""

    def __init__(
        self,
        ticks: Sequence[Tick],
        start_balance: float = START_BALANCE,
        contract_size: float = CONTRACT_SIZE,
        warmup_ms: int = DEFAULT_WARMUP_MS,
        start_ms: int | None = None,
    ) -> None:
        if not ticks:
            raise ValueError("no ticks")
        self.real_ticks = list(ticks)
        self.start_balance = start_balance
        self.contract_size = contract_size
        self._start_ms = start_ms
        self.custom_ticks: list[Tick] = []
        self.custom_branch: int | None = None
        self.custom_spread = 0.0
        self.period = "t100"
        self.grid_step = 0.10
        self.scenarios = [Scenario("Scenario 1")]
        self.active_index = 0
        self._ticket_seq = 0
        self._warmup_ms = warmup_ms
        self.cursor = self._start_cursor()
        self._bar_cache_key: tuple[str, int] | None = None
        self._bar_cache: list[Bar] = []

    def _start_cursor(self) -> int:
        base = self.real_ticks[0].ts_ms if self._start_ms is None else self._start_ms
        end = base + self._warmup_ms
        low = 0
        high = len(self.real_ticks) - 1
        found = 0
        while low <= high:
            mid = (low + high) // 2
            if self.real_ticks[mid].ts_ms <= end:
                found = mid
                low = mid + 1
            else:
                high = mid - 1
        return max(0, found)

    @property
    def ticks(self) -> list[Tick]:
        if self.custom_ticks and self.custom_branch is not None:
            return self.real_ticks[: self.custom_branch + 1] + self.custom_ticks
        return self.real_ticks

    @property
    def n(self) -> int:
        return len(self.ticks)

    def tick(self, index: int | None = None) -> Tick:
        return self.ticks[self.cursor if index is None else index]

    def index_at_or_after(self, ts_ms: int) -> int:
        """The first revealed tick at or after a timestamp, clamped to the tape."""
        low = 0
        high = self.n
        while low < high:
            mid = (low + high) // 2
            if self.ticks[mid].ts_ms < ts_ms:
                low = mid + 1
            else:
                high = mid
        return min(max(0, low), self.n - 1)

    def active(self) -> Scenario:
        return self.scenarios[self.active_index]

    def set_period(self, period: str) -> None:
        if period not in PERIODS:
            return
        self.period = period
        self._invalidate_bars()

    def _invalidate_bars(self) -> None:
        self._bar_cache_key = None
        self._bar_cache = []

    def bars(self) -> list[Bar]:
        spec = PERIODS[self.period]
        key = (self.period, self.cursor)
        if self._bar_cache_key == key:
            return self._bar_cache
        kind = str(spec["kind"])
        result: list[Bar] = []
        if kind == "tickbar":
            count = int(spec["count"])
            current: Bar | None = None
            for index in range(self.cursor + 1):
                tick = self.ticks[index]
                if current is None or current.v >= count:
                    current = Bar(
                        tick.ts_ms,
                        tick.bid,
                        tick.bid,
                        tick.bid,
                        tick.bid,
                        tick.ask,
                        1,
                        index,
                        index,
                    )
                    result.append(current)
                else:
                    current = Bar(
                        current.t,
                        current.o,
                        max(current.h, tick.bid),
                        min(current.lo, tick.bid),
                        tick.bid,
                        tick.ask,
                        current.v + 1,
                        current.first,
                        index,
                    )
                    result[-1] = current
        elif kind == "timebar":
            span = int(spec["ms"])
            current = None
            bucket = None
            for index in range(self.cursor + 1):
                tick = self.ticks[index]
                key_time = tick.ts_ms // span * span
                if current is None or key_time != bucket:
                    current = Bar(
                        key_time, tick.bid, tick.bid, tick.bid, tick.bid, tick.ask, 1, index, index
                    )
                    bucket = key_time
                    result.append(current)
                else:
                    current = Bar(
                        current.t,
                        current.o,
                        max(current.h, tick.bid),
                        min(current.lo, tick.bid),
                        tick.bid,
                        tick.ask,
                        current.v + 1,
                        current.first,
                        index,
                    )
                    result[-1] = current
        self._bar_cache_key = key
        self._bar_cache = result
        return result

    def series_length(self) -> int:
        return self.cursor + 1 if self.period == "tick" else len(self.bars())

    def bar_index_for_tick(self, tick_index: int) -> float:
        if self.period == "tick":
            return float(tick_index)
        spec = PERIODS[self.period]
        kind = str(spec["kind"])
        if kind == "tickbar":
            return float(tick_index // int(spec["count"]))
        bars = self.bars()
        if not bars:
            return 0.0
        if tick_index > bars[-1].last:
            span = int(spec["ms"])
            return len(bars) - 1 + (self.ticks[tick_index].ts_ms - bars[-1].t) / span
        low = 0
        high = len(bars) - 1
        found = 0
        while low <= high:
            mid = (low + high) // 2
            if bars[mid].first <= tick_index:
                found = mid
                low = mid + 1
            else:
                high = mid - 1
        return float(found)

    def custom_preview(self) -> list[tuple[int, Tick]]:
        if not self.custom_ticks or self.custom_branch is None:
            return []
        out: list[tuple[int, Tick]] = []
        start = self.custom_branch + 1
        for offset, tick in enumerate(self.custom_ticks):
            index = start + offset
            if index > self.cursor:
                out.append((index, tick))
        return out

    def custom_end_index(self) -> int:
        if self.custom_ticks:
            return self.n - 1
        return self.custom_branch if self.custom_branch is not None else self.cursor

    def set_custom_branch(self) -> None:
        if self.custom_branch is None:
            self.custom_branch = self.cursor
            self.custom_spread = max(0.0, self.tick().ask - self.tick().bid)

    def add_custom_ticks(self, target_index: int, target_bid: float) -> None:
        self.set_custom_branch()
        end = self.custom_end_index()
        if target_index <= end:
            return
        branch = self.custom_branch
        if branch is None:
            return
        last = self.custom_ticks[-1] if self.custom_ticks else self.real_ticks[branch]
        total = min(target_index - end, MAX_CUSTOM_TICKS - len(self.custom_ticks))
        if total <= 0:
            return
        for step in range(1, total + 1):
            fraction = step / total
            bid = last.bid + (target_bid - last.bid) * fraction
            ts = last.ts_ms + step * 250
            self.custom_ticks.append(Tick(ts, round(bid, 6), round(bid + self.custom_spread, 6)))
        self._invalidate_bars()

    def clear_custom(self) -> None:
        branch = self.custom_branch
        self.custom_ticks = []
        self.custom_branch = None
        self.custom_spread = 0.0
        if branch is not None:
            self.cursor = min(branch, len(self.real_ticks) - 1)
        else:
            self.cursor = min(self.cursor, len(self.real_ticks) - 1)
        self._invalidate_bars()
        for scenario in self.scenarios:
            scenario.tickets = []
            scenario.prediction = Prediction()

    def advance(self, count: int) -> int:
        target = min(self.n - 1, self.cursor + count)
        if target == self.cursor:
            return 0
        old = self.cursor
        for index in range(old + 1, target + 1):
            tick = self.ticks[index]
            for scenario in self.scenarios:
                for ticket in scenario.tickets:
                    if ticket.status == "open":
                        self._check_stops(ticket, tick, index)
        self.cursor = target
        self._invalidate_bars()
        closed = sum(
            1
            for scenario in self.scenarios
            for ticket in scenario.tickets
            if ticket.status == "closed"
            and ticket.close_index is not None
            and old < ticket.close_index <= target
        )
        return closed

    def run_to_end(self) -> None:
        self.advance(self.n - 1 - self.cursor)

    def next_bar(self) -> int:
        if self.period == "tick":
            return self.advance(10)
        spec = PERIODS[self.period]
        kind = str(spec["kind"])
        if kind == "tickbar":
            count = int(spec["count"])
            complete = (self.cursor + 1) % count
            return self.advance(count if complete == 0 else count - complete)
        span = int(spec["ms"])
        bucket = self.tick().ts_ms // span * span
        target_time = bucket + span
        low = 0
        high = self.n
        while low < high:
            mid = (low + high) // 2
            if self.ticks[mid].ts_ms < target_time:
                low = mid + 1
            else:
                high = mid
        target = low - 1
        if target <= self.cursor:
            target_time += span
            low = 0
            high = self.n
            while low < high:
                mid = (low + high) // 2
                if self.ticks[mid].ts_ms < target_time:
                    low = mid + 1
                else:
                    high = mid
            target = low - 1
        return self.advance(target - self.cursor)

    def reset(self) -> None:
        self.cursor = self._start_cursor()
        self._invalidate_bars()
        for scenario in self.scenarios:
            scenario.tickets = []
            scenario.prediction = Prediction()

    def open_ticket(
        self,
        side: str,
        lots: float,
        sl: float | None,
        tp: float | None,
    ) -> Ticket:
        if side not in ("buy", "sell"):
            raise ValueError("side must be buy or sell")
        if lots <= 0:
            raise ValueError("volume must be positive")
        tick = self.tick()
        entry = tick.ask if side == "buy" else tick.bid
        if sl is not None:
            if side == "buy" and sl >= entry:
                raise ValueError("a buy needs S/L below its ask entry")
            if side == "sell" and sl <= entry:
                raise ValueError("a sell needs S/L above its bid entry")
        if tp is not None:
            if side == "buy" and tp <= entry:
                raise ValueError("a buy needs T/P above its ask entry")
            if side == "sell" and tp >= entry:
                raise ValueError("a sell needs T/P below its bid entry")
        self._ticket_seq += 1
        ticket = Ticket(self._ticket_seq, side, lots, entry, sl, tp, self.cursor)
        scenario = self.active()
        scenario.tickets.append(ticket)
        self._check_stops(ticket, tick, self.cursor)
        return ticket

    def close_ticket(self, ticket_id: int) -> Ticket | None:
        for ticket in self.active().tickets:
            if ticket.id == ticket_id and ticket.status == "open":
                price = self.tick().bid if ticket.side == "buy" else self.tick().ask
                self._settle(ticket, price, "manual", self.cursor)
                return ticket
        return None

    def _check_stops(self, ticket: Ticket, tick: Tick, index: int) -> None:
        if ticket.side == "buy":
            if ticket.sl is not None and tick.bid <= ticket.sl:
                self._settle(ticket, ticket.sl, "S/L", index)
            elif ticket.tp is not None and tick.bid >= ticket.tp:
                self._settle(ticket, ticket.tp, "T/P", index)
        else:
            if ticket.sl is not None and tick.ask >= ticket.sl:
                self._settle(ticket, ticket.sl, "S/L", index)
            elif ticket.tp is not None and tick.ask <= ticket.tp:
                self._settle(ticket, ticket.tp, "T/P", index)

    def _settle(self, ticket: Ticket, price: float, reason: str, index: int) -> None:
        ticket.status = "closed"
        ticket.close_index = index
        ticket.close_price = price
        ticket.close_reason = reason
        ticket.realized = self.ticket_pnl(ticket, price)

    def ticket_pnl(self, ticket: Ticket, exit_price: float) -> float:
        direction = 1.0 if ticket.side == "buy" else -1.0
        return (exit_price - ticket.entry) * direction * ticket.lots * self.contract_size

    def floating(self, scenario: Scenario | None = None) -> float:
        scenario = scenario or self.active()
        tick = self.tick()
        total = 0.0
        for ticket in scenario.tickets:
            if ticket.status == "open":
                total += self.ticket_pnl(ticket, tick.bid if ticket.side == "buy" else tick.ask)
        return total

    def balance(self, scenario: Scenario | None = None) -> float:
        scenario = scenario or self.active()
        return self.start_balance + sum(
            ticket.realized for ticket in scenario.tickets if ticket.status == "closed"
        )

    def equity(self, scenario: Scenario | None = None) -> float:
        scenario = scenario or self.active()
        return self.balance(scenario) + self.floating(scenario)

    def add_prediction(self, index: int, price: float) -> None:
        if self.cursor >= self.n - 1:
            raise ValueError("the cursor is at the last tick")
        target = max(self.cursor + 1, min(index, self.n - 1))
        prediction = self.active().prediction
        if prediction.anchor_index is None:
            prediction.anchor_index = self.cursor
            prediction.anchor_price = self.tick().bid
        prediction.points = [(i, p) for i, p in prediction.points if i != target]
        prediction.points.append((target, price))
        prediction.points.sort()

    def undo_prediction(self) -> None:
        prediction = self.active().prediction
        if prediction.points:
            prediction.points.pop()
            if not prediction.points:
                prediction.anchor_index = None
                prediction.anchor_price = None

    def clear_prediction(self) -> None:
        self.active().prediction = Prediction()

    def scored(self) -> list[PredictionScore]:
        prediction = self.active().prediction
        out: list[PredictionScore] = []
        anchor = prediction.anchor_index or 0
        for position, (index, price) in enumerate(prediction.points):
            if index > self.cursor:
                break
            previous = prediction.points[position - 1] if position else None
            previous_predicted = previous[1] if previous else prediction.anchor_price
            previous_actual = self.ticks[previous[0]].bid if previous else self.ticks[anchor].bid
            actual = self.ticks[index].bid
            base = previous_predicted if previous_predicted is not None else actual
            predicted_direction = (price > base) - (price < base)
            actual_direction = (actual > previous_actual) - (actual < previous_actual)
            out.append(
                PredictionScore(
                    (index, price),
                    actual,
                    abs(price - actual),
                    predicted_direction != 0 and predicted_direction == actual_direction,
                )
            )
        return out

    def prediction_summary(self, scenario: Scenario | None = None) -> PredictionSummary:
        previous = self.active_index
        if scenario is not None:
            self.active_index = self.scenarios.index(scenario)
        try:
            scored = self.scored()
        finally:
            self.active_index = previous
        if not scored:
            return PredictionSummary(0, None, None)
        mae = sum(item.error for item in scored) / len(scored)
        hit_rate = sum(1 for item in scored if item.hit) / len(scored)
        return PredictionSummary(len(scored), mae, hit_rate)

    def ticket_stats(self, scenario: Scenario | None = None) -> tuple[int, float | None]:
        scenario = scenario or self.active()
        closed = [ticket for ticket in scenario.tickets if ticket.status == "closed"]
        if not closed:
            return len(scenario.tickets), None
        wins = sum(1 for ticket in closed if ticket.realized > 0)
        return len(scenario.tickets), wins / len(closed)

    def max_drawdown(self, scenario: Scenario | None = None) -> float:
        scenario = scenario or self.active()
        peak = self.start_balance
        worst = 0.0
        for index in range(self.n):
            tick = self.ticks[index]
            realized = 0.0
            floating = 0.0
            for ticket in scenario.tickets:
                if ticket.status == "closed" and ticket.close_index is not None:
                    if ticket.close_index <= index:
                        realized += ticket.realized
                    else:
                        floating += self.ticket_pnl(
                            ticket, tick.bid if ticket.side == "buy" else tick.ask
                        )
                elif ticket.open_index <= index:
                    floating += self.ticket_pnl(
                        ticket, tick.bid if ticket.side == "buy" else tick.ask
                    )
            equity = self.start_balance + realized + floating
            peak = max(peak, equity)
            worst = max(worst, peak - equity)
        return worst

    def summaries(self) -> list[ScenarioSummary]:
        rows: list[ScenarioSummary] = []
        for scenario in self.scenarios:
            tickets, win_rate = self.ticket_stats(scenario)
            prediction = self.prediction_summary(scenario)
            rows.append(
                ScenarioSummary(
                    scenario.name,
                    self.equity(scenario),
                    self.max_drawdown(scenario),
                    tickets,
                    win_rate,
                    prediction.mae,
                    prediction.hit_rate,
                )
            )
        rows.sort(key=lambda row: (-row.equity, row.name))
        return rows

    def add_scenario(self, name: str | None = None) -> Scenario:
        scenario = Scenario(name or f"Scenario {len(self.scenarios) + 1}")
        self.scenarios.append(scenario)
        self.active_index = len(self.scenarios) - 1
        return scenario

    def duplicate_scenario(self) -> Scenario:
        source = self.active()
        copy = Scenario(
            source.name + " copy",
            [
                Ticket(
                    ticket.id,
                    ticket.side,
                    ticket.lots,
                    ticket.entry,
                    ticket.sl,
                    ticket.tp,
                    ticket.open_index,
                    ticket.status,
                    ticket.close_index,
                    ticket.close_price,
                    ticket.close_reason,
                    ticket.realized,
                )
                for ticket in source.tickets
            ],
            Prediction(
                list(source.prediction.points),
                source.prediction.anchor_index,
                source.prediction.anchor_price,
            ),
        )
        self.scenarios.append(copy)
        self.active_index = len(self.scenarios) - 1
        return copy

    def delete_scenario(self) -> None:
        if len(self.scenarios) == 1:
            return
        self.scenarios.pop(self.active_index)
        self.active_index = max(0, self.active_index - 1)
