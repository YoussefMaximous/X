"""The MT4 start file: build it, and check it can only start the tester."""

from __future__ import annotations

from datetime import date

TESTER_KEYS = frozenset(
    {
        "TestExpert",
        "TestSymbol",
        "TestPeriod",
        "TestModel",
        "TestSpread",
        "TestOptimization",
        "TestDateEnable",
        "TestFromDate",
        "TestToDate",
        "TestReport",
        "TestReplaceReport",
        "TestShutdownTerminal",
        "TestVisualEnable",
    }
)

TESTER_FIXED_LINES = (
    "ExpertsEnable=false",
    "ExpertsTrades=false",
    "ExpertsDllImport=false",
    "ExpertsExpImport=false",
    "EnableNews=false",
    "EnableDDE=false",
    "AutoConfiguration=false",
    "ProxyEnable=true",
    "ProxyServer=127.0.0.1:9",
    "ProxyType=HTTP",
)


def build_start_file(
    symbol: str,
    from_day: date,
    to_day_exclusive: date,
    spread: int,
    expert: str = "LossLensProbe",
) -> str:
    lines = [
        f"TestExpert={expert}",
        f"TestSymbol={symbol}",
        "TestPeriod=M1",
        "TestModel=0",
        f"TestSpread={spread}",
        "TestOptimization=false",
        "TestDateEnable=true",
        f"TestFromDate={from_day:%Y.%m.%d}",
        f"TestToDate={to_day_exclusive:%Y.%m.%d}",
        r"TestReport=tester\losslens_report",
        "TestReplaceReport=true",
        "TestShutdownTerminal=true",
        "TestVisualEnable=false",
        *TESTER_FIXED_LINES,
    ]
    return "\n".join(lines) + "\n"


def check_start_file(text: str) -> list[str]:
    problems: list[str] = []
    seen_keys: set[str] = set()
    seen_fixed: set[str] = set()
    optimization_value: str | None = None

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            problems.append(f"line {number}: not a key=value line: {line!r}")
            continue
        if key in seen_keys:
            problems.append(f"line {number}: duplicate key {key!r}")
        seen_keys.add(key)
        if line in TESTER_FIXED_LINES:
            seen_fixed.add(line)
        elif key in TESTER_KEYS:
            if key == "TestOptimization":
                optimization_value = value
        else:
            problems.append(f"line {number}: key {key!r} is not allowed")

    for fixed in TESTER_FIXED_LINES:
        if fixed not in seen_fixed:
            problems.append(f"missing fixed line: {fixed}")

    if optimization_value != "false":
        problems.append("TestOptimization must be false")

    return problems
