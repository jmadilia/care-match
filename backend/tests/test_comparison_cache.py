import threading
import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.evaluation import cache
from app.evaluation.comparison import run_comparison
from app.models.comparison_cache import ComparisonCacheEntry
from app.schemas.comparison import ComparisonRequest, ComparisonResult


@pytest.fixture(autouse=True)
def _fresh_cache() -> Iterator[None]:
    cache.clear_cache()
    yield
    cache.clear_cache()


def _request(seed: int = 1) -> ComparisonRequest:
    return ComparisonRequest(seeds=[seed], provider_count=5, client_count=20)


def _stored(db: Session) -> int:
    return db.execute(select(func.count()).select_from(ComparisonCacheEntry)).scalar_one()


def _counting(monkeypatch: pytest.MonkeyPatch) -> list[ComparisonRequest]:
    calls: list[ComparisonRequest] = []

    def counting(request: ComparisonRequest) -> ComparisonResult:
        calls.append(request)
        return run_comparison(request)

    monkeypatch.setattr(cache, "run_comparison", counting)
    return calls


def test_computed_result_is_stored_and_reused_by_another_instance(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _counting(monkeypatch)
    request = _request()

    first = cache.get_comparison(request, db_session)
    assert _stored(db_session) == 1

    # A different instance has an empty in-memory cache but shares the database.
    cache.clear_cache()
    second = cache.get_comparison(request, db_session)

    assert len(calls) == 1
    assert second == first


def test_without_a_session_nothing_is_stored(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _counting(monkeypatch)

    cache.get_comparison(_request())
    cache.clear_cache()
    cache.get_comparison(_request())

    assert len(calls) == 2
    assert _stored(db_session) == 0


def test_a_new_code_version_does_not_reuse_stored_results(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _counting(monkeypatch)
    cache.get_comparison(_request(), db_session)

    cache.clear_cache()
    monkeypatch.setattr(cache, "CODE_VERSION", "a-later-commit")
    cache.get_comparison(_request(), db_session)

    assert len(calls) == 2
    assert _stored(db_session) == 2


def test_stored_results_are_pruned_to_the_newest(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cache, "MAX_SHARED_ENTRIES", 2)

    for seed in (1, 2, 3):
        cache.get_comparison(_request(seed), db_session)

    assert _stored(db_session) == 2
    kept = {
        cache._shared_key(_request(2)),
        cache._shared_key(_request(3)),
    }
    assert set(db_session.execute(select(ComparisonCacheEntry.key)).scalars()) == kept


def test_a_failing_shared_cache_falls_back_to_computing(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: object, **_kwargs: object) -> None:
        raise OperationalError("select", {}, Exception("database unreachable"))

    monkeypatch.setattr(db_session, "get", broken)
    monkeypatch.setattr(db_session, "execute", broken)

    result = cache.get_comparison(_request(), db_session)

    assert result == run_comparison(_request())


def test_identical_concurrent_requests_share_one_computation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = threading.Event()
    release = threading.Event()
    calls: list[ComparisonRequest] = []

    def slow(request: ComparisonRequest) -> ComparisonResult:
        calls.append(request)
        started.set()
        release.wait(timeout=10)
        return run_comparison(request)

    monkeypatch.setattr(cache, "run_comparison", slow)
    results: list[ComparisonResult] = []

    def worker() -> None:
        results.append(cache.get_comparison(_request()))

    threads = [threading.Thread(target=worker) for _ in range(4)]
    threads[0].start()
    assert started.wait(timeout=10)
    for thread in threads[1:]:
        thread.start()
    time.sleep(0.2)  # let the others reach the in-flight lock before the first finishes
    release.set()
    for thread in threads:
        thread.join(timeout=30)

    assert len(calls) == 1
    assert len(results) == 4
    assert all(result == results[0] for result in results)
    assert cache._inflight == {}


def test_deployed_route_stores_results_but_local_does_not(
    api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _request(1).model_dump(mode="json")

    monkeypatch.setattr(settings, "ENVIRONMENT", "local")
    assert api.post("/api/v1/comparisons", json=body).status_code == 201
    assert _stored(db_session) == 0

    cache.clear_cache()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert api.post("/api/v1/comparisons", json=body).status_code == 201
    assert _stored(db_session) == 1
