import json
import re
from datetime import UTC, date, datetime

import pyarrow as pa

from losslens.app.build import build_app
from losslens.cli import main
from losslens.ticks.store import TickStore, make_entry

DAY = date(2026, 3, 3)
BASE = 1772496000


def _store(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    ticks = [
        (BASE + 10 * 3600, 2650.00, 2650.20),
        (BASE + 10 * 3600 + 30, 2650.10, 2650.30),
        (BASE + 10 * 3600 + 60, 2650.20, 2650.40),
        (BASE + 10 * 3600 + 120, 2649.90, 2650.10),
    ]
    store.write_day(
        DAY,
        pa.table(
            {
                "ts_ms": [tick[0] * 1000 for tick in ticks],
                "bid": [tick[1] for tick in ticks],
                "ask": [tick[2] for tick in ticks],
                "bid_vol": [0.0 for _ in ticks],
                "ask_vol": [0.0 for _ in ticks],
            }
        ),
    )
    manifest = store.load_manifest()
    manifest["days"][DAY.isoformat()] = make_entry(
        DAY,
        "complete",
        len(ticks),
        ticks[0][0] * 1000,
        ticks[-1][0] * 1000,
        "test",
        datetime(2026, 11, 20, 12, tzinfo=UTC),
    )
    store.save_manifest(manifest)
    return store


def _payload(html):
    match = re.search(r"const DATA = (.*?);\n", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


def test_build_app_embeds_the_bars(tmp_path):
    out = tmp_path / "chart.html"
    path = build_app(_store(tmp_path), "XAUUSD", DAY, out)

    html = path.read_text(encoding="utf-8")
    data = _payload(html)

    assert data["symbol"] == "XAUUSD"
    assert data["day"] == "2026-03-03"
    assert data["digits"] == 2
    assert data["ticks"] == 4
    assert data["offset_hours"] == 2
    assert data["bid"] == 2649.90
    assert data["ask"] == 2650.10
    assert data["bars"] == [
        [BASE + 12 * 3600, 2650.0, 2650.1, 2650.0, 2650.1, 2],
        [BASE + 12 * 3600 + 60, 2650.2, 2650.2, 2650.2, 2650.2, 1],
        [BASE + 12 * 3600 + 120, 2649.9, 2649.9, 2649.9, 2649.9, 1],
    ]


def test_build_app_page_has_the_native_parts_and_no_outside_calls(tmp_path):
    html = build_app(_store(tmp_path), "XAUUSD", DAY, tmp_path / "chart.html").read_text(
        encoding="utf-8"
    )

    for text in ("Market Watch", "Terminal", "Journal", "M1", "M5", "D1", "File", "Charts"):
        assert text in html
    for text in ("://", "fetch(", "<script src=", "WebSocket"):
        assert text not in html


def test_cli_build_app(tmp_path, monkeypatch, capsys):
    _store(tmp_path)
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))
    out = tmp_path / "chart.html"

    code = main(
        [
            "app",
            "build",
            "--symbol",
            "XAUUSD",
            "--day",
            "2026-03-03",
            "--out",
            str(out),
        ]
    )

    assert code == 0
    output = capsys.readouterr().out
    assert "chart:" in output
    assert out.is_file()
