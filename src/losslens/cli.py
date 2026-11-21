"""Command line for loss-lens."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from collections import Counter
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

from . import __version__
from .mt4 import check as mt4_check
from .mt4 import compile as mt4_compile
from .mt4 import copy as mt4_copy
from .mt4 import export as mt4_export
from .mt4 import fxt as mt4_fxt
from .mt4 import run as mt4_run
from .playground import PlaygroundError, build_playground
from .ticks import dukascopy, importer, quality
from .ticks.store import (
    DONE_STATUSES,
    TickStore,
    classify_status,
    iso_utc,
    make_entry,
    read_ticks,
    resolve_data_root,
    utc_now,
)

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _store(symbol: str) -> TickStore:
    return TickStore(resolve_data_root(), symbol)


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
    import_cmd.add_argument("--ts-format", required=True, choices=["epoch_ms", "epoch_s", "iso"])
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

    mt4 = commands.add_parser("mt4", help="MT4 copy, export, compile and run")
    mt4_commands = mt4.add_subparsers(dest="mt4_command", required=True)

    setup = mt4_commands.add_parser("setup", help="make the separate MT4 copy")
    setup.add_argument("--from", dest="source", required=True)
    setup.add_argument("--server", required=True)
    setup.add_argument("--replace", action="store_true")
    setup.set_defaults(func=cmd_mt4_setup)

    compile_cmd = mt4_commands.add_parser("compile", help="compile the probe EA")
    compile_cmd.set_defaults(func=cmd_mt4_compile)

    export_cmd = mt4_commands.add_parser("export", help="write MT4 history files")
    export_cmd.add_argument("--symbol", required=True)
    export_cmd.add_argument("--from", dest="start", required=True, type=_date_arg)
    export_cmd.add_argument("--to", dest="end", required=True, type=_date_arg)
    export_cmd.add_argument("--no-fxt", action="store_true")
    export_cmd.set_defaults(func=cmd_mt4_export)

    inspect = mt4_commands.add_parser("inspect-fxt", help="decode an FXT file")
    inspect.add_argument("file")
    inspect.set_defaults(func=cmd_mt4_inspect_fxt)

    run_cmd = mt4_commands.add_parser("run", help="run the probe in the tester")
    run_cmd.add_argument("--symbol", required=True)
    run_cmd.add_argument("--from", dest="start", required=True, type=_date_arg)
    run_cmd.add_argument("--to", dest="end", required=True, type=_date_arg)
    run_cmd.add_argument("--spread", type=int, default=30)
    run_cmd.add_argument("--timeout", type=float, default=600)
    run_cmd.add_argument(
        "--visual",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="show MT4's visual tester chart; much slower (default: off)",
    )
    run_cmd.set_defaults(func=cmd_mt4_run)

    check = mt4_commands.add_parser("check-ticks", help="compare probe ticks with the store")
    check.add_argument("--symbol", required=True)
    check.add_argument("--from", dest="start", required=True, type=_date_arg)
    check.add_argument("--to", dest="end", required=True, type=_date_arg)
    check.set_defaults(func=cmd_mt4_check_ticks)

    playground = commands.add_parser("playground", help="local tick playground page")
    playground_commands = playground.add_subparsers(dest="playground_command", required=True)
    build = playground_commands.add_parser(
        "build", help="write one self-contained Playground HTML file"
    )
    build.add_argument("--symbol", required=True)
    build.add_argument("--day", required=True, type=_date_arg)
    build.add_argument("--from", dest="start", type=_hhmm_arg, default=0)
    build.add_argument("--to", dest="end", type=_hhmm_arg, default=60)
    build.add_argument("--out", required=True)
    build.add_argument("--max-ticks", type=int, default=50_000)
    build.set_defaults(func=cmd_playground_build)

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

    store = _store(symbol)
    try:
        result = sync_days(store, symbol, start, end, force=args.force)
    except dukascopy.SetupError as exc:
        print(f"setup problem: {exc}", file=sys.stderr)
        return 2
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
    temp_root: Path | str | None = None,
) -> dict[str, Any]:
    """Sync [start, end) one UTC day at a time; never record a failed day."""
    dukascopy.cleanup_stale_temp_dirs(temp_root)

    if download is None:
        download_fn: Callable[[str, date], Path | None] = partial(
            dukascopy.download_day, temp_root=temp_root
        )
    else:
        download_fn = download
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
                printer(
                    f"{iso}  {status:<9} {ticks:>9}  {0.0:7.2f}s  (skipped)",
                    flush=True,
                )
                day += timedelta(days=1)
                continue

        day_started = time.perf_counter()
        csv_path: Path | None = None
        try:
            error: Exception | None = None
            for attempt in range(retries + 1):
                try:
                    csv_path = download_fn(symbol, day)
                    error = None
                    break
                except dukascopy.SetupError:
                    raise
                except Exception as exc:  # a failed day is retried, then left unrecorded
                    error = exc
                    if attempt < retries:
                        time.sleep(retry_pause)

            if error is not None:
                failures.append(iso)
                counts["failed"] += 1
                printer(
                    f"{iso}  {'failed':<9} {0:>9}  "
                    f"{time.perf_counter() - day_started:7.2f}s  {str(error)[:300]}",
                    flush=True,
                )
            else:
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
                    f"{iso}  {status:<9} {ticks:>9}  {time.perf_counter() - day_started:7.2f}s",
                    flush=True,
                )
        except dukascopy.SetupError:
            raise
        except Exception as exc:
            failures.append(iso)
            counts["failed"] += 1
            printer(
                f"{iso}  {'failed':<9} {0:>9}  "
                f"{time.perf_counter() - day_started:7.2f}s  {str(exc)[:300]}",
                flush=True,
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
        + f", {elapsed:.2f}s",
        flush=True,
    )
    return {"failures": failures, "counts": dict(counts), "elapsed_seconds": elapsed}


def cmd_ticks_verify(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    store = _store(symbol)
    report = quality.verify_symbol(store, args.start, args.end)
    _print_quality(report)
    summary = report["summary"]
    bad = (
        summary["out_of_order_rows"]
        or summary["integrity_problems"]
        or summary["files_not_in_manifest"]
    )
    return 1 if bad else 0


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
    problems = [(item["date"], item["problems"]) for item in report["days"] if item["problems"]]
    for day, day_problems in problems:
        print(f"  {day}: {', '.join(day_problems)}")
    print(
        "Statuses: "
        + ", ".join(f"{key}={value}" for key, value in sorted(summary["days_per_status"].items()))
    )
    print(f"Total ticks: {summary['total_ticks']}")
    print(f"Out-of-order rows: {summary['out_of_order_rows']}")
    print(f"Integrity problems: {summary['integrity_problems']}")
    files_not_in_manifest = summary["files_not_in_manifest"]
    print(
        "Files not in manifest: "
        + (", ".join(files_not_in_manifest) if files_not_in_manifest else "none")
    )
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
    print(f"Quality report: {report['report_path']}")


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


def cmd_playground_build(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    try:
        result = build_playground(
            _store(symbol),
            symbol,
            args.day,
            args.start,
            args.end,
            Path(args.out),
            args.max_ticks,
        )
    except PlaygroundError as exc:
        print(f"playground: {exc}", file=sys.stderr)
        return 2
    print(f"playground: {result.path}")
    print(f"ticks: {result.ticks}")
    print(f"first tick: {iso_utc(result.first_ts_ms)}")
    print(f"last tick: {iso_utc(result.last_ts_ms)}")
    print(f"bytes: {result.bytes_written}")
    return 0


def cmd_ticks_import(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    store = _store(symbol)
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
    store = _store(symbol)
    manifest = store.load_manifest()
    entries = manifest.get("days", {})
    if not entries:
        print(f"{symbol}: no days stored")
        return 0

    dates = sorted(entries)
    counts = Counter(entry.get("status", "unknown") for entry in entries.values())
    total_ticks = sum(int(entry.get("ticks", 0)) for entry in entries.values())
    disk_size = sum(
        path.stat().st_size for path in store.symbol_dir.rglob("*.parquet") if path.is_file()
    )
    print(f"symbol: {symbol}")
    print(f"range: {dates[0]} .. {dates[-1]}")
    print("days: " + ", ".join(f"{status}={count}" for status, count in sorted(counts.items())))
    print(f"total ticks: {total_ticks}")
    print(f"disk size: {disk_size / (1024 * 1024):.2f} MB")
    return 0


def _copy_root() -> Path:
    return mt4_copy.copy_target(resolve_data_root())


def cmd_mt4_setup(args: argparse.Namespace) -> int:
    target = _copy_root()
    try:
        copied = mt4_copy.setup_copy(Path(args.source), args.server, target, replace=args.replace)
    except (mt4_copy.SetupError, OSError) as exc:
        print(f"setup failed: {exc}", file=sys.stderr)
        return 2
    for name, size in copied:
        print(f"{name}  {size} bytes")
    print(f"copy: {target}")
    return 0


def cmd_mt4_compile(args: argparse.Namespace) -> int:
    copy_root = _copy_root()
    try:
        output = mt4_compile.compile_probe(copy_root)
    except (mt4_compile.CompileError, OSError) as exc:
        print(f"compile failed: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


def cmd_mt4_export(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    copy_root = _copy_root()
    try:
        result = mt4_export.export_range(
            _store(symbol),
            copy_root,
            symbol,
            args.start,
            args.end,
            no_fxt=args.no_fxt,
        )
    except (mt4_export.ExportError, OSError) as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        return 2
    print(f"hst: {result['hst']}")
    print(f"bars: {result['bars']}")
    if "fxt" in result:
        print(f"fxt: {result['fxt']}")
        print(f"fxt records: {result['fxt_records']}")
    print(f"export seconds: {result['seconds']:.3f}")
    return 0


def cmd_mt4_inspect_fxt(args: argparse.Namespace) -> int:
    try:
        print(mt4_fxt.inspect_fxt(Path(args.file)))
    except OSError as exc:
        print(f"inspect failed: {exc}", file=sys.stderr)
        return 2
    return 0


def cmd_mt4_run(args: argparse.Namespace) -> int:
    try:
        result = mt4_run.run_tester(
            _copy_root(),
            args.symbol.upper(),
            args.start,
            args.end,
            args.spread,
            args.timeout,
            visual=args.visual,
        )
    except (mt4_run.RunError, OSError) as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 2
    print(f"seconds: {result.seconds:.3f}")
    print(f"visual mode: {'on' if args.visual else 'off'}")
    print(f"ended by timeout: {result.timed_out}")
    print(f"report files: {[str(path) for path in result.report_files]}")
    print(f"probe info: {result.probe_info}")
    print(f"probe ticks: {result.probe_ticks}")
    if result.output:
        print(result.output)
    return 0


def cmd_mt4_check_ticks(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    probe = _copy_root() / "tester" / "files" / mt4_run.PROBE_TICKS
    try:
        comparison = mt4_check.check_probe_ticks(
            _store(symbol), probe, symbol, args.start, args.end
        )
    except (OSError, ValueError) as exc:
        print(f"check failed: {exc}", file=sys.stderr)
        return 2
    print(f"ticks in store: {comparison.store_ticks}")
    print(f"ticks probe given: {comparison.probe_ticks}")
    print(f"ticks skipped at start: {comparison.skipped_start}")
    print(f"ticks skipped at end: {comparison.skipped_end}")
    print(f"time differences: {comparison.time_differences}")
    print(f"bid differences: {comparison.bid_differences}")
    for store_row, probe_row in comparison.first_differences:
        print(f"first difference: store={store_row} probe={probe_row}")
    print(f"smallest ask-bid: {comparison.min_spread}")
    print(f"largest ask-bid: {comparison.max_spread}")
    print(f"RESULT: {'identical' if comparison.identical else 'different'}")
    return 0


def _row_text(table: Any, index: int) -> str:
    return ", ".join(f"{name}={table[name][index].as_py()}" for name in table.column_names)


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def _date_arg(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text!r}") from exc


def _hhmm_arg(text: str) -> int:
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (AttributeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"expected HH:MM in UTC, got {text!r}") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise argparse.ArgumentTypeError(f"expected HH:MM between 00:00 and 23:59, got {text!r}")
    return hour * 60 + minute


def _iso_to_ms(text: str) -> int:
    try:
        dt = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"invalid ISO time: {text!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return (dt.astimezone(UTC) - EPOCH) // timedelta(milliseconds=1)
