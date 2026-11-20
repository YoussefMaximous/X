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
        "[Common]",
        *TESTER_FIXED_LINES,
        "[Tester]",
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
    ]
    return "\n".join(lines) + "\n"


def check_start_file(text: str) -> list[str]:
    problems: list[str] = []
    seen_keys: set[str] = set()
    seen_fixed: set[str] = set()
    section: str | None = None
    seen_common = False
    seen_tester = False
    optimization_value: str | None = None

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            if line == "[Common]":
                if seen_common:
                    problems.append(f"line {number}: duplicate [Common]")
                if seen_tester:
                    problems.append(f"line {number}: [Common] must come before [Tester]")
                seen_common = True
                section = "common"
            elif line == "[Tester]":
                if seen_tester:
                    problems.append(f"line {number}: duplicate [Tester]")
                if not seen_common:
                    problems.append(f"line {number}: [Common] must come first")
                seen_tester = True
                section = "tester"
            else:
                problems.append(f"line {number}: section {line!r} is not allowed")
                section = None
            continue

        key, separator, value = line.partition("=")
        if not separator:
            problems.append(f"line {number}: not a key=value line: {line!r}")
            continue
        if key in seen_keys:
            problems.append(f"line {number}: duplicate key {key!r}")
        seen_keys.add(key)

        if section is None:
            problems.append(f"line {number}: {key!r} is outside [Common] and [Tester]")
        elif line in TESTER_FIXED_LINES:
            if section != "common":
                problems.append(f"line {number}: fixed line {line!r} must be under [Common]")
            seen_fixed.add(line)
        elif key in TESTER_KEYS:
            if section != "tester":
                problems.append(f"line {number}: {key!r} must be under [Tester]")
            if key == "TestOptimization":
                optimization_value = value
        else:
            problems.append(f"line {number}: key {key!r} is not allowed")

    if not seen_common:
        problems.append("missing section [Common]")
    if not seen_tester:
        problems.append("missing section [Tester]")
    for fixed in TESTER_FIXED_LINES:
        if fixed not in seen_fixed:
            problems.append(f"missing fixed line: {fixed}")
    if optimization_value != "false":
        problems.append("TestOptimization must be false")

    return problems
