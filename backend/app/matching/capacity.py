import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.schemas.match import MatchStatus

CAPACITY_HOLDING_STATUSES: frozenset[MatchStatus] = frozenset(
    {MatchStatus.PROPOSED, MatchStatus.ACCEPTED}
)


def provider_loads(
    db: Session, provider_ids: Sequence[uuid.UUID], strategy: str | None = None
) -> dict[uuid.UUID, int]:
    """Count capacity-holding matches per provider, derived at query time.

    Scoped to one strategy when given, since each strategy is its own universe over the same
    population. Providers with no matches map to 0.
    """
    loads = dict.fromkeys(provider_ids, 0)
    if not provider_ids:
        return loads

    query = (
        select(Match.provider_id, func.count())
        .where(
            Match.provider_id.in_(provider_ids),
            Match.status.in_([status.value for status in CAPACITY_HOLDING_STATUSES]),
        )
        .group_by(Match.provider_id)
    )
    if strategy is not None:
        query = query.where(Match.strategy == strategy)

    for provider_id, count in db.execute(query):
        loads[provider_id] = count
    return loads
