"""Per-day quality checks for the tick store."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pyarrow.compute as pc

from .store import DAY_MS, EPOCH_DATE, TickStore, iso_utc, utc_now

GAP_SECONDS = 300


def verify_symbol(
    store: TickStore, from_day: date | None = None, to_day: date | None = None
) -> dict[str, Any]:
    manifest = store.load_manifest()
    all_days = sorted(manifest.get("days", {}).items())
    entry_dates = [date.fromisoformat(iso) for iso, _ in all_days]

    if to_day is None:
        to_day = utc_now().date() - timedelta(days=1)
    if from_day is None:
        from_day = min(entry_dates) if entry_dates else to_day

    selected = [
        (date.fromisoformat(iso), entry)
        for iso, entry in all_days
        if from_day <= date.fromisoformat(iso) <= to_day
    ]

    days = [_day_report(store, day, entry) for day, entry in selected]

    status_counts: dict[str, int] = {}
    for _, entry in selected:
        status = entry.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    ticks_by_day = {item["date"]: item["ticks"] for item in days}
    missing_weekdays: list[str] = []
    cursor = from_day
    while cursor <= to_day:
        if cursor.weekday() < 5 and ticks_by_day.get(cursor.isoformat(), 0) == 0:
            missing_weekdays.append(cursor.isoformat())
        cursor += timedelta(days=1)

    largest_jump = None
    with_data = [item for item in days if item["ticks"] > 0]
    for previous, current in zip(with_data, with_data[1:], strict=False):
        change = current["first_bid"] - previous["last_bid"]
        if largest_jump is None or abs(change) > abs(largest_jump["change"]):
            largest_jump = {
                "from_date": previous["date"],
                "to_date": current["date"],
                "change": change,
            }

    total_ticks = sum(int(entry.get("ticks", 0)) for _, entry in selected)
    out_of_order_rows = sum(item["out_of_order_rows"] for item in days)
    integrity_problems = sum(len(item["problems"]) for item in days)

    manifest_dates = {item["date"] for item in days}
    files_not_in_manifest: list[str] = []
    for path in store.symbol_dir.rglob("*.parquet"):
        try:
            file_day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if from_day <= file_day <= to_day and file_day.isoformat() not in manifest_dates:
            files_not_in_manifest.append(file_day.isoformat())
    files_not_in_manifest = sorted(set(files_not_in_manifest))

    report = {
        "symbol": store.symbol,
        "generated_at_utc": utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
        "range": {"from": from_day.isoformat(), "to": to_day.isoformat()},
        "days": days,
        "summary": {
            "days_per_status": status_counts,
            "total_ticks": total_ticks,
            "missing_weekdays": missing_weekdays,
            "out_of_order_rows": out_of_order_rows,
            "integrity_problems": integrity_problems,
            "files_not_in_manifest": files_not_in_manifest,
            "largest_bid_change_between_days": largest_jump,
        },
    }
    path = store.root / "reports" / f"quality-{store.symbol}.json"
    _write_json(path, report)
    return report


def _day_report(store: TickStore, day: date, entry: dict[str, Any]) -> dict[str, Any]:
    entry_ticks = int(entry.get("ticks", 0))
    exists = store.day_path(day).exists()
    problems: list[str] = []
    if entry.get("status") == "empty" and exists:
        problems.append("unexpected_file")
    if entry_ticks > 0 and not exists:
        problems.append("file_missing")

    table = store.read_day(day)
    n = 0 if table is None else table.num_rows
    if exists and n != entry_ticks:
        problems.append("row_count_mismatch")

    day_start = (day - EPOCH_DATE).days * DAY_MS
    day_end = day_start + DAY_MS
    base: dict[str, Any] = {
        "date": day.isoformat(),
        "status": entry.get("status"),
        "manifest_ticks": entry_ticks,
        "ticks": 0,
        "first_ts_ms": None,
        "last_ts_ms": None,
        "first_utc": None,
        "last_utc": None,
        "largest_gap_seconds": None,
        "long_gaps": [],
        "out_of_order_rows": 0,
        "ask_below_bid_rows": 0,
        "nonpositive_price_rows": 0,
        "spread_median": None,
        "spread_p99": None,
        "spread_max": None,
        "first_bid": None,
        "last_bid": None,
        "rows_outside_day": 0,
        "problems": problems,
    }
    if table is None or table.num_rows == 0:
        return base

    n = table.num_rows
    ts = table["ts_ms"]
    bid = table["bid"]
    ask = table["ask"]
    spread = pc.subtract(ask, bid)

    first_ms = int(ts[0].as_py())
    last_ms = int(ts[-1].as_py())
    base["ticks"] = n
    base["first_ts_ms"] = first_ms
    base["last_ts_ms"] = last_ms
    base["first_utc"] = iso_utc(first_ms)
    base["last_utc"] = iso_utc(last_ms)
    base["first_bid"] = float(bid[0].as_py())
    base["last_bid"] = float(bid[-1].as_py())
    if entry.get("first_ts_ms") != first_ms or entry.get("last_ts_ms") != last_ms:
        problems.append("first_last_mismatch")

    outside = pc.or_(pc.less(ts, day_start), pc.greater_equal(ts, day_end))
    base["rows_outside_day"] = int(pc.sum(outside).as_py())
    if base["rows_outside_day"] > 0:
        problems.append("rows_outside_day")

    if n > 1:
        diffs = pc.subtract(ts.slice(1), ts.slice(0, n - 1))
        base["largest_gap_seconds"] = pc.max(diffs).as_py() / 1000.0
        base["out_of_order_rows"] = int(pc.sum(pc.less(diffs, 0)).as_py())
        long_mask = pc.greater(diffs, GAP_SECONDS * 1000)
        starts = pc.filter(ts.slice(0, n - 1), long_mask).to_pylist()
        ends = pc.filter(ts.slice(1), long_mask).to_pylist()
        base["long_gaps"] = [
            {
                "from_ts_ms": int(start),
                "to_ts_ms": int(end),
                "from_utc": iso_utc(start),
                "to_utc": iso_utc(end),
                "seconds": (int(end) - int(start)) / 1000.0,
            }
            for start, end in zip(starts, ends, strict=True)
        ]

    base["ask_below_bid_rows"] = int(pc.sum(pc.less(ask, bid)).as_py())
    base["nonpositive_price_rows"] = int(
        pc.sum(pc.or_(pc.less_equal(bid, 0), pc.less_equal(ask, 0))).as_py()
    )
    quantiles = pc.quantile(spread, q=[0.5, 0.99], interpolation="linear").to_pylist()
    base["spread_median"] = float(quantiles[0])
    base["spread_p99"] = float(quantiles[1])
    base["spread_max"] = float(pc.max(spread).as_py())
    return base


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
