import statistics
import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db.scratch import scratch_session
from app.matching.strategies.greedy import run_greedy
from app.matching.strategies.optimal import run_optimal
from app.matching.strategies.stable_matching import run_stable_matching
from app.models.simulation_run import SimulationRun
from app.schemas.comparison import (
  ComparisonRequest,
  ComparisonResult,
  SeededStrategyRun,
  StrategyAggregate,
)
from app.schemas.strategy_run import StrategyRunSummary
from app.simulation.service import generate_for_run

_STRATEGIES: list[Callable[[Session, uuid.UUID], StrategyRunSummary]] = [
  run_greedy,
  run_stable_matching,
  run_optimal,
]


def run_comparison(request: ComparisonRequest) -> ComparisonResult:
  """Run every strategy against the same population for each seed, so differences in the
  results come from the strategy, not from different populations. Everything here happens
  in a scratch session that's always rolled back: these simulation runs exist only to
  produce the numbers below, nothing from them should persist.
  """
  per_seed: list[SeededStrategyRun] = []

  with scratch_session() as db:
    for seed in request.seeds:
      run = SimulationRun(
        name=f"comparison-seed-{seed}",
        scenario=request.scenario,
        seed=seed,
        provider_count=request.provider_count,
        client_count=request.client_count,
      )
      db.add(run)
      db.flush()
      generate_for_run(db, run)

      for strategy_fn in _STRATEGIES:
        summary = strategy_fn(db, run.id)
        per_seed.append(SeededStrategyRun(seed=seed, **summary.model_dump()))

  return ComparisonResult(
    scenario=request.scenario,
    seeds=request.seeds,
    provider_count=request.provider_count,
    client_count=request.client_count,
    per_seed=per_seed,
    aggregates=_aggregate(per_seed),
  )


def _aggregate(per_seed: list[SeededStrategyRun]) -> list[StrategyAggregate]:
  # dict preserves first-seen order, so strategies come out greedy, stable_matching,
  # optimal, matching the order _STRATEGIES ran them in, rather than alphabetically.
  by_strategy: dict[str, list[SeededStrategyRun]] = {}
  for run in per_seed:
    by_strategy.setdefault(run.strategy, []).append(run)

  return [
    StrategyAggregate(
      strategy=strategy,
      runs=len(runs),
      mean_fill_rate=round(statistics.mean(run.fill_rate for run in runs), 4),
      std_fill_rate=_stdev([run.fill_rate for run in runs]),
      mean_match_score_mean=round(statistics.mean(run.mean_match_score for run in runs), 4),
      mean_match_score_std=_stdev([run.mean_match_score for run in runs]),
      mean_provider_utilization_std=round(
        statistics.mean(run.provider_utilization_std for run in runs), 4
      ),
    )
    for strategy, runs in by_strategy.items()
  ]


def _stdev(values: list[float]) -> float:
  return round(statistics.stdev(values), 4) if len(values) > 1 else 0.0
