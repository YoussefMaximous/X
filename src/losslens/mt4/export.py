"""Write MT4 history files from the tick store."""

from __future__ import annotations

import math
import struct
import time
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path

import pyarrow as pa

from losslens.ticks.store import TickStore

COPYRIGHT = b"Copyright 2005-2025, MetaQuotes Ltd."
SYMBOL_DECIMALS = {"XAUUSD": 2}
HST_VERSION = 401
HST_HEADER_SIZE = 148
HST_RECORD_FORMAT = "<qddddqiq"
HST_RECORD_SIZE = 60


class ExportError(RuntimeError):
    """The export cannot be made safely or the data is not ready."""


def round_price(value: float, digits: int = 2) -> float:
    scale = 10**digits
    return math.copysign(math.floor(abs(value) * scale + 0.5) / scale, value)


def _nth_weekday(year: int, month: int, weekday: int, number: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (number - 1))


def _summer_bounds(year: int) -> tuple[datetime, datetime]:
    start_day = _nth_weekday(year, 3, 6, 2)
    end_day = _nth_weekday(year, 11, 6, 1)
    start = datetime.combine(start_day, clock_time(7, 0), tzinfo=UTC)
    end = datetime.combine(end_day, clock_time(6, 0), tzinfo=UTC)
    return start, end


def server_offset_seconds(utc_seconds: int) -> int:
    moment = datetime.fromtimestamp(utc_seconds, tz=UTC)
    start, end = _summer_bounds(moment.year)
    return 3 * 3600 if start <= moment < end else 2 * 3600


def server_seconds(utc_seconds: int) -> int:
    return utc_seconds + server_offset_seconds(utc_seconds)


def _ticks_of_day(store: TickStore, day: date, symbol: str) -> pa.Table:
    entry = store.load_manifest().get("days", {}).get(day.isoformat())
    if not entry or entry.get("status") != "complete":
        raise ExportError(f"{day.isoformat()} is not stored as complete")
    table = store.read_day(day)
    if table is None:
        raise ExportError(f"{day.isoformat()} has no file")
    return table


def _bars_for_table(
    table: pa.Table, digits: int
) -> list[tuple[int, float, float, float, float, int]]:
    bars: list[tuple[int, float, float, float, float, int]] = []
    current_minute: int | None = None
    open_price = high = low = close = 0.0
    volume = 0
    timestamps = table["ts_ms"].to_pylist()
    bids = table["bid"].to_pylist()
    for ts_ms, raw_bid in zip(timestamps, bids, strict=True):
        bid = round_price(float(raw_bid), digits)
        minute = int(ts_ms) // 60_000
        if current_minute is None:
            current_minute = minute
            open_price = high = low = close = bid
            volume = 1
        elif minute == current_minute:
            high = max(high, bid)
            low = min(low, bid)
            close = bid
            volume += 1
        else:
            bars.append(
                (
                    server_seconds(current_minute * 60),
                    open_price,
                    high,
                    low,
                    close,
                    volume,
                )
            )
            current_minute = minute
            open_price = high = low = close = bid
            volume = 1
    if current_minute is not None:
        bars.append(
            (
                server_seconds(current_minute * 60),
                open_price,
                high,
                low,
                close,
                volume,
            )
        )
    return bars


def hst_bytes(
    symbol: str, bars: list[tuple[int, float, float, float, float, int]], digits: int
) -> bytes:
    header = struct.pack("<i", HST_VERSION)
    header += COPYRIGHT.ljust(64, b"\0")[:64]
    header += symbol.encode("ascii").ljust(12, b"\0")[:12]
    header += struct.pack("<iiii", 1, digits, 0, 0)
    header += struct.pack("<13i", *([0] * 13))
    if len(header) != HST_HEADER_SIZE:
        raise ExportError("internal HST header size is wrong")
    records = b"".join(
        struct.pack(HST_RECORD_FORMAT, bar_time, open_price, high, low, close, volume, 0, 0)
        for bar_time, open_price, high, low, close, volume in bars
    )
    return header + records


def export_range(
    store: TickStore,
    copy_root: Path,
    symbol: str,
    from_day: date,
    to_day: date,
    *,
    no_fxt: bool,
) -> dict[str, object]:
    if not no_fxt:
        raise ExportError("the .fxt writer is not measured yet; use --no-fxt")
    digits = SYMBOL_DECIMALS.get(symbol.upper())
    if digits is None:
        raise ExportError(f"no decimals known for {symbol}")

    started = time.perf_counter()
    bars: list[tuple[int, float, float, float, float, int]] = []
    day = from_day
    while day <= to_day:
        bars.extend(_bars_for_table(_ticks_of_day(store, day, symbol), digits))
        day += timedelta(days=1)

    history = copy_root / "history" / "default"
    history.mkdir(parents=True, exist_ok=True)
    hst_path = history / f"{symbol.upper()}1.hst"
    hst_path.write_bytes(hst_bytes(symbol.upper(), bars, digits))
    return {
        "hst": hst_path,
        "bars": len(bars),
        "seconds": time.perf_counter() - started,
    }
