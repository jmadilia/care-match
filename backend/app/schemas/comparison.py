from pydantic import BaseModel, Field

from app.schemas.strategy_run import StrategyRunSummary
from app.simulation.config import ScenarioName


class ComparisonRequest(BaseModel):
  scenario: ScenarioName = ScenarioName.BALANCED
  seeds: list[int] = Field(min_length=1, max_length=50)
  provider_count: int = Field(gt=0)
  client_count: int = Field(gt=0)


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
