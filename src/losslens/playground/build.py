"""Read a tick window and write one self-contained Playground HTML file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

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
    dataset_id = _dataset_id(symbol, day, start_label, end_label, count, first_ts, last_ts)
    payload: dict[str, object] = {
        "datasetId": dataset_id,
        "symbol": symbol,
        "day": day.isoformat(),
        "window": {"from": start_label, "to": end_label},
        "fromMs": from_ms,
        "toMs": to_ms,
        "contractSize": CONTRACT_SIZE,
        "startBalance": START_BALANCE,
        "tickCount": count,
        "firstTick": ticks[0],
        "lastTick": ticks[-1],
        "ticks": ticks,
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
    )


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
