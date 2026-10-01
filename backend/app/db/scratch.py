from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import engine


@contextmanager
def scratch_session() -> Generator[Session, None, None]:
    """A session whose writes are always rolled back on exit, for throwaway work that
    must never persist: test fixtures, and the strategy-comparison harness's synthetic
    populations. join_transaction_mode="create_savepoint" means every commit() the caller
    makes releases a savepoint rather than the outer transaction, so nothing escapes the
    final rollback.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
