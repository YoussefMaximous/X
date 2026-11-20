"""Generic CSV import into the tick store."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

from .store import DAY_MS, TickStore, day_from_ms, make_entry, normalise, utc_now

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class CsvImportError(ValueError):
    """A CSV could not be imported as ticks."""


def import_csv(
    store: TickStore,
    csv_path: Path,
    ts_col: str,
    bid_col: str,
    ask_col: str,
    bid_vol_col: str | None = None,
    ask_vol_col: str | None = None,
    ts_format: str = "epoch_ms",
    utc_offset_minutes: int = 0,
) -> dict[str, Any]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise CsvImportError(f"file not found: {csv_path}")

    table = pacsv.read_csv(csv_path)
    missing = [name for name in (ts_col, bid_col, ask_col) if name not in table.column_names]
    if missing:
        raise CsvImportError(f"CSV is missing columns: {missing}")

    ts_ms = _to_epoch_ms(table[ts_col], ts_format, utc_offset_minutes)

    def price(name: str) -> pa.Array:
        column = pc.cast(table[name], pa.float64())
        if pc.any(pc.is_null(column)).as_py():
            raise CsvImportError(f"column {name!r} contains empty or non-numeric values")
        return column

    bid = price(bid_col)
    ask = price(ask_col)
    n = len(ts_ms)

    def volume(name: str | None) -> pa.Array:
        if not name:
            return pa.array([0] * n, pa.float32())
        if name not in table.column_names:
            raise CsvImportError(f"CSV is missing column: {name}")
        column = pc.cast(table[name], pa.float32())
        if pc.any(pc.is_null(column)).as_py():
            raise CsvImportError(f"column {name!r} contains empty or non-numeric values")
        return column

    shaped = normalise(
        pa.table(
            {
                "ts_ms": ts_ms,
                "bid": bid,
                "ask": ask,
                "bid_vol": volume(bid_vol_col),
                "ask_vol": volume(ask_vol_col),
            }
        )
    )

    ts_values = shaped["ts_ms"]
    day_numbers = pc.unique(pc.divide(ts_values, DAY_MS)).to_pylist()
    day_numbers = sorted(int(value) for value in day_numbers)

    manifest = store.load_manifest()
    fetched_at = utc_now()
    source = f"import:{csv_path.name}"
    written: dict[str, int] = {}

    for day_number in day_numbers:
        day_start = day_number * DAY_MS
        day_end = day_start + DAY_MS
        mask = pc.and_(
            pc.greater_equal(ts_values, day_start), pc.less(ts_values, day_end)
        )
        part = shaped.filter(mask)
        if part.num_rows == 0:
            continue
        day = day_from_ms(day_start)
        store.write_day(day, part)
        entry = make_entry(
            day,
            "imported",
            part.num_rows,
            int(part["ts_ms"][0].as_py()),
            int(part["ts_ms"][-1].as_py()),
            source,
            fetched_at,
        )
        manifest.setdefault("days", {})[day.isoformat()] = entry
        store.save_manifest(manifest)
        written[day.isoformat()] = part.num_rows

    return {
        "symbol": store.symbol,
        "file": csv_path.name,
        "days": written,
        "total_ticks": sum(written.values()),
    }


def _to_epoch_ms(
    column: pa.ChunkedArray, ts_format: str, utc_offset_minutes: int
) -> pa.Array:
    offset_ms = int(utc_offset_minutes) * 60_000

    if ts_format == "iso":
        values = column.to_pylist()
        out: list[int] = []
        for value in values:
            if value is None:
                raise CsvImportError("timestamp column contains an empty value")
            if isinstance(value, datetime):
                dt = value
            else:
                text = str(value).strip()
                if not text:
                    raise CsvImportError("timestamp column contains an empty value")
                dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc) - timedelta(milliseconds=offset_ms)
            else:
                dt = dt.astimezone(timezone.utc)
            out.append((dt - EPOCH) // timedelta(milliseconds=1))
        return pa.array(out, pa.int64())

    if ts_format == "epoch_s":
        values = pc.cast(column, pa.float64())
        if pc.any(pc.is_null(values)).as_py():
            raise CsvImportError("timestamp column contains empty or non-numeric values")
        ms = pc.cast(pc.round(pc.multiply(values, 1000.0)), pa.int64())
        return pc.subtract(ms, offset_ms) if offset_ms else ms

    if ts_format == "epoch_ms":
        if pa.types.is_timestamp(column.type):
            ms = pc.cast(pc.cast(column, pa.timestamp("ms")), pa.int64())
        else:
            values = pc.cast(column, pa.float64())
            if pc.any(pc.is_null(values)).as_py():
                raise CsvImportError("timestamp column contains empty or non-numeric values")
            ms = pc.cast(pc.round(values), pa.int64())
        return pc.subtract(ms, offset_ms) if offset_ms else ms

    raise CsvImportError(f"unknown --ts-format: {ts_format}")
