"""Read the summary and closed trades from an MT4 Strategy Tester report."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_TITLE_RE = re.compile(r"<title>\s*Strategy Tester:\s*(.*?)</title>", re.IGNORECASE | re.DOTALL)
_VERSION_RE = re.compile(r'<meta\s+name="version"\s+content="([^"]*)"', re.IGNORECASE)
_SERVER_RE = re.compile(r'<meta\s+name="server"\s+content="([^"]*)"', re.IGNORECASE)
_PROFIT_FACTOR_RE = re.compile(
    r"<td>\s*Profit factor\s*</td>\s*<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL
)
_DRAWDOWN_RE = re.compile(
    r"<td>\s*Maximal drawdown\s*</td>\s*<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL
)
_TRADE_HEADER = (
    "#",
    "Time",
    "Type",
    "Order",
    "Size",
    "Price",
    "S / L",
    "T / P",
    "Profit",
    "Balance",
)
_SUMMARY_LABELS = (
    "Symbol",
    "Period",
    "Model",
    "Bars in test",
    "Ticks modelled",
    "Modelling quality",
    "Initial deposit",
    "Spread",
    "Total net profit",
    "Total trades",
)


class ReportError(RuntimeError):
    """The file is not a strategy tester report we can read."""


@dataclass(frozen=True)
class TesterTrade:
    ticket: int
    close_time: str
    kind: str
    order: str
    size: float
    close_price: float
    stop_loss: float | None
    take_profit: float | None
    profit: float
    balance: float


@dataclass(frozen=True)
class TesterReport:
    expert: str
    server: str
    build: str
    symbol: str
    period: str
    model: str
    bars: int
    ticks_modelled: int
    modelling_quality: float
    initial_deposit: float
    spread: int
    total_net_profit: float
    total_trades: int
    trades: tuple[TesterTrade, ...]
    profit_factor: float | None = None
    max_drawdown: float = 0.0


def _text(fragment: str) -> str:
    text = _TAG_RE.sub("", fragment)
    for source, target in (
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
    ):
        text = text.replace(source, target)
    return text.strip()


def _cells(row: str) -> list[str]:
    return [_text(cell) for cell in _CELL_RE.findall(row)]


def _summary(rows: list[list[str]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for cells in rows:
        for index, cell in enumerate(cells):
            if cell not in _SUMMARY_LABELS:
                continue
            for following in cells[index + 1 :]:
                if following:
                    values[cell] = following
                    break
    return values


def _number(value: str) -> float:
    return float(value.replace(",", "").replace("%", "").strip())


def _integer(value: str) -> int:
    return int(_number(value))


def _optional_price(value: str) -> float | None:
    return None if not value else _number(value)


def _optional_number(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = _text(value)
    return _number(cleaned) if cleaned else None


def _trades(rows: list[list[str]]) -> tuple[TesterTrade, ...]:
    start: int | None = None
    for index, cells in enumerate(rows):
        if tuple(cells[:10]) == _TRADE_HEADER:
            start = index
            break
    if start is None:
        return ()
    trades: list[TesterTrade] = []
    for cells in rows[start + 1 :]:
        if len(cells) != 10 or not cells[0].isdigit():
            break
        trades.append(
            TesterTrade(
                ticket=int(cells[0]),
                close_time=cells[1],
                kind=cells[2],
                order=cells[3],
                size=_number(cells[4]),
                close_price=_number(cells[5]),
                stop_loss=_optional_price(cells[6]),
                take_profit=_optional_price(cells[7]),
                profit=_number(cells[8]),
                balance=_number(cells[9]),
            )
        )
    return tuple(trades)


def parse_report_text(text: str) -> TesterReport:
    if "<html" not in text.lower():
        raise ReportError("not an HTML strategy tester report")
    title = _TITLE_RE.search(text)
    if title is None:
        raise ReportError("no 'Strategy Tester' title")
    rows = [_cells(row) for row in _ROW_RE.findall(text)]
    summary = _summary(rows)
    missing = [label for label in _SUMMARY_LABELS if label not in summary]
    if missing:
        raise ReportError("missing report fields: " + ", ".join(missing))
    version = _VERSION_RE.search(text)
    server = _SERVER_RE.search(text)
    profit_match = _PROFIT_FACTOR_RE.search(text)
    drawdown_match = _DRAWDOWN_RE.search(text)
    profit_factor = _optional_number(profit_match.group(1)) if profit_match else None
    max_drawdown = 0.0
    if drawdown_match is not None:
        max_drawdown = _number(_text(drawdown_match.group(1)).split("(")[0].strip())
    return TesterReport(
        expert=_text(title.group(1)),
        server=_text(server.group(1)) if server is not None else "",
        build=_text(version.group(1)) if version is not None else "",
        symbol=summary["Symbol"],
        period=summary["Period"],
        model=summary["Model"],
        bars=_integer(summary["Bars in test"]),
        ticks_modelled=_integer(summary["Ticks modelled"]),
        modelling_quality=_number(summary["Modelling quality"]),
        initial_deposit=_number(summary["Initial deposit"]),
        spread=_integer(summary["Spread"]),
        total_net_profit=_number(summary["Total net profit"]),
        total_trades=_integer(summary["Total trades"]),
        trades=_trades(rows),
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
    )


def parse_report(path: Path) -> TesterReport:
    return parse_report_text(Path(path).read_text(encoding="utf-8", errors="replace"))
