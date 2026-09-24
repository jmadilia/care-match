from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.candidate import CandidateRead


def recommend_candidates(
    db: Session, client: Client, strategy: str | None, limit: int
) -> list[CandidateRead]:
    """Rank the client's eligible providers by fit, using capacity derived from existing matches.

    Only providers in the client's own simulation run are considered.
    """
    raise NotImplementedError
