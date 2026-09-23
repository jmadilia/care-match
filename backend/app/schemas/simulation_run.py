import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.simulation.config import ScenarioName


class SimulationRunBase(BaseModel):
  name: str
  scenario: ScenarioName = ScenarioName.BALANCED
  seed: int
  provider_count: int = Field(gt=0)
  client_count: int = Field(gt=0)


class SimulationRunCreate(SimulationRunBase):
  pass


class SimulationRunRead(SimulationRunBase):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  created_at: datetime


class StateBalance(BaseModel):
  state: str
  weekly_capacity: float
  client_count: int
  capacity_to_demand_ratio: float


class PopulationSummary(BaseModel):
  provider_count: int
  client_count: int
  total_weekly_capacity: int
  unservable_client_share: float
  mean_eligible_providers: float
  mean_best_specialty_fit: float
  state_balance: list[StateBalance]
