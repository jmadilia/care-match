import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MatchStatus(StrEnum):
  PROPOSED = "PROPOSED"
  ACCEPTED = "ACCEPTED"
  DECLINED = "DECLINED"


class MatchBase(BaseModel):
  client_id: uuid.UUID
  provider_id: uuid.UUID
  strategy: str
  score: float
  status: MatchStatus = Field(default=MatchStatus.PROPOSED)


class MatchCreate(MatchBase):
  pass


class MatchUpdate(BaseModel):
  strategy: str | None = None
  score: float | None = None
  status: MatchStatus | None = None


class MatchRead(MatchBase):
  model_config = ConfigDict(from_attributes=True)

  id: uuid.UUID
  created_at: datetime