import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: DbSession) -> list[Client]:
  return list(db.scalars(select(Client).order_by(Client.created_at.desc())))


@router.post("", response_model=ClientRead, status_code=201)
def create_client(client_in: ClientCreate, db: DbSession) -> Client:
  client = Client(**client_in.model_dump())
  db.add(client)
  db.commit()
  db.refresh(client)
  return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: uuid.UUID, db: DbSession) -> Client:
  client = db.get(Client, client_id)
  if client is None:
    raise HTTPException(status_code=404, detail="Client not found")
  return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
  client_id: uuid.UUID, client_in: ClientUpdate, db: DbSession
) -> Client:
  client = db.get(Client, client_id)
  if client is None:
    raise HTTPException(status_code=404, detail="Client not found")
  for field, value in client_in.model_dump(exclude_unset=True).items():
    setattr(client, field, value)
  db.commit()
  db.refresh(client)
  return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: uuid.UUID, db: DbSession) -> None:
  client = db.get(Client, client_id)
  if client is None:
    raise HTTPException(status_code=404, detail="Client not found")
  db.delete(client)
  db.commit()