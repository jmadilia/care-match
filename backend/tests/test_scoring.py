import pytest

from app.matching.scoring import DEFAULT_WEIGHTS, ScoringWeights, score_pair
from app.schemas.client import ClientUrgency
from app.simulation.config import BALANCED
from app.simulation.generator import GeneratedClient, GeneratedProvider, generate_population


def _client(
    needs: list[str], language: str = "en", modality: str = "video"
) -> GeneratedClient:
    return GeneratedClient(
        name="c",
        state="CA",
        insurance_payer="Aetna",
        needed_specialties=needs,
        preferred_modality=modality,
        preferred_language=language,
        urgency=ClientUrgency.ROUTINE,
        arrival_day=0,
    )


def _provider(
    specialties: list[str], languages: list[str], modalities: list[str]
) -> GeneratedProvider:
    return GeneratedProvider(
        name="p",
        license_states=["CA"],
        specialties=specialties,
        modalities=modalities,
        languages=languages,
        insurance_panels=["Aetna"],
        weekly_capacity=1,
    )


def test_default_weights_are_specialty_language_modality() -> None:
    assert DEFAULT_WEIGHTS == ScoringWeights(specialty=0.5, language=0.3, modality=0.2)


def test_perfect_fit_scores_one() -> None:
    client = _client(["anxiety", "trauma"], language="es", modality="video")
    provider = _provider(["anxiety", "trauma", "adhd"], ["en", "es"], ["video"])
    assert score_pair(client, provider) == pytest.approx(1.0)


def test_no_fit_scores_zero() -> None:
    client = _client(["ocd"], language="es", modality="in_person")
    provider = _provider(["anxiety"], ["en"], ["video"])
    assert score_pair(client, provider) == pytest.approx(0.0)


def test_specialty_component_is_the_fraction_of_needs_covered() -> None:
    client = _client(["anxiety", "trauma"])
    provider = _provider(["anxiety"], ["en"], ["video"])
    assert score_pair(client, provider) == pytest.approx(0.5 * 0.5 + 0.3 + 0.2)


def test_a_client_with_no_stated_needs_gets_full_specialty_credit() -> None:
    provider = _provider(["anxiety"], ["en"], ["video"])
    assert score_pair(_client([]), provider) == pytest.approx(1.0)


def test_language_and_modality_mismatch_each_lower_the_score() -> None:
    client = _client(["anxiety"], language="es", modality="in_person")
    full = _provider(["anxiety"], ["es"], ["in_person"])
    wrong_language = _provider(["anxiety"], ["en"], ["in_person"])
    wrong_modality = _provider(["anxiety"], ["es"], ["video"])

    assert score_pair(client, full) - score_pair(client, wrong_language) == pytest.approx(0.3)
    assert score_pair(client, full) - score_pair(client, wrong_modality) == pytest.approx(0.2)


def test_weights_are_normalized_so_scale_does_not_matter() -> None:
    client = _client(["anxiety", "trauma"], language="es")
    provider = _provider(["anxiety"], ["en"], ["video"])

    assert score_pair(client, provider, ScoringWeights(5, 3, 2)) == pytest.approx(
        score_pair(client, provider, DEFAULT_WEIGHTS)
    )


def test_custom_weights_change_the_balance() -> None:
    client = _client(["anxiety", "trauma"])
    provider = _provider(["anxiety"], ["en"], ["video"])

    specialty_only = ScoringWeights(specialty=1, language=0, modality=0)
    assert score_pair(client, provider, specialty_only) == pytest.approx(0.5)


def test_score_stays_within_zero_and_one() -> None:
    population = generate_population(1, 20, 50, BALANCED)
    scores = [score_pair(c, p) for c in population.clients for p in population.providers]
    assert all(0.0 <= score <= 1.0 for score in scores)
    assert len(set(scores)) > 1


@pytest.mark.parametrize(
    ("specialty", "language", "modality"), [(-1, 1, 1), (0, 0, 0), (1, -0.5, 1)]
)
def test_invalid_weights_are_rejected(specialty: float, language: float, modality: float) -> None:
    with pytest.raises(ValueError):
        ScoringWeights(specialty=specialty, language=language, modality=modality)
