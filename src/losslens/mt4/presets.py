"""Read and write MT4 expert inputs: .set presets and .mq4 declarations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_INPUT_RE = re.compile(
    r"(?:extern|input|sinput)\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=\s*([^;]+);",
    re.IGNORECASE,
)


class PresetError(RuntimeError):
    """The expert inputs cannot be read or written."""


@dataclass(frozen=True)
class ExpertInput:
    name: str
    value: str
    start: str | None = None
    step: str | None = None
    stop: str | None = None


def parse_set(text: str) -> tuple[ExpertInput, ...]:
    order: list[str] = []
    fields: dict[str, dict[str, str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";") or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        name, comma, field = key.partition(",")
        name = name.strip()
        if not name:
            continue
        if name not in fields:
            fields[name] = {}
            order.append(name)
        if comma:
            fields[name][field.strip().lower()] = value
        else:
            fields[name]["value"] = value
    return tuple(
        ExpertInput(
            name=name,
            value=fields[name].get("value", ""),
            start=fields[name].get("1"),
            step=fields[name].get("2"),
            stop=fields[name].get("3"),
        )
        for name in order
    )


def render_set(inputs: tuple[ExpertInput, ...]) -> str:
    lines = ["; saved by loss-lens"]
    for item in inputs:
        lines.append(f"{item.name}={item.value}")
        if item.start is not None or item.step is not None or item.stop is not None:
            lines.append(f"{item.name},F=0")
            lines.append(f"{item.name},1={item.start or '0'}")
            lines.append(f"{item.name},2={item.step or '0'}")
            lines.append(f"{item.name},3={item.stop or '0'}")
    return "\n".join(lines) + "\n"


def parse_mq4_inputs(text: str) -> tuple[ExpertInput, ...]:
    cleaned = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"//[^\n]*", "", cleaned)
    return tuple(
        ExpertInput(name=match.group(2), value=match.group(3).strip())
        for match in _INPUT_RE.finditer(cleaned)
    )


def read_inputs(path: Path) -> tuple[ExpertInput, ...]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".set":
        return parse_set(source.read_text(encoding="utf-8", errors="replace"))
    if suffix in (".mq4", ".mqh"):
        return parse_mq4_inputs(source.read_text(encoding="utf-8", errors="replace"))
    raise PresetError(f"expected a .set or .mq4 file, got {source.suffix or 'no suffix'}")


def write_set(path: Path, inputs: tuple[ExpertInput, ...]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_set(inputs), encoding="utf-8", newline="\n")
    return target
