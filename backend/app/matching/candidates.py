from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.matching.constraints import ClientLike, ProviderLike, is_eligible
from app.matching.scoring import (
    DEFAULT_WEIGHTS,
    ScorableClient,
    ScorableProvider,
    ScoringWeights,
    score_pair,
)


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
    candidates = [
        Candidate(provider, score_pair(client, provider, weights), remaining)
        for provider, remaining in providers
        if remaining > 0 and is_eligible(client, provider)
    ]
    # The sort is stable, so full ties keep the caller's order.
    candidates.sort(key=lambda candidate: (-candidate.score, -candidate.remaining_capacity))
    return candidates
