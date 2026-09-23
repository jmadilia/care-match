import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun
from app.schemas.provider import ProviderCreate, ProviderRead, ProviderUpdate

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderRead])
def list_providers(
    db: DbSession, simulation_run_id: uuid.UUID | None = None
) -> list[Provider]:
    query = select(Provider).order_by(Provider.created_at.desc())
    if simulation_run_id is not None:
        query = query.where(Provider.simulation_run_id == simulation_run_id)
    return list(db.scalars(query))


@router.post("", response_model=ProviderRead, status_code=201)
def create_provider(provider_in: ProviderCreate, db: DbSession) -> Provider:
    if (
        provider_in.simulation_run_id is not None
        and db.get(SimulationRun, provider_in.simulation_run_id) is None
    ):
        raise HTTPException(status_code=404, detail="Simulation run not found")

    provider = Provider(**provider_in.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(provider_id: uuid.UUID, db: DbSession) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.patch("/{provider_id}", response_model=ProviderRead)
def update_provider(
    provider_id: uuid.UUID, provider_in: ProviderUpdate, db: DbSession
) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    for field, value in provider_in.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/{provider_id}", status_code=204)
def delete_provider(provider_id: uuid.UUID, db: DbSession) -> None:
    provider = db.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
