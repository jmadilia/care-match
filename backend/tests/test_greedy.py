import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.greedy import run_greedy
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun


def _run(db: Session, seed: int = 1) -> SimulationRun:
    run = SimulationRun(name="Greedy Test", seed=seed, provider_count=1, client_count=1)
    db.add(run)
    db.flush()
    return run


def _provider(
    db: Session,
    run: SimulationRun,
    capacity: int = 1,
    states: list[str] | None = None,
    panels: list[str] | None = None,
    specialties: list[str] | None = None,
) -> Provider:
    provider = Provider(
        name=f"p-{uuid.uuid4().hex[:8]}",
        license_states=states or ["CA"],
        specialties=specialties or ["anxiety"],
        modalities=["video"],
        languages=["en"],
        insurance_panels=panels or ["Aetna"],
        weekly_capacity=capacity,
        simulation_run_id=run.id,
    )
    db.add(provider)
    db.flush()
    return provider


def _client(
    db: Session,
    run: SimulationRun,
    arrival_day: int = 0,
    needs: list[str] | None = None,
    state: str = "CA",
    payer: str = "Aetna",
) -> Client:
    client = Client(
        name=f"c-{uuid.uuid4().hex[:8]}",
        state=state,
        insurance_payer=payer,
        needed_specialties=needs or ["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency="ROUTINE",
        arrival_day=arrival_day,
        simulation_run_id=run.id,
    )
    db.add(client)
    db.flush()
    return client


def test_greedy_matches_a_single_eligible_pair(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run)
    client = _client(db_session, run)

    summary = run_greedy(db_session, run.id)

    assert summary.strategy == "greedy"
    assert summary.client_count == 1
    assert summary.matched_count == 1
    assert summary.unmatched_count == 0
    assert summary.fill_rate == 1.0
    assert summary.mean_match_score == 1.0

    matches = list(db_session.scalars(select(Match).where(Match.client_id == client.id)))
    assert len(matches) == 1
    assert matches[0].provider_id == provider.id
    assert matches[0].status == "PROPOSED"


def test_greedy_leaves_ineligible_clients_unmatched(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run, states=["NY"])
    client = _client(db_session, run, state="CA")

    summary = run_greedy(db_session, run.id)

    assert summary.matched_count == 0
    assert summary.unmatched_count == 1
    assert summary.fill_rate == 0.0
    assert summary.mean_match_score == 0.0
    assert list(db_session.scalars(select(Match).where(Match.client_id == client.id))) == []


def test_greedy_respects_capacity_and_processes_in_arrival_order(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=1)
    first = _client(db_session, run, arrival_day=0)
    second = _client(db_session, run, arrival_day=1)

    summary = run_greedy(db_session, run.id)

    assert summary.matched_count == 1
    assert summary.unmatched_count == 1

    matches = list(
        db_session.scalars(select(Match).where(Match.client_id.in_([first.id, second.id])))
    )
    assert len(matches) == 1
    assert matches[0].client_id == first.id
    assert matches[0].provider_id == provider.id


def test_greedy_picks_the_best_fit_among_available_providers(db_session: Session) -> None:
    run = _run(db_session)
    weak = _provider(db_session, run, specialties=["anxiety"])
    strong = _provider(db_session, run, specialties=["anxiety", "trauma"])
    client = _client(db_session, run, needs=["anxiety", "trauma"])

    run_greedy(db_session, run.id)

    match = db_session.scalars(select(Match).where(Match.client_id == client.id)).one()
    assert match.provider_id == strong.id
    assert match.provider_id != weak.id
    assert match.score == 1.0


def test_running_greedy_twice_raises(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run)
    _client(db_session, run)

    run_greedy(db_session, run.id)
    with pytest.raises(StrategyAlreadyRunError):
        run_greedy(db_session, run.id)


def test_greedy_endpoint_returns_summary_and_404_and_409(api: TestClient) -> None:
    create_res = api.post(
        "/api/v1/simulation-runs",
        json={"name": "Greedy Endpoint", "seed": 1, "provider_count": 5, "client_count": 5},
    )
    run_id = create_res.json()["id"]
    api.post(f"/api/v1/simulation-runs/{run_id}/generate")

    first = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/greedy")
    assert first.status_code == 201
    summary = first.json()
    assert summary["strategy"] == "greedy"
    assert summary["client_count"] == 5
    assert summary["matched_count"] + summary["unmatched_count"] == 5

    second = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/greedy")
    assert second.status_code == 409

    missing = api.post(f"/api/v1/simulation-runs/{uuid.uuid4()}/strategies/greedy")
    assert missing.status_code == 404
