import os
from datetime import date

import pytest

from losslens.cli import sync_days
from losslens.ticks import dukascopy
from losslens.ticks.store import TickStore


def test_old_temp_folders_are_removed_and_new_ones_kept(tmp_path):
    old = tmp_path / "losslens-duka-old"
    old.mkdir()
    os.utime(old, (1000, 1000))
    new = tmp_path / "losslens-duka-new"
    new.mkdir()
    os.utime(new, (2000, 2000))

    removed = dukascopy.cleanup_stale_temp_dirs(tmp_path, now=5000)

    assert removed == [old]
    assert not old.exists()
    assert new.exists()


def test_sync_cleans_stale_temp_folders_when_it_starts(tmp_path):
    old = tmp_path / "losslens-duka-old"
    old.mkdir()
    os.utime(old, (1000, 1000))
    store = TickStore(tmp_path / "store", "XAUUSD")
    day = date(2026, 3, 3)

    result = sync_days(
        store,
        "XAUUSD",
        day,
        day,
        printer=lambda *args, **kwargs: None,
        temp_root=tmp_path,
    )

    assert result["failures"] == []
    assert not old.exists()


def test_interrupted_download_removes_its_temp_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(dukascopy.shutil, "which", lambda name: "npx")
    monkeypatch.setattr(dukascopy, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(dukascopy, "find_browser", lambda: "chrome.exe")
    package = tmp_path / "node_modules" / "dukascopy-node"
    package.mkdir(parents=True)
    (package / "package.json").write_text("{}", encoding="utf-8")

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(dukascopy.subprocess, "run", interrupted)

    with pytest.raises(KeyboardInterrupt):
        dukascopy.download_day("XAUUSD", date(2026, 3, 3), temp_root=tmp_path)

    assert list(tmp_path.glob("losslens-duka-*")) == []
