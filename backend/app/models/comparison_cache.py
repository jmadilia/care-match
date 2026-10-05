from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ComparisonCacheEntry(Base):
  """A computed comparison, kept so every serverless instance can reuse it."""

  __tablename__ = "comparison_cache"

  key: Mapped[str] = mapped_column(String(64), primary_key=True)
  result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
  # clock_timestamp() rather than now(): now() is the transaction's start time, so rows
  # written in one transaction would tie and "newest N" would be ambiguous.
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.clock_timestamp(), index=True
  )
