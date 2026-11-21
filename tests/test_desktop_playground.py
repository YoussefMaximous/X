"""Tests for the native X Playground model, without a window."""

from __future__ import annotations

import pytest

from losslens.desktop.playground_model import PlaygroundModel, Tick

BASE = 1_772_496_000_000


def _ticks(prices: list[float], step_ms: int = 1_000, spread: float = 0.2) -> list[Tick]:
    return [
        Tick(BASE + index * step_ms, price, round(price + spread, 6))
        for index, price in enumerate(prices)
    ]


def _model(prices: list[float], step_ms: int = 1_000, spread: float = 0.2) -> PlaygroundModel:
    return PlaygroundModel(_ticks(prices, step_ms, spread), warmup_ms=0)


def test_warmup_reveals_the_first_five_minutes() -> None:
    ticks = _ticks([100.0 + index / 10 for index in range(61)], step_ms=10_000)
    model = PlaygroundModel(ticks)

    assert model.cursor == 30
    assert model.tick().ts_ms == BASE + 300_000


def test_start_time_opens_a_chosen_session() -> None:
    ticks = _ticks([100.0 + index / 10 for index in range(100)], step_ms=10_000)
    model = PlaygroundModel(ticks, start_ms=BASE + 50_000)

    assert model.cursor == 35
    assert model.tick().ts_ms == BASE + 350_000


def test_tick_bars_and_time_bars() -> None:
    prices = [100.0 + index for index in range(10)]
    model = _model(prices)
    model.advance(9)

    model.set_period("t1")
    assert len(model.bars()) == 10
    assert model.bars()[3].o == 103.0
    assert model.bars()[3].v == 1

    model.set_period("t10")
    assert len(model.bars()) == 1
    assert model.bars()[0].h == 109.0
    assert model.bars()[0].ac == 109.2

    minute_ticks = _ticks([100.0, 101.0, 102.0, 103.0], step_ms=30_000)
    minute_model = PlaygroundModel(minute_ticks, warmup_ms=0)
    minute_model.advance(3)
    minute_model.set_period("m1")
    bars = minute_model.bars()
    assert len(bars) == 2
    assert bars[0].t == BASE // 60_000 * 60_000
    assert bars[0].c == 101.0
    assert bars[1].c == 103.0


def test_next_bar_stops_on_the_bar_boundary() -> None:
    model = _model([100.0 + index for index in range(25)])
    model.set_period("t10")

    model.next_bar()
    assert model.cursor == 9
    model.next_bar()
    assert model.cursor == 19
    model.next_bar()
    assert model.cursor == 24

    model.cursor = 5
    model._invalidate_bars()
    model.next_bar()
    assert model.cursor == 9

    minute_model = PlaygroundModel(
        _ticks([100.0 + index for index in range(10)], step_ms=15_000), warmup_ms=0
    )
    minute_model.set_period("m1")
    minute_model.next_bar()
    assert minute_model.cursor == 3
    minute_model.next_bar()
    assert minute_model.cursor == 7


def test_buy_ticket_closes_at_take_profit() -> None:
    model = _model([100.0, 101.0, 102.0], spread=0.2)

    ticket = model.open_ticket("buy", 0.1, 99.5, 101.0)
    assert ticket.entry == 100.2
    assert ticket.status == "open"

    model.advance(1)
    assert ticket.status == "closed"
    assert ticket.close_reason == "T/P"
    assert ticket.close_price == 101.0
    assert ticket.realized == pytest.approx(8.0)
    assert model.balance() == pytest.approx(10_008.0)


def test_sell_ticket_closes_at_stop_loss() -> None:
    model = _model([100.0, 100.6], spread=0.2)

    ticket = model.open_ticket("sell", 0.1, 100.5, None)
    assert ticket.entry == 100.0

    model.advance(1)
    assert ticket.status == "closed"
    assert ticket.close_reason == "S/L"
    assert ticket.close_price == 100.5
    assert ticket.realized == pytest.approx(-5.0)


def test_prediction_scores_direction_and_mae() -> None:
    model = _model([100.0, 101.0, 99.0, 102.0])

    model.add_prediction(1, 101.0)
    model.advance(1)
    summary = model.prediction_summary()
    assert summary.count == 1
    assert summary.mae == 0.0
    assert summary.hit_rate == 1.0

    model.add_prediction(3, 100.0)
    model.advance(2)
    summary = model.prediction_summary()
    assert summary.count == 2
    assert summary.mae == 1.0
    assert summary.hit_rate == 0.5


def test_custom_tape_replaces_the_future_and_clears_to_the_branch() -> None:
    model = _model([100.0 + index for index in range(10)])
    model.advance(2)
    branch = model.cursor

    model.set_custom_branch()
    model.add_custom_ticks(20, 110.0)

    assert model.custom_branch == branch
    assert model.n == 21
    assert len(model.custom_ticks) == 18
    assert model.tick().ts_ms == BASE + 2_000
    assert model.custom_preview()[0][0] == branch + 1

    model.advance(5)
    assert model.cursor == 7
    assert len(model.custom_preview()) == 13

    model.clear_custom()
    assert model.cursor == branch
    assert model.n == 10
    assert not model.custom_ticks
    assert model.custom_branch is None


def test_index_at_or_after_is_clamped() -> None:
    model = _model([100.0 + index for index in range(10)])

    assert model.index_at_or_after(BASE + 2_500) == 3
    assert model.index_at_or_after(BASE - 1) == 0
    assert model.index_at_or_after(BASE + 99_000) == 9
