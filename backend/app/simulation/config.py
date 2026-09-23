from dataclasses import dataclass, replace
from enum import StrEnum

from app.schemas.client import ClientUrgency

STATES: tuple[str, ...] = ("CA", "NY", "TX", "FL", "IL", "WA", "MA", "GA")
PAYERS: tuple[str, ...] = (
    "Aetna",
    "Cigna",
    "UnitedHealthcare",
    "BlueCross",
    "Humana",
    "Medicaid",
)
SPECIALTIES: tuple[str, ...] = (
    "anxiety",
    "depression",
    "trauma",
    "adhd",
    "couples",
    "ocd",
    "eating_disorders",
    "substance_use",
)
LANGUAGES: tuple[str, ...] = ("en", "es", "zh", "vi")
MODALITIES: tuple[str, ...] = ("video", "in_person")


class ScenarioName(StrEnum):
    BALANCED = "balanced"
    UNDERSUPPLIED_STATE = "undersupplied_state"
    SCARCE_SPECIALTY = "scarce_specialty"


@dataclass(frozen=True)
class ScenarioConfig:
    """Every knob the generator reads. Weights are relative and need not sum to 1.

    demand_supply_ratio is client_count divided by total provider capacity. A matched
    client holds a slot for the whole horizon, so no weeks-to-slots conversion applies.
    provider_*_probabilities are independent per-provider chances, not shares.
    """

    name: ScenarioName
    description: str
    horizon_days: int
    demand_supply_ratio: float
    max_license_states: int
    multi_state_probability: float
    panel_size_range: tuple[int, int]
    provider_specialty_range: tuple[int, int]
    client_need_range: tuple[int, int]
    state_demand_weights: dict[str, float]
    state_supply_weights: dict[str, float]
    payer_demand_weights: dict[str, float]
    payer_supply_weights: dict[str, float]
    specialty_demand_weights: dict[str, float]
    specialty_supply_weights: dict[str, float]
    language_demand_weights: dict[str, float]
    provider_language_probabilities: dict[str, float]
    modality_demand_weights: dict[str, float]
    provider_modality_probabilities: dict[str, float]
    urgency_weights: dict[ClientUrgency, float]


BALANCED = ScenarioConfig(
    name=ScenarioName.BALANCED,
    description=(
        "Supply tracks demand by state and specialty with realistic skew: Medicaid, "
        "Spanish and rare specialties are scarce. Overall load sits right at capacity."
    ),
    horizon_days=28,
    demand_supply_ratio=1.0,
    max_license_states=3,
    multi_state_probability=0.25,
    panel_size_range=(1, 4),
    provider_specialty_range=(2, 5),
    client_need_range=(1, 3),
    state_demand_weights={
        "CA": 0.26, "TX": 0.21, "FL": 0.15, "NY": 0.13,
        "IL": 0.08, "GA": 0.07, "WA": 0.05, "MA": 0.05,
    },
    state_supply_weights={
        "CA": 0.26, "TX": 0.18, "FL": 0.14, "NY": 0.15,
        "IL": 0.08, "GA": 0.06, "WA": 0.06, "MA": 0.07,
    },
    payer_demand_weights={
        "BlueCross": 0.32, "UnitedHealthcare": 0.24, "Aetna": 0.14,
        "Cigna": 0.12, "Medicaid": 0.13, "Humana": 0.05,
    },
    payer_supply_weights={
        "BlueCross": 0.30, "UnitedHealthcare": 0.27, "Aetna": 0.19,
        "Cigna": 0.15, "Medicaid": 0.07, "Humana": 0.02,
    },
    specialty_demand_weights={
        "anxiety": 0.22, "depression": 0.20, "trauma": 0.34, "adhd": 0.09,
        "couples": 0.06, "ocd": 0.03, "eating_disorders": 0.02, "substance_use": 0.04,
    },
    specialty_supply_weights={
        "anxiety": 0.31, "depression": 0.30, "trauma": 0.17, "couples": 0.075,
        "adhd": 0.07, "substance_use": 0.04, "ocd": 0.02, "eating_disorders": 0.015,
    },
    language_demand_weights={"en": 0.85, "es": 0.11, "zh": 0.025, "vi": 0.015},
    provider_language_probabilities={"en": 1.0, "es": 0.055, "zh": 0.02, "vi": 0.01},
    modality_demand_weights={"video": 0.85, "in_person": 0.15},
    provider_modality_probabilities={"video": 1.0, "in_person": 0.25},
    urgency_weights={
        ClientUrgency.ROUTINE: 0.75,
        ClientUrgency.ELEVATED: 0.18,
        ClientUrgency.URGENT: 0.07,
    },
)

UNDERSUPPLIED_STATE = replace(
    BALANCED,
    name=ScenarioName.UNDERSUPPLIED_STATE,
    description="Texas demand stays high while its provider supply collapses.",
    state_supply_weights={**BALANCED.state_supply_weights, "TX": 0.04},
)

SCARCE_SPECIALTY = replace(
    BALANCED,
    name=ScenarioName.SCARCE_SPECIALTY,
    description="Trauma demand stays high while few providers offer it.",
    specialty_supply_weights={**BALANCED.specialty_supply_weights, "trauma": 0.03},
)

SCENARIOS: dict[ScenarioName, ScenarioConfig] = {
    ScenarioName.BALANCED: BALANCED,
    ScenarioName.UNDERSUPPLIED_STATE: UNDERSUPPLIED_STATE,
    ScenarioName.SCARCE_SPECIALTY: SCARCE_SPECIALTY,
}


def get_scenario(name: ScenarioName) -> ScenarioConfig:
    return SCENARIOS[name]
