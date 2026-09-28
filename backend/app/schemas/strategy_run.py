from pydantic import BaseModel


class StrategyRunSummary(BaseModel):
  strategy: str
  client_count: int
  matched_count: int
  unmatched_count: int
  fill_rate: float
  mean_match_score: float
