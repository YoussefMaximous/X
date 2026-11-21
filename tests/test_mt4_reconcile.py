from datetime import date
from pathlib import Path

import pyarrow as pa
import pytest

from losslens.cli import main
from losslens.mt4.reconcile import ReconcileError, reconcile_trades
from losslens.mt4.report import TesterReport as Report
from losslens.mt4.report import TesterTrade as Trade
from losslens.ticks.store import TickStore

WINTER = date(2026, 3, 3)
SUMMER = date(2026, 7, 15)
WINTER_BASE = 1772496000
SUMMER_BASE = 1784073600
REPORT_FIXTURE = Path(__file__).parent / "fixtures" / "mt4_report_probe.htm"


def _table(ticks):
    return pa.table(
        {
            "ts_ms": [tick[0] for tick in ticks],
            "bid": [tick[1] for tick in ticks],
            "ask": [tick[2] for tick in ticks],
            "bid_vol": [0.0 for _ in ticks],
            "ask_vol": [0.0 for _ in ticks],
        }
    )


def _store(tmp_path):
    store = TickStore(tmp_path, "XAUUSD")
    store.write_day(
        WINTER,
        _table(
            [
                ((WINTER_BASE + 10 * 3600) * 1000, 2650.00, 2650.20),
                ((WINTER_BASE + 10 * 3600 + 30) * 1000, 2650.10, 2650.30),
            ]
        ),
    )
    store.write_day(
        SUMMER,
        _table([((SUMMER_BASE + 9 * 3600) * 1000, 2650.00, 2650.20)]),
    )
    return store


def _trade(ticket, close_time, kind, close_price):
    return Trade(
        ticket=ticket,
        close_time=close_time,
        kind=kind,
        order=str(ticket),
        size=0.10,
        close_price=close_price,
        stop_loss=None,
        take_profit=None,
        profit=0.0,
        balance=10000.0,
    )


def _report(trades):
    return Report(
        expert="Test",
        server="Server",
        build="Build 1492",
        symbol="XAUUSD",
        period="1 Minute (M1)",
        model="Every tick",
        bars=1,
        ticks_modelled=1,
        modelling_quality=0.0,
        initial_deposit=10000.0,
        spread=30,
        total_net_profit=0.0,
        total_trades=len(trades),
        trades=tuple(trades),
    )


def test_reconcile_finds_buy_at_bid_and_sell_at_ask(tmp_path):
    report = _report(
        [
            _trade(1, "2026.03.03 12:00", "buy", 2650.00),
            _trade(2, "2026.03.03 12:00", "sell", 2650.20),
        ]
    )

    result = reconcile_trades(_store(tmp_path), report)

    assert result.reconciled
    assert result.checked == 2
    assert result.found == 2
    assert result.missing == 0
    assert all(check.difference == 0 for check in result.checks)


def test_reconcile_marks_a_missing_close(tmp_path):
    report = _report(
        [
            _trade(1, "2026.03.03 12:00", "buy", 2650.00),
            _trade(3, "2026.03.03 12:01", "buy", 2650.00),
        ]
    )

    result = reconcile_trades(_store(tmp_path), report)

    assert not result.reconciled
    assert result.found == 1
    assert result.missing == 1
    assert result.checks[1].ticket == 3
    assert result.checks[1].found is False


def test_reconcile_uses_the_summer_offset(tmp_path):
    report = _report([_trade(4, "2026.07.15 12:00", "buy", 2650.00)])

    result = reconcile_trades(_store(tmp_path), report)

    assert result.reconciled
    assert result.checks[0].found


def test_unreadable_time_is_refused(tmp_path):
    report = _report([_trade(1, "not a time", "buy", 2650.00)])

    with pytest.raises(ReconcileError, match="unreadable trade time"):
        reconcile_trades(_store(tmp_path), report)


def _report_with_trade(close_time, kind, close_price):
    base = REPORT_FIXTURE.read_text(encoding="utf-8")
    row = (
        f"<tr align=right><td>1</td><td>{close_time}</td><td>{kind}</td>"
        f"<td>1</td><td>0.10</td><td>{close_price}</td><td></td><td></td>"
        "<td>0.00</td><td>10000.00</td></tr>\n"
    )
    head, separator, tail = base.rpartition("</table>")
    return head + row + separator + tail


def test_cli_reconcile(tmp_path, monkeypatch, capsys):
    _store(tmp_path)
    monkeypatch.setenv("LOSSLENS_DATA", str(tmp_path))
    report = tmp_path / "report.htm"
    report.write_text(_report_with_trade("2026.03.03 12:00", "buy", "2650.00"), encoding="utf-8")

    code = main(["mt4", "reconcile", "--report", str(report), "--symbol", "XAUUSD"])

    assert code == 0
    output = capsys.readouterr().out
    assert "trades checked: 1" in output
    assert "found in ticks: 1" in output
    assert "RESULT: reconciled" in output
