"""Check that the trades in an MT4 report exist in the tick store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from losslens.ticks.store import TickStore

from .export import round_price, server_seconds
from .report import TesterReport, TesterTrade


class ReconcileError(RuntimeError):
    """A report trade cannot be placed against the stored ticks."""


@dataclass(frozen=True)
class TradeCheck:
    ticket: int
    close_time: str
    kind: str
    close_price: float
    found: bool
    tick_time_ms: int | None
    tick_price: float | None
    difference: float | None


@dataclass(frozen=True)
class ReconcileResult:
    checked: int
    found: int
    missing: int
    checks: tuple[TradeCheck, ...]

    @property
    def reconciled(self) -> bool:
        return self.checked == self.found


def _server_to_utc(server_epoch: int) -> int:
    for hours in (2, 3):
        candidate = server_epoch - hours * 3600
        if server_seconds(candidate) == server_epoch:
            return candidate
    raise ReconcileError(f"cannot map server time {server_epoch} to UTC")


def _server_window(text: str) -> tuple[int, int]:
    for shape, span in (("%Y.%m.%d %H:%M:%S", 1), ("%Y.%m.%d %H:%M", 60)):
        try:
            moment = datetime.strptime(text, shape)
        except ValueError:
            continue
        start = int(moment.replace(tzinfo=UTC).timestamp())
        return start, start + span
    raise ReconcileError(f"unreadable trade time {text!r}")


def _trade_check(store: TickStore, trade: TesterTrade) -> TradeCheck:
    server_start, server_end = _server_window(trade.close_time)
    utc_start = _server_to_utc(server_start)
    utc_end = _server_to_utc(server_end)
    table = store.read_ticks(utc_start * 1000, utc_end * 1000)
    column = "bid" if trade.kind.lower().startswith("buy") else "ask"
    for ts_ms, raw_price in zip(table["ts_ms"].to_pylist(), table[column].to_pylist(), strict=True):
        price = round_price(float(raw_price), 2)
        difference = abs(price - trade.close_price)
        if difference <= 0.005:
            return TradeCheck(
                ticket=trade.ticket,
                close_time=trade.close_time,
                kind=trade.kind,
                close_price=trade.close_price,
                found=True,
                tick_time_ms=int(ts_ms),
                tick_price=price,
                difference=difference,
            )
    return TradeCheck(
        ticket=trade.ticket,
        close_time=trade.close_time,
        kind=trade.kind,
        close_price=trade.close_price,
        found=False,
        tick_time_ms=None,
        tick_price=None,
        difference=None,
    )


def reconcile_trades(store: TickStore, report: TesterReport) -> ReconcileResult:
    checks = tuple(_trade_check(store, trade) for trade in report.trades)
    found = sum(1 for check in checks if check.found)
    return ReconcileResult(
        checked=len(checks),
        found=found,
        missing=len(checks) - found,
        checks=checks,
    )
