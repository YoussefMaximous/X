from pathlib import Path

import pytest

from losslens.cli import main
from losslens.mt4.journal import JournalError, parse_journal, parse_journal_text

FIXTURE = Path(__file__).parent / "fixtures" / "mt4_tester.log"


def test_parse_measured_journal():
    lines = parse_journal(FIXTURE)

    assert len(lines) == 8
    assert lines[0].level == 0
    assert lines[0].time == "00:59:31.832"
    assert "loaded successfully" in lines[0].message
    assert lines[2].message == "TestGenerator: spread set to 30"
    assert lines[3].level == 2
    assert "test started" in lines[3].message
    assert "471348 tick events" in lines[6].message
    assert "removed" in lines[7].message


def test_continuation_line_stays_in_the_same_message():
    lines = parse_journal_text("0\t00:00:00.000\tfirst\nsecond line\n")

    assert len(lines) == 1
    assert lines[0].message == "first\nsecond line"


def test_line_without_columns_is_refused():
    with pytest.raises(JournalError, match="no level and time"):
        parse_journal_text("not a journal\n")


def test_non_integer_level_is_refused():
    with pytest.raises(JournalError, match="not an integer"):
        parse_journal_text("x\t00:00:00.000\tmessage\n")


def test_cli_parse_journal(capsys):
    assert main(["mt4", "parse-journal", str(FIXTURE)]) == 0

    output = capsys.readouterr().out
    assert "lines: 8" in output
    assert "spread set to 30" in output
    assert "removed" in output


def test_cli_tail_limits_the_output(capsys):
    assert main(["mt4", "parse-journal", str(FIXTURE), "--tail", "2"]) == 0

    output = capsys.readouterr().out
    assert "spread set to 30" not in output
    assert "tick events" in output
    assert "removed" in output
