from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.matching.constraints import ClientLike, ProviderLike
from app.matching.scoring import DEFAULT_WEIGHTS, ScorableClient, ScorableProvider, ScoringWeights


class RankableClient(ClientLike, ScorableClient, Protocol): ...


class RankableProvider(ProviderLike, ScorableProvider, Protocol): ...


@dataclass(frozen=True)
class Candidate[P]:
    provider: P
    score: float
    remaining_capacity: int


def rank_candidates[P: RankableProvider](
    client: RankableClient,
    providers: Sequence[tuple[P, int]],
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> list[Candidate[P]]:
    """Keep eligible providers with spare capacity, best score first; ties go to more spare room.

    Each input pair is (provider, remaining_capacity), so callers decide how load is tracked.
    """
    raise NotImplementedError
