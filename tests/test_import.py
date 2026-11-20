from datetime import date
from pathlib import Path

from losslens.ticks import importer
from losslens.ticks.store import TickStore

FIXTURES = Path(__file__).parent / "fixtures"


def test_import_iso_with_utc_offset_splits_at_midnight(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    result = importer.import_csv(
        store,
        FIXTURES / "import_sample.csv",
        "time",
        "bid",
        "ask",
        ts_format="iso",
        utc_offset_minutes=120,
    )

    assert result["days"] == {"2026-03-02": 1, "2026-03-03": 2}
    assert result["total_ticks"] == 3

    first_day = store.read_day(date(2026, 3, 2))
    assert first_day["ts_ms"].to_pylist() == [1772494200000]

    second_day = store.read_day(date(2026, 3, 3))
    assert second_day["ts_ms"].to_pylist() == [1772497800000, 1772497801000]
    assert second_day["bid_vol"].to_pylist() == [0.0, 0.0]

    entry = store.load_manifest()["days"]["2026-03-03"]
    assert entry["status"] == "imported"
    assert entry["source"] == "import:import_sample.csv"
    assert entry["ticks"] == 2


def test_import_epoch_seconds_with_offset(tmp_path):
    csv = tmp_path / "seconds.csv"
    csv.write_text(
        "ts,bid,ask,bv,av\n1772496000,100.0,101.0,1,2\n1772496001,100.5,101.5,1,2\n",
        encoding="utf-8",
    )
    store = TickStore(tmp_path, "XAUUSD")
    result = importer.import_csv(
        store,
        csv,
        "ts",
        "bid",
        "ask",
        bid_vol_col="bv",
        ask_vol_col="av",
        ts_format="epoch_s",
        utc_offset_minutes=1,
    )

    assert result["days"] == {"2026-03-02": 2}
    table = store.read_day(date(2026, 3, 2))
    assert table["ts_ms"].to_pylist() == [1772495940000, 1772495941000]
    assert table["bid_vol"].to_pylist() == [1.0, 1.0]
    assert table["ask_vol"].to_pylist() == [2.0, 2.0]


def test_import_replaces_the_days_it_contains(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    csv = tmp_path / "one.csv"
    csv.write_text("ts,bid,ask\n1772496000000,100,101\n", encoding="utf-8")
    importer.import_csv(store, csv, "ts", "bid", "ask", ts_format="epoch_ms")

    csv.write_text("ts,bid,ask\n1772496000000,200,201\n", encoding="utf-8")
    importer.import_csv(store, csv, "ts", "bid", "ask", ts_format="epoch_ms")

    table = store.read_day(date(2026, 3, 3))
    assert table.num_rows == 1
    assert table["bid"][0].as_py() == 200.0
    assert store.load_manifest()["days"]["2026-03-03"]["ticks"] == 1
