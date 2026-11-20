"""Download one UTC day of Dukascopy ticks into a temporary CSV."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv

from .store import empty_table, normalise

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


def instrument_for(symbol: str) -> str:
    try:
        return INSTRUMENTS[symbol.upper()]
    except KeyError:
        raise DownloadError(
            f"no Dukascopy instrument mapping for {symbol!r}; "
            "use 'ticks import' for other tick files"
        ) from None


def find_browser() -> str | None:
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return None


def download_day(symbol: str, day: date) -> Path | None:
    """Download one UTC day; return the CSV path, or None when the day is empty.

    The caller owns the returned file's temporary folder and must delete it.
    """
    instrument = instrument_for(symbol)
    npx = shutil.which("npx")
    if not npx:
        raise DownloadError("npx was not found on PATH; install Node.js and run npm install")

    local_package = Path.cwd() / "node_modules" / "dukascopy-node" / "package.json"
    if not local_package.exists():
        raise DownloadError(
            "dukascopy-node is not installed; run 'npm install' from the repository root"
        )

    browser = find_browser()
    if not browser:
        raise DownloadError(
            "Chrome or Edge was not found in its standard install folder; "
            "run 'npx dukascopy-node --install-browser' once"
        )

    work_dir = Path(tempfile.mkdtemp(prefix="losslens-duka-"))
    cmd = [
        npx,
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
            cwd=Path.cwd(),
            timeout=600,
        )
    except Exception as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise DownloadError(f"could not start dukascopy-node: {exc}") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        shutil.rmtree(work_dir, ignore_errors=True)
        raise DownloadError(
            f"dukascopy-node exited {proc.returncode}: {detail[-800:]}"
        )

    files = sorted(work_dir.rglob("*.csv"))
    if not files:
        shutil.rmtree(work_dir, ignore_errors=True)
        return None
    return max(files, key=lambda p: p.stat().st_size)


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
