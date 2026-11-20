import struct
from datetime import datetime

import pyarrow as pa

from losslens.mt4 import export


def _table(rows):
    return pa.table(
        {
            "ts_ms": [row[0] for row in rows],
            "bid": [row[1] for row in rows],
            "ask": [row[1] + 0.2 for row in rows],
            "bid_vol": [0.0 for _ in rows],
            "ask_vol": [0.0 for _ in rows],
        }
    )


def _ms(text):
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)


def test_server_offset_at_dst_boundaries():
    cases = (
        ("2026-03-08T06:59:59+00:00", 2),
        ("2026-03-08T07:00:00+00:00", 3),
        ("2026-11-01T05:59:59+00:00", 3),
        ("2026-11-01T06:00:00+00:00", 2),
    )
    for text, hours in cases:
        moment = datetime.fromisoformat(text)
        seconds = int(moment.timestamp())
        assert export.server_offset_seconds(seconds) == hours * 3600


def test_price_rounding_half_away_from_zero():
    assert export.round_price(2650.125) == 2650.13
    assert export.round_price(2650.124) == 2650.12
    assert export.round_price(-2650.125) == -2650.13


def test_hst_bytes_for_five_ticks_across_two_minutes():
    rows = [
        (_ms("2026-03-03T10:00:00.100Z"), 2650.124),
        (_ms("2026-03-03T10:00:00.200Z"), 2650.125),
        (_ms("2026-03-03T10:00:00.300Z"), 2650.130),
        (_ms("2026-03-03T10:01:00.100Z"), 2650.120),
        (_ms("2026-03-03T10:01:00.200Z"), 2650.110),
    ]
    bars = export._bars_for_table(_table(rows), 2)
    expected_bars = [
        (
            export.server_seconds(_ms("2026-03-03T10:00:00Z") // 1000),
            2650.12,
            2650.13,
            2650.12,
            2650.13,
            3,
        ),
        (
            export.server_seconds(_ms("2026-03-03T10:01:00Z") // 1000),
            2650.12,
            2650.12,
            2650.11,
            2650.11,
            2,
        ),
    ]
    assert bars == expected_bars

    header = struct.pack("<i", 401)
    header += b"Copyright 2005-2025, MetaQuotes Ltd.".ljust(64, b"\0")[:64]
    header += b"XAUUSD".ljust(12, b"\0")[:12]
    header += struct.pack("<iiii", 1, 2, 0, 0)
    header += struct.pack("<13i", *([0] * 13))
    records = b"".join(struct.pack("<qddddqiq", *bar[:5], bar[5], 0, 0) for bar in expected_bars)
    assert export.hst_bytes("XAUUSD", bars, 2) == header + records
    assert len(header) == export.HST_HEADER_SIZE
    assert len(records) == 2 * export.HST_RECORD_SIZE
