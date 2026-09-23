import random
from collections.abc import Mapping
from dataclasses import dataclass

from app.schemas.client import ClientUrgency
from app.simulation.config import ScenarioConfig


@dataclass(frozen=True)
class GeneratedProvider:
    name: str
    license_states: list[str]
    specialties: list[str]
    modalities: list[str]
    languages: list[str]
    insurance_panels: list[str]
    weekly_capacity: int


@dataclass(frozen=True)
class GeneratedClient:
    name: str
    state: str
    insurance_payer: str
    needed_specialties: list[str]
    preferred_modality: str
    preferred_language: str
    urgency: ClientUrgency
    arrival_day: int


@dataclass(frozen=True)
class Population:
    providers: list[GeneratedProvider]
    clients: list[GeneratedClient]


def generate_population(
    seed: int, provider_count: int, client_count: int, config: ScenarioConfig
) -> Population:
    """Deterministically build a provider and client population; same seed, same output."""
    # Separate streams so changing provider_count leaves the clients untouched, and vice versa.
    provider_rng = random.Random(f"{seed}:providers")
    client_rng = random.Random(f"{seed}:clients")
    return Population(
        providers=_generate_providers(provider_rng, provider_count, client_count, config),
        clients=_generate_clients(client_rng, client_count, config),
    )


def _generate_providers(
    rng: random.Random, provider_count: int, client_count: int, config: ScenarioConfig
) -> list[GeneratedProvider]:
    """Draw providers, scaling weekly_capacity so demand over capacity hits demand_supply_ratio."""
    total_capacity = max(provider_count, round(client_count / config.demand_supply_ratio))
    # Every provider keeps one slot; the rest are shared out unevenly (part-time vs full caseloads).
    spare = _apportion(
        total_capacity - provider_count, [rng.uniform(0.5, 1.5) for _ in range(provider_count)]
    )

    providers: list[GeneratedProvider] = []
    for index in range(provider_count):
        specialty_count = rng.randint(*config.provider_specialty_range)
        panel_size = rng.randint(*config.panel_size_range)
        providers.append(
            GeneratedProvider(
                name=f"Provider-{index + 1:04d}",
                license_states=_license_states(rng, config),
                specialties=_weighted_sample(rng, config.specialty_supply_weights, specialty_count),
                modalities=_independent_picks(rng, config.provider_modality_probabilities),
                languages=_independent_picks(rng, config.provider_language_probabilities),
                insurance_panels=_weighted_sample(rng, config.payer_supply_weights, panel_size),
                weekly_capacity=1 + spare[index],
            )
        )
    return providers


def _generate_clients(
    rng: random.Random, client_count: int, config: ScenarioConfig
) -> list[GeneratedClient]:
    """Draw clients and spread their arrival_day across config.horizon_days."""
    # Sorted so client numbering follows arrival order.
    arrival_days = sorted(rng.randrange(config.horizon_days) for _ in range(client_count))

    clients: list[GeneratedClient] = []
    for index, arrival_day in enumerate(arrival_days):
        need_count = rng.randint(*config.client_need_range)
        clients.append(
            GeneratedClient(
                name=f"Client-{index + 1:04d}",
                state=_weighted_choice(rng, config.state_demand_weights),
                insurance_payer=_weighted_choice(rng, config.payer_demand_weights),
                needed_specialties=_weighted_sample(
                    rng, config.specialty_demand_weights, need_count
                ),
                preferred_modality=_weighted_choice(rng, config.modality_demand_weights),
                preferred_language=_weighted_choice(rng, config.language_demand_weights),
                urgency=_weighted_choice(rng, config.urgency_weights),
                arrival_day=arrival_day,
            )
        )
    return clients


def _license_states(rng: random.Random, config: ScenarioConfig) -> list[str]:
    home = _weighted_choice(rng, config.state_supply_weights)
    states = [home]
    if config.max_license_states > 1 and rng.random() < config.multi_state_probability:
        extra_count = rng.randint(1, config.max_license_states - 1)
        # Extra licenses follow demand: providers add states where the clients are.
        others = {s: w for s, w in config.state_demand_weights.items() if s != home}
        states += _weighted_sample(rng, others, extra_count)
    return states


def _weighted_choice[K](rng: random.Random, weights: Mapping[K, float]) -> K:
    keys = list(weights)
    return rng.choices(keys, weights=[weights[key] for key in keys])[0]


def _weighted_sample[K](rng: random.Random, weights: Mapping[K, float], count: int) -> list[K]:
    remaining = dict(weights)
    picked: list[K] = []
    for _ in range(min(count, len(remaining))):
        choice = _weighted_choice(rng, remaining)
        picked.append(choice)
        del remaining[choice]
    return picked


def _independent_picks(rng: random.Random, probabilities: Mapping[str, float]) -> list[str]:
    picks = [key for key, probability in probabilities.items() if rng.random() < probability]
    return picks or [max(probabilities, key=lambda key: probabilities[key])]


def _apportion(total: int, weights: list[float]) -> list[int]:
    """Split total into integer shares proportional to weights, summing to exactly total."""
    weight_sum = sum(weights)
    ideals = [total * weight / weight_sum for weight in weights]
    shares = [int(ideal) for ideal in ideals]
    by_remainder = sorted(range(len(weights)), key=lambda i: ideals[i] - shares[i], reverse=True)
    for i in by_remainder[: total - sum(shares)]:
        shares[i] += 1
    return shares
