import random
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
    raise NotImplementedError


def _generate_providers(
    rng: random.Random, provider_count: int, client_count: int, config: ScenarioConfig
) -> list[GeneratedProvider]:
    """Draw providers, scaling weekly_capacity so demand over capacity hits demand_supply_ratio."""
    raise NotImplementedError


def _generate_clients(
    rng: random.Random, client_count: int, config: ScenarioConfig
) -> list[GeneratedClient]:
    """Draw clients and spread their arrival_day across config.horizon_days."""
    raise NotImplementedError
