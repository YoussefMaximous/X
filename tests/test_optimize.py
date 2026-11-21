import json
from datetime import date

from losslens.cli import main
from losslens.mt4.presets import parse_set
from losslens.optimize import core

SET_TEXT = """Lots=0.10
Lots,1=0.01
Lots,2=0.01
Lots,3=0.10
StopLoss=50
"""


def _config(budget=5, constraints=None):
    return core.config_from_inputs(
        parse_set(SET_TEXT),
        expert="TestEA",
        symbol="XAUUSD",
        from_day=date(2026, 3, 3),
        to_day=date(2026, 3, 3),
        spread=30,
        budget=budget,
        seed=1,
        objective="net_profit",
        constraints=constraints,
    )


def test_config_from_set_keeps_ranges_and_fixed_values():
    config = _config()

    assert len(config.parameters) == 1
    assert config.parameters[0].name == "Lots"
    assert config.parameters[0].kind == "float"
    assert config.parameters[0].low == 0.01
    assert config.parameters[0].high == 0.10
    assert config.parameters[0].step == 0.01
    assert config.fixed == {"StopLoss": "50"}
    assert config.constraints == {}
    assert config.engine == "random"


def test_config_round_trips_through_json():
    config = _config()

    assert core.OptimizerConfig.from_dict(config.to_dict()) == config


def test_sample_trials_covers_a_small_grid():
    config = core.config_from_inputs(
        parse_set("A=1\nA,1=1\nA,2=1\nA,3=3\nB=10\nB,1=10\nB,2=10\nB,3=20"),
        expert="TestEA",
        symbol="XAUUSD",
        from_day=date(2026, 3, 3),
        to_day=date(2026, 3, 3),
        spread=30,
        budget=10,
        seed=1,
        objective="net_profit",
    )

    trials = list(core.sample_trials(config, 10, core.Rng(1)))

    assert len(trials) == 6
    assert len({(trial["A"], trial["B"]) for trial in trials}) == 6


def test_render_trial_set_includes_fixed_and_ranged_values():
    config = _config()

    text = core.render_trial_set(config, {"Lots": 0.05})

    assert "StopLoss=50" in text
    assert "Lots=0.05" in text


def test_run_trials_writes_results_and_summary(tmp_path):
    config = _config(budget=5)

    def evaluate(_path, values):
        return {"net_profit": values["Lots"] * 100, "trades": 10, "max_drawdown": 5}

    records = core.run_trials(config, tmp_path, evaluate)

    assert len(records) == 5
    assert (tmp_path / "results.jsonl").is_file()
    data = core.summary(records)
    assert data["trials"] == 5
    assert data["best_trial"] is not None
    best = core.best_record(records)
    assert best is not None
    assert best["objective"] == max(record["objective"] for record in records)


def test_constraints_mark_ineligible_trials(tmp_path):
    config = _config(budget=5, constraints={"min_trades": 20, "max_drawdown": None})

    def evaluate(_path, values):
        return {"net_profit": values["Lots"], "trades": 10, "max_drawdown": 5}

    records = core.run_trials(config, tmp_path, evaluate)

    assert all(record["eligible"] is False for record in records)
    assert core.best_eligible_record(records) is None


def test_stop_advice_reports_a_plateau():
    records = [
        {"trial": number, "objective": float(number), "eligible": True} for number in range(1, 25)
    ]
    records[-10:] = [
        {"trial": number, "objective": 10.0, "eligible": True} for number in range(15, 25)
    ]

    advice = core.stop_advice(records, budget=30)

    assert advice["plateau"] is True
    assert advice["recommended_stop"] is True
    assert advice["remaining"] == 6


def test_decide_and_winner(tmp_path):
    config = _config(budget=3)

    def evaluate(_path, values):
        return {"net_profit": values["Lots"], "trades": 10, "max_drawdown": 5}

    core.run_trials(config, tmp_path, evaluate)
    decision = core.decide(tmp_path, 2, "more robust on nearby values")
    path, loaded = core.winner_set(tmp_path, tmp_path / "winner.set")

    assert decision["trial"] == 2
    assert loaded["reason"] == "more robust on nearby values"
    assert path.is_file()
    assert "Lots=" in path.read_text(encoding="utf-8")


def test_cli_plan_run_and_choose(tmp_path, capsys):
    preset = tmp_path / "expert.set"
    preset.write_text(SET_TEXT, encoding="utf-8")
    run_dir = tmp_path / "run"

    code = main(
        [
            "optimize",
            "plan",
            "--set",
            str(preset),
            "--expert",
            "TestEA",
            "--symbol",
            "XAUUSD",
            "--from",
            "2026-03-03",
            "--to",
            "2026-03-03",
            "--budget",
            "5",
            "--out",
            str(run_dir),
            "--json",
        ]
    )
    assert code == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["config"]["parameters"][0]["name"] == "Lots"
    assert plan["questions"]

    code = main(
        [
            "optimize",
            "run",
            "--config",
            str(run_dir / "config.json"),
            "--out",
            str(run_dir),
            "--dry-run",
            "--json",
        ]
    )
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["trials"] == 5

    code = main(["optimize", "status", "--run", str(run_dir), "--json"])
    assert code == 0
    status = json.loads(capsys.readouterr().out)
    assert status["summary"]["trials"] == 5

    code = main(["optimize", "shortlist", "--run", str(run_dir), "--limit", "3", "--json"])
    assert code == 0
    shortlist = json.loads(capsys.readouterr().out)
    assert len(shortlist["top"]) == 3

    code = main(
        [
            "optimize",
            "decide",
            "--run",
            str(run_dir),
            "--trial",
            "2",
            "--reason",
            "we prefer the flatter neighbourhood",
            "--json",
        ]
    )
    assert code == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["trial"] == 2

    code = main(
        [
            "optimize",
            "winner",
            "--run",
            str(run_dir),
            "--out",
            str(run_dir / "winner.set"),
            "--json",
        ]
    )
    assert code == 0
    assert (run_dir / "winner.set").is_file()

    code = main(["optimize", "best", "--run", str(run_dir), "--out", str(run_dir / "best.set")])
    assert code == 0
    assert (run_dir / "best.set").is_file()


def test_smac_engine_runs_with_dry_metrics(tmp_path):
    config = core.config_from_inputs(
        parse_set(SET_TEXT),
        expert="TestEA",
        symbol="XAUUSD",
        from_day=date(2026, 3, 3),
        to_day=date(2026, 3, 3),
        spread=30,
        budget=5,
        seed=1,
        objective="net_profit",
        engine="smac",
    )

    records = core.run_smac(
        config,
        tmp_path,
        lambda _path, values: core.dry_metrics(config, values),
    )

    assert len(records) == 5
    assert (tmp_path / "results.jsonl").is_file()
    assert core.summary(records)["best_trial"] is not None


def test_cli_smac_dry_run(tmp_path, capsys):
    preset = tmp_path / "expert.set"
    preset.write_text(SET_TEXT, encoding="utf-8")
    run_dir = tmp_path / "run"
    assert (
        main(
            [
                "optimize",
                "plan",
                "--set",
                str(preset),
                "--expert",
                "TestEA",
                "--symbol",
                "XAUUSD",
                "--from",
                "2026-03-03",
                "--to",
                "2026-03-03",
                "--budget",
                "4",
                "--engine",
                "smac",
                "--out",
                str(run_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()

    code = main(
        [
            "optimize",
            "run",
            "--config",
            str(run_dir / "config.json"),
            "--out",
            str(run_dir),
            "--dry-run",
            "--json",
        ]
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["trials"] == 4
    assert data["best_trial"] is not None


def test_cli_run_without_evaluator_is_refused(tmp_path, capsys):
    preset = tmp_path / "expert.set"
    preset.write_text(SET_TEXT, encoding="utf-8")
    run_dir = tmp_path / "run"
    assert (
        main(
            [
                "optimize",
                "plan",
                "--set",
                str(preset),
                "--expert",
                "TestEA",
                "--symbol",
                "XAUUSD",
                "--from",
                "2026-03-03",
                "--to",
                "2026-03-03",
                "--out",
                str(run_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()

    code = main(["optimize", "run", "--config", str(run_dir / "config.json")])

    assert code == 2
    assert "MT4 evaluator is not enabled" in capsys.readouterr().err
