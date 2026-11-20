"""Download one UTC day of Dukascopy ticks into a temporary CSV."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.csv as pacsv

from .store import empty_table, normalise, repository_root

INSTRUMENTS = {
    "XAUUSD": "xauusd",
}

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


class DownloadError(RuntimeError):
    """A day's download failed; the day must not be recorded."""


class SetupError(RuntimeError):
    """The machine is not set up for downloading; retrying cannot help."""


def instrument_for(symbol: str) -> str:
    try:
        return INSTRUMENTS[symbol.upper()]
    except KeyError:
        raise SetupError(
            f"no Dukascopy instrument mapping for {symbol!r}; "
            "use 'ticks import' for other tick files"
        ) from None


def find_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def cleanup_stale_temp_dirs(
    temp_root: Path | str | None = None,
    *,
    max_age_seconds: float = 3600,
    now: float | None = None,
) -> list[Path]:
    """Remove old losslens download folders; leave recent ones for running syncs."""
    root = Path(temp_root) if temp_root is not None else Path(tempfile.gettempdir())
    if not root.is_dir():
        return []
    cutoff = (time.time() if now is None else now) - max_age_seconds
    removed: list[Path] = []
    for path in root.glob("losslens-duka-*"):
        if not path.is_dir():
            continue
        try:
            if path.stat().st_mtime > cutoff:
                continue
            shutil.rmtree(path, ignore_errors=True)
            removed.append(path)
        except OSError:
            continue
    return removed


def _download_script(root: Path) -> Path:
    """Read the bin entry named dukascopy-node from the pinned package."""
    package_dir = root / "node_modules" / "dukascopy-node"
    package_file = package_dir / "package.json"
    if not package_file.is_file():
        raise SetupError(
            "dukascopy-node is not installed; run 'npm install' in the repository folder"
        )
    try:
        package = cast(dict[str, Any], json.loads(package_file.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"could not read {package_file}: {exc}") from exc

    bin_value = package.get("bin")
    script: str | None = None
    if isinstance(bin_value, dict):
        entry = bin_value.get("dukascopy-node")
        script = entry if isinstance(entry, str) else None
    elif isinstance(bin_value, str):
        script = bin_value
    if not script:
        raise SetupError("dukascopy-node package has no 'bin' entry named 'dukascopy-node'")

    path = (package_dir / script).resolve()
    if not path.is_file():
        raise SetupError(f"dukascopy-node script not found: {path}")
    return path


def download_day(symbol: str, day: date, temp_root: Path | str | None = None) -> Path | None:
    """Download one UTC day; return the CSV path, or None when the day is empty.

    The caller owns the returned file's temporary folder and must delete it.
    """
    instrument = instrument_for(symbol)
    node = shutil.which("node")
    if not node:
        raise SetupError("node was not found on PATH; install Node.js and run npm install")

    root = repository_root()
    script = _download_script(root)

    browser = find_browser()
    if not browser:
        raise SetupError(
            "Chrome or Edge was not found in its standard install folder; "
            "install Google Chrome or Microsoft Edge"
        )

    work_dir = Path(
        tempfile.mkdtemp(
            prefix="losslens-duka-",
            dir=str(temp_root) if temp_root is not None else None,
        )
    )
    keep = False
    try:
        cmd = [
            node,
            str(script),
            "dukascopy-node",
            "-i",
            instrument,
            "-from",
            day.isoformat(),
            "-to",
            (day + timedelta(days=1)).isoformat(),
            "-t",
            "tick",
            "-f",
            "csv",
            "-v",
            "-vu",
            "units",
            "-r",
            "3",
            "-rp",
            "1500",
            "-s",
            "--chrome-path",
            browser,
            "-dir",
            str(work_dir),
        ]

        env = os.environ.copy()
        existing_options = env.get("NODE_OPTIONS", "").strip()
        env["NODE_OPTIONS"] = (existing_options + " --use-system-ca").strip()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="replace",
                env=env,
                cwd=root,
                stdin=subprocess.DEVNULL,
                timeout=600,
            )
        except Exception as exc:
            raise DownloadError(f"could not start dukascopy-node: {exc}") from exc

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise DownloadError(f"dukascopy-node exited {proc.returncode}: {detail[-800:]}")

        files = sorted(work_dir.rglob("*.csv"))
        if not files:
            return None
        keep = True
        return max(files, key=lambda path: path.stat().st_size)
    finally:
        if not keep:
            shutil.rmtree(work_dir, ignore_errors=True)


def read_dukascopy_csv(path: Path | None) -> pa.Table:
    """Map a Dukascopy CSV by column name (ask comes before bid) and sort it."""
    if path is None or not path.exists() or path.stat().st_size == 0:
        return empty_table()

    csv_table = pacsv.read_csv(
        path,
        convert_options=pacsv.ConvertOptions(
            column_types={
                "timestamp": pa.int64(),
                "askPrice": pa.float64(),
                "bidPrice": pa.float64(),
                "askVolume": pa.float32(),
                "bidVolume": pa.float32(),
            }
        ),
    )

    required = {"timestamp", "askPrice", "bidPrice", "askVolume", "bidVolume"}
    missing = required - set(csv_table.column_names)
    if missing:
        raise DownloadError(f"downloaded CSV is missing columns: {sorted(missing)}")

    table = pa.table(
        {
            "ts_ms": csv_table["timestamp"],
            "bid": csv_table["bidPrice"],
            "ask": csv_table["askPrice"],
            "bid_vol": csv_table["bidVolume"],
            "ask_vol": csv_table["askVolume"],
        }
    )
    return normalise(table)
