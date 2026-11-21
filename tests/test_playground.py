import json
import re
from datetime import UTC, date, datetime

import pyarrow as pa
import pytest

from losslens.cli import main
from losslens.ticks.store import TickStore

DAY = date(2026, 3, 3)
TICKS = [
    [1772546400100, 2650.10, 2650.40],
    [1772546405200, 2650.25, 2650.55],
    [1772546410300, 2650.05, 2650.35],
    [1772546415400, 2649.90, 2650.20],
    [1772546420500, 2650.35, 2650.65],
    [1772546425600, 2650.60, 2650.90],
]
SCRIPT = re.compile(
    r'<script id="tick-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)


@pytest.fixture
def tick_store(tmp_path, monkeypatch):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [tick[0] for tick in TICKS],
                "bid": [tick[1] for tick in TICKS],
                "ask": [tick[2] for tick in TICKS],
                "bid_vol": [0.0] * len(TICKS),
                "ask_vol": [0.0] * len(TICKS),
            }
        ),
    )
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))
    return tmp_path


def build(tmp_path, *extra):
    out = tmp_path / "playground.html"
    args = [
        "playground",
        "build",
        "--symbol",
        "XAUUSD",
        "--day",
        "2026-03-03",
        "--from",
        "14:00",
        "--to",
        "14:01",
        "--out",
        str(out),
        *extra,
    ]
    return main(args), out


def test_build_writes_one_self_contained_page(tick_store, tmp_path):
    code, out = build(tmp_path)

    assert code == 0
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    match = SCRIPT.search(html)
    assert match is not None
    data = json.loads(match.group(1))
    assert data["symbol"] == "XAUUSD"
    assert data["day"] == "2026-03-03"
    assert data["window"] == {"from": "14:00", "to": "14:01"}
    assert data["tickCount"] == len(TICKS)
    assert len(data["ticks"]) == len(TICKS)
    assert data["firstTick"] == TICKS[0]
    assert data["lastTick"] == TICKS[-1]
    assert data["ticks"][0] == TICKS[0]
    assert data["ticks"][-1] == TICKS[-1]

    assert "://" not in html
    assert "fetch(" not in html
    assert "<script src=" not in html
    assert "WebSocket" not in html

    for label in (
        "Next tick",
        "Next 10",
        "Next 100",
        "Reset",
        "Buy",
        "Sell",
        "Both ways",
        "Run to end",
        "PAUSED",
        "FUTURE HIDDEN",
    ):
        assert label in html
    assert 'id="grid-step"' in html
    assert 'id="grid-custom"' in html
    for step in ("0.01", "0.05", "0.10", "0.25", "0.50", "1.00", "custom"):
        assert f'value="{step}"' in html

    for name in (
        "Order" + "Send(",
        "Order" + "Close(",
        "Order" + "CloseBy(",
        "Order" + "Modify(",
        "Order" + "Delete(",
    ):
        assert name not in html


def test_build_stops_with_a_clear_message_when_over_the_cap(tick_store, tmp_path, capsys):
    code, out = build(tmp_path, "--max-ticks", "2")

    assert code == 2
    assert not out.exists()
    error = capsys.readouterr().err
    assert "the window has 6 ticks, more than --max-ticks 2" in error
    assert "choose a shorter --from/--to window" in error


def test_window_bounds_are_utc_epoch_milliseconds(tick_store, tmp_path):
    code, out = build(tmp_path)

    assert code == 0
    html = out.read_text(encoding="utf-8")
    match = SCRIPT.search(html)
    assert match is not None
    data = json.loads(match.group(1))
    expected_from = (
        int(
            (datetime(2026, 3, 3, tzinfo=UTC) - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds()
            * 1000
        )
        + 14 * 60 * 60 * 1000
    )
    expected_to = expected_from + 60_000
    assert data["fromMs"] == expected_from
    assert data["toMs"] == expected_to
    assert data["tickCount"] == 6
