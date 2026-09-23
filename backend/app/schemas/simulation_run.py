import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SimulationRunBase(BaseModel):
  name: str
  seed: int
  provider_count: int = Field(gt=0)
  client_count: int = Field(gt=0)


class SimulationRunCreate(SimulationRunBase):
  pass


class SimulationRunRead(SimulationRunBase):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  created_at: datetime
