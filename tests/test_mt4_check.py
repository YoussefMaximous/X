import struct
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa

from losslens.cli import main
from losslens.mt4.check import check_probe_ticks, check_report
from losslens.mt4.export import round_price, server_seconds
from losslens.mt4.report import TesterReport as Report
from losslens.ticks.store import TickStore, make_entry

DAY = date(2026, 3, 3)
BASE = 1772496000


def _store(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [(BASE + offset) * 1000 for offset in (0, 1, 2)],
                "bid": [100.0, 101.0, 102.0],
                "ask": [101.0, 102.0, 103.0],
                "bid_vol": [0.0, 0.0, 0.0],
                "ask_vol": [0.0, 0.0, 0.0],
            }
        ),
    )
    manifest = store.load_manifest()
    manifest["days"][DAY.isoformat()] = make_entry(
        DAY,
        "complete",
        3,
        BASE * 1000,
        (BASE + 2) * 1000,
        "test",
        datetime(2026, 11, 20, 12, tzinfo=UTC),
    )
    store.save_manifest(manifest)
    return store


def _probe(path, rows):
    data = b"".join(
        struct.pack(
            "<qddqq",
            server_seconds(timestamp),
            round_price(bid),
            round_price(bid + 1),
            1,
            server_seconds(timestamp),
        )
        for timestamp, bid in rows
    )
    path.write_bytes(data)
    return path


def test_identical_with_ticks_skipped_at_the_end(tmp_path):
    store = _store(tmp_path)
    probe = _probe(tmp_path / "probe.bin", [(BASE, 100.0), (BASE + 1, 101.0)])

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert result.identical
    assert result.skipped_end == 1


def test_identical_with_ticks_skipped_at_the_start(tmp_path):
    store = _store(tmp_path)
    probe = _probe(tmp_path / "probe.bin", [(BASE + 1, 101.0), (BASE + 2, 102.0)])

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert result.identical
    assert result.skipped_start == 1


def test_a_compared_bid_difference_is_not_identical(tmp_path):
    store = _store(tmp_path)
    probe = _probe(tmp_path / "probe.bin", [(BASE, 100.0), (BASE + 1, 999.0)])

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert not result.identical
    assert result.bid_differences == 1


def test_extra_probe_ticks_are_not_identical(tmp_path):
    store = _store(tmp_path)
    probe = _probe(
        tmp_path / "probe.bin",
        [(BASE, 100.0), (BASE + 1, 101.0), (BASE + 2, 102.0), (BASE + 3, 103.0)],
    )

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert not result.identical


def test_empty_probe_is_not_identical(tmp_path):
    store = _store(tmp_path)
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"")

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert not result.identical
    assert result.probe_ticks == 0


def test_ticks_at_or_after_broker_midnight_are_not_expected(tmp_path):
    cutoff = 1772582400
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [(cutoff - 7200 - 1) * 1000, (cutoff - 7200) * 1000],
                "bid": [100.0, 101.0],
                "ask": [101.0, 102.0],
                "bid_vol": [0.0, 0.0],
                "ask_vol": [0.0, 0.0],
            }
        ),
    )
    probe = _probe(tmp_path / "probe.bin", [(cutoff - 7201, 100.0)])

    result = check_probe_ticks(store, probe, "XAUUSD", DAY, DAY)

    assert result.identical
    assert result.store_ticks == 1
    assert result.skipped_end == 0


def _tester_report(bars, ticks):
    return Report(
        expert="Test",
        server="Server",
        build="Build 1492",
        symbol="XAUUSD",
        period="1 Minute (M1)",
        model="Every tick",
        bars=bars,
        ticks_modelled=ticks,
        modelling_quality=0.0,
        initial_deposit=0.0,
        spread=30,
        total_net_profit=0.0,
        total_trades=0,
        trades=(),
    )


def test_check_report_matches_our_fxt_counts(tmp_path):
    result = check_report(_store(tmp_path), _tester_report(1, 3), "XAUUSD", DAY, DAY)

    assert result.identical
    assert result.store_ticks == 3
    assert result.store_bars == 1


def test_check_report_sees_mt4_generated_counts(tmp_path):
    result = check_report(_store(tmp_path), _tester_report(1320, 471448), "XAUUSD", DAY, DAY)

    assert not result.identical
    assert result.report_ticks == 471448
    assert result.store_ticks == 3


def test_cli_check_report(tmp_path, monkeypatch, capsys):
    _store(tmp_path)
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))
    text = (Path(__file__).parent / "fixtures" / "mt4_report_probe.htm").read_text(encoding="utf-8")
    text = text.replace("<td align=right>1320</td>", "<td align=right>1</td>", 1)
    text = text.replace("<td align=right>471448</td>", "<td align=right>3</td>", 1)
    report = tmp_path / "report.htm"
    report.write_text(text, encoding="utf-8")

    code = main(
        [
            "mt4",
            "check-report",
            "--report",
            str(report),
            "--symbol",
            "XAUUSD",
            "--from",
            "2026-03-03",
            "--to",
            "2026-03-03",
        ]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "report ticks: 3" in output
    assert "store ticks: 3" in output
    assert "RESULT: identical" in output
