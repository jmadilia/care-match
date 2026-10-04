from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.candidate import CandidateRead
from app.simulation.config import (
  LANGUAGES,
  MODALITIES,
  PAYERS,
  SPECIALTIES,
  STATES,
  ScenarioName,
)

MAX_SEED = 100_000
MAX_LIMIT = 20


def _require_in(name: str, values: Sequence[str], allowed: Sequence[str]) -> None:
  unknown = [value for value in values if value not in allowed]
  if unknown:
    raise ValueError(f"{name} must be one of {', '.join(allowed)} (got {', '.join(unknown)})")


class IntakeRequest(BaseModel):
  """A client's answers plus which generated provider pool to rank against. Nothing here is
  stored, and no name is collected: the pool is regenerated from (scenario, seed) per request."""

  scenario: ScenarioName = ScenarioName.BALANCED
  seed: int = Field(default=1, ge=0, le=MAX_SEED)
  state: str
  insurance_payer: str
  needed_specialties: list[str] = Field(min_length=1, max_length=len(SPECIALTIES))
  preferred_modality: str
  preferred_language: str
  limit: int = Field(default=5, ge=1, le=MAX_LIMIT)

  # The matching engine compares exact strings against the generator's closed vocabulary, so
  # anything outside it could only ever return an empty list.
  @model_validator(mode="after")
  def _in_vocabulary(self) -> Self:
    _require_in("state", [self.state], STATES)
    _require_in("insurance_payer", [self.insurance_payer], PAYERS)
    _require_in("needed_specialties", self.needed_specialties, SPECIALTIES)
    _require_in("preferred_modality", [self.preferred_modality], MODALITIES)
    _require_in("preferred_language", [self.preferred_language], LANGUAGES)
    if len(set(self.needed_specialties)) != len(self.needed_specialties):
      raise ValueError("needed_specialties must not repeat a specialty")
    return self


class IntakeResult(BaseModel):
  scenario: ScenarioName
  seed: int
  pool_provider_count: int
  candidates: list[CandidateRead]
