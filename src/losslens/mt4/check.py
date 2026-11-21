"""Compare the probe's recorded ticks with the tick store."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from losslens.ticks.store import TickStore

from .export import date_range_seconds, fxt_totals, round_price, server_seconds
from .report import TesterReport

PROBE_RECORD = struct.Struct("<qddqq")


@dataclass
class TickComparison:
    store_ticks: int
    probe_ticks: int
    skipped_start: int
    skipped_end: int
    time_differences: int
    bid_differences: int
    first_differences: list[tuple[dict[str, float], dict[str, float]]]
    min_spread: float | None
    max_spread: float | None
    identical: bool


@dataclass
class ReportComparison:
    report_ticks: int
    store_ticks: int
    report_bars: int
    store_bars: int
    identical: bool


def check_report(
    store: TickStore,
    report: TesterReport,
    symbol: str,
    from_day: date,
    to_day: date,
) -> ReportComparison:
    """Tell whether a tester report counted exactly the ticks we exported."""
    store_bars, store_ticks = fxt_totals(store, symbol, from_day, to_day)
    return ReportComparison(
        report_ticks=report.ticks_modelled,
        store_ticks=store_ticks,
        report_bars=report.bars,
        store_bars=store_bars,
        identical=report.ticks_modelled == store_ticks and report.bars == store_bars,
    )


def check_probe_ticks(
    store: TickStore, probe_file: Path, symbol: str, from_day: date, to_day: date
) -> TickComparison:
    store_rows: list[tuple[int, float]] = []
    _, cutoff = date_range_seconds(from_day, to_day)
    day = from_day
    while day <= to_day:
        table = store.read_day(day)
        if table is not None:
            for ts_ms, bid in zip(
                table["ts_ms"].to_pylist(), table["bid"].to_pylist(), strict=True
            ):
                utc_seconds = int(ts_ms) // 1000
                server = server_seconds(utc_seconds)
                if server >= cutoff:
                    continue
                store_rows.append((server, round_price(float(bid))))
        day += timedelta(days=1)

    raw = Path(probe_file).read_bytes()
    if len(raw) % PROBE_RECORD.size != 0:
        raise ValueError("probe tick file is not a whole number of 40-byte records")
    probe_rows = []
    spreads = []
    for offset in range(0, len(raw), PROBE_RECORD.size):
        tick_time, bid, ask, _volume, _bar_time = PROBE_RECORD.unpack_from(raw, offset)
        probe_rows.append((int(tick_time), round_price(float(bid))))
        spreads.append(float(ask) - float(bid))

    start = 0
    if probe_rows and store_rows:
        first_time = probe_rows[0][0]
        while start < len(store_rows) and store_rows[start][0] < first_time:
            start += 1

    compared = min(len(probe_rows), max(0, len(store_rows) - start))
    time_differences = 0
    bid_differences = 0
    first_differences: list[tuple[dict[str, float], dict[str, float]]] = []
    for index in range(compared):
        store_time, store_bid = store_rows[start + index]
        probe_time, probe_bid = probe_rows[index]
        if store_time != probe_time:
            time_differences += 1
        if store_bid != probe_bid:
            bid_differences += 1
        if (store_time, store_bid) != (probe_time, probe_bid) and len(first_differences) < 3:
            first_differences.append(
                (
                    {"time": store_time, "bid": store_bid},
                    {"time": probe_time, "bid": probe_bid},
                )
            )
    skipped_end = max(0, len(store_rows) - start - len(probe_rows))
    identical = (
        bool(probe_rows)
        and time_differences == 0
        and bid_differences == 0
        and len(probe_rows) <= max(0, len(store_rows) - start)
    )
    return TickComparison(
        store_ticks=len(store_rows),
        probe_ticks=len(probe_rows),
        skipped_start=start,
        skipped_end=skipped_end,
        time_differences=time_differences,
        bid_differences=bid_differences,
        first_differences=first_differences,
        min_spread=min(spreads) if spreads else None,
        max_spread=max(spreads) if spreads else None,
        identical=identical,
    )
