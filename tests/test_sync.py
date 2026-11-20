from datetime import date, datetime, timezone
from pathlib import Path

from losslens.cli import sync_days
from losslens.ticks.store import TickStore, make_entry

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
DAY = date(2026, 3, 3)


def _quiet(*args, **kwargs):
    pass


def _store(tmp_path):
    return TickStore(tmp_path, "XAUUSD")


def test_failed_download_is_not_recorded(tmp_path):
    store = _store(tmp_path)

    def boom(symbol, day):
        raise RuntimeError("network down")

    result = sync_days(
        store,
        "XAUUSD",
        DAY,
        date(2026, 3, 4),
        download=boom,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )

    assert result["failures"] == ["2026-03-03"]
    assert store.load_manifest()["days"] == {}
    assert not store.day_path(DAY).exists()


def test_finished_days_are_skipped_unless_forced(tmp_path):
    store = _store(tmp_path)
    manifest = store.load_manifest()
    manifest["days"]["2026-03-03"] = make_entry(
        DAY, "complete", 5, 1, 2, "dukascopy:xauusd", NOW
    )
    store.save_manifest(manifest)
    calls = []

    def fake(symbol, day):
        calls.append(day)
        return None

    result = sync_days(
        store,
        "XAUUSD",
        DAY,
        date(2026, 3, 4),
        download=fake,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )
    assert calls == []
    assert result["counts"] == {"complete": 1}
    assert result["failures"] == []

    def boom(symbol, day):
        raise RuntimeError("forced download failed")

    forced = sync_days(
        store,
        "XAUUSD",
        DAY,
        date(2026, 3, 4),
        force=True,
        download=boom,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )
    assert forced["failures"] == ["2026-03-03"]
    assert store.load_manifest()["days"]["2026-03-03"]["ticks"] == 5
    assert store.load_manifest()["days"]["2026-03-03"]["status"] == "complete"


def test_imported_days_are_never_downloaded_even_with_force(tmp_path):
    store = _store(tmp_path)
    manifest = store.load_manifest()
    manifest["days"]["2026-03-03"] = make_entry(
        DAY, "imported", 7, 1, 2, "import:mine.csv", NOW
    )
    store.save_manifest(manifest)

    def boom(symbol, day):
        raise AssertionError("must not download an imported day")

    result = sync_days(
        store,
        "XAUUSD",
        DAY,
        date(2026, 3, 4),
        force=True,
        download=boom,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )
    assert result["failures"] == []
    assert result["counts"] == {"imported": 1}


def test_empty_day_writes_no_parquet(tmp_path):
    store = _store(tmp_path)

    def nothing(symbol, day):
        return None

    result = sync_days(
        store,
        "XAUUSD",
        date(2026, 3, 7),
        date(2026, 3, 8),
        download=nothing,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )

    assert result["counts"] == {"empty": 1}
    assert not store.day_path(date(2026, 3, 7)).exists()
    entry = store.load_manifest()["days"]["2026-03-07"]
    assert entry["status"] == "empty"
    assert entry["ticks"] == 0
    assert entry["first_ts_ms"] is None


def test_partial_day_is_not_marked_complete(tmp_path):
    store = _store(tmp_path)

    def nothing(symbol, day):
        return None

    today = date(2026, 11, 20)
    result = sync_days(
        store,
        "XAUUSD",
        today,
        date(2026, 11, 21),
        download=nothing,
        now_fn=lambda: datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc),
        retries=0,
        printer=_quiet,
    )
    assert result["counts"] == {"partial": 1}
    assert store.load_manifest()["days"]["2026-11-20"]["status"] == "partial"


def test_successful_download_is_converted_and_temp_folder_removed(tmp_path):
    store = _store(tmp_path)

    def fake(symbol, day):
        folder = Path(tmp_path) / "downloads" / day.isoformat()
        folder.mkdir(parents=True)
        path = folder / "xauusd-tick.csv"
        path.write_text(
            "timestamp,askPrice,bidPrice,askVolume,bidVolume\n"
            "1772496001086,5346.605,5345.755,120,90\n",
            encoding="utf-8",
        )
        return path

    result = sync_days(
        store,
        "XAUUSD",
        DAY,
        date(2026, 3, 4),
        download=fake,
        now_fn=lambda: NOW,
        retries=0,
        printer=_quiet,
    )

    assert result["counts"] == {"complete": 1}
    assert result["failures"] == []
    table = store.read_day(DAY)
    assert table.num_rows == 1
    assert table["ask"][0].as_py() == 5346.605
    assert not (Path(tmp_path) / "downloads" / "2026-03-03").exists()
