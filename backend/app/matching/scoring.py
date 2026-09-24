from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class ScorableClient(Protocol):
    @property
    def needed_specialties(self) -> Sequence[str]: ...

    @property
    def preferred_language(self) -> str: ...

    @property
    def preferred_modality(self) -> str: ...


class ScorableProvider(Protocol):
    @property
    def specialties(self) -> Sequence[str]: ...

    @property
    def languages(self) -> Sequence[str]: ...

    @property
    def modalities(self) -> Sequence[str]: ...


@dataclass(frozen=True)
class ScoringWeights:
    """Relative importance of each fit component; normalized when scoring."""

    specialty: float = 0.5
    language: float = 0.3
    modality: float = 0.2


DEFAULT_WEIGHTS = ScoringWeights()


def score_pair(
    client: ScorableClient,
    provider: ScorableProvider,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> float:
    """Soft fit in [0, 1]: specialty overlap, language match, modality match."""
    raise NotImplementedError
