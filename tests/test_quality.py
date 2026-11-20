from datetime import UTC, date, datetime

import pyarrow as pa
import pyarrow.parquet as pq

from losslens.cli import main
from losslens.ticks import quality
from losslens.ticks.store import TickStore, make_entry

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
DAY = date(2026, 3, 3)
BASE = 1772496000000


def _make_problem_day(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    path = store.day_path(DAY)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "ts_ms": [BASE, BASE + 2000, BASE + 1000, BASE + 401000],
            "bid": [100.0, 100.0, 100.0, 100.0],
            "ask": [101.0, 99.0, 101.0, 101.0],
            "bid_vol": [0.0, 0.0, 0.0, 0.0],
            "ask_vol": [0.0, 0.0, 0.0, 0.0],
        }
    )
    pq.write_table(table, path)

    manifest = store.load_manifest()
    manifest["days"][DAY.isoformat()] = make_entry(
        DAY, "complete", 4, BASE, BASE + 401000, "test", NOW
    )
    store.save_manifest(manifest)
    return store


def test_verify_detects_out_of_order_ask_below_bid_and_a_400s_gap(tmp_path):
    store = _make_problem_day(tmp_path)
    report = quality.verify_symbol(store, DAY, DAY)

    day = report["days"][0]
    assert day["ticks"] == 4
    assert day["out_of_order_rows"] == 1
    assert day["ask_below_bid_rows"] == 1
    assert day["largest_gap_seconds"] == 400.0
    assert day["long_gaps"] == [
        {
            "from_ts_ms": BASE + 1000,
            "to_ts_ms": BASE + 401000,
            "from_utc": "2026-03-03T00:00:01.000Z",
            "to_utc": "2026-03-03T00:06:41.000Z",
            "seconds": 400.0,
        }
    ]
    assert report["summary"]["out_of_order_rows"] == 1
    assert report["summary"]["total_ticks"] == 4
    assert (tmp_path / "reports" / "quality-XAUUSD.json").exists()


def test_verify_cli_exits_one_when_a_day_is_out_of_order(tmp_path, monkeypatch):
    _make_problem_day(tmp_path)
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)

    assert main(["ticks", "verify", "--symbol", "XAUUSD"]) == 1


def test_verify_clean_day_exits_zero(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [BASE, BASE + 1000],
                "bid": [100.0, 101.0],
                "ask": [100.5, 101.5],
                "bid_vol": [0.0, 0.0],
                "ask_vol": [0.0, 0.0],
            }
        ),
    )
    manifest = store.load_manifest()
    manifest["days"][DAY.isoformat()] = make_entry(
        DAY, "complete", 2, BASE, BASE + 1000, "test", NOW
    )
    store.save_manifest(manifest)
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)

    report = quality.verify_symbol(store, DAY, DAY)
    assert report["summary"]["integrity_problems"] == 0
    assert report["summary"]["files_not_in_manifest"] == []
    assert report["days"][0]["problems"] == []

    assert (
        main(
            ["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]
        )
        == 0
    )


def _one_row(store, ts=BASE):
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [ts],
                "bid": [100.0],
                "ask": [101.0],
                "bid_vol": [0.0],
                "ask_vol": [0.0],
            }
        ),
    )


def _entry(store, ticks, first, last, status="complete"):
    manifest = store.load_manifest()
    manifest["days"][DAY.isoformat()] = make_entry(DAY, status, ticks, first, last, "test", NOW)
    store.save_manifest(manifest)


def test_verify_reports_a_missing_day_file(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    _entry(store, 1, BASE, BASE)

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["days"][0]["problems"] == ["file_missing"]
    assert report["summary"]["integrity_problems"] == 1
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)
    assert (
        main(
            ["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]
        )
        == 1
    )


def test_verify_reports_an_unexpected_empty_day_file(tmp_path):
    from losslens.ticks.store import SCHEMA

    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(DAY, SCHEMA.empty_table())
    _entry(store, 0, None, None, status="empty")

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["days"][0]["problems"] == ["unexpected_file"]
    assert report["summary"]["integrity_problems"] == 1


def test_verify_reports_a_row_count_mismatch(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    _one_row(store)
    _entry(store, 2, BASE, BASE)

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["days"][0]["problems"] == ["row_count_mismatch"]
    assert report["summary"]["integrity_problems"] == 1


def test_verify_reports_a_first_last_mismatch(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    _one_row(store)
    _entry(store, 1, BASE + 1, BASE + 2)

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["days"][0]["problems"] == ["first_last_mismatch"]
    assert report["summary"]["integrity_problems"] == 1


def test_verify_reports_rows_outside_the_day(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [BASE, BASE + 86_400_000],
                "bid": [100.0, 100.0],
                "ask": [101.0, 101.0],
                "bid_vol": [0.0, 0.0],
                "ask_vol": [0.0, 0.0],
            }
        ),
    )
    _entry(store, 2, BASE, BASE + 86_400_000)

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["days"][0]["problems"] == ["rows_outside_day"]
    assert report["days"][0]["rows_outside_day"] == 1
    assert report["summary"]["integrity_problems"] == 1


def test_verify_reports_a_file_without_a_manifest_entry(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    _one_row(store)

    report = quality.verify_symbol(store, DAY, DAY)

    assert report["summary"]["files_not_in_manifest"] == ["2026-03-03"]
    assert report["summary"]["integrity_problems"] == 0
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)
    assert (
        main(
            ["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]
        )
        == 1
    )


def test_default_verify_finds_a_file_before_the_first_manifest_day(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    _one_row(store)
    _entry(store, 1, BASE, BASE)
    store.write_day(
        date(2025, 12, 30),
        pa.table(
            {
                "ts_ms": [BASE],
                "bid": [100.0],
                "ask": [101.0],
                "bid_vol": [0.0],
                "ask_vol": [0.0],
            }
        ),
    )

    report = quality.verify_symbol(store)

    assert "2025-12-30" in report["summary"]["files_not_in_manifest"]
    assert (
        "2025-12-30"
        not in quality.verify_symbol(store, DAY, DAY)["summary"]["files_not_in_manifest"]
    )
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)
    assert main(["ticks", "verify", "--symbol", "XAUUSD"]) == 1


def test_verify_prints_the_report_path_it_wrote(tmp_path, monkeypatch, capsys):
    store = TickStore(tmp_path, "XAUUSD")
    _one_row(store)
    _entry(store, 1, BASE, BASE)
    expected = str(tmp_path / "reports" / "quality-XAUUSD.json")
    monkeypatch.setattr("losslens.cli.resolve_data_root", lambda: tmp_path)

    report = quality.verify_symbol(store, DAY, DAY)
    assert report["report_path"] == expected
    assert (
        main(
            ["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]
        )
        == 0
    )
    assert f"Quality report: {expected}" in capsys.readouterr().out


def test_weekdays_without_data_are_listed(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [BASE],
                "bid": [100.0],
                "ask": [101.0],
                "bid_vol": [0.0],
                "ask_vol": [0.0],
            }
        ),
    )
    manifest = store.load_manifest()
    manifest["days"]["2026-03-03"] = make_entry(DAY, "complete", 1, BASE, BASE, "test", NOW)
    store.save_manifest(manifest)

    report = quality.verify_symbol(store, date(2026, 3, 3), date(2026, 3, 8))
    assert report["summary"]["missing_weekdays"] == [
        "2026-03-04",
        "2026-03-05",
        "2026-03-06",
    ]
