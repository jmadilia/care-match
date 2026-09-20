import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_states: Mapped[list[str]] = mapped_column(ARRAY(String(2)), nullable=False)
    specialties: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
    modalities: Mapped[list[str]] = mapped_column(ARRAY(String(32)), nullable=False)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False)
    insurance_panels: Mapped[list[str]] = mapped_column(ARRAY(String(128)), nullable=False)
    weekly_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
