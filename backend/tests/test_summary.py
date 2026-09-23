from app.schemas.client import ClientUrgency
from app.simulation.config import BALANCED, SCARCE_SPECIALTY
from app.simulation.generator import (
    GeneratedClient,
    GeneratedProvider,
    Population,
    generate_population,
)
from app.simulation.summary import summarize_population


def _client(state: str, payer: str, needs: list[str]) -> GeneratedClient:
    return GeneratedClient(
        name="c",
        state=state,
        insurance_payer=payer,
        needed_specialties=needs,
        preferred_modality="video",
        preferred_language="en",
        urgency=ClientUrgency.ROUTINE,
        arrival_day=0,
    )


def _provider(
    states: list[str], panels: list[str], specialties: list[str], capacity: int
) -> GeneratedProvider:
    return GeneratedProvider(
        name="p",
        license_states=states,
        specialties=specialties,
        modalities=["video"],
        languages=["en"],
        insurance_panels=panels,
        weekly_capacity=capacity,
    )


def test_summary_of_a_hand_built_population() -> None:
    population = Population(
        providers=[
            _provider(["CA"], ["Aetna"], ["anxiety", "trauma"], 4),
            _provider(["CA", "NY"], ["Aetna", "Cigna"], ["anxiety"], 2),
        ],
        clients=[
            _client("CA", "Aetna", ["anxiety", "trauma"]),
            _client("NY", "Cigna", ["trauma"]),
            _client("TX", "Aetna", ["anxiety"]),
        ],
    )

    summary = summarize_population(population)

    assert summary.provider_count == 2
    assert summary.client_count == 3
    assert summary.total_weekly_capacity == 6
    assert summary.unservable_client_share == round(1 / 3, 4)
    assert summary.mean_eligible_providers == 1.0
    assert summary.mean_best_specialty_fit == 0.5

    balance = {row.state: row for row in summary.state_balance}
    assert list(balance) == ["CA", "NY", "TX"]
    assert balance["CA"].weekly_capacity == 5.0
    assert balance["CA"].capacity_to_demand_ratio == 5.0
    assert balance["NY"].weekly_capacity == 1.0
    assert balance["NY"].capacity_to_demand_ratio == 1.0
    assert balance["TX"].weekly_capacity == 0.0
    assert balance["TX"].capacity_to_demand_ratio == 0.0


def test_state_capacity_adds_up_to_total_capacity() -> None:
    summary = summarize_population(generate_population(1, 60, 300, BALANCED))

    # With 300 clients every modeled state has demand, so no state row is omitted.
    assert len(summary.state_balance) == 8
    state_total = sum(row.weekly_capacity for row in summary.state_balance)
    assert abs(state_total - summary.total_weekly_capacity) < 0.1


def test_marketplace_is_hard_but_not_degenerate() -> None:
    summary = summarize_population(generate_population(1, 60, 300, BALANCED))

    assert summary.total_weekly_capacity == 300
    assert 0.005 < summary.unservable_client_share < 0.15
    assert summary.mean_eligible_providers > 3
    assert 0 < summary.mean_best_specialty_fit < 1


def test_scarce_specialty_scenario_lowers_specialty_fit_not_eligibility() -> None:
    balanced = summarize_population(generate_population(1, 60, 300, BALANCED))
    scarce = summarize_population(generate_population(1, 60, 300, SCARCE_SPECIALTY))

    assert scarce.mean_best_specialty_fit < balanced.mean_best_specialty_fit
    assert scarce.unservable_client_share == balanced.unservable_client_share
