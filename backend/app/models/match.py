import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Match(Base):
  __tablename__ = "matches"

  id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
  client_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("clients.id")
  )
  provider_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("providers.id")
  )
  strategy: Mapped[str] = mapped_column(String(255), nullable=False)
  score: Mapped[float] = mapped_column(Float, nullable=False)
  status: Mapped[str] = mapped_column(String(64), nullable=False)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )