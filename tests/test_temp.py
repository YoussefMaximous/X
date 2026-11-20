import json
import os
import subprocess
from datetime import date
from types import SimpleNamespace

import pytest

from losslens.cli import sync_days
from losslens.ticks import dukascopy
from losslens.ticks.store import TickStore


def _fake_package(tmp_path, bin_entry="./dist/cli/index.js"):
    package = tmp_path / "node_modules" / "dukascopy-node"
    script = package / "dist" / "cli" / "index.js"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    (package / "package.json").write_text(
        json.dumps({"bin": {"dukascopy-node": bin_entry}}), encoding="utf-8"
    )
    return package, script


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
    monkeypatch.setattr(dukascopy.shutil, "which", lambda name: "node")
    monkeypatch.setattr(dukascopy, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(dukascopy, "find_browser", lambda: "chrome.exe")
    _fake_package(tmp_path)

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(dukascopy.subprocess, "run", interrupted)

    with pytest.raises(KeyboardInterrupt):
        dukascopy.download_day("XAUUSD", date(2026, 3, 3), temp_root=tmp_path)

    assert list(tmp_path.glob("losslens-duka-*")) == []


def test_download_command_uses_node_and_the_package_bin(tmp_path, monkeypatch):
    _, script = _fake_package(tmp_path)
    monkeypatch.setattr(dukascopy.shutil, "which", lambda name: "C:/fake/node.exe")
    monkeypatch.setattr(dukascopy, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(dukascopy, "find_browser", lambda: "chrome.exe")
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(dukascopy.subprocess, "run", fake_run)

    result = dukascopy.download_day("XAUUSD", date(2026, 3, 3), temp_root=tmp_path)

    assert result is None
    assert captured["cmd"][0] == "C:/fake/node.exe"
    assert captured["cmd"][1] == str(script.resolve())
    assert captured["cmd"][2] == "-i"
    assert captured["kwargs"]["stdin"] == subprocess.DEVNULL


def test_missing_bin_entry_is_a_setup_error(tmp_path, monkeypatch):
    package = tmp_path / "node_modules" / "dukascopy-node"
    package.mkdir(parents=True)
    (package / "package.json").write_text('{"bin": {}}', encoding="utf-8")
    monkeypatch.setattr(dukascopy.shutil, "which", lambda name: "node")
    monkeypatch.setattr(dukascopy, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(dukascopy, "find_browser", lambda: "chrome.exe")

    with pytest.raises(dukascopy.SetupError):
        dukascopy.download_day("XAUUSD", date(2026, 3, 3), temp_root=tmp_path)


def test_missing_node_is_a_setup_error(tmp_path, monkeypatch):
    monkeypatch.setattr(dukascopy.shutil, "which", lambda name: None)

    with pytest.raises(dukascopy.SetupError):
        dukascopy.download_day("XAUUSD", date(2026, 3, 3), temp_root=tmp_path)
