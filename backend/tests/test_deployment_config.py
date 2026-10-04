import pytest
from sqlalchemy import text
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import Settings, settings
from app.db.session import build_engine


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (
            "postgres://u:p@host.example/db?sslmode=require",
            "postgresql+psycopg://u:p@host.example/db?sslmode=require",
        ),
        (
            "postgresql://u:p@host.example/db?sslmode=require",
            "postgresql+psycopg://u:p@host.example/db?sslmode=require",
        ),
        (
            "postgresql+psycopg://u:p@host.example/db",
            "postgresql+psycopg://u:p@host.example/db",
        ),
        ("sqlite:///local.db", "sqlite:///local.db"),
    ],
)
def test_database_url_is_normalized_to_the_psycopg_driver(given: str, expected: str) -> None:
    assert Settings(_env_file=None, DATABASE_URL=given).DATABASE_URL == expected


def test_local_engine_keeps_a_connection_pool() -> None:
    engine = build_engine(settings.DATABASE_URL, "local")
    try:
        assert isinstance(engine.pool, QueuePool)
    finally:
        engine.dispose()


def test_deployed_engine_does_not_pool_connections() -> None:
    engine = build_engine(settings.DATABASE_URL, "production")
    try:
        assert isinstance(engine.pool, NullPool)
    finally:
        engine.dispose()


@pytest.mark.parametrize("environment", ["local", "production"])
def test_prepared_statements_are_disabled_behind_either_pool(environment: str) -> None:
    engine = build_engine(settings.DATABASE_URL, environment)
    try:
        with engine.connect() as connection:
            # More statements than psycopg's default prepare threshold of 5, to prove the
            # setting holds up under repeated use rather than just at connect time.
            for _ in range(8):
                assert connection.execute(text("select 1")).scalar() == 1
            assert connection.connection.driver_connection.prepare_threshold is None  # type: ignore[union-attr]
    finally:
        engine.dispose()
