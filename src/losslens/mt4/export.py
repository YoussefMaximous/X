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
FXT_HEADER_SIZE = 728
FXT_RECORD_FORMAT = "<qddddqii"
FXT_RECORD_SIZE = 56
EPOCH_DATE = date(1970, 1, 1)

# The 728-byte header MT4 build 1492 wrote for XAUUSD M1, with the six fields
# below patched per export. Everything else is left as MT4 wrote it.
FXT_HEADER_HEX = """
95010000436f7079726967687420323030302d323032362c204d65746151756f
746573204c74642e000000000000000000000000000000000000000000000000
0000000049434d61726b65747353432d44656d6f303400000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
000000005841555553440000000000000100000000000000280500001058a669
c475a769000000002a419e12e42937405841550000000000000000001e000000
02000000000000007b14ae47e17a843f01000000102700000100000000000000
0100000000000000000000000000594000000000000000000000000000000000
00000000010000000000000000000000e5d022dbf94e48c09cc420b072884040
0300000088130000010000000000000032000000000000000000000000005940
00000000000000000000000000004940000000000000f03f5841550000000000
00000000000000000000000000001c4000000000000000000100000000000000
0000000000000000000000000000000000000000000000008024a6690076a769
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000
"""
FXT_HEADER_TEMPLATE = bytes.fromhex(FXT_HEADER_HEX)
if len(FXT_HEADER_TEMPLATE) != FXT_HEADER_SIZE:
    raise RuntimeError("measured FXT header template is not 728 bytes")


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


def date_range_seconds(from_day: date, to_day: date) -> tuple[int, int]:
    """The two FXT date fields: 00:00 UTC of --from and of the day after --to.

    The end is also the tick cutoff: broker midnight after the last test day,
    written as a server-clock timestamp.
    """
    start = (from_day - EPOCH_DATE).days * 86_400
    end = (to_day + timedelta(days=1) - EPOCH_DATE).days * 86_400
    return start, end


def _fxt_parts(
    table: pa.Table,
    digits: int,
    spread: int,
    header_template: bytes,
    *,
    cutoff: int | None = None,
) -> tuple[int, int, int, bytearray]:
    if len(header_template) != FXT_HEADER_SIZE:
        raise ExportError("FXT header template is not 728 bytes")
    records = bytearray()
    current_minute: int | None = None
    first_bar: int | None = None
    last_bar: int | None = None
    bars = 0
    open_price = high = low = close = 0.0
    volume = 0
    timestamps = table["ts_ms"].to_pylist()
    bids = table["bid"].to_pylist()
    for ts_ms, raw_bid in zip(timestamps, bids, strict=True):
        server = server_seconds(int(ts_ms) // 1000)
        if cutoff is not None and server >= cutoff:
            continue
        bid = round_price(float(raw_bid), digits)
        minute = server - (server % 60)
        if current_minute is None:
            current_minute = minute
            first_bar = minute
            bars = 1
            open_price = high = low = close = bid
            volume = 1
        elif minute == current_minute:
            high = max(high, bid)
            low = min(low, bid)
            close = bid
            volume += 1
        else:
            current_minute = minute
            bars += 1
            open_price = high = low = close = bid
            volume = 1
        records.extend(
            struct.pack(
                FXT_RECORD_FORMAT,
                current_minute,
                open_price,
                high,
                low,
                close,
                volume,
                server,
                0,
            )
        )
    if first_bar is None or current_minute is None:
        raise ExportError("cannot write an FXT with no ticks")
    last_bar = current_minute
    return bars, first_bar, last_bar, records


def build_fxt_for_table(
    table: pa.Table,
    spread: int,
    header_template: bytes = FXT_HEADER_TEMPLATE,
    digits: int = 2,
    from_day: date | None = None,
    to_day: date | None = None,
) -> bytes:
    start_seconds: int | None = None
    end_seconds: int | None = None
    if from_day is not None and to_day is not None:
        start_seconds, end_seconds = date_range_seconds(from_day, to_day)
    bars, first_bar, last_bar, records = _fxt_parts(
        table, digits, spread, header_template, cutoff=end_seconds
    )
    header = bytearray(header_template)
    struct.pack_into("<i", header, 216, bars)
    struct.pack_into("<i", header, 220, first_bar)
    struct.pack_into("<i", header, 224, last_bar)
    struct.pack_into("<i", header, 252, spread)
    if start_seconds is not None and end_seconds is not None:
        struct.pack_into("<i", header, 472, start_seconds)
        struct.pack_into("<i", header, 476, end_seconds)
    return bytes(header) + bytes(records)


def fxt_totals(store: TickStore, symbol: str, from_day: date, to_day: date) -> tuple[int, int]:
    """The number of FXT bars and records export_range would write."""
    digits = SYMBOL_DECIMALS.get(symbol.upper())
    if digits is None:
        raise ExportError(f"no decimals known for {symbol}")
    _, cutoff = date_range_seconds(from_day, to_day)
    bars = 0
    records = 0
    day = from_day
    while day <= to_day:
        table = _ticks_of_day(store, day, symbol)
        count, _, _, part = _fxt_parts(table, digits, 30, FXT_HEADER_TEMPLATE, cutoff=cutoff)
        bars += count
        records += len(part) // FXT_RECORD_SIZE
        day += timedelta(days=1)
    return bars, records


def export_range(
    store: TickStore,
    copy_root: Path,
    symbol: str,
    from_day: date,
    to_day: date,
    *,
    no_fxt: bool,
    spread: int = 30,
) -> dict[str, object]:
    digits = SYMBOL_DECIMALS.get(symbol.upper())
    if digits is None:
        raise ExportError(f"no decimals known for {symbol}")

    started = time.perf_counter()
    bars: list[tuple[int, float, float, float, float, int]] = []
    fxt_parts: list[bytearray] = []
    fxt_bars = 0
    fxt_records = 0
    fxt_first_bar = fxt_last_bar = 0
    start_seconds, end_seconds = date_range_seconds(from_day, to_day)
    day = from_day
    while day <= to_day:
        table = _ticks_of_day(store, day, symbol)
        bars.extend(_bars_for_table(table, digits))
        if not no_fxt:
            count, first_bar, last_bar, records = _fxt_parts(
                table, digits, spread, FXT_HEADER_TEMPLATE, cutoff=end_seconds
            )
            if not fxt_parts:
                fxt_first_bar = first_bar
            fxt_bars += count
            fxt_records += len(records) // FXT_RECORD_SIZE
            fxt_last_bar = last_bar
            fxt_parts.append(records)
        day += timedelta(days=1)

    history = copy_root / "history" / "default"
    history.mkdir(parents=True, exist_ok=True)
    hst_path = history / f"{symbol.upper()}1.hst"
    hst_path.write_bytes(hst_bytes(symbol.upper(), bars, digits))

    result: dict[str, object] = {
        "hst": hst_path,
        "bars": len(bars),
        "seconds": time.perf_counter() - started,
    }
    if not no_fxt:
        header = bytearray(FXT_HEADER_TEMPLATE)
        struct.pack_into("<i", header, 216, fxt_bars)
        struct.pack_into("<i", header, 220, fxt_first_bar)
        struct.pack_into("<i", header, 224, fxt_last_bar)
        struct.pack_into("<i", header, 252, spread)
        struct.pack_into("<i", header, 472, start_seconds)
        struct.pack_into("<i", header, 476, end_seconds)
        fxt_dir = copy_root / "tester" / "history"
        fxt_dir.mkdir(parents=True, exist_ok=True)
        fxt_path = fxt_dir / f"{symbol.upper()}1_0.fxt"
        if fxt_path.exists():
            fxt_path.chmod(0o666)
        fxt_path.write_bytes(bytes(header) + b"".join(fxt_parts))
        fxt_path.chmod(0o444)
        result["fxt"] = fxt_path
        result["fxt_records"] = fxt_records
    return result
