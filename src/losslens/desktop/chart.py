"""Pure chart data for the X desktop app."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime

from losslens.mt4 import export
from losslens.ticks.store import TickStore


class ChartError(RuntimeError):
    """The chart data cannot be loaded."""


@dataclass(frozen=True)
class Bar:
    t: int
    o: float
    h: float
    lo: float
    c: float
    v: int


@dataclass(frozen=True)
class ChartData:
    symbol: str
    day: date
    digits: int
    bid_bars: list[Bar]
    ask_bars: list[Bar]
    last_bid: float
    last_ask: float
    ticks: int
    offset_hours: int


def bars_from_rows(
    rows: Iterable[tuple[int, float, float, float, float, int]],
) -> list[Bar]:
    return [Bar(*row) for row in rows]


def aggregate(bars: list[Bar], minutes: int) -> list[Bar]:
    if minutes <= 1:
        return list(bars)
    span = minutes * 60
    out: list[Bar] = []
    current_key: int | None = None
    current: Bar | None = None
    for bar in bars:
        key = bar.t // span
        if current is None or key != current_key:
            if current is not None:
                out.append(current)
            current_key = key
            current = Bar(key * span, bar.o, bar.h, bar.lo, bar.c, bar.v)
        else:
            current = Bar(
                current.t,
                current.o,
                max(current.h, bar.h),
                min(current.lo, bar.lo),
                bar.c,
                current.v + bar.v,
            )
    if current is not None:
        out.append(current)
    return out


def price_text(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


def time_text(t: int, minutes: int) -> str:
    moment = datetime.fromtimestamp(t, tz=UTC)
    if minutes >= 1440:
        return moment.strftime("%d.%m")
    return moment.strftime("%H:%M")


def latest_day(symbol: str) -> date:
    store = TickStore(symbol=symbol)
    days = [
        day
        for day, entry in store.manifest_days().items()
        if entry.get("status") == "complete" and int(entry.get("ticks", 0)) > 0
    ]
    if not days:
        raise ChartError(f"no complete tick day for {symbol}")
    return date.fromisoformat(max(days))


def load_chart_data(symbol: str, day: date) -> ChartData:
    code = symbol.upper()
    store = TickStore(symbol=code)
    table = store.read_day(day)
    if table is None or table.num_rows == 0:
        raise ChartError(f"{day.isoformat()} has no stored ticks")
    digits = export.SYMBOL_PRECISION.get(code, 3)
    bid_bars = bars_from_rows(export._bars_for_table(table, digits))
    ask_bars = bars_from_rows(export._bars_for_table(table, digits, "ask"))
    if not bid_bars:
        raise ChartError(f"{day.isoformat()} has no bars")
    first_utc = int(table["ts_ms"][0].as_py()) // 1000
    return ChartData(
        symbol=code,
        day=day,
        digits=digits,
        bid_bars=bid_bars,
        ask_bars=ask_bars,
        last_bid=float(table["bid"][-1].as_py()),
        last_ask=float(table["ask"][-1].as_py()),
        ticks=table.num_rows,
        offset_hours=export.server_offset_seconds(first_utc) // 3600,
    )
