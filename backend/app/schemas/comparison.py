from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.strategy_run import StrategyRunSummary
from app.simulation.config import ScenarioName

# Request limits for the public comparison endpoint. Measured: one seed takes about 5s at
# 300 clients and 10s at 1000, mostly fixed overhead, so the number of seeds matters as much
# as population size. Bounding seeds x clients keeps the worst accepted request near a minute.
MAX_SEEDS = 10
MAX_PROVIDERS = 200
MAX_CLIENTS = 1000
MAX_CLIENT_RUNS = 5000


class ComparisonRequest(BaseModel):
  scenario: ScenarioName = ScenarioName.BALANCED
  seeds: list[int] = Field(min_length=1, max_length=MAX_SEEDS)
  provider_count: int = Field(gt=0, le=MAX_PROVIDERS)
  client_count: int = Field(gt=0, le=MAX_CLIENTS)

  @model_validator(mode="after")
  def _within_work_budget(self) -> Self:
    if len(self.seeds) * self.client_count > MAX_CLIENT_RUNS:
      raise ValueError(
        f"seeds x clients must not exceed {MAX_CLIENT_RUNS} "
        f"(got {len(self.seeds)} x {self.client_count})"
      )
    return self


class SeededStrategyRun(StrategyRunSummary):
  seed: int


class StrategyAggregate(BaseModel):
  strategy: str
  runs: int
  mean_fill_rate: float
  std_fill_rate: float
  mean_match_score_mean: float
  mean_match_score_std: float
  mean_provider_utilization_std: float
  mean_fill_rate_by_urgency: dict[str, float]


class ComparisonResult(BaseModel):
  scenario: ScenarioName
  seeds: list[int]
  provider_count: int
  client_count: int
  per_seed: list[SeededStrategyRun]
  aggregates: list[StrategyAggregate]
