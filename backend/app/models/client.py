import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Client(Base):
  __tablename__ = "clients"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
  )
  name: Mapped[str] = mapped_column(String(255), nullable=False)
  state: Mapped[str] = mapped_column(String(2), nullable=False)
  insurance_payer: Mapped[str] = mapped_column(String(255), nullable=False)
  needed_specialties: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
  preferred_modality: Mapped[str] = mapped_column(String(32), nullable=False)
  preferred_language: Mapped[str] = mapped_column(String(64), nullable=False)
  urgency: Mapped[str] = mapped_column(String(255), nullable=False)
  arrival_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
  simulation_run_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("simulation_runs.id"), nullable=True
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )