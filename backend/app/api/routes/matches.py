import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.schemas.match import MatchCreate, MatchRead, MatchStatus, MatchUpdate

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(
  db: DbSession,
  client_id: uuid.UUID | None = None,
  provider_id: uuid.UUID | None = None,
  strategy: str | None = None,
  status: MatchStatus | None = None,
) -> list[Match]:
  query = select(Match).order_by(Match.created_at.desc())
  if client_id is not None:
    query = query.where(Match.client_id == client_id)
  if provider_id is not None:
    query = query.where(Match.provider_id == provider_id)
  if strategy is not None:
    query = query.where(Match.strategy == strategy)
  if status is not None:
    query = query.where(Match.status == status)
  return list(db.scalars(query))


@router.post("", response_model=MatchRead, status_code=201)
def create_match(match_in: MatchCreate, db: DbSession) -> Match:
  if db.get(Client, match_in.client_id) is None:
    raise HTTPException(status_code=404, detail="Client not found")
  if db.get(Provider, match_in.provider_id) is None:
    raise HTTPException(status_code=404, detail="Provider not found")

  match = Match(**match_in.model_dump())
  db.add(match)
  db.commit()
  db.refresh(match)
  return match


@router.get("/{match_id}", response_model=MatchRead)
def get_match(match_id: uuid.UUID, db: DbSession) -> Match:
  match = db.get(Match, match_id)
  if match is None:
    raise HTTPException(status_code=404, detail="Match not found")
  return match


@router.patch("/{match_id}", response_model=MatchRead)
def update_match(match_id: uuid.UUID, match_in: MatchUpdate, db: DbSession) -> Match:
  match = db.get(Match, match_id)
  if match is None:
    raise HTTPException(status_code=404, detail="Match not found")
  for field, value in match_in.model_dump(exclude_unset=True).items():
    setattr(match, field, value)
  db.commit()
  db.refresh(match)
  return match
