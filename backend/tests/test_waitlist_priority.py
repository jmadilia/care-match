import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.waitlist_priority import _priority, run_waitlist_priority
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun
from app.models.waitlist_entry import WaitlistEntry


def _run(db: Session, seed: int = 1) -> SimulationRun:
    run = SimulationRun(name="Waitlist Test", seed=seed, provider_count=1, client_count=1)
    db.add(run)
    db.flush()
    return run


def _provider(
    db: Session,
    run: SimulationRun,
    capacity: int = 1,
    states: list[str] | None = None,
    panels: list[str] | None = None,
) -> Provider:
    provider = Provider(
        name=f"p-{uuid.uuid4().hex[:8]}",
        license_states=states or ["CA"],
        specialties=["anxiety"],
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
    urgency: str = "ROUTINE",
    state: str = "CA",
    payer: str = "Aetna",
) -> Client:
    client = Client(
        name=f"c-{uuid.uuid4().hex[:8]}",
        state=state,
        insurance_payer=payer,
        needed_specialties=["anxiety"],
        preferred_modality="video",
        preferred_language="en",
        urgency=urgency,
        arrival_day=arrival_day,
        simulation_run_id=run.id,
    )
    db.add(client)
    db.flush()
    return client


def test_priority_formula_crosses_urgency_tiers_with_aging() -> None:
    class Stub:
        urgency = "ROUTINE"
        arrival_day = 0

    routine = Stub()
    assert _priority(routine, 0) == 0.0
    assert _priority(routine, 6) == 3.0  # catches ELEVATED's baseline after 6 days
    assert _priority(routine, 14) == 7.0  # catches URGENT's baseline after 14 days
    assert _priority(routine, 20) == 10.0  # keeps climbing past that


def test_waitlist_priority_matches_a_single_eligible_pair(db_session: Session) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run)
    client = _client(db_session, run)

    summary = run_waitlist_priority(db_session, run.id)

    assert summary.strategy == "waitlist_priority"
    assert summary.matched_count == 1
    assert summary.unmatched_count == 0

    match = db_session.scalars(select(Match).where(Match.client_id == client.id)).one()
    assert match.provider_id == provider.id

    entry = db_session.scalars(
        select(WaitlistEntry).where(WaitlistEntry.client_id == client.id)
    ).one()
    assert entry.status == "MATCHED"
    assert entry.resolved_at is not None


def test_waitlist_priority_expires_ineligible_clients(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run, states=["NY"])
    client = _client(db_session, run, state="CA")

    summary = run_waitlist_priority(db_session, run.id)

    assert summary.matched_count == 0
    assert summary.unmatched_count == 1

    entry = db_session.scalars(
        select(WaitlistEntry).where(WaitlistEntry.client_id == client.id)
    ).one()
    assert entry.status == "EXPIRED"
    assert entry.resolved_at is not None


def test_later_urgent_arrival_bumps_an_earlier_routine_holder(db_session: Session) -> None:
    """The only provider has one slot. A routine client takes it on day 0 since nobody
    else is competing. An urgent client arriving later outranks them on priority alone,
    same fit score, and bumps them even though the routine client got there first."""
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=1)
    early_routine = _client(db_session, run, arrival_day=0, urgency="ROUTINE")
    later_urgent = _client(db_session, run, arrival_day=5, urgency="URGENT")

    run_waitlist_priority(db_session, run.id)

    match = db_session.scalars(
        select(Match).where(Match.client_id.in_([early_routine.id, later_urgent.id]))
    ).one()
    assert match.client_id == later_urgent.id
    assert match.provider_id == provider.id

    bumped_entry = db_session.scalars(
        select(WaitlistEntry).where(WaitlistEntry.client_id == early_routine.id)
    ).one()
    assert bumped_entry.status == "EXPIRED"  # no other provider to fall back to


def test_waitlist_priority_fills_every_slot_of_a_multi_capacity_provider(
    db_session: Session,
) -> None:
    run = _run(db_session)
    provider = _provider(db_session, run, capacity=2)
    first, second, third = (
        _client(db_session, run, arrival_day=day) for day in (0, 1, 2)
    )

    summary = run_waitlist_priority(db_session, run.id)

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


def test_running_waitlist_priority_twice_raises(db_session: Session) -> None:
    run = _run(db_session)
    _provider(db_session, run)
    _client(db_session, run)

    run_waitlist_priority(db_session, run.id)
    with pytest.raises(StrategyAlreadyRunError):
        run_waitlist_priority(db_session, run.id)


def test_waitlist_priority_endpoint_returns_summary_and_404_and_409(api: TestClient) -> None:
    create_res = api.post(
        "/api/v1/simulation-runs",
        json={"name": "Waitlist Endpoint", "seed": 1, "provider_count": 5, "client_count": 5},
    )
    run_id = create_res.json()["id"]
    api.post(f"/api/v1/simulation-runs/{run_id}/generate")

    first = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/waitlist-priority")
    assert first.status_code == 201
    summary = first.json()
    assert summary["strategy"] == "waitlist_priority"
    assert summary["matched_count"] + summary["unmatched_count"] == 5

    second = api.post(f"/api/v1/simulation-runs/{run_id}/strategies/waitlist-priority")
    assert second.status_code == 409

    missing = api.post(f"/api/v1/simulation-runs/{uuid.uuid4()}/strategies/waitlist-priority")
    assert missing.status_code == 404
