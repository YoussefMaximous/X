from datetime import date, datetime, timezone

import pyarrow as pa
import pyarrow.parquet as pq

from losslens.cli import main
from losslens.ticks import quality
from losslens.ticks.store import TickStore, make_entry

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
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
    monkeypatch.setattr("losslens.cli.DATA_ROOT", tmp_path)

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
    monkeypatch.setattr("losslens.cli.DATA_ROOT", tmp_path)

    assert main(["ticks", "verify", "--symbol", "XAUUSD", "--from", "2026-03-03", "--to", "2026-03-03"]) == 0


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
    manifest["days"]["2026-03-03"] = make_entry(
        DAY, "complete", 1, BASE, BASE, "test", NOW
    )
    store.save_manifest(manifest)

    report = quality.verify_symbol(store, date(2026, 3, 3), date(2026, 3, 8))
    assert report["summary"]["missing_weekdays"] == [
        "2026-03-04",
        "2026-03-05",
        "2026-03-06",
    ]
