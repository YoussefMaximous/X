from datetime import date, datetime, timezone

import pyarrow as pa

from losslens.ticks.store import DAY_MS, SCHEMA, TickStore, classify_status


def test_day_file_is_written_atomically(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    table = pa.table(
        {
            "ts_ms": [1772496001000, 1772496000000],
            "bid": [1.2, 1.1],
            "ask": [1.3, 1.2],
            "bid_vol": [1.0, 1.0],
            "ask_vol": [2.0, 2.0],
        }
    )
    path = store.write_day(date(2026, 3, 3), table)

    assert path == tmp_path / "ticks" / "XAUUSD" / "2026" / "2026-03-03.parquet"
    assert path.exists()
    assert not list(path.parent.glob("*.tmp"))
    assert store.read_day(date(2026, 3, 3)).schema == SCHEMA


def test_status_rule_from_fetch_time():
    day = date(2026, 3, 3)
    before_cutoff = datetime(2026, 3, 4, 5, 59, tzinfo=timezone.utc)
    after_cutoff = datetime(2026, 3, 4, 6, 0, tzinfo=timezone.utc)
    assert classify_status(before_cutoff, day, 10) == "partial"
    assert classify_status(after_cutoff, day, 10) == "complete"
    assert classify_status(after_cutoff, day, 0) == "empty"


def test_read_ticks_range_edges_across_two_days(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    day1 = 1772496000000  # 2026-03-03T00:00:00Z
    store.write_day(
        date(2026, 3, 3),
        pa.table(
            {
                "ts_ms": [day1 - 1, day1, day1 + 500],
                "bid": [1.0, 2.0, 3.0],
                "ask": [1.1, 2.1, 3.1],
                "bid_vol": [0.0, 0.0, 0.0],
                "ask_vol": [0.0, 0.0, 0.0],
            }
        ),
    )
    store.write_day(
        date(2026, 3, 4),
        pa.table(
            {
                "ts_ms": [day1 + DAY_MS, day1 + DAY_MS + 500],
                "bid": [4.0, 5.0],
                "ask": [4.1, 5.1],
                "bid_vol": [0.0, 0.0],
                "ask_vol": [0.0, 0.0],
            }
        ),
    )

    table = store.read_ticks(day1, day1 + DAY_MS)

    assert table["ts_ms"].to_pylist() == [day1, day1 + 500]
    assert table.schema == SCHEMA

    empty = store.read_ticks(day1 - 100, day1 - 50)
    assert empty.num_rows == 0
    assert empty.schema == SCHEMA


def test_read_ticks_keeps_duplicate_timestamps_in_source_order(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    day1 = 1772496000000
    store.write_day(
        date(2026, 3, 3),
        pa.table(
            {
                "ts_ms": [day1, day1, day1],
                "bid": [10.0, 20.0, 30.0],
                "ask": [10.1, 20.1, 30.1],
                "bid_vol": [0.0, 0.0, 0.0],
                "ask_vol": [0.0, 0.0, 0.0],
            }
        ),
    )
    table = store.read_ticks(day1, day1 + 1)
    assert table["bid"].to_pylist() == [10.0, 20.0, 30.0]
