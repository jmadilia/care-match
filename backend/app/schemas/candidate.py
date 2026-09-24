from pydantic import BaseModel

from app.schemas.provider import ProviderRead


class CandidateRead(BaseModel):
  provider: ProviderRead
  score: float
  remaining_capacity: int
