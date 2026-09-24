from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.candidates import rank_candidates
from app.matching.capacity import provider_loads
from app.models.client import Client
from app.models.provider import Provider
from app.schemas.candidate import CandidateRead
from app.schemas.provider import ProviderRead


def recommend_candidates(
    db: Session, client: Client, strategy: str | None, limit: int
) -> list[CandidateRead]:
    """Rank the client's eligible providers by fit, using capacity derived from existing matches.

    Only providers in the client's own simulation run are considered.
    """
    providers = list(
        db.scalars(select(Provider).where(Provider.simulation_run_id == client.simulation_run_id))
    )
    loads = provider_loads(db, [provider.id for provider in providers], strategy)
    with_room = [
        (provider, provider.weekly_capacity - loads[provider.id]) for provider in providers
    ]

    ranked = rank_candidates(client, with_room)
    return [
        CandidateRead(
            provider=ProviderRead.model_validate(candidate.provider),
            score=round(candidate.score, 4),
            remaining_capacity=candidate.remaining_capacity,
        )
        for candidate in ranked[:limit]
    ]
