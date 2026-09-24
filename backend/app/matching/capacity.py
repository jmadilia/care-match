import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

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
    raise NotImplementedError
