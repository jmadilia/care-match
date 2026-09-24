import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.matching.candidates import Candidate, rank_candidates
from app.matching.capacity import provider_loads
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.schemas.client import ClientUrgency
from app.simulation.generator import GeneratedClient, GeneratedProvider


def _gclient(
    state: str = "CA", payer: str = "Aetna", needs: list[str] | None = None
) -> GeneratedClient:
    return GeneratedClient(
        name="c",
        state=state,
        insurance_payer=payer,
        needed_specialties=needs if needs is not None else ["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency=ClientUrgency.ROUTINE,
        arrival_day=0,
    )


def _gprovider(
    name: str,
    states: list[str] | None = None,
    panels: list[str] | None = None,
    specialties: list[str] | None = None,
) -> GeneratedProvider:
    return GeneratedProvider(
        name=name,
        license_states=states or ["CA"],
        specialties=specialties or ["anxiety"],
        modalities=["video"],
        languages=["en"],
        insurance_panels=panels or ["Aetna"],
        weekly_capacity=1,
    )


def _names(candidates: list[Candidate[GeneratedProvider]]) -> list[str]:
    return [candidate.provider.name for candidate in candidates]


def test_rank_candidates_drops_ineligible_providers() -> None:
    providers = [
        (_gprovider("ok"), 1),
        (_gprovider("wrong-state", states=["NY"]), 1),
        (_gprovider("wrong-payer", panels=["Cigna"]), 1),
    ]
    assert _names(rank_candidates(_gclient(), providers)) == ["ok"]


def test_rank_candidates_drops_providers_with_no_spare_capacity() -> None:
    providers = [(_gprovider("full"), 0), (_gprovider("open"), 1)]
    assert _names(rank_candidates(_gclient(), providers)) == ["open"]


def test_rank_candidates_returns_nothing_when_nobody_is_eligible() -> None:
    providers = [(_gprovider("far", states=["NY"]), 3)]
    assert rank_candidates(_gclient(), providers) == []


def test_rank_candidates_sorts_best_score_first() -> None:
    client = _gclient(needs=["anxiety", "trauma"])
    providers = [
        (_gprovider("none", specialties=["adhd"]), 1),
        (_gprovider("full", specialties=["anxiety", "trauma"]), 1),
        (_gprovider("half", specialties=["anxiety"]), 1),
    ]
    ranked = rank_candidates(client, providers)
    assert _names(ranked) == ["full", "half", "none"]
    assert ranked[0].score > ranked[1].score > ranked[2].score


def test_rank_candidates_breaks_ties_by_spare_capacity() -> None:
    providers = [(_gprovider("tight"), 1), (_gprovider("roomy"), 5)]
    assert _names(rank_candidates(_gclient(), providers)) == ["roomy", "tight"]


def test_rank_candidates_keeps_caller_order_on_full_ties() -> None:
    providers = [(_gprovider(name), 2) for name in ("a", "b", "c")]
    assert _names(rank_candidates(_gclient(), providers)) == ["a", "b", "c"]


def test_rank_candidates_works_on_generated_and_database_rows() -> None:
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

    from_db = rank_candidates(db_client, [(db_provider, 1)])
    assert len(from_db) == 1 and from_db[0].score == 1.0
    assert len(rank_candidates(_gclient(), [(db_provider, 1)])) == 1
    assert len(rank_candidates(db_client, [(_gprovider("g"), 1)])) == 1


def _db_provider(db: Session, capacity: int = 5) -> Provider:
    provider = Provider(
        name="p",
        license_states=["CA"],
        specialties=["anxiety"],
        modalities=["video"],
        languages=["en"],
        insurance_panels=["Aetna"],
        weekly_capacity=capacity,
    )
    db.add(provider)
    db.flush()
    return provider


def _db_client(db: Session) -> Client:
    row = Client(
        name="c",
        state="CA",
        insurance_payer="Aetna",
        needed_specialties=["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency="ROUTINE",
    )
    db.add(row)
    db.flush()
    return row


def _db_match(db: Session, client: Client, provider: Provider, strategy: str, status: str) -> None:
    db.add(
        Match(
            client_id=client.id,
            provider_id=provider.id,
            strategy=strategy,
            score=0.5,
            status=status,
        )
    )
    db.flush()


def test_provider_loads_count_only_capacity_holding_matches(db_session: Session) -> None:
    busy, idle = _db_provider(db_session), _db_provider(db_session)
    client = _db_client(db_session)
    _db_match(db_session, client, busy, "greedy", "PROPOSED")
    _db_match(db_session, client, busy, "greedy", "ACCEPTED")
    _db_match(db_session, client, busy, "greedy", "DECLINED")

    loads = provider_loads(db_session, [busy.id, idle.id])

    assert loads == {busy.id: 2, idle.id: 0}
    assert provider_loads(db_session, []) == {}


def test_provider_loads_are_scoped_to_one_strategy(db_session: Session) -> None:
    provider = _db_provider(db_session)
    client = _db_client(db_session)
    _db_match(db_session, client, provider, "greedy", "PROPOSED")
    _db_match(db_session, client, provider, "greedy", "PROPOSED")
    _db_match(db_session, client, provider, "stable", "PROPOSED")

    assert provider_loads(db_session, [provider.id], "greedy") == {provider.id: 2}
    assert provider_loads(db_session, [provider.id], "stable") == {provider.id: 1}
    assert provider_loads(db_session, [provider.id], "optimal") == {provider.id: 0}
    assert provider_loads(db_session, [provider.id]) == {provider.id: 3}


def _run(api: TestClient) -> str:
    payload = {"name": "Candidate Run", "seed": 1, "provider_count": 5, "client_count": 5}
    res = api.post("/api/v1/simulation-runs", json=payload)
    assert res.status_code == 201
    return str(res.json()["id"])


def _api_provider(
    api: TestClient,
    run_id: str,
    name: str,
    states: list[str] | None = None,
    panels: list[str] | None = None,
    specialties: list[str] | None = None,
    capacity: int = 2,
) -> str:
    res = api.post(
        "/api/v1/providers",
        json={
            "name": name,
            "license_states": states or ["CA"],
            "specialties": specialties or ["anxiety"],
            "modalities": ["video"],
            "languages": ["en"],
            "insurance_panels": panels or ["Aetna"],
            "weekly_capacity": capacity,
            "simulation_run_id": run_id,
        },
    )
    assert res.status_code == 201
    return str(res.json()["id"])


def _api_client(api: TestClient, run_id: str, needs: list[str] | None = None) -> str:
    res = api.post(
        "/api/v1/clients",
        json={
            "name": "Candidate Client",
            "state": "CA",
            "insurance_payer": "Aetna",
            "needed_specialties": needs or ["anxiety"],
            "preferred_modality": "video",
            "preferred_language": "en",
            "simulation_run_id": run_id,
        },
    )
    assert res.status_code == 201
    return str(res.json()["id"])


def test_candidates_endpoint_ranks_eligible_providers_in_the_clients_run(api: TestClient) -> None:
    run_id, other_run_id = _run(api), _run(api)
    _api_provider(api, run_id, "half", specialties=["anxiety"])
    _api_provider(api, run_id, "best", specialties=["anxiety", "trauma"])
    _api_provider(api, run_id, "wrong-state", states=["NY"])
    _api_provider(api, run_id, "wrong-payer", panels=["Cigna"])
    _api_provider(api, other_run_id, "other-run", specialties=["anxiety", "trauma"])
    client_id = _api_client(api, run_id, needs=["anxiety", "trauma"])

    res = api.get(f"/api/v1/clients/{client_id}/candidates")

    assert res.status_code == 200
    candidates = res.json()
    assert [c["provider"]["name"] for c in candidates] == ["best", "half"]
    assert candidates[0]["score"] == 1.0
    assert candidates[1]["score"] == 0.75
    assert all(c["remaining_capacity"] == 2 for c in candidates)

    limited = api.get(f"/api/v1/clients/{client_id}/candidates", params={"limit": 1}).json()
    assert [c["provider"]["name"] for c in limited] == ["best"]


def test_candidates_endpoint_reflects_capacity_used_by_existing_matches(api: TestClient) -> None:
    run_id = _run(api)
    provider_id = _api_provider(api, run_id, "solo", capacity=1)
    client_a, client_b = _api_client(api, run_id), _api_client(api, run_id)
    url = f"/api/v1/clients/{client_a}/candidates"

    assert len(api.get(url).json()) == 1

    match_res = api.post(
        "/api/v1/matches",
        json={
            "client_id": client_b,
            "provider_id": provider_id,
            "strategy": "greedy",
            "score": 0.9,
        },
    )
    assert match_res.status_code == 201
    match_id = match_res.json()["id"]

    assert api.get(url, params={"strategy": "greedy"}).json() == []
    assert api.get(url).json() == []
    assert len(api.get(url, params={"strategy": "stable"}).json()) == 1

    api.patch(f"/api/v1/matches/{match_id}", json={"status": "DECLINED"})
    assert len(api.get(url, params={"strategy": "greedy"}).json()) == 1


def test_candidates_endpoint_unknown_client_returns_404(api: TestClient) -> None:
    res = api.get(f"/api/v1/clients/{uuid.uuid4()}/candidates")
    assert res.status_code == 404


def test_candidates_endpoint_rejects_out_of_range_limit(api: TestClient) -> None:
    assert api.get(f"/api/v1/clients/{uuid.uuid4()}/candidates?limit=0").status_code == 422
    assert api.get(f"/api/v1/clients/{uuid.uuid4()}/candidates?limit=51").status_code == 422
