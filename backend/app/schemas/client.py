import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClientUrgency(StrEnum):
  ROUTINE = "ROUTINE"
  ELEVATED = "ELEVATED"
  URGENT = "URGENT"


class ClientBase(BaseModel):
  name: str
  state: str
  insurance_payer: str
  needed_specialties: list[str]
  preferred_modality: str
  preferred_language: str
  urgency: ClientUrgency = Field(default=ClientUrgency.ROUTINE)
  arrival_day: int | None = Field(default=None, ge=0)
  simulation_run_id: uuid.UUID | None = None


class ClientCreate(ClientBase):
  pass


class ClientUpdate(BaseModel):
  name: str | None = None
  state: str | None = None
  insurance_payer: str | None = None
  needed_specialties: list[str] | None = None
  preferred_modality: str | None = None
  preferred_language: str | None = None
  urgency: ClientUrgency | None = Field(default=ClientUrgency.ROUTINE)


class ClientRead(ClientBase):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  created_at: datetime