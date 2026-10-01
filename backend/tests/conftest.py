from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.scratch import scratch_session
from app.db.session import get_db
from app.main import app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """A session whose work is rolled back at the end, so tests leave no rows behind."""
    with scratch_session() as session:
        yield session


@pytest.fixture
def api(db_session: Session) -> Generator[TestClient, None, None]:
    """A test client whose requests share the rolled-back session."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
