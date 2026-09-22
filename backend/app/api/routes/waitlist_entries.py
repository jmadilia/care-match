import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.client import Client
from app.models.waitlist_entry import WaitlistEntry
from app.schemas.waitlist_entry import (
  WaitlistEntryCreate,
  WaitlistEntryRead,
  WaitlistEntryUpdate,
  WaitlistStatus,
)

router = APIRouter(prefix="/waitlist-entries", tags=["waitlist-entries"])


@router.get("", response_model=list[WaitlistEntryRead])
def list_waitlist_entries(
  db: DbSession,
  client_id: uuid.UUID | None = None,
  status: WaitlistStatus | None = None,
) -> list[WaitlistEntry]:
  query = select(WaitlistEntry).order_by(WaitlistEntry.created_at.asc())
  if client_id is not None:
    query = query.where(WaitlistEntry.client_id == client_id)
  if status is not None:
    query = query.where(WaitlistEntry.status == status)
  return list(db.scalars(query))


@router.post("", response_model=WaitlistEntryRead, status_code=201)
def create_waitlist_entry(entry_in: WaitlistEntryCreate, db: DbSession) -> WaitlistEntry:
  if db.get(Client, entry_in.client_id) is None:
    raise HTTPException(status_code=404, detail="Client not found")

  entry = WaitlistEntry(client_id=entry_in.client_id, status=WaitlistStatus.WAITING)
  db.add(entry)
  db.commit()
  db.refresh(entry)
  return entry


@router.get("/{entry_id}", response_model=WaitlistEntryRead)
def get_waitlist_entry(entry_id: uuid.UUID, db: DbSession) -> WaitlistEntry:
  entry = db.get(WaitlistEntry, entry_id)
  if entry is None:
    raise HTTPException(status_code=404, detail="Waitlist entry not found")
  return entry


@router.patch("/{entry_id}", response_model=WaitlistEntryRead)
def update_waitlist_entry(
  entry_id: uuid.UUID, entry_in: WaitlistEntryUpdate, db: DbSession
) -> WaitlistEntry:
  entry = db.get(WaitlistEntry, entry_id)
  if entry is None:
    raise HTTPException(status_code=404, detail="Waitlist entry not found")

  update_data = entry_in.model_dump(exclude_unset=True)
  new_status = update_data.get("status")
  if new_status is not None and new_status != WaitlistStatus.WAITING and entry.resolved_at is None:
    entry.resolved_at = datetime.now(UTC)

  for field, value in update_data.items():
    setattr(entry, field, value)
  db.commit()
  db.refresh(entry)
  return entry
