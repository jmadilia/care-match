import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.simulation_run import SimulationRun
from app.schemas.simulation_run import (
  PopulationSummary,
  SimulationRunCreate,
  SimulationRunRead,
)
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
