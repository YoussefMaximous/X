"""Read a tick window and write one self-contained Playground HTML file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from losslens.mt4 import export, presets, reconcile
from losslens.mt4 import report as mt4_report
from losslens.ticks.store import TickStore

from .page import render_page

DEFAULT_MAX_TICKS = 50_000
CONTRACT_SIZE = 100
START_BALANCE = 10_000
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class PlaygroundError(Exception):
    """A problem the command can print in plain words and stop on."""


@dataclass(frozen=True)
class PlaygroundResult:
    """What the build wrote, for the command line to print and tests to check."""

    path: Path
    ticks: int
    first_ts_ms: int
    last_ts_ms: int
    dataset_id: str
    bytes_written: int
    expert_inputs: int = 0
    expert_report_trades: int = 0
    expert_window_trades: int = 0


def minute_label(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def window_bounds(day: date, start_minutes: int, end_minutes: int) -> tuple[int, int]:
    """Return the UTC millisecond bounds of a same-day HH:MM window."""
    if not 0 <= start_minutes < end_minutes <= 24 * 60:
        raise PlaygroundError("--from must be before --to on the same UTC day")
    day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    from_dt = day_start + timedelta(minutes=start_minutes)
    to_dt = day_start + timedelta(minutes=end_minutes)
    return _milliseconds(from_dt), _milliseconds(to_dt)


def build_playground(
    store: TickStore,
    symbol: str,
    day: date,
    start_minutes: int,
    end_minutes: int,
    out: Path,
    max_ticks: int = DEFAULT_MAX_TICKS,
    inputs_path: Path | None = None,
    report_path: Path | None = None,
) -> PlaygroundResult:
    """Build the page from TickStore.read_ticks, capped before any work is done."""
    if max_ticks < 1:
        raise PlaygroundError("--max-ticks must be at least 1")
    from_ms, to_ms = window_bounds(day, start_minutes, end_minutes)
    table = store.read_ticks(from_ms, to_ms)
    count = table.num_rows
    start_label = minute_label(start_minutes)
    end_label = minute_label(end_minutes)
    if count == 0:
        raise PlaygroundError(
            f"no ticks for {symbol} between {day.isoformat()} {start_label} and "
            f"{end_label} UTC; choose another day or window"
        )
    if count > max_ticks:
        raise PlaygroundError(
            f"the window has {count} ticks, more than --max-ticks {max_ticks}; "
            "choose a shorter --from/--to window"
        )

    ticks = _rows(table)
    first_ts = int(ticks[0][0])
    last_ts = int(ticks[-1][0])
    digits = export.SYMBOL_DECIMALS.get(symbol.upper(), 2)
    dataset_id = _dataset_id(symbol, day, start_label, end_label, count, first_ts, last_ts)
    expert_inputs = _read_expert_inputs(inputs_path)
    expert_report, total_trades, window_trades = _read_expert_report(
        store, report_path, from_ms, to_ms
    )
    expert = _expert_payload(inputs_path, report_path, expert_inputs, expert_report)
    payload: dict[str, object] = {
        "datasetId": dataset_id,
        "symbol": symbol,
        "day": day.isoformat(),
        "window": {"from": start_label, "to": end_label},
        "fromMs": from_ms,
        "toMs": to_ms,
        "digits": digits,
        "contractSize": CONTRACT_SIZE,
        "startBalance": START_BALANCE,
        "tickCount": count,
        "firstTick": ticks[0],
        "lastTick": ticks[-1],
        "ticks": ticks,
        "expert": expert,
    }
    embedded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    embedded = embedded.replace("<", "\\u003c")
    html = render_page(embedded)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        os.replace(tmp, out)
    finally:
        if tmp.exists():
            tmp.unlink()

    return PlaygroundResult(
        path=out,
        ticks=count,
        first_ts_ms=first_ts,
        last_ts_ms=last_ts,
        dataset_id=dataset_id,
        bytes_written=out.stat().st_size,
        expert_inputs=len(expert_inputs),
        expert_report_trades=total_trades,
        expert_window_trades=window_trades,
    )


def _read_expert_inputs(path: Path | None) -> list[dict[str, str | None]]:
    if path is None:
        return []
    try:
        return [
            {
                "name": item.name,
                "value": item.value,
                "start": item.start,
                "step": item.step,
                "stop": item.stop,
            }
            for item in presets.read_inputs(path)
        ]
    except (presets.PresetError, OSError) as exc:
        raise PlaygroundError(f"cannot read expert inputs: {exc}") from exc


def _read_expert_report(
    store: TickStore,
    path: Path | None,
    from_ms: int,
    to_ms: int,
) -> tuple[dict[str, Any] | None, int, int]:
    if path is None:
        return None, 0, 0
    try:
        tester = mt4_report.parse_report(path)
    except (mt4_report.ReportError, OSError) as exc:
        raise PlaygroundError(f"cannot read expert report: {exc}") from exc

    server_from = _server_moment(from_ms // 1000)
    server_to = _server_moment((to_ms - 1) // 1000)
    ordered = sorted(tester.trades, key=lambda trade: _report_time(trade.close_time))
    window_start_balance = tester.initial_deposit
    window_trades = []
    for trade in ordered:
        trade_time = _report_time(trade.close_time)
        if trade_time < server_from:
            window_start_balance = trade.balance
        elif trade_time < server_to:
            window_trades.append(trade)
        else:
            break
    filtered = replace(tester, trades=tuple(window_trades))
    try:
        checks = reconcile.reconcile_trades(store, filtered)
    except (reconcile.ReconcileError, OSError) as exc:
        raise PlaygroundError(f"cannot read expert report: {exc}") from exc

    trades: list[dict[str, Any]] = []
    for trade, check in zip(window_trades, checks.checks, strict=True):
        trade_time = _report_time(trade.close_time)
        tick_time = check.tick_time_ms
        found = bool(check.found and tick_time is not None and from_ms <= tick_time < to_ms)
        close_utc_ms = _server_to_utc_seconds(int(trade_time.timestamp())) * 1000
        trades.append(
            {
                "ticket": trade.ticket,
                "closeTime": trade.close_time,
                "kind": trade.kind,
                "size": trade.size,
                "closePrice": trade.close_price,
                "profit": trade.profit,
                "balance": trade.balance,
                "closeTsMs": check.tick_time_ms,
                "closeUtcMs": close_utc_ms,
                "found": found,
                "inWindow": True,
            }
        )

    payload: dict[str, Any] = {
        "file": path.name,
        "expert": tester.expert,
        "symbol": tester.symbol,
        "period": tester.period,
        "model": tester.model,
        "initialDeposit": tester.initial_deposit,
        "totalNetProfit": tester.total_net_profit,
        "totalTrades": tester.total_trades,
        "windowStartBalance": window_start_balance,
        "windowTradeCount": len(trades),
        "foundWindowTrades": sum(1 for trade in trades if trade["found"]),
        "trades": trades,
    }
    return payload, len(tester.trades), len(trades)


def _expert_payload(
    inputs_path: Path | None,
    report_path: Path | None,
    inputs: list[dict[str, str | None]],
    report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if inputs_path is None and report_path is None:
        return None
    name = "Expert"
    if report is not None and report.get("expert"):
        name = str(report["expert"])
    elif inputs_path is not None:
        name = inputs_path.stem
    return {
        "name": name,
        "inputsFile": inputs_path.name if inputs_path is not None else None,
        "reportFile": report_path.name if report_path is not None else None,
        "inputs": inputs,
        "report": report,
    }


def _report_time(text: str) -> datetime:
    for shape in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(text, shape).replace(tzinfo=UTC)
        except ValueError:
            continue
    raise PlaygroundError(f"unreadable trade time in expert report: {text!r}")


def _server_moment(utc_seconds: int) -> datetime:
    offset = export.server_offset_seconds(utc_seconds)
    return datetime.fromtimestamp(utc_seconds + offset, tz=UTC)


def _server_to_utc_seconds(server_epoch: int) -> int:
    for hours in (2, 3):
        candidate = server_epoch - hours * 3600
        if export.server_offset_seconds(candidate) == hours * 3600:
            return candidate
    raise PlaygroundError(f"cannot map server time {server_epoch} to UTC")


def _rows(table: Any) -> list[list[float]]:
    rows = table.to_pylist()
    ticks: list[list[float]] = []
    for row in rows:
        ticks.append(
            [
                int(row["ts_ms"]),
                float(row["bid"]),
                float(row["ask"]),
            ]
        )
    return ticks


def _dataset_id(
    symbol: str,
    day: date,
    start_label: str,
    end_label: str,
    count: int,
    first_ts: int,
    last_ts: int,
) -> str:
    window = f"{start_label.replace(':', '')}-{end_label.replace(':', '')}"
    return f"{symbol}-{day.isoformat()}-{window}-{count}-{first_ts}-{last_ts}"


def _milliseconds(moment: datetime) -> int:
    return (moment - EPOCH) // timedelta(milliseconds=1)
