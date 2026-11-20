from datetime import date
from pathlib import Path

import pyarrow as pa

import losslens
from losslens.ticks.store import (
    TickStore,
    find_repository_root,
    read_ticks,
    resolve_data_root,
)


def test_losslens_data_env_is_honoured(monkeypatch, tmp_path):
    custom = tmp_path / "custom"
    monkeypatch.setenv("LOSSLENS_DATA", str(custom))

    assert resolve_data_root() == custom
    assert TickStore().root == custom


def test_repository_root_is_found_from_the_package(monkeypatch):
    monkeypatch.delenv("LOSSLENS_DATA", raising=False)

    root = find_repository_root()

    assert root is not None
    assert (root / "pyproject.toml").is_file()
    package = Path(losslens.__file__).resolve()
    assert package.is_relative_to(root)
    assert resolve_data_root() == root / "data"


def test_read_ticks_uses_the_same_data_root(monkeypatch, tmp_path):
    custom = tmp_path / "custom"
    monkeypatch.setenv("LOSSLENS_DATA", str(custom))
    store = TickStore(symbol="XAUUSD")
    store.write_day(
        date(2026, 3, 3),
        pa.table(
            {
                "ts_ms": [1772496000000],
                "bid": [100.0],
                "ask": [101.0],
                "bid_vol": [0.0],
                "ask_vol": [0.0],
            }
        ),
    )

    table = read_ticks("XAUUSD", 1772496000000, 1772496000001)

    assert table.num_rows == 1
