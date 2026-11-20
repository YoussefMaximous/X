import pyarrow as pa
from losslens.ticks import dukascopy
from losslens.ticks.store import SCHEMA


def test_dukascopy_csv_maps_ask_before_bid_by_name(tmp_path):
    csv = tmp_path / "xauusd-tick.csv"
    csv.write_text(
        "timestamp,askPrice,bidPrice,askVolume,bidVolume\n"
        "1772496002000,5346.755,5345.855,120,90\n"
        "1772496001086,5346.605,5345.755,110,80\n",
        encoding="utf-8",
    )

    table = dukascopy.read_dukascopy_csv(csv)

    assert table.schema == SCHEMA
    assert table["ts_ms"].to_pylist() == [1772496001086, 1772496002000]
    assert table["bid"].to_pylist() == [5345.755, 5345.855]
    assert table["ask"].to_pylist() == [5346.605, 5346.755]
    assert table["bid_vol"].to_pylist() == [80.0, 90.0]
    assert table["ask_vol"].to_pylist() == [110.0, 120.0]


def test_dukascopy_empty_file_is_an_empty_table(tmp_path):
    csv = tmp_path / "empty.csv"
    csv.write_bytes(b"")
    assert dukascopy.read_dukascopy_csv(csv).num_rows == 0


def test_instrument_mapping_is_explicit():
    assert dukascopy.instrument_for("XAUUSD") == "xauusd"
    assert dukascopy.instrument_for("xauusd") == "xauusd"
    try:
        dukascopy.instrument_for("EURUSD")
    except dukascopy.DownloadError:
        pass
    else:
        raise AssertionError("expected an explicit mapping error")


def test_table_values_survive_csv_round_trip(tmp_path):
    csv = tmp_path / "sample.csv"
    csv.write_text(
        "timestamp,askPrice,bidPrice,askVolume,bidVolume\n"
        "1772496001086,5346.605,5345.755,120,90\n",
        encoding="utf-8",
    )
    table = dukascopy.read_dukascopy_csv(csv)
    assert table.num_rows == 1
    assert isinstance(table, pa.Table)
    assert table["ts_ms"][0].as_py() == 1772496001086
