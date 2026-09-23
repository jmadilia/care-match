from app.schemas.client import ClientUrgency
from app.simulation.config import (
    BALANCED,
    LANGUAGES,
    MODALITIES,
    PAYERS,
    SCARCE_SPECIALTY,
    SCENARIOS,
    SPECIALTIES,
    STATES,
    UNDERSUPPLIED_STATE,
    ScenarioConfig,
    ScenarioName,
    get_scenario,
)
from app.simulation.generator import generate_population


def test_every_scenario_name_has_a_config() -> None:
    assert set(SCENARIOS) == set(ScenarioName)
    for name in ScenarioName:
        assert get_scenario(name).name == name


def test_same_seed_produces_identical_population() -> None:
    first = generate_population(1, 20, 100, BALANCED)
    second = generate_population(1, 20, 100, BALANCED)
    assert first == second


def test_different_seeds_produce_different_populations() -> None:
    assert generate_population(1, 20, 100, BALANCED) != generate_population(2, 20, 100, BALANCED)


def test_clients_do_not_depend_on_provider_count() -> None:
    few = generate_population(1, 20, 100, BALANCED)
    many = generate_population(1, 50, 100, BALANCED)
    assert few.clients == many.clients
    assert few.providers != many.providers


def test_counts_match_the_request() -> None:
    population = generate_population(1, 20, 100, BALANCED)
    assert len(population.providers) == 20
    assert len(population.clients) == 100
    assert len({p.name for p in population.providers}) == 20
    assert len({c.name for c in population.clients}) == 100


def test_generated_values_come_from_the_config_vocabularies() -> None:
    population = generate_population(1, 60, 300, BALANCED)

    for provider in population.providers:
        assert 1 <= len(provider.license_states) <= BALANCED.max_license_states
        assert set(provider.license_states) <= set(STATES)
        assert len(set(provider.license_states)) == len(provider.license_states)
        assert BALANCED.provider_specialty_range[0] <= len(provider.specialties)
        assert len(provider.specialties) <= BALANCED.provider_specialty_range[1]
        assert set(provider.specialties) <= set(SPECIALTIES)
        assert BALANCED.panel_size_range[0] <= len(provider.insurance_panels)
        assert len(provider.insurance_panels) <= BALANCED.panel_size_range[1]
        assert set(provider.insurance_panels) <= set(PAYERS)
        assert provider.modalities and set(provider.modalities) <= set(MODALITIES)
        assert "en" in provider.languages and set(provider.languages) <= set(LANGUAGES)

    for client in population.clients:
        assert client.state in STATES
        assert client.insurance_payer in PAYERS
        assert BALANCED.client_need_range[0] <= len(client.needed_specialties)
        assert len(client.needed_specialties) <= BALANCED.client_need_range[1]
        assert set(client.needed_specialties) <= set(SPECIALTIES)
        assert len(set(client.needed_specialties)) == len(client.needed_specialties)
        assert client.preferred_modality in MODALITIES
        assert client.preferred_language in LANGUAGES
        assert client.urgency in set(ClientUrgency)


def test_arrival_days_fall_within_the_horizon_in_order() -> None:
    days = [c.arrival_day for c in generate_population(1, 20, 200, BALANCED).clients]
    assert all(0 <= day < BALANCED.horizon_days for day in days)
    assert days == sorted(days)


def test_total_capacity_tracks_demand_supply_ratio() -> None:
    population = generate_population(1, 20, 100, BALANCED)
    total = sum(p.weekly_capacity for p in population.providers)
    assert total == round(100 / BALANCED.demand_supply_ratio)
    assert all(p.weekly_capacity >= 1 for p in population.providers)


def test_every_provider_keeps_at_least_one_slot_when_demand_is_tiny() -> None:
    population = generate_population(1, 50, 10, BALANCED)
    assert all(p.weekly_capacity == 1 for p in population.providers)


def test_medicaid_and_spanish_are_scarce_on_the_supply_side() -> None:
    population = generate_population(3, 400, 400, BALANCED)
    medicaid = sum("Medicaid" in p.insurance_panels for p in population.providers) / 400
    spanish = sum("es" in p.languages for p in population.providers) / 400
    assert 0.10 < medicaid < 0.30
    assert 0.02 < spanish < 0.10


def test_undersupplied_state_scenario_starves_that_state() -> None:
    def texas_share(config: ScenarioConfig) -> float:
        population = generate_population(3, 400, 400, config)
        return sum("TX" in p.license_states for p in population.providers) / 400

    assert texas_share(UNDERSUPPLIED_STATE) < texas_share(BALANCED) * 0.7


def test_scarce_specialty_scenario_starves_that_specialty() -> None:
    def trauma_share(config: ScenarioConfig) -> float:
        population = generate_population(3, 400, 400, config)
        return sum("trauma" in p.specialties for p in population.providers) / 400

    assert trauma_share(SCARCE_SPECIALTY) < trauma_share(BALANCED) * 0.5
