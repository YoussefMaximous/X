"""AI-native optimization: a config, a space, trials and a results file."""

from __future__ import annotations

import itertools
import json
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

from ConfigSpace import Configuration, ConfigurationSpace, Float, Integer
from smac import HyperparameterOptimizationFacade, Scenario

from losslens.mt4.presets import ExpertInput, render_set


class OptimizeError(RuntimeError):
    """The optimization config or run folder cannot be used."""


class Rng:
    """A small deterministic generator, so the optimizer needs no extra import."""

    def __init__(self, seed: int) -> None:
        self.state = (seed & 0xFFFFFFFF) or 1

    def next_float(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / 4294967296

    def randint(self, low: int, high: int) -> int:
        return low + int(self.next_float() * (high - low + 1))

    def uniform(self, low: float, high: float) -> float:
        return low + self.next_float() * (high - low)

    def choice(self, values: list[float]) -> float:
        return values[int(self.next_float() * len(values))]


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    kind: str
    low: float
    high: float
    step: float = 0.0

    def values(self) -> list[float]:
        if self.kind == "int":
            low = int(round(self.low))
            high = int(round(self.high))
            step = max(1, int(round(self.step))) if self.step else 0
            return [float(value) for value in range(low, high + 1, step or 1)]
        if self.step > 0:
            count = int(math.floor((self.high - self.low) / self.step + 1e-9)) + 1
            return [self.low + index * self.step for index in range(max(1, count))]
        return []

    def sample(self, rng: Rng) -> float:
        values = self.values()
        if values:
            return rng.choice(values)
        if self.kind == "int":
            return float(rng.randint(int(round(self.low)), int(round(self.high))))
        return rng.uniform(self.low, self.high)

    def text(self, value: float) -> str:
        if self.kind == "int":
            return str(int(round(value)))
        return f"{value:.10g}"


@dataclass(frozen=True)
class OptimizerConfig:
    expert: str
    symbol: str
    from_day: date
    to_day: date
    spread: int
    budget: int
    seed: int
    objective: str
    engine: str
    parameters: tuple[ParameterSpec, ...]
    fixed: dict[str, str]
    constraints: dict[str, float | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "expert": self.expert,
            "symbol": self.symbol,
            "from": self.from_day.isoformat(),
            "to": self.to_day.isoformat(),
            "spread": self.spread,
            "budget": self.budget,
            "seed": self.seed,
            "objective": self.objective,
            "engine": self.engine,
            "parameters": [
                {
                    "name": item.name,
                    "kind": item.kind,
                    "low": item.low,
                    "high": item.high,
                    "step": item.step,
                }
                for item in self.parameters
            ],
            "fixed": self.fixed,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OptimizerConfig:
        parameters = tuple(
            ParameterSpec(
                name=str(item["name"]),
                kind=str(item["kind"]),
                low=float(item["low"]),
                high=float(item["high"]),
                step=float(item.get("step", 0.0)),
            )
            for item in cast(list[dict[str, Any]], raw["parameters"])
        )
        return cls(
            expert=str(raw["expert"]),
            symbol=str(raw["symbol"]).upper(),
            from_day=date.fromisoformat(str(raw["from"])),
            to_day=date.fromisoformat(str(raw["to"])),
            spread=int(raw["spread"]),
            budget=int(raw["budget"]),
            seed=int(raw["seed"]),
            objective=str(raw["objective"]),
            engine=str(raw.get("engine", "random")),
            parameters=parameters,
            fixed={
                str(key): str(value) for key, value in cast(dict[str, Any], raw["fixed"]).items()
            },
            constraints={
                str(key): (None if value is None else float(value))
                for key, value in cast(dict[str, Any], raw.get("constraints", {})).items()
            },
        )


def _kind(value: str, start: str, step: str, stop: str) -> str:
    if value.lower() in ("true", "false"):
        return "int"
    if any("." in part for part in (value, start, step, stop) if part):
        return "float"
    return "int"


def config_from_inputs(
    inputs: tuple[ExpertInput, ...],
    *,
    expert: str,
    symbol: str,
    from_day: date,
    to_day: date,
    spread: int,
    budget: int,
    seed: int,
    objective: str,
    constraints: dict[str, float | None] | None = None,
    engine: str = "random",
) -> OptimizerConfig:
    parameters: list[ParameterSpec] = []
    fixed: dict[str, str] = {}
    for item in inputs:
        if item.start is not None and item.stop is not None:
            low = float(item.start)
            high = float(item.stop)
            step = float(item.step) if item.step else 0.0
            parameters.append(
                ParameterSpec(
                    name=item.name,
                    kind=_kind(item.value, item.start, item.step or "", item.stop),
                    low=low,
                    high=high,
                    step=step,
                )
            )
        else:
            fixed[item.name] = item.value
    if not parameters:
        raise OptimizeError("the .set has no optimization ranges (start/step/stop)")
    return OptimizerConfig(
        expert=expert,
        symbol=symbol.upper(),
        from_day=from_day,
        to_day=to_day,
        spread=spread,
        budget=budget,
        seed=seed,
        objective=objective,
        engine=engine,
        parameters=tuple(parameters),
        fixed=fixed,
        constraints={} if constraints is None else constraints,
    )


def sample_trials(config: OptimizerConfig, count: int, rng: Rng) -> Iterator[dict[str, float]]:
    names = [item.name for item in config.parameters]
    grids = [item.values() for item in config.parameters]
    total = 1
    for grid in grids:
        if not grid:
            total = 0
            break
        total *= len(grid)
    if total > 0 and total <= count:
        for combination in itertools.product(*grids):
            yield dict(zip(names, combination, strict=False))
        return
    seen: set[tuple[float, ...]] = set()
    attempts = 0
    while len(seen) < count and attempts < count * 100:
        attempts += 1
        combination = tuple(item.sample(rng) for item in config.parameters)
        if combination in seen:
            continue
        seen.add(combination)
        yield dict(zip(names, combination, strict=False))


def render_trial_set(config: OptimizerConfig, values: dict[str, float]) -> str:
    items = [ExpertInput(name, value) for name, value in config.fixed.items()]
    items.extend(ExpertInput(item.name, item.text(values[item.name])) for item in config.parameters)
    return render_set(tuple(items))


def dry_metrics(config: OptimizerConfig, values: dict[str, float]) -> dict[str, float]:
    """A deterministic objective for validating the loop without MT4."""
    score = 100.0
    for item in config.parameters:
        middle = (item.low + item.high) / 2
        span = item.high - item.low or 1.0
        score -= abs(values[item.name] - middle) / span * 10
    return {
        "net_profit": round(score, 4),
        "trades": 10.0,
        "max_drawdown": round(100 - score, 4),
    }


def _eligible(config: OptimizerConfig, metrics: dict[str, float]) -> bool:
    min_trades = config.constraints.get("min_trades")
    max_drawdown = config.constraints.get("max_drawdown")
    if min_trades is not None and float(metrics.get("trades", 0.0)) < min_trades:
        return False
    if max_drawdown is not None and float(metrics.get("max_drawdown", float("inf"))) > max_drawdown:
        return False
    return True


def run_trials(
    config: OptimizerConfig,
    out_dir: Path,
    evaluate: Callable[[Path, dict[str, float]], dict[str, float]],
    *,
    resume: bool = False,
) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    trials_dir = out_dir / "trials"
    trials_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    done: set[int] = set()
    records: list[dict[str, Any]] = []
    if resume and results_path.exists():
        records = load_results(out_dir)
        done = {int(record["trial"]) for record in records}
    rng = Rng(config.seed)
    for number, values in enumerate(sample_trials(config, config.budget, rng), start=1):
        if number in done:
            continue
        trial_path = trials_dir / f"{number:04d}.set"
        trial_path.write_text(render_trial_set(config, values), encoding="utf-8", newline="\n")
        try:
            metrics = evaluate(trial_path, values)
            objective = float(metrics[config.objective])
            error = None
        except (KeyError, OSError, ValueError) as exc:
            metrics = {}
            objective = None
            error = str(exc)
        record = {
            "trial": number,
            "values": values,
            "metrics": metrics,
            "objective": objective,
            "eligible": _eligible(config, metrics) if objective is not None else False,
            "set": trial_path.relative_to(out_dir).as_posix(),
            "error": error,
        }
        records.append(record)
        with results_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    return records


def _snap(spec: ParameterSpec, value: float) -> float:
    if spec.step > 0:
        steps = round((value - spec.low) / spec.step)
        value = spec.low + steps * spec.step
    if spec.kind == "int":
        return float(int(round(value)))
    return float(value)


def run_smac(
    config: OptimizerConfig,
    out_dir: Path,
    evaluate: Callable[[Path, dict[str, float]], dict[str, float]],
    *,
    resume: bool = False,
) -> list[dict[str, Any]]:
    if config.budget <= 0:
        raise OptimizeError("budget must be positive")
    if resume:
        raise OptimizeError("resume is not supported with the smac engine yet")
    out_dir = Path(out_dir)
    trials_dir = out_dir / "trials"
    trials_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    if results_path.exists():
        results_path.unlink()
    records: list[dict[str, Any]] = []
    trial = 0
    space = ConfigurationSpace(seed=config.seed)
    for item in config.parameters:
        if item.kind == "int":
            space.add(Integer(item.name, (int(round(item.low)), int(round(item.high)))))
        else:
            space.add(Float(item.name, (item.low, item.high)))

    def target(configuration: Configuration, seed: int = 0) -> float:
        nonlocal trial
        del seed
        trial += 1
        values = {
            item.name: _snap(item, float(configuration[item.name])) for item in config.parameters
        }
        trial_path = trials_dir / f"{trial:04d}.set"
        trial_path.write_text(render_trial_set(config, values), encoding="utf-8", newline="\n")
        try:
            metrics = evaluate(trial_path, values)
            objective = float(metrics[config.objective])
            error = None
        except (KeyError, OSError, ValueError) as exc:
            metrics = {}
            objective = None
            error = str(exc)
        record = {
            "trial": trial,
            "engine": "smac",
            "values": values,
            "metrics": metrics,
            "objective": objective,
            "eligible": _eligible(config, metrics) if objective is not None else False,
            "set": trial_path.relative_to(out_dir).as_posix(),
            "error": error,
        }
        records.append(record)
        with results_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        if objective is None:
            return float("inf")
        return -objective

    scenario = Scenario(
        space,
        name="losslens",
        output_directory=out_dir / "smac3_output",
        deterministic=True,
        objectives="cost",
        n_trials=config.budget,
        seed=config.seed,
        n_workers=1,
        use_default_config=False,
    )
    facade = HyperparameterOptimizationFacade(
        scenario,
        target,
        overwrite=True,
        logging_level=False,
    )
    facade.optimize()
    return records


def load_results(out_dir: Path) -> list[dict[str, Any]]:
    path = Path(out_dir) / "results.jsonl"
    if not path.exists():
        return []
    return [
        cast(dict[str, Any], json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def best_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [record for record in records if record.get("objective") is not None]
    if not scored:
        return None
    return max(scored, key=lambda record: float(record["objective"]))


def best_eligible_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [
        record
        for record in records
        if record.get("objective") is not None and record.get("eligible", True)
    ]
    if not scored:
        return None
    return max(scored, key=lambda record: float(record["objective"]))


def summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    best = best_record(records)
    eligible = best_eligible_record(records)
    scored = sum(1 for record in records if record.get("objective") is not None)
    return {
        "trials": len(records),
        "scored": scored,
        "failed": len(records) - scored,
        "eligible": sum(1 for record in records if record.get("eligible", False)),
        "best_trial": best["trial"] if best is not None else None,
        "best_objective": best["objective"] if best is not None else None,
        "best_values": best["values"] if best is not None else None,
        "best_set": best["set"] if best is not None else None,
        "best_eligible_trial": eligible["trial"] if eligible is not None else None,
        "best_eligible_objective": eligible["objective"] if eligible is not None else None,
    }


def shortlist(records: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    scored = [
        record
        for record in records
        if record.get("objective") is not None and record.get("eligible", True)
    ]
    ranked = sorted(scored, key=lambda record: float(record["objective"]), reverse=True)
    top = ranked[: max(1, limit)]
    diverse = None
    if top:
        chosen = {int(record["trial"]) for record in top}
        rest = [record for record in ranked if int(record["trial"]) not in chosen]
        if rest:
            names = list(top[0]["values"].keys())

            def distance(record: dict[str, Any]) -> float:
                return sum(
                    abs(float(record["values"][name]) - float(top[0]["values"][name]))
                    for name in names
                )

            diverse = max(rest, key=distance)
    return {
        "eligible": len(scored),
        "total": len(records),
        "top": top,
        "diverse": diverse,
    }


def decide(run_dir: Path, trial: int, reason: str) -> dict[str, Any]:
    records = load_results(run_dir)
    record = next((item for item in records if int(item["trial"]) == trial), None)
    if record is None:
        raise OptimizeError(f"trial {trial} is not in the results")
    decision = {
        "trial": trial,
        "reason": reason,
        "record": record,
        "chosen_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    path = Path(run_dir) / "decision.json"
    path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def read_decision(run_dir: Path) -> dict[str, Any] | None:
    path = Path(run_dir) / "decision.json"
    if not path.exists():
        return None
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def winner_set(run_dir: Path, out_path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    decision = read_decision(run_dir)
    if decision is None:
        raise OptimizeError("no winner chosen; run optimize decide first")
    source = Path(run_dir) / str(decision["record"]["set"])
    target = Path(out_path) if out_path is not None else Path(run_dir) / "winner.set"
    target.write_bytes(source.read_bytes())
    return target, decision


def stop_advice(records: list[dict[str, Any]], budget: int) -> dict[str, Any]:
    scored = [record for record in records if record.get("objective") is not None]
    remaining = max(0, budget - len(records))
    best = best_record(records)
    best_objective = float(best["objective"]) if best is not None else None
    if len(scored) < 10:
        return {
            "recommended_stop": remaining == 0,
            "reason": "too few scored trials to judge convergence",
            "remaining": remaining,
            "best_objective": best_objective,
            "plateau": False,
        }
    window = min(10, max(3, len(scored) // 3))
    earlier = scored[:-window]
    recent = scored[-window:]
    best_before = max(float(item["objective"]) for item in earlier) if earlier else None
    best_recent = max(float(item["objective"]) for item in recent)
    improved = best_before is None or best_recent > best_before + 1e-9
    plateau = not improved
    recommended = remaining == 0 or (plateau and len(scored) >= 20)
    if remaining == 0:
        reason = "budget is exhausted"
    elif plateau:
        reason = f"no new best in the last {window} scored trials"
    else:
        reason = "still improving"
    return {
        "recommended_stop": recommended,
        "reason": reason,
        "remaining": remaining,
        "best_objective": best_objective,
        "plateau": plateau,
    }
