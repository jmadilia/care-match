import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.optimal import run_optimal
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun


def _run(db: Session, seed: int = 1) -> SimulationRun:
    run = SimulationRun(name="Optimal Test", seed=seed, provider_count=1, client_count=1)
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
        arrival_day=0,
        simulation_run_id=run.id,
    )
    db.add(client)
    db.flush()
    return client


def test_optimal_matches_a_single_eligible_pair(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run)
    client = _client(db_session, run)

    summary = run_optimal(db_session, run.id)

    assert summary.strategy == "optimal"
    assert summary.matched_count == 1
    assert summary.unmatched_count == 0
    assert summary.mean_match_score == 1.0

    match = db_session.scalars(select(Match).where(Match.client_id == client.id)).one()
    assert match.provider_id == provider.id


def test_optimal_leaves_ineligible_clients_unmatched(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run, states=["NY"])
    client = _client(db_session, run, state="CA")

    summary = run_optimal(db_session, run.id)

    assert summary.matched_count == 0
    assert summary.unmatched_count == 1
    assert list(db_session.scalars(select(Match).where(Match.client_id == client.id))) == []


def test_optimal_beats_greedy_on_total_score_when_order_would_mislead(db_session: Session) -> None:
    """A single-slot provider that fits both specialties is approached first by a
    partial-fit client, which greedy would take immediately. Optimal looks at the whole
    batch and gives the slot to whichever client actually maximizes total score, here the
    full-fit client, leaving the partial-fit one unmatched since there's nowhere else for
    either of them to go."""
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=1, specialties=["anxiety", "trauma"])
    partial = _client(db_session, run, needs=["anxiety", "adhd"])
    full = _client(db_session, run, needs=["anxiety", "trauma"])

    run_optimal(db_session, run.id)

    match = db_session.scalars(
        select(Match).where(Match.client_id.in_([partial.id, full.id]))
    ).one()
    assert match.client_id == full.id
    assert match.provider_id == provider.id
    assert match.score == 1.0


def test_optimal_fills_every_slot_of_a_multi_capacity_provider(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=2)
    first, second, third = (_client(db_session, run) for _ in range(3))

    summary = run_optimal(db_session, run.id)

    assert summary.matched_count == 2
    assert summary.unmatched_count == 1
    matched = {
        m.client_id
        for m in db_session.scalars(
            select(Match).where(Match.client_id.in_([first.id, second.id, third.id]))
        )
    }
    assert len(matched) == 2
    for match in db_session.scalars(select(Match).where(Match.client_id.in_(matched))):
        assert match.provider_id == provider.id


def test_optimal_with_no_providers_leaves_everyone_unmatched(db_session: Session) -> None:
    run = _run(db_session)
    client = _client(db_session, run)

    summary = run_optimal(db_session, run.id)

    assert summary.client_count == 1
    assert summary.matched_count == 0
    assert summary.unmatched_count == 1
    assert list(db_session.scalars(select(Match).where(Match.client_id == client.id))) == []


def test_running_optimal_twice_raises(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run)
    _client(db_session, run)

    run_optimal(db_session, run.id)
    with pytest.raises(StrategyAlreadyRunError):
        run_optimal(db_session, run.id)


def test_optimal_endpoint_returns_summary_and_404_and_409(api: TestClient) -> None:
    create_res = api.post(
        "/api/v1/simulation-runs",
        json={"name": "Optimal Endpoint", "seed": 1, "provider_count": 5, "client_count": 5},
    )
    run_id = create_res.json()["id"]
    api.post(f"/api/v1/simulation-runs/{run_id}/generate")

    first = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/optimal")
    assert first.status_code == 201
    summary = first.json()
    assert summary["strategy"] == "optimal"
    assert summary["matched_count"] + summary["unmatched_count"] == 5

    second = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/optimal")
    assert second.status_code == 409

    missing = api.post(f"/api/v1/simulation-runs/{uuid.uuid4()}/strategies/optimal")
    assert missing.status_code == 404
