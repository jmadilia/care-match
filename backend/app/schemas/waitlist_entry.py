import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class WaitlistStatus(StrEnum):
  WAITING = "WAITING"
  MATCHED = "MATCHED"
  EXPIRED = "EXPIRED"


class WaitlistEntryCreate(BaseModel):
  client_id: uuid.UUID


class WaitlistEntryUpdate(BaseModel):
  status: WaitlistStatus | None = None


class WaitlistEntryRead(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  client_id: uuid.UUID
  status: WaitlistStatus
  created_at: datetime
  resolved_at: datetime | None
