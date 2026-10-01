import uuid
from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.matching.strategies.greedy import run_greedy
from app.matching.strategies.optimal import run_optimal
from app.matching.strategies.stable_matching import run_stable_matching
from app.matching.strategies.waitlist_priority import run_waitlist_priority
from app.models.simulation_run import SimulationRun
from app.schemas.strategy_run import StrategyRunSummary
from app.simulation.service import generate_for_run


def _generate_run(db: Session, seed: int) -> SimulationRun:
    run = SimulationRun(name=f"determinism-{seed}", seed=seed, provider_count=20, client_count=80)
    db.add(run)
    db.flush()
    generate_for_run(db, run)
    return run


@pytest.mark.parametrize(
    "run_strategy", [run_greedy, run_stable_matching, run_optimal, run_waitlist_priority]
)
def test_strategy_is_deterministic_across_separately_generated_populations(
    db_session: Session,
    run_strategy: Callable[[Session, uuid.UUID], StrategyRunSummary],
) -> None:
    """Same seed, but two independently generated populations rather than one population
    queried twice, since database row order (not just the seed) must not affect the
    outcome. This is a regression test for a real bug: client/provider queries tie-broke
    on created_at, which is identical for every row in one bulk insert, so Postgres could
    return ties in a different order across separate queries even with the same seed.
    """
    first_run = _generate_run(db_session, seed=7)
    second_run = _generate_run(db_session, seed=7)

    first_summary = run_strategy(db_session, first_run.id)
    second_summary = run_strategy(db_session, second_run.id)

    assert first_summary.model_dump() == second_summary.model_dump()
