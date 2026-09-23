from collections import Counter, defaultdict

from app.matching.constraints import is_eligible
from app.schemas.simulation_run import PopulationSummary, StateBalance
from app.simulation.generator import Population


def summarize_population(population: Population) -> PopulationSummary:
    """Describe how hard the marketplace is: unservable share, eligibility spread, state balance."""
    providers, clients = population.providers, population.clients

    eligible_counts: list[int] = []
    best_fits: list[float] = []
    for client in clients:
        eligible = [provider for provider in providers if is_eligible(client, provider)]
        eligible_counts.append(len(eligible))
        if eligible:
            needs = set(client.needed_specialties)
            best_fits.append(
                max(len(needs & set(provider.specialties)) / len(needs) for provider in eligible)
            )

    # A provider's capacity is split evenly across their licensed states so the totals still add up.
    capacity_by_state: defaultdict[str, float] = defaultdict(float)
    for provider in providers:
        share = provider.weekly_capacity / len(provider.license_states)
        for state in provider.license_states:
            capacity_by_state[state] += share

    clients_by_state = Counter(client.state for client in clients)
    state_balance = [
        StateBalance(
            state=state,
            weekly_capacity=round(capacity_by_state[state], 2),
            client_count=count,
            capacity_to_demand_ratio=round(capacity_by_state[state] / count, 2),
        )
        for state, count in sorted(clients_by_state.items())
    ]

    return PopulationSummary(
        provider_count=len(providers),
        client_count=len(clients),
        total_weekly_capacity=sum(provider.weekly_capacity for provider in providers),
        unservable_client_share=round(eligible_counts.count(0) / len(clients), 4),
        mean_eligible_providers=round(sum(eligible_counts) / len(clients), 2),
        mean_best_specialty_fit=round(sum(best_fits) / len(best_fits), 4) if best_fits else 0.0,
        state_balance=state_balance,
    )
