from pathlib import Path

import pytest

from losslens.cli import main
from losslens.mt4.report import ReportError, parse_report, parse_report_text

FIXTURE = Path(__file__).parent / "fixtures" / "mt4_report_probe.htm"


def test_parse_probe_report():
    report = parse_report(FIXTURE)

    assert report.expert == "LossLensProbe"
    assert report.server == "ICMarketsSC-Demo04"
    assert report.build == "Build 1492"
    assert report.symbol == "XAUUSD (Gold vs US Dollar)"
    assert report.period.startswith("1 Minute (M1)")
    assert report.model.startswith("Every tick")
    assert report.bars == 1320
    assert report.ticks_modelled == 471448
    assert report.modelling_quality == 23.16
    assert report.initial_deposit == 10000.0
    assert report.spread == 30
    assert report.total_net_profit == 0.0
    assert report.total_trades == 0
    assert report.trades == ()


def _report_with_trades() -> str:
    base = FIXTURE.read_text(encoding="utf-8")
    rows = (
        "<tr align=right><td>1</td><td>2026.03.03 14:05</td><td>buy</td>"
        "<td>11</td><td>0.10</td><td>2650.00</td><td>2640.00</td>"
        "<td>2660.00</td><td>10.00</td><td>10010.00</td></tr>\n"
        "<tr align=right><td>2</td><td>2026.03.03 15:05</td><td>sell</td>"
        "<td>12</td><td>0.20</td><td>2645.50</td><td></td>"
        "<td></td><td>-5.00</td><td>10005.00</td></tr>\n"
    )
    head, separator, tail = base.rpartition("</table>")
    text = head + rows + separator + tail
    return text.replace(
        "<tr align=left><td>Total trades</td><td align=right>0</td>",
        "<tr align=left><td>Total trades</td><td align=right>2</td>",
    )


def test_parse_closed_trades():
    report = parse_report_text(_report_with_trades())

    assert report.total_trades == 2
    assert len(report.trades) == 2

    first, second = report.trades
    assert first.ticket == 1
    assert first.close_time == "2026.03.03 14:05"
    assert first.kind == "buy"
    assert first.order == "11"
    assert first.size == 0.10
    assert first.close_price == 2650.0
    assert first.stop_loss == 2640.0
    assert first.take_profit == 2660.0
    assert first.profit == 10.0
    assert first.balance == 10010.0

    assert second.ticket == 2
    assert second.kind == "sell"
    assert second.order == "12"
    assert second.size == 0.20
    assert second.close_price == 2645.5
    assert second.stop_loss is None
    assert second.take_profit is None
    assert second.profit == -5.0
    assert second.balance == 10005.0


def test_missing_fields_are_refused(tmp_path):
    path = tmp_path / "not-a-report.htm"
    path.write_text(
        "<html><head><title>Strategy Tester: X</title></head><body></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(ReportError, match="missing report fields"):
        parse_report(path)


def test_non_html_is_refused():
    with pytest.raises(ReportError, match="not an HTML"):
        parse_report_text("this is not a report")


def test_cli_parse_report(capsys):
    assert main(["mt4", "parse-report", str(FIXTURE)]) == 0

    output = capsys.readouterr().out
    assert "expert: LossLensProbe" in output
    assert "bars: 1320" in output
    assert "ticks modelled: 471448" in output
    assert "total trades: 0" in output
