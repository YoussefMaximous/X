"""Read the tab-separated journal MT4's strategy tester writes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class JournalError(RuntimeError):
    """The file is not a tester journal we can read."""


@dataclass(frozen=True)
class JournalLine:
    level: int
    time: str
    message: str


def parse_journal_text(text: str) -> tuple[JournalLine, ...]:
    lines: list[JournalLine] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t", 2)
        if len(parts) != 3:
            if not lines:
                raise JournalError(f"line has no level and time: {raw!r}")
            previous = lines[-1]
            lines[-1] = JournalLine(previous.level, previous.time, previous.message + "\n" + raw)
            continue
        level_text, time_text, message = parts
        try:
            level = int(level_text)
        except ValueError as exc:
            raise JournalError(f"level is not an integer: {level_text!r}") from exc
        lines.append(JournalLine(level, time_text, message))
    return tuple(lines)


def parse_journal(path: Path) -> tuple[JournalLine, ...]:
    return parse_journal_text(Path(path).read_text(encoding="utf-8", errors="replace"))
