"""Build one self-contained, local MT4-style chart page."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from losslens.mt4 import export
from losslens.ticks.store import TickStore


class AppError(RuntimeError):
    """The chart page cannot be built from the stored data."""


def build_app(
    store: TickStore,
    symbol: str,
    day: date,
    out_path: Path | None = None,
) -> Path:
    code = symbol.upper()
    digits = export.SYMBOL_DECIMALS.get(code)
    if digits is None:
        raise AppError(f"no decimals known for {symbol}")
    try:
        table = export._ticks_of_day(store, day, code)
    except export.ExportError as exc:
        raise AppError(str(exc)) from exc
    bars = export._bars_for_table(table, digits)
    if not bars:
        raise AppError(f"{day.isoformat()} has no bars")
    first_utc = int(table["ts_ms"][0].as_py()) // 1000
    last_row = table.num_rows - 1
    payload = {
        "symbol": code,
        "day": day.isoformat(),
        "digits": digits,
        "ticks": table.num_rows,
        "offset_hours": export.server_offset_seconds(first_utc) // 3600,
        "bid": float(table["bid"][last_row].as_py()),
        "ask": float(table["ask"][last_row].as_py()),
        "bars": bars,
    }
    template = Path(__file__).with_name("template.html").read_text(encoding="utf-8")
    html = template.replace("/*__DATA__*/", json.dumps(payload, separators=(",", ":")))
    target = out_path or (store.root / "app" / f"{code}-{day.isoformat()}.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8", newline="\n")
    return target
