from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def build_engine(database_url: str, environment: str) -> Engine:
    options: dict[str, Any] = {
        # Disables psycopg's automatic server-side prepared statements, which don't survive a
        # transaction-mode connection pooler (what hosted serverless Postgres puts in front).
        "connect_args": {"prepare_threshold": None},
    }
    if environment == "local":
        options["pool_pre_ping"] = True
    else:
        # Serverless instances are short-lived and numerous, so holding a pool per instance
        # only multiplies idle connections. Pooling belongs to the database's own pooler.
        options["poolclass"] = NullPool
    return create_engine(database_url, **options)


engine = build_engine(settings.DATABASE_URL, settings.ENVIRONMENT)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
