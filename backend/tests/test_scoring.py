import pytest

from app.matching.scoring import DEFAULT_WEIGHTS, ScoringWeights

NOT_IMPLEMENTED = "score_pair not implemented yet"


def test_default_weights_are_specialty_language_modality() -> None:
    assert DEFAULT_WEIGHTS == ScoringWeights(specialty=0.5, language=0.3, modality=0.2)


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_perfect_fit_scores_one() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_no_fit_scores_zero() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_specialty_component_is_the_fraction_of_needs_covered() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_language_and_modality_mismatch_each_lower_the_score() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_weights_are_normalized_so_scale_does_not_matter() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_score_stays_within_zero_and_one() -> None: ...
