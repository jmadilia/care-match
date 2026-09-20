import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProviderBase(BaseModel):
    name: str
    license_states: list[str]
    specialties: list[str]
    modalities: list[str]
    languages: list[str]
    insurance_panels: list[str]
    weekly_capacity: int = Field(gt=0)


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    name: str | None = None
    license_states: list[str] | None = None
    specialties: list[str] | None = None
    modalities: list[str] | None = None
    languages: list[str] | None = None
    insurance_panels: list[str] | None = None
    weekly_capacity: int | None = Field(default=None, gt=0)


class ProviderRead(ProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
