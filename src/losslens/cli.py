"""Command line for loss-lens."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .ticks import dukascopy, importer, quality
from .ticks.store import (
    DONE_STATUSES,
    TickStore,
    classify_status,
    make_entry,
    read_ticks,
    utc_now,
)

DATA_ROOT = Path("data")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="losslens", description="Local tick data and defect lens for MT4 EAs"
    )
    parser.add_argument("--version", action="version", version=f"losslens {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    ticks = commands.add_parser("ticks", help="tick store commands")
    tick_commands = ticks.add_subparsers(dest="ticks_command", required=True)

    sync = tick_commands.add_parser("sync", help="download and store daily ticks")
    sync.add_argument("--symbol", required=True)
    sync.add_argument("--from", dest="start", required=True, type=_date_arg)
    sync.add_argument(
        "--to",
        dest="end",
        type=_date_arg,
        help="exclusive end date; defaults to tomorrow UTC (so today is included)",
    )
    sync.add_argument("--force", action="store_true", help="re-download finished days")
    sync.set_defaults(func=cmd_ticks_sync)

    verify = tick_commands.add_parser("verify", help="check stored ticks and write a report")
    verify.add_argument("--symbol", required=True)
    verify.add_argument("--from", dest="start", type=_date_arg)
    verify.add_argument("--to", dest="end", type=_date_arg, help="inclusive end date")
    verify.set_defaults(func=cmd_ticks_verify)

    query = tick_commands.add_parser("query", help="read ticks through the one read function")
    query.add_argument("--symbol", required=True)
    query.add_argument("--from", dest="start", required=True)
    query.add_argument("--to", dest="end", required=True)
    query.set_defaults(func=cmd_ticks_query)

    import_cmd = tick_commands.add_parser("import", help="import another tick CSV")
    import_cmd.add_argument("--symbol", required=True)
    import_cmd.add_argument("--file", required=True)
    import_cmd.add_argument("--ts-col", required=True)
    import_cmd.add_argument("--bid-col", required=True)
    import_cmd.add_argument("--ask-col", required=True)
    import_cmd.add_argument("--bid-vol-col")
    import_cmd.add_argument("--ask-vol-col")
    import_cmd.add_argument(
        "--ts-format", required=True, choices=["epoch_ms", "epoch_s", "iso"]
    )
    import_cmd.add_argument(
        "--utc-offset-minutes",
        type=int,
        default=0,
        help="how far the file's clock is ahead of UTC",
    )
    import_cmd.set_defaults(func=cmd_ticks_import)

    status = tick_commands.add_parser("status", help="show what the store covers")
    status.add_argument("--symbol", required=True)
    status.set_defaults(func=cmd_ticks_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("interrupted; finished days are safe, run the command again", file=sys.stderr)
        return 130


def cmd_ticks_sync(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    start = args.start
    end = args.end or (utc_now().date() + timedelta(days=1))
    if start >= end:
        print("--from must be before --to", file=sys.stderr)
        return 2

    store = TickStore(DATA_ROOT, symbol)
    result = sync_days(store, symbol, start, end, force=args.force)
    if result["failures"]:
        print("Failed days: " + ", ".join(result["failures"]))
        return 1
    return 0


def sync_days(
    store: TickStore,
    symbol: str,
    start: date,
    end: date,
    force: bool = False,
    download: Callable[[str, date], Path | None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
    retries: int = 3,
    retry_pause: float = 5.0,
    printer: Callable[..., None] = print,
) -> dict[str, Any]:
    """Sync [start, end) one UTC day at a time; never record a failed day."""
    download = download or dukascopy.download_day
    now_fn = now_fn or utc_now
    manifest = store.load_manifest()
    counts: Counter[str] = Counter()
    failures: list[str] = []
    started = time.perf_counter()
    day = start

    while day < end:
        iso = day.isoformat()
        entry = manifest.get("days", {}).get(iso)
        if entry:
            status = entry.get("status")
            if status == "imported" or (not force and status in DONE_STATUSES):
                ticks = int(entry.get("ticks", 0))
                counts[str(status)] += 1
                printer(f"{iso}  {status:<9} {ticks:>9}  {0.0:7.2f}s  (skipped)")
                day += timedelta(days=1)
                continue

        day_started = time.perf_counter()
        csv_path: Path | None = None
        error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                csv_path = download(symbol, day)
                error = None
                break
            except Exception as exc:  # a failed day is retried, then left unrecorded
                error = exc
                if attempt < retries:
                    time.sleep(retry_pause)

        if error is not None:
            failures.append(iso)
            counts["failed"] += 1
            printer(
                f"{iso}  {'failed':<9} {0:>9}  {time.perf_counter() - day_started:7.2f}s  "
                f"{str(error)[:300]}"
            )
            day += timedelta(days=1)
            continue

        try:
            table = dukascopy.read_dukascopy_csv(csv_path)
            ticks = table.num_rows
            fetched_at = now_fn()
            status = classify_status(fetched_at, day, ticks)

            if ticks:
                store.write_day(day, table)
                first_ts = int(table["ts_ms"][0].as_py())
                last_ts = int(table["ts_ms"][-1].as_py())
            else:
                store.delete_day(day)
                first_ts = None
                last_ts = None

            entry = make_entry(
                day,
                status,
                ticks,
                first_ts,
                last_ts,
                f"dukascopy:{dukascopy.instrument_for(symbol)}",
                fetched_at,
            )
            manifest.setdefault("days", {})[iso] = entry
            store.save_manifest(manifest)
            counts[status] += 1
            printer(
                f"{iso}  {status:<9} {ticks:>9}  "
                f"{time.perf_counter() - day_started:7.2f}s"
            )
        except Exception as exc:
            failures.append(iso)
            counts["failed"] += 1
            printer(
                f"{iso}  {'failed':<9} {0:>9}  {time.perf_counter() - day_started:7.2f}s  "
                f"{str(exc)[:300]}"
            )
        finally:
            if csv_path is not None:
                shutil.rmtree(csv_path.parent, ignore_errors=True)

        day += timedelta(days=1)

    elapsed = time.perf_counter() - started
    total_days = (end - start).days
    printer(
        "Summary: "
        f"{total_days} day(s), "
        + ", ".join(
            f"{name}={counts.get(name, 0)}"
            for name in ("complete", "empty", "partial", "imported", "failed")
        )
        + f", {elapsed:.2f}s"
    )
    return {"failures": failures, "counts": dict(counts), "elapsed_seconds": elapsed}


def cmd_ticks_verify(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    store = TickStore(DATA_ROOT, symbol)
    report = quality.verify_symbol(store, args.start, args.end)
    _print_quality(report)
    return 1 if report["summary"]["out_of_order_rows"] else 0


def _print_quality(report: dict[str, Any]) -> None:
    print(
        f"{'date':<10} {'status':<9} {'ticks':>9} {'gap_s':>8} {'ooo':>4} "
        f"{'ask<bid':>7} {'sp_p50':>8} {'sp_p99':>8} {'sp_max':>8}"
    )
    for item in report["days"]:
        gap = "-" if item["largest_gap_seconds"] is None else f"{item['largest_gap_seconds']:.1f}"
        print(
            f"{item['date']:<10} {str(item['status']):<9} {item['ticks']:>9} {gap:>8} "
            f"{item['out_of_order_rows']:>4} {item['ask_below_bid_rows']:>7} "
            f"{_number(item['spread_median']):>8} {_number(item['spread_p99']):>8} "
            f"{_number(item['spread_max']):>8}"
        )

    summary = report["summary"]
    print(
        "Statuses: "
        + ", ".join(f"{key}={value}" for key, value in sorted(summary["days_per_status"].items()))
    )
    print(f"Total ticks: {summary['total_ticks']}")
    print(f"Out-of-order rows: {summary['out_of_order_rows']}")
    missing = summary["missing_weekdays"]
    print("Weekdays with no data: " + (", ".join(missing) if missing else "none"))
    jump = summary["largest_bid_change_between_days"]
    if jump is None:
        print("Largest bid change between days: none")
    else:
        print(
            "Largest bid change between days: "
            f"{jump['change']:.3f} ({jump['from_date']} -> {jump['to_date']})"
        )
    print(f"Quality report: data/reports/quality-{report['symbol']}.json")


def cmd_ticks_query(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    from_ms = _iso_to_ms(args.start)
    to_ms = _iso_to_ms(args.end)
    started = time.perf_counter()
    table = read_ticks(symbol, from_ms, to_ms)
    read_ms = (time.perf_counter() - started) * 1000.0

    print(f"symbol: {symbol}")
    print(f"range: {args.start} .. {args.end} (from inclusive, to exclusive)")
    print(f"rows: {table.num_rows}")
    if table.num_rows:
        print("first: " + _row_text(table, 0))
        print("last: " + _row_text(table, table.num_rows - 1))
    print(f"read_ms: {read_ms:.2f}")
    return 0


def cmd_ticks_import(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    store = TickStore(DATA_ROOT, symbol)
    try:
        result = importer.import_csv(
            store,
            Path(args.file),
            args.ts_col,
            args.bid_col,
            args.ask_col,
            bid_vol_col=args.bid_vol_col,
            ask_vol_col=args.ask_vol_col,
            ts_format=args.ts_format,
            utc_offset_minutes=args.utc_offset_minutes,
        )
    except importer.CsvImportError as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 2

    for day, ticks in sorted(result["days"].items()):
        print(f"{day}  imported  {ticks:>9}")
    print(f"Imported {result['total_ticks']} ticks from {result['file']}")
    return 0


def cmd_ticks_status(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    store = TickStore(DATA_ROOT, symbol)
    manifest = store.load_manifest()
    entries = manifest.get("days", {})
    if not entries:
        print(f"{symbol}: no days stored")
        return 0

    dates = sorted(entries)
    counts = Counter(entry.get("status", "unknown") for entry in entries.values())
    total_ticks = sum(int(entry.get("ticks", 0)) for entry in entries.values())
    disk_size = sum(
        path.stat().st_size
        for path in store.symbol_dir.rglob("*.parquet")
        if path.is_file()
    )
    print(f"symbol: {symbol}")
    print(f"range: {dates[0]} .. {dates[-1]}")
    print(
        "days: "
        + ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
    )
    print(f"total ticks: {total_ticks}")
    print(f"disk size: {disk_size / (1024 * 1024):.2f} MB")
    return 0


def _row_text(table: Any, index: int) -> str:
    return ", ".join(
        f"{name}={table[name][index].as_py()}" for name in table.column_names
    )


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def _date_arg(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text!r}") from exc


def _iso_to_ms(text: str) -> int:
    try:
        dt = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"invalid ISO time: {text!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt.astimezone(timezone.utc) - EPOCH) // timedelta(milliseconds=1)
