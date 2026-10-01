import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.stable_matching import run_stable_matching
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun


def _run(db: Session, seed: int = 1) -> SimulationRun:
    run = SimulationRun(name="Stable Test", seed=seed, provider_count=1, client_count=1)
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


def test_stable_matching_matches_a_single_eligible_pair(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run)
    client = _client(db_session, run)

    summary = run_stable_matching(db_session, run.id)

    assert summary.strategy == "stable_matching"
    assert summary.matched_count == 1
    assert summary.unmatched_count == 0
    assert summary.mean_match_score == 1.0

    matches = list(db_session.scalars(select(Match).where(Match.client_id == client.id)))
    assert len(matches) == 1
    assert matches[0].provider_id == provider.id


def test_stable_matching_leaves_ineligible_clients_unmatched(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run, states=["NY"])
    client = _client(db_session, run, state="CA")

    summary = run_stable_matching(db_session, run.id)

    assert summary.matched_count == 0
    assert summary.unmatched_count == 1
    assert list(db_session.scalars(select(Match).where(Match.client_id == client.id))) == []


def test_stable_matching_bumps_a_weaker_client_for_a_stronger_one(db_session: Session) -> None:
    """A solo provider with one slot prefers a full-fit client over a partial one, so the
    partial-fit client gets bumped and ends up unmatched, regardless of proposal order."""
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=1, specialties=["anxiety", "trauma"])
    weak = _client(db_session, run, needs=["anxiety", "adhd"])  # adhd uncovered: partial fit
    strong = _client(db_session, run, needs=["anxiety", "trauma"])  # fully covered

    run_stable_matching(db_session, run.id)

    match = db_session.scalars(
        select(Match).where(Match.client_id.in_([weak.id, strong.id]))
    ).one()
    assert match.client_id == strong.id
    assert match.provider_id == provider.id
    assert match.score == 1.0


def test_stable_matching_fills_every_slot_of_a_multi_capacity_provider(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=2)
    first, second, third = (_client(db_session, run) for _ in range(3))

    summary = run_stable_matching(db_session, run.id)

    assert summary.matched_count == 2
    assert summary.unmatched_count == 1
    matched_clients = {
        m.client_id
        for m in db_session.scalars(
            select(Match).where(Match.client_id.in_([first.id, second.id, third.id]))
        )
    }
    assert len(matched_clients) == 2
    assert all(m_id in {first.id, second.id, third.id} for m_id in matched_clients)
    for match in db_session.scalars(
        select(Match).where(Match.client_id.in_(matched_clients))
    ):
        assert match.provider_id == provider.id


def test_stable_matching_is_indifferent_to_client_processing_order(db_session: Session) -> None:
    """Gale-Shapley's result doesn't depend on the order free clients are processed in,
    only on the preference lists, so reversed arrival order should reach the same outcome."""
    run_a = _run(db_session, seed=1)
    provider_a = _provider(db_session, run_a, capacity=1, specialties=["anxiety", "trauma"])
    _client(db_session, run_a, arrival_day=0, needs=["anxiety", "adhd"])
    strong_a = _client(db_session, run_a, arrival_day=1, needs=["anxiety", "trauma"])

    run_b = _run(db_session, seed=2)
    provider_b = _provider(db_session, run_b, capacity=1, specialties=["anxiety", "trauma"])
    strong_b = _client(db_session, run_b, arrival_day=0, needs=["anxiety", "trauma"])
    _client(db_session, run_b, arrival_day=1, needs=["anxiety", "adhd"])

    run_stable_matching(db_session, run_a.id)
    run_stable_matching(db_session, run_b.id)

    match_a = db_session.scalars(select(Match).where(Match.provider_id == provider_a.id)).one()
    match_b = db_session.scalars(select(Match).where(Match.provider_id == provider_b.id)).one()
    assert match_a.client_id == strong_a.id
    assert match_b.client_id == strong_b.id


def test_running_stable_matching_twice_raises(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run)
    _client(db_session, run)

    run_stable_matching(db_session, run.id)
    with pytest.raises(StrategyAlreadyRunError):
        run_stable_matching(db_session, run.id)


def test_stable_matching_endpoint_returns_summary_and_404_and_409(api: TestClient) -> None:
    create_res = api.post(
        "/api/v1/simulation-runs",
        json={"name": "Stable Endpoint", "seed": 1, "provider_count": 5, "client_count": 5},
    )
    run_id = create_res.json()["id"]
    api.post(f"/api/v1/simulation-runs/{run_id}/generate")

    first = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/stable-matching")
    assert first.status_code == 201
    summary = first.json()
    assert summary["strategy"] == "stable_matching"
    assert summary["matched_count"] + summary["unmatched_count"] == 5

    second = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/stable-matching")
    assert second.status_code == 409

    missing = api.post(f"/api/v1/simulation-runs/{uuid.uuid4()}/strategies/stable-matching")
    assert missing.status_code == 404
