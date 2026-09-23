import pytest

from app.simulation.config import SCENARIOS, ScenarioName, get_scenario

NOT_IMPLEMENTED = "generator not implemented yet"


def test_every_scenario_name_has_a_config() -> None:
    assert set(SCENARIOS) == set(ScenarioName)
    for name in ScenarioName:
        assert get_scenario(name).name == name


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_same_seed_produces_identical_population() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_different_seeds_produce_different_populations() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_counts_match_the_request() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_generated_values_come_from_the_config_vocabularies() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_arrival_days_fall_within_the_horizon() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_total_capacity_tracks_demand_supply_ratio() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_marketplace_is_hard_but_not_degenerate() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_undersupplied_state_scenario_starves_that_state() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_scarce_specialty_scenario_starves_that_specialty() -> None: ...

