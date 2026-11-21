from losslens.desktop.chart import Bar, aggregate, bars_from_rows, price_text, time_text


def test_aggregate_five_one_minute_bars():
    bars = [
        Bar(0, 10.0, 12.0, 9.0, 11.0, 1),
        Bar(60, 11.0, 13.0, 10.0, 12.0, 2),
        Bar(120, 12.0, 12.5, 8.0, 9.5, 3),
        Bar(180, 9.5, 11.0, 9.0, 10.5, 4),
        Bar(240, 10.5, 14.0, 10.0, 13.5, 5),
    ]

    result = aggregate(bars, 5)

    assert len(result) == 1
    assert result[0] == Bar(0, 10.0, 14.0, 8.0, 13.5, 15)


def test_aggregate_one_minute_returns_a_copy():
    bars = [Bar(0, 1.0, 2.0, 0.5, 1.5, 1)]

    result = aggregate(bars, 1)

    assert result == bars
    assert result is not bars


def test_price_and_time_text():
    assert price_text(2650.1234, 3) == "2650.123"
    assert price_text(2650.1, 2) == "2650.10"
    assert time_text(0, 1) == "00:00"
    assert time_text(0, 1440) == "01.01"


def test_bars_from_rows():
    assert bars_from_rows([(0, 1.0, 2.0, 0.5, 1.5, 1)]) == [Bar(0, 1.0, 2.0, 0.5, 1.5, 1)]
