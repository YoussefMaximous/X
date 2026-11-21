import pytest

from losslens.cli import main
from losslens.mt4.presets import (
    ExpertInput,
    PresetError,
    parse_mq4_inputs,
    parse_set,
    read_inputs,
    render_set,
    write_set,
)

SET_TEXT = """; saved by MetaTrader
Lots=0.10
Lots,F=0
Lots,1=0.01
Lots,2=0.01
Lots,3=0.10
StopLoss=50
"""

MQ4_TEXT = """
extern double Lots = 0.10;
input int StopLoss = 50; // comment
input string Comment = "hello";
input bool UseTrail = true;
"""


def test_parse_set_with_ranges():
    inputs = parse_set(SET_TEXT)

    assert [item.name for item in inputs] == ["Lots", "StopLoss"]
    assert inputs[0] == ExpertInput("Lots", "0.10", "0.01", "0.01", "0.10")
    assert inputs[1] == ExpertInput("StopLoss", "50")


def test_render_set_round_trips():
    inputs = parse_set(SET_TEXT)

    assert parse_set(render_set(inputs)) == inputs
    assert "Lots,1=0.01" in render_set(inputs)
    assert "Lots,3=0.10" in render_set(inputs)


def test_parse_mq4_inputs():
    inputs = parse_mq4_inputs(MQ4_TEXT)

    assert [item.name for item in inputs] == ["Lots", "StopLoss", "Comment", "UseTrail"]
    assert inputs[0].value == "0.10"
    assert inputs[1].value == "50"
    assert inputs[2].value == '"hello"'
    assert inputs[3].value == "true"


def test_read_inputs_rejects_unknown_suffix(tmp_path):
    path = tmp_path / "inputs.txt"
    path.write_text("Lots=0.10\n", encoding="utf-8")

    with pytest.raises(PresetError, match="expected"):
        read_inputs(path)


def test_write_set(tmp_path):
    inputs = parse_set(SET_TEXT)
    path = write_set(tmp_path / "expert.set", inputs)

    assert path.is_file()
    assert path.read_text(encoding="utf-8") == render_set(inputs)


def test_cli_lists_inputs(tmp_path, capsys):
    path = tmp_path / "expert.set"
    path.write_text(SET_TEXT, encoding="utf-8")

    assert main(["mt4", "inputs", str(path)]) == 0

    output = capsys.readouterr().out
    assert "Lots=0.10  [0.01 .. 0.10 step 0.01]" in output
    assert "StopLoss=50" in output
