import struct
from datetime import date, datetime

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


def test_fxt_bytes_for_five_ticks_across_two_minutes():
    rows = [
        (_ms("2026-03-03T10:00:00.100Z"), 2650.124),
        (_ms("2026-03-03T10:00:00.200Z"), 2650.125),
        (_ms("2026-03-03T10:00:00.300Z"), 2650.130),
        (_ms("2026-03-03T10:01:00.100Z"), 2650.120),
        (_ms("2026-03-03T10:01:00.200Z"), 2650.110),
    ]
    template = bytes([0xAA]) * export.FXT_HEADER_SIZE

    result = export.build_fxt_for_table(
        _table(rows), 30, template, 2, date(2026, 3, 3), date(2026, 3, 3)
    )

    first_bar = export.server_seconds(_ms("2026-03-03T10:00:00Z") // 1000)
    last_bar = export.server_seconds(_ms("2026-03-03T10:01:00Z") // 1000)
    first_tick = export.server_seconds(_ms("2026-03-03T10:00:00Z") // 1000)
    last_tick = export.server_seconds(_ms("2026-03-03T10:01:00Z") // 1000)
    expected_header = bytearray(template)
    struct.pack_into("<i", expected_header, 216, 2)
    struct.pack_into("<i", expected_header, 220, first_bar)
    struct.pack_into("<i", expected_header, 224, last_bar)
    struct.pack_into("<i", expected_header, 252, 30)
    struct.pack_into("<i", expected_header, 472, 1772496000)
    struct.pack_into("<i", expected_header, 476, 1772582400)
    expected_records = [
        (first_bar, 2650.12, 2650.12, 2650.12, 2650.12, 1, first_tick, 0),
        (first_bar, 2650.12, 2650.13, 2650.12, 2650.13, 2, first_tick, 0),
        (first_bar, 2650.12, 2650.13, 2650.12, 2650.13, 3, first_tick, 0),
        (last_bar, 2650.12, 2650.12, 2650.12, 2650.12, 1, last_tick, 0),
        (last_bar, 2650.12, 2650.12, 2650.11, 2650.11, 2, last_tick, 0),
    ]
    expected = bytes(expected_header) + b"".join(
        struct.pack(export.FXT_RECORD_FORMAT, *record) for record in expected_records
    )

    assert result == expected
    assert result[216:220] == struct.pack("<i", 2)
    patched = set()
    for offset in (216, 220, 224, 252, 472, 476):
        patched.update(range(offset, offset + 4))
    assert all(result[index] == template[index] for index in range(728) if index not in patched)
    assert len(result) == export.FXT_HEADER_SIZE + 5 * export.FXT_RECORD_SIZE


def test_fxt_records_stop_at_broker_midnight():
    cutoff = 1772582400
    assert export.server_seconds(_ms("2026-03-03T21:59:58Z") // 1000) == cutoff - 2
    assert export.server_seconds(_ms("2026-03-03T21:59:59Z") // 1000) == cutoff - 1
    assert export.server_seconds(_ms("2026-03-03T22:00:00Z") // 1000) == cutoff

    rows = [
        (_ms("2026-03-03T21:59:58.000Z"), 2650.10),
        (_ms("2026-03-03T21:59:59.000Z"), 2650.11),
        (_ms("2026-03-03T22:00:00.000Z"), 2650.12),
        (_ms("2026-03-03T22:00:01.000Z"), 2650.13),
    ]
    template = bytes([0xAA]) * export.FXT_HEADER_SIZE

    result = export.build_fxt_for_table(
        _table(rows), 30, template, 2, date(2026, 3, 3), date(2026, 3, 3)
    )

    records = list(struct.iter_unpack(export.FXT_RECORD_FORMAT, result[export.FXT_HEADER_SIZE :]))
    assert len(records) == 2
    assert [record[0] for record in records] == [cutoff - 60, cutoff - 60]
    assert [record[6] for record in records] == [cutoff - 2, cutoff - 1]
    assert all(record[0] < cutoff and record[6] < cutoff for record in records)
    assert struct.unpack_from("<i", result, 216)[0] == 1
    assert struct.unpack_from("<i", result, 220)[0] == cutoff - 60
    assert struct.unpack_from("<i", result, 224)[0] == cutoff - 60
    assert struct.unpack_from("<i", result, 472)[0] == 1772496000
    assert struct.unpack_from("<i", result, 476)[0] == cutoff
