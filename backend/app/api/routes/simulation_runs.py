import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.greedy import run_greedy
from app.matching.strategies.optimal import run_optimal
from app.matching.strategies.stable_matching import run_stable_matching
from app.matching.strategies.waitlist_priority import run_waitlist_priority
from app.models.simulation_run import SimulationRun
from app.schemas.simulation_run import (
  PopulationSummary,
  SimulationRunCreate,
  SimulationRunRead,
)
from app.schemas.strategy_run import StrategyRunSummary
from app.simulation.service import RunAlreadyGeneratedError, generate_for_run

router = APIRouter(prefix="/simulation-runs", tags=["simulation-runs"])


@router.get("", response_model=list[SimulationRunRead])
def list_simulation_runs(db: DbSession) -> list[SimulationRun]:
  return list(db.scalars(select(SimulationRun).order_by(SimulationRun.created_at.desc())))


@router.post("", response_model=SimulationRunRead, status_code=201)
def create_simulation_run(run_in: SimulationRunCreate, db: DbSession) -> SimulationRun:
  run = SimulationRun(**run_in.model_dump())
  db.add(run)
  db.commit()
  db.refresh(run)
  return run


@router.get("/{run_id}", response_model=SimulationRunRead)
def get_simulation_run(run_id: uuid.UUID, db: DbSession) -> SimulationRun:
  run = db.get(SimulationRun, run_id)
  if run is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  return run


@router.post("/{run_id}/generate", response_model=PopulationSummary, status_code=201)
def generate_simulation_run(run_id: uuid.UUID, db: DbSession) -> PopulationSummary:
  run = db.get(SimulationRun, run_id)
  if run is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  try:
    return generate_for_run(db, run)
  except RunAlreadyGeneratedError:
    raise HTTPException(
      status_code=409, detail="Simulation run already has a generated population"
    ) from None


@router.post("/{run_id}/strategies/greedy", response_model=StrategyRunSummary, status_code=201)
def run_greedy_strategy(run_id: uuid.UUID, db: DbSession) -> StrategyRunSummary:
  if db.get(SimulationRun, run_id) is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  try:
    return run_greedy(db, run_id)
  except StrategyAlreadyRunError:
    raise HTTPException(
      status_code=409, detail="greedy has already been run for this simulation run"
    ) from None


@router.post(
  "/{run_id}/strategies/stable-matching", response_model=StrategyRunSummary, status_code=201
)
def run_stable_matching_strategy(run_id: uuid.UUID, db: DbSession) -> StrategyRunSummary:
  if db.get(SimulationRun, run_id) is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  try:
    return run_stable_matching(db, run_id)
  except StrategyAlreadyRunError:
    raise HTTPException(
      status_code=409, detail="stable_matching has already been run for this simulation run"
    ) from None


@router.post("/{run_id}/strategies/optimal", response_model=StrategyRunSummary, status_code=201)
def run_optimal_strategy(run_id: uuid.UUID, db: DbSession) -> StrategyRunSummary:
  if db.get(SimulationRun, run_id) is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  try:
    return run_optimal(db, run_id)
  except StrategyAlreadyRunError:
    raise HTTPException(
      status_code=409, detail="optimal has already been run for this simulation run"
    ) from None


@router.post(
  "/{run_id}/strategies/waitlist-priority", response_model=StrategyRunSummary, status_code=201
)
def run_waitlist_priority_strategy(run_id: uuid.UUID, db: DbSession) -> StrategyRunSummary:
  if db.get(SimulationRun, run_id) is None:
    raise HTTPException(status_code=404, detail="Simulation run not found")
  try:
    return run_waitlist_priority(db, run_id)
  except StrategyAlreadyRunError:
    raise HTTPException(
      status_code=409, detail="waitlist_priority has already been run for this simulation run"
    ) from None
