from app.matching.constraints import is_eligible
from app.models.client import Client
from app.models.provider import Provider
from app.schemas.client import ClientUrgency
from app.simulation.generator import GeneratedClient, GeneratedProvider


def _generated_client(state: str, payer: str) -> GeneratedClient:
    return GeneratedClient(
        name="c",
        state=state,
        insurance_payer=payer,
        needed_specialties=["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency=ClientUrgency.ROUTINE,
        arrival_day=0,
    )


def _generated_provider(states: list[str], panels: list[str]) -> GeneratedProvider:
    return GeneratedProvider(
        name="p",
        license_states=states,
        specialties=["anxiety"],
        modalities=["video"],
        languages=["en"],
        insurance_panels=panels,
        weekly_capacity=1,
    )


def test_is_eligible_requires_licensed_state_and_paneled_payer() -> None:
    provider = _generated_provider(["CA", "NY"], ["Aetna", "Cigna"])

    assert is_eligible(_generated_client("CA", "Aetna"), provider)
    assert is_eligible(_generated_client("NY", "Cigna"), provider)
    assert not is_eligible(_generated_client("TX", "Aetna"), provider)
    assert not is_eligible(_generated_client("CA", "Humana"), provider)
    assert not is_eligible(_generated_client("TX", "Humana"), provider)


def test_is_eligible_accepts_generated_and_database_rows() -> None:
    db_client = Client(
        name="c",
        state="CA",
        insurance_payer="Aetna",
        needed_specialties=["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency="ROUTINE",
    )
    db_provider = Provider(
        name="p",
        license_states=["CA"],
        specialties=["anxiety"],
        modalities=["video"],
        languages=["en"],
        insurance_panels=["Aetna"],
        weekly_capacity=1,
    )

    assert is_eligible(db_client, db_provider)
    assert is_eligible(db_client, _generated_provider(["CA"], ["Aetna"]))
    assert is_eligible(_generated_client("CA", "Aetna"), db_provider)
