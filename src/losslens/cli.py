"""Command line for loss-lens."""

from __future__ import annotations

import argparse
import json
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
from .app import build as app_build
from .mt4 import check as mt4_check
from .mt4 import compile as mt4_compile
from .mt4 import copy as mt4_copy
from .mt4 import export as mt4_export
from .mt4 import fxt as mt4_fxt
from .mt4 import journal as mt4_journal
from .mt4 import presets as mt4_presets
from .mt4 import reconcile as mt4_reconcile
from .mt4 import report as mt4_report
from .mt4 import run as mt4_run
from .optimize import core as optimize_core
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

    app = commands.add_parser("app", help="build the local chart page")
    app_commands = app.add_subparsers(dest="app_command", required=True)
    app_build_cmd = app_commands.add_parser("build", help="write one self-contained chart page")
    app_build_cmd.add_argument("--symbol", required=True)
    app_build_cmd.add_argument("--day", required=True, type=_date_arg)
    app_build_cmd.add_argument("--out")
    app_build_cmd.add_argument("--inputs", help="a .set preset or an .mq4 source")
    app_build_cmd.set_defaults(func=cmd_app_build)

    optimize = commands.add_parser("optimize", help="AI-native EA optimization")
    optimize_commands = optimize.add_subparsers(dest="optimize_command", required=True)

    plan = optimize_commands.add_parser("plan", help="read a .set and write config.json")
    plan.add_argument("--set", dest="preset", required=True)
    plan.add_argument("--expert", required=True)
    plan.add_argument("--symbol", required=True)
    plan.add_argument("--from", dest="start", required=True, type=_date_arg)
    plan.add_argument("--to", dest="end", required=True, type=_date_arg)
    plan.add_argument("--spread", type=int, default=30)
    plan.add_argument("--budget", type=int, default=50)
    plan.add_argument("--seed", type=int, default=1)
    plan.add_argument("--objective", default="net_profit")
    plan.add_argument("--engine", default="random")
    plan.add_argument("--min-trades", type=int)
    plan.add_argument("--max-drawdown", type=float)
    plan.add_argument("--out", required=True)
    plan.add_argument("--json", action="store_true", dest="as_json")
    plan.set_defaults(func=cmd_optimize_plan)

    opt_run = optimize_commands.add_parser("run", help="run the planned trials")
    opt_run.add_argument("--config", required=True)
    opt_run.add_argument("--out")
    opt_run.add_argument("--dry-run", action="store_true")
    opt_run.add_argument("--resume", action="store_true")
    opt_run.add_argument("--json", action="store_true", dest="as_json")
    opt_run.set_defaults(func=cmd_optimize_run)

    opt_status = optimize_commands.add_parser(
        "status", help="show a run's progress and stop advice"
    )
    opt_status.add_argument("--run", required=True)
    opt_status.add_argument("--json", action="store_true", dest="as_json")
    opt_status.set_defaults(func=cmd_optimize_status)

    shortlist = optimize_commands.add_parser(
        "shortlist", help="show candidates for the user to discuss"
    )
    shortlist.add_argument("--run", required=True)
    shortlist.add_argument("--limit", type=int, default=5)
    shortlist.add_argument("--json", action="store_true", dest="as_json")
    shortlist.set_defaults(func=cmd_optimize_shortlist)

    decide = optimize_commands.add_parser("decide", help="record the chosen trial and why")
    decide.add_argument("--run", required=True)
    decide.add_argument("--trial", type=int, required=True)
    decide.add_argument("--reason", required=True)
    decide.add_argument("--json", action="store_true", dest="as_json")
    decide.set_defaults(func=cmd_optimize_decide)

    best = optimize_commands.add_parser("best", help="write the best-scoring .set")
    best.add_argument("--run", required=True)
    best.add_argument("--out")
    best.add_argument("--json", action="store_true", dest="as_json")
    best.set_defaults(func=cmd_optimize_best)

    winner = optimize_commands.add_parser("winner", help="write the chosen winner .set")
    winner.add_argument("--run", required=True)
    winner.add_argument("--out")
    winner.add_argument("--json", action="store_true", dest="as_json")
    winner.set_defaults(func=cmd_optimize_winner)

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

    parse_report = mt4_commands.add_parser(
        "parse-report", help="read an MT4 strategy tester report"
    )
    parse_report.add_argument("file")
    parse_report.set_defaults(func=cmd_mt4_parse_report)

    parse_journal = mt4_commands.add_parser("parse-journal", help="read an MT4 tester journal")
    parse_journal.add_argument("file")
    parse_journal.add_argument("--tail", type=int, default=20)
    parse_journal.set_defaults(func=cmd_mt4_parse_journal)

    inputs = mt4_commands.add_parser("inputs", help="list an expert's inputs")
    inputs.add_argument("file")
    inputs.set_defaults(func=cmd_mt4_inputs)

    reconcile = mt4_commands.add_parser(
        "reconcile", help="check report trades exist in the tick store"
    )
    reconcile.add_argument("--report", required=True)
    reconcile.add_argument("--symbol", required=True)
    reconcile.set_defaults(func=cmd_mt4_reconcile)

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

    check_report = mt4_commands.add_parser(
        "check-report", help="check a tester report used our ticks"
    )
    check_report.add_argument("--report", required=True)
    check_report.add_argument("--symbol", required=True)
    check_report.add_argument("--from", dest="start", required=True, type=_date_arg)
    check_report.add_argument("--to", dest="end", required=True, type=_date_arg)
    check_report.set_defaults(func=cmd_mt4_check_report)

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
    except OSError as exc:
        print(f"playground: could not write {args.out}: {exc}", file=sys.stderr)
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


def cmd_app_build(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    out = Path(args.out) if args.out else None
    inputs = Path(args.inputs) if args.inputs else None
    try:
        path = app_build.build_app(_store(symbol), symbol, args.day, out, inputs)
    except (app_build.AppError, OSError) as exc:
        print(f"app build failed: {exc}", file=sys.stderr)
        return 2
    print(f"chart: {path}")
    print(f"size: {path.stat().st_size} bytes")
    return 0


def _load_optimizer_config(path: str) -> optimize_core.OptimizerConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return optimize_core.OptimizerConfig.from_dict(raw)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise optimize_core.OptimizeError(f"cannot read config: {exc}") from exc


def cmd_optimize_plan(args: argparse.Namespace) -> int:
    try:
        inputs = mt4_presets.read_inputs(Path(args.preset))
        config = optimize_core.config_from_inputs(
            inputs,
            expert=args.expert,
            symbol=args.symbol,
            from_day=args.start,
            to_day=args.end,
            spread=args.spread,
            budget=args.budget,
            seed=args.seed,
            objective=args.objective,
            engine=args.engine,
            constraints={
                "min_trades": float(args.min_trades) if args.min_trades is not None else None,
                "max_drawdown": args.max_drawdown,
            },
        )
    except (mt4_presets.PresetError, optimize_core.OptimizeError, OSError) as exc:
        print(f"plan failed: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    config_path = out / "config.json"
    config_path.write_text(json.dumps(config.to_dict(), indent=2) + "\n", encoding="utf-8")
    questions: list[dict[str, object]] = [
        {
            "id": "objective",
            "question": "What are we optimizing for?",
            "options": ["net_profit", "profit_factor", "max_drawdown"],
            "current": config.objective,
        },
        {
            "id": "risk",
            "question": "What is the largest drawdown you accept?",
            "current": config.constraints.get("max_drawdown"),
        },
        {
            "id": "trades",
            "question": "What is the minimum number of trades?",
            "current": config.constraints.get("min_trades"),
        },
        {
            "id": "period",
            "question": "Should we validate the winner on another period?",
            "current": None,
        },
    ]
    data = {"config": config.to_dict(), "config_file": str(config_path), "questions": questions}
    if args.as_json:
        print(json.dumps(data, indent=2))
        return 0
    print(f"expert: {config.expert}")
    print(f"symbol: {config.symbol}")
    print(f"range: {config.from_day} .. {config.to_day}")
    print(f"spread: {config.spread}")
    print(f"budget: {config.budget}")
    print(f"objective: {config.objective}")
    print("parameters:")
    for item in config.parameters:
        print(f"  {item.name}: {item.kind} {item.low} .. {item.high} step {item.step or 'random'}")
    if config.fixed:
        print("fixed: " + ", ".join(f"{key}={value}" for key, value in config.fixed.items()))
    print("questions for the user:")
    for question in questions:
        print(f"  - {question['question']}")
    print(f"config: {config_path}")
    return 0


def cmd_optimize_run(args: argparse.Namespace) -> int:
    try:
        config = _load_optimizer_config(args.config)
    except optimize_core.OptimizeError as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else Path(args.config).parent
    if not args.dry_run:
        print(
            "run failed: the MT4 evaluator is not enabled in this build; "
            "use --dry-run until the Lead allows TestExpertParameters",
            file=sys.stderr,
        )
        return 2
    try:
        if config.engine == "smac":
            records = optimize_core.run_smac(
                config,
                out,
                lambda _path, values: optimize_core.dry_metrics(config, values),
            )
        elif config.engine == "random":
            records = optimize_core.run_trials(
                config,
                out,
                lambda _path, values: optimize_core.dry_metrics(config, values),
                resume=args.resume,
            )
        else:
            print(f"run failed: unknown engine {config.engine!r}", file=sys.stderr)
            return 2
    except optimize_core.OptimizeError as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 2
    data = optimize_core.summary(records)
    data["results"] = str(out / "results.jsonl")
    if args.as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0


def cmd_optimize_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run)
    records = optimize_core.load_results(run_dir)
    data = optimize_core.summary(records)
    budget = len(records)
    try:
        budget = _load_optimizer_config(str(run_dir / "config.json")).budget
    except optimize_core.OptimizeError:
        pass
    advice = optimize_core.stop_advice(records, budget)
    output = {
        "summary": data,
        "advice": advice,
        "decision": optimize_core.read_decision(run_dir),
    }
    if args.as_json:
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    for key, value in data.items():
        print(f"{key}: {value}")
    print(f"recommended_stop: {advice['recommended_stop']}")
    print(f"why: {advice['reason']}")
    print(f"remaining: {advice['remaining']}")
    return 0


def cmd_optimize_shortlist(args: argparse.Namespace) -> int:
    records = optimize_core.load_results(Path(args.run))
    data = optimize_core.shortlist(records, args.limit)
    if args.as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    print(f"eligible: {data['eligible']} of {data['total']}")
    for record in data["top"]:
        print(f"trial {record['trial']}: {record['objective']} {record['values']}")
    if data["diverse"] is not None:
        record = data["diverse"]
        print(f"most different: trial {record['trial']}: {record['objective']} {record['values']}")
    return 0


def cmd_optimize_decide(args: argparse.Namespace) -> int:
    try:
        decision = optimize_core.decide(Path(args.run), args.trial, args.reason)
    except optimize_core.OptimizeError as exc:
        print(f"decide failed: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps(decision, indent=2, sort_keys=True))
    else:
        print(f"winner: trial {decision['trial']}")
        print(f"reason: {decision['reason']}")
        print(f"objective: {decision['record']['objective']}")
    return 0


def cmd_optimize_winner(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else None
    try:
        path, decision = optimize_core.winner_set(Path(args.run), out)
    except (optimize_core.OptimizeError, OSError) as exc:
        print(f"winner failed: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps({"winner": str(path), "decision": decision}, indent=2, sort_keys=True))
    else:
        print(f"winner: {path}")
        print(f"trial: {decision['trial']}")
        print(f"reason: {decision['reason']}")
    return 0


def cmd_optimize_best(args: argparse.Namespace) -> int:
    run_dir = Path(args.run)
    records = optimize_core.load_results(run_dir)
    best = optimize_core.best_record(records)
    if best is None:
        print("best failed: no scored trials", file=sys.stderr)
        return 2
    source = run_dir / str(best["set"])
    target = Path(args.out) if args.out else run_dir / "best.set"
    target.write_bytes(source.read_bytes())
    if args.as_json:
        print(json.dumps({"best": str(target), "record": best}, indent=2, sort_keys=True))
    else:
        print(f"best: {target}")
        print(f"trial: {best['trial']}")
        print(f"objective: {best['objective']}")
        print(f"values: {best['values']}")
    return 0


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


def cmd_mt4_parse_report(args: argparse.Namespace) -> int:
    try:
        parsed = mt4_report.parse_report(Path(args.file))
    except (mt4_report.ReportError, OSError) as exc:
        print(f"parse failed: {exc}", file=sys.stderr)
        return 2
    print(f"expert: {parsed.expert}")
    print(f"server: {parsed.server}")
    print(f"build: {parsed.build}")
    print(f"symbol: {parsed.symbol}")
    print(f"period: {parsed.period}")
    print(f"model: {parsed.model}")
    print(f"bars: {parsed.bars}")
    print(f"ticks modelled: {parsed.ticks_modelled}")
    print(f"modelling quality: {parsed.modelling_quality:.2f}%")
    print(f"initial deposit: {parsed.initial_deposit:.2f}")
    print(f"spread: {parsed.spread}")
    print(f"total net profit: {parsed.total_net_profit:.2f}")
    print(f"total trades: {parsed.total_trades}")
    for trade in parsed.trades:
        print(
            f"trade {trade.ticket}: {trade.kind} {trade.size} at {trade.close_price} "
            f"on {trade.close_time}, profit {trade.profit:.2f}, balance {trade.balance:.2f}"
        )
    return 0


def cmd_mt4_parse_journal(args: argparse.Namespace) -> int:
    try:
        lines = mt4_journal.parse_journal(Path(args.file))
    except (mt4_journal.JournalError, OSError) as exc:
        print(f"parse failed: {exc}", file=sys.stderr)
        return 2
    print(f"lines: {len(lines)}")
    tail = max(0, args.tail)
    for line in lines[-tail:] if tail else ():
        print(f"{line.level} {line.time} {line.message}")
    return 0


def cmd_mt4_inputs(args: argparse.Namespace) -> int:
    try:
        items = mt4_presets.read_inputs(Path(args.file))
    except (mt4_presets.PresetError, OSError) as exc:
        print(f"inputs failed: {exc}", file=sys.stderr)
        return 2
    for item in items:
        line = f"{item.name}={item.value}"
        if item.start is not None or item.step is not None or item.stop is not None:
            line += f"  [{item.start or '0'} .. {item.stop or '0'} step {item.step or '0'}]"
        print(line)
    return 0


def cmd_mt4_reconcile(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    try:
        parsed = mt4_report.parse_report(Path(args.report))
        result = mt4_reconcile.reconcile_trades(_store(symbol), parsed)
    except (mt4_report.ReportError, mt4_reconcile.ReconcileError, OSError) as exc:
        print(f"reconcile failed: {exc}", file=sys.stderr)
        return 2
    print(f"trades checked: {result.checked}")
    print(f"found in ticks: {result.found}")
    print(f"missing: {result.missing}")
    for check in result.checks:
        if not check.found:
            print(
                f"missing trade {check.ticket}: {check.kind} {check.close_price} "
                f"at {check.close_time}"
            )
    print(f"RESULT: {'reconciled' if result.reconciled else 'not reconciled'}")
    return 0


def cmd_mt4_run(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    try:
        result = mt4_run.run_tester(
            _copy_root(),
            symbol,
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
    if result.report is None:
        print("report: not found")
    else:
        print(f"report ticks: {result.report.ticks_modelled}")
        print(f"report bars: {result.report.bars}")
        try:
            comparison = mt4_check.check_report(
                _store(symbol), result.report, symbol, args.start, args.end
            )
        except (mt4_export.ExportError, OSError) as exc:
            print(f"report check skipped: {exc}", file=sys.stderr)
        else:
            print(f"store ticks: {comparison.store_ticks}")
            print(f"store bars: {comparison.store_bars}")
            print(f"RESULT: {'identical' if comparison.identical else 'different'}")
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


def cmd_mt4_check_report(args: argparse.Namespace) -> int:
    symbol = args.symbol.upper()
    try:
        parsed = mt4_report.parse_report(Path(args.report))
        comparison = mt4_check.check_report(_store(symbol), parsed, symbol, args.start, args.end)
    except (mt4_report.ReportError, mt4_export.ExportError, OSError) as exc:
        print(f"check failed: {exc}", file=sys.stderr)
        return 2
    print(f"report ticks: {comparison.report_ticks}")
    print(f"store ticks: {comparison.store_ticks}")
    print(f"report bars: {comparison.report_bars}")
    print(f"store bars: {comparison.store_bars}")
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
