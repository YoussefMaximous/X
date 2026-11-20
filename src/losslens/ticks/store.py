"""Tick store: Parquet day files, manifest and the one read function."""

from __future__ import annotations

import json
import os
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from losslens import __version__

DAY_MS = 86_400_000
EPOCH_DATE = date(1970, 1, 1)
DEFAULT_DATA_ROOT = Path("data")

SCHEMA = pa.schema(
    [
        pa.field("ts_ms", pa.int64()),
        pa.field("bid", pa.float64()),
        pa.field("ask", pa.float64()),
        pa.field("bid_vol", pa.float32()),
        pa.field("ask_vol", pa.float32()),
    ]
)

DONE_STATUSES = ("complete", "empty", "imported")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def empty_table() -> pa.Table:
    return SCHEMA.empty_table()


def normalise(table: pa.Table) -> pa.Table:
    """Return the table in storage-contract shape, sorted stably by ts_ms."""
    n = table.num_rows
    for name in ("ts_ms", "bid", "ask"):
        if name not in table.column_names:
            raise ValueError(f"missing required column: {name}")

    bid_vol = table["bid_vol"] if "bid_vol" in table.column_names else pa.array([0] * n, pa.float32())
    ask_vol = table["ask_vol"] if "ask_vol" in table.column_names else pa.array([0] * n, pa.float32())

    shaped = pa.table(
        {
            "ts_ms": pc.cast(table["ts_ms"], pa.int64()),
            "bid": pc.cast(table["bid"], pa.float64()),
            "ask": pc.cast(table["ask"], pa.float64()),
            "bid_vol": pc.cast(bid_vol, pa.float32()),
            "ask_vol": pc.cast(ask_vol, pa.float32()),
        }
    )

    if n > 1:
        shaped = shaped.append_column("_row", pa.array(range(n), pa.int64()))
        shaped = shaped.sort_by([("ts_ms", "ascending"), ("_row", "ascending")])
        shaped = shaped.drop_columns(["_row"])
    return shaped


def classify_status(fetched_at: datetime, day: date, ticks: int) -> str:
    """Apply the manifest status rule for a freshly fetched UTC day."""
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    day_end = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1)
    if fetched_at >= day_end + timedelta(hours=6):
        return "complete" if ticks > 0 else "empty"
    return "partial"


def make_entry(
    day: date,
    status: str,
    ticks: int,
    first_ts_ms: int | None,
    last_ts_ms: int | None,
    source: str,
    fetched_at: datetime,
) -> dict[str, Any]:
    return {
        "date": day.isoformat(),
        "status": status,
        "ticks": ticks,
        "first_ts_ms": first_ts_ms,
        "last_ts_ms": last_ts_ms,
        "source": source,
        "fetched_at_utc": fetched_at.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "tool_version": __version__,
    }


def iso_utc(ms: int) -> str:
    return (
        (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=int(ms)))
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def day_from_ms(ms: int) -> date:
    return EPOCH_DATE + timedelta(days=int(ms) // DAY_MS)


def _row_bounds(table: pa.Table, from_ms: int, to_ms: int) -> tuple[int, int]:
    """Return [lo, hi) row indices by binary search on the sorted ts_ms column."""
    column = table["ts_ms"].combine_chunks()
    if isinstance(column, pa.ChunkedArray):
        column = column.chunk(0)
    if column.null_count == 0 and column.offset == 0:
        values = memoryview(column.buffers()[1]).cast("q")
    else:  # pragma: no cover - contract says sorted, non-null int64
        values = column.to_pylist()
    return bisect_left(values, from_ms), bisect_left(values, to_ms)


@dataclass
class TickStore:
    root: Path = DEFAULT_DATA_ROOT
    symbol: str = "XAUUSD"

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.symbol_dir = self.root / "ticks" / self.symbol
        self.manifest_path = self.symbol_dir / "manifest.json"

    def day_path(self, day: date) -> Path:
        return self.symbol_dir / f"{day.year:04d}" / f"{day.isoformat()}.parquet"

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"symbol": self.symbol, "days": {}}
        with self.manifest_path.open("r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        manifest.setdefault("symbol", self.symbol)
        manifest.setdefault("days", {})
        return manifest

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        self.symbol_dir.mkdir(parents=True, exist_ok=True)
        data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        _atomic_write_text(self.manifest_path, data)

    def write_day(self, day: date, table: pa.Table) -> Path:
        path = self.day_path(day)
        path.parent.mkdir(parents=True, exist_ok=True)
        shaped = normalise(table)
        tmp = path.with_name(path.name + ".tmp")
        try:
            pq.write_table(shaped, tmp, compression="zstd")
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                tmp.unlink()
        return path

    def read_day(self, day: date) -> pa.Table | None:
        path = self.day_path(day)
        if not path.exists():
            return None
        # ParquetFile.read avoids the expensive dataset/filesystem setup that
        # pq.read_table pays on its first call in a fresh process.
        table = pq.ParquetFile(path).read(columns=SCHEMA.names)
        return table.select(SCHEMA.names)

    def delete_day(self, day: date) -> None:
        path = self.day_path(day)
        if path.exists():
            path.unlink()

    def read_ticks(self, from_ms: int, to_ms: int) -> pa.Table:
        if to_ms <= from_ms:
            return empty_table()
        first = int(from_ms) // DAY_MS
        last = (int(to_ms) - 1) // DAY_MS
        parts: list[pa.Table] = []
        for day_number in range(first, last + 1):
            table = self.read_day(EPOCH_DATE + timedelta(days=day_number))
            if table is None or table.num_rows == 0:
                continue
            lo, hi = _row_bounds(table, from_ms, to_ms)
            if hi > lo:
                parts.append(table.slice(lo, hi - lo))
        if not parts:
            return empty_table()
        return pa.concat_tables(parts)

    def manifest_days(self) -> dict[str, dict[str, Any]]:
        return self.load_manifest().get("days", {})


def read_ticks(symbol: str, from_ms: int, to_ms: int) -> pa.Table:
    """The one read function every later part uses."""
    return TickStore(DEFAULT_DATA_ROOT, symbol).read_ticks(from_ms, to_ms)


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
