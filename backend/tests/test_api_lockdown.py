import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.router import build_api_router
from app.core.config import Settings
from app.db.session import get_db

ID = uuid.uuid4()


def _app(*, admin_enabled: bool, admin_key: str | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(
        build_api_router(admin_enabled=admin_enabled, admin_key=admin_key), prefix="/api/v1"
    )
    return app


ADMIN_REQUESTS = [
    ("GET", "/api/v1/providers"),
    ("POST", "/api/v1/providers"),
    ("DELETE", f"/api/v1/providers/{ID}"),
    ("GET", "/api/v1/clients"),
    ("GET", f"/api/v1/clients/{ID}/candidates"),
    ("GET", "/api/v1/matches"),
    ("GET", "/api/v1/waitlist-entries"),
    ("GET", "/api/v1/simulation-runs"),
    ("POST", f"/api/v1/simulation-runs/{ID}/generate"),
    ("POST", f"/api/v1/simulation-runs/{ID}/strategies/greedy"),
    ("POST", f"/api/v1/simulation-runs/{ID}/strategies/optimal"),
]


@pytest.mark.parametrize(("method", "path"), ADMIN_REQUESTS)
def test_admin_routes_do_not_exist_when_the_admin_api_is_disabled(method: str, path: str) -> None:
    client = TestClient(_app(admin_enabled=False))
    # 404, not 405 or 401: the path is absent, not merely protected.
    assert client.request(method, path).status_code == 404


def test_public_routes_stay_available_when_the_admin_api_is_disabled() -> None:
    client = TestClient(_app(admin_enabled=False))

    assert client.get("/api/v1/health").status_code == 200
    # Reaching validation (422) rather than 404 proves the route is mounted.
    assert client.post("/api/v1/comparisons", json={}).status_code == 422
    assert client.post("/api/v1/intake", json={}).status_code == 422


def test_admin_routes_require_the_key_when_one_is_configured(db_session: Session) -> None:
    app = _app(admin_enabled=True, admin_key="s3cret")
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    assert client.get("/api/v1/providers").status_code == 401
    assert client.get("/api/v1/providers", headers={"X-Admin-Key": "wrong"}).status_code == 403
    assert client.get("/api/v1/providers", headers={"X-Admin-Key": "s3cret"}).status_code == 200
    # The key guards the admin surface only.
    assert client.get("/api/v1/health").status_code == 200


def test_admin_routes_are_open_when_enabled_without_a_key(db_session: Session) -> None:
    app = _app(admin_enabled=True)
    app.dependency_overrides[get_db] = lambda: db_session
    assert TestClient(app).get("/api/v1/providers").status_code == 200


def test_the_admin_api_defaults_to_on_locally_and_off_elsewhere() -> None:
    assert Settings(_env_file=None).admin_api_enabled is True
    assert Settings(_env_file=None, ENVIRONMENT="production").admin_api_enabled is False


def test_the_admin_api_can_be_switched_explicitly() -> None:
    assert Settings(_env_file=None, ADMIN_API_ENABLED=False).admin_api_enabled is False
    enabled = Settings(
        _env_file=None, ENVIRONMENT="production", ADMIN_API_ENABLED=True, ADMIN_API_KEY="k"
    )
    assert enabled.admin_api_enabled is True


def test_enabling_the_admin_api_outside_local_without_a_key_fails_closed() -> None:
    with pytest.raises(ValidationError, match="requires ADMIN_API_KEY"):
        Settings(_env_file=None, ENVIRONMENT="production", ADMIN_API_ENABLED=True)
