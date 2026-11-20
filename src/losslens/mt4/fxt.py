"""Decode MT4 FXT files for inspection."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

EXPECTED_HEADER = 728
EXPECTED_RECORD = 56
EXPECTED_FORMAT = "<qddddqii"


@dataclass
class FxtLayout:
    header_size: int
    record_size: int
    record_format: str


def detect_layout(size: int) -> FxtLayout | None:
    for header_size, record_size, record_format in (
        (EXPECTED_HEADER, EXPECTED_RECORD, EXPECTED_FORMAT),
        (148, 60, "<qddddqiq"),
    ):
        if size >= header_size and (size - header_size) % record_size == 0:
            return FxtLayout(header_size, record_size, record_format)
    return None


def inspect_fxt(path: Path) -> str:
    data = Path(path).read_bytes()
    layout = detect_layout(len(data))
    if layout is None:
        return f"file: {path}\nsize: {len(data)}\nlayout: not recognised"
    count = (len(data) - layout.header_size) // layout.record_size
    lines = [
        f"file: {path}",
        f"size: {len(data)}",
        f"header size: {layout.header_size}",
        f"record size: {layout.record_size}",
        f"records: {count}",
        "header fields:",
    ]
    for offset in range(0, min(layout.header_size, 64), 4):
        raw = data[offset : offset + 4]
        integer = struct.unpack_from("<i", raw)[0]
        lines.append(f"  {offset:4d}: {raw.hex()}  int={integer}")
    records = []
    for index in range(count):
        offset = layout.header_size + index * layout.record_size
        records.append(struct.unpack_from(layout.record_format, data, offset))
    for label, subset in (("first", records[:5]), ("last", records[-5:])):
        lines.append(f"{label} records:")
        for record in subset:
            lines.append(f"  {record}")
    return "\n".join(lines)
