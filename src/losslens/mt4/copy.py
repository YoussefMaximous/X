"""Make the separate MT4 copy from an exact list of files."""

from __future__ import annotations

import shutil
from pathlib import Path

MT4_COPY_FILES = (
    "terminal.exe",
    "metaeditor.exe",
    "history/<server>/symbols.raw",
    "history/<server>/symgroups.raw",
)


class SetupError(RuntimeError):
    """The MT4 copy could not be made safely."""


def copy_target(data_root: Path) -> Path:
    return data_root / "mt4" / "terminal"


def setup_copy(
    source: Path, server: str, target: Path, *, replace: bool = False
) -> list[tuple[str, int]]:
    source = Path(source)
    target = Path(target)
    if (target / "terminal.exe").exists() and not replace:
        raise SetupError(f"the copy already exists at {target}; pass --replace to remove it")

    paths: list[tuple[str, Path]] = [
        ("terminal.exe", source / "terminal.exe"),
        ("metaeditor.exe", source / "metaeditor.exe"),
        (
            "history/default/symbols.raw",
            source / "history" / server / "symbols.raw",
        ),
        (
            "history/default/symgroups.raw",
            source / "history" / server / "symgroups.raw",
        ),
    ]
    missing = [name for name, path in paths if not path.is_file()]
    if missing:
        raise SetupError("missing source files: " + ", ".join(missing))

    if replace and target.exists():
        shutil.rmtree(target)
    (target / "history" / "default").mkdir(parents=True, exist_ok=True)

    copied: list[tuple[str, int]] = []
    for name, path in paths:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied.append((name, destination.stat().st_size))
    return copied
