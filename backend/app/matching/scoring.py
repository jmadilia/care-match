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

    def __post_init__(self) -> None:
        weights = (self.specialty, self.language, self.modality)
        if min(weights) < 0 or sum(weights) <= 0:
            raise ValueError("weights must be non-negative and sum to more than zero")


DEFAULT_WEIGHTS = ScoringWeights()


def score_pair(
    client: ScorableClient,
    provider: ScorableProvider,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> float:
    """Soft fit in [0, 1]: specialty overlap, language match, modality match."""
    needs = set(client.needed_specialties)
    specialty_fit = len(needs & set(provider.specialties)) / len(needs) if needs else 1.0
    language_fit = 1.0 if client.preferred_language in provider.languages else 0.0
    modality_fit = 1.0 if client.preferred_modality in provider.modalities else 0.0

    total = weights.specialty + weights.language + weights.modality
    weighted = (
        weights.specialty * specialty_fit
        + weights.language * language_fit
        + weights.modality * modality_fit
    )
    return weighted / total
