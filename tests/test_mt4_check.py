import struct
from datetime import date

import pyarrow as pa

from losslens.mt4.check import check_probe_ticks
from losslens.mt4.export import round_price, server_seconds
from losslens.ticks.store import TickStore

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
