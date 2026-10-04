import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

VALID = {
    "scenario": "balanced",
    "seed": 1,
    "state": "CA",
    "insurance_payer": "Aetna",
    "needed_specialties": ["anxiety"],
    "preferred_modality": "video",
    "preferred_language": "en",
}


def _stable(candidates: list[dict]) -> list[tuple]:  # type: ignore[type-arg]
    # Provider ids and timestamps are fresh per request (the pool is regenerated and
    # discarded), so compare on the fields that are a function of the seed.
    return [
        (
            c["provider"]["name"],
            tuple(c["provider"]["specialties"]),
            c["provider"]["weekly_capacity"],
            c["score"],
            c["remaining_capacity"],
        )
        for c in candidates
    ]


def test_intake_returns_ranked_eligible_candidates(api: TestClient) -> None:
    res = api.post("/api/v1/intake", json=VALID)

    assert res.status_code == 200
    body = res.json()
    assert body["scenario"] == "balanced"
    assert body["seed"] == 1
    assert body["pool_provider_count"] == 20

    candidates = body["candidates"]
    assert 0 < len(candidates) <= 5
    scores = [c["score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)
    for candidate in candidates:
        provider = candidate["provider"]
        assert "CA" in provider["license_states"]
        assert "Aetna" in provider["insurance_panels"]
        assert candidate["remaining_capacity"] > 0
        assert 0.0 <= candidate["score"] <= 1.0


def test_intake_is_deterministic_for_a_seed(api: TestClient) -> None:
    first = api.post("/api/v1/intake", json=VALID).json()["candidates"]
    second = api.post("/api/v1/intake", json=VALID).json()["candidates"]
    assert _stable(first) == _stable(second)


def test_intake_pool_depends_on_the_seed(api: TestClient) -> None:
    one = api.post("/api/v1/intake", json={**VALID, "seed": 1, "limit": 20}).json()
    two = api.post("/api/v1/intake", json={**VALID, "seed": 2, "limit": 20}).json()
    assert _stable(one["candidates"]) != _stable(two["candidates"])


def test_intake_respects_limit(api: TestClient) -> None:
    res = api.post("/api/v1/intake", json={**VALID, "limit": 2})
    assert len(res.json()["candidates"]) <= 2


def test_intake_stores_nothing(api: TestClient, db_session: Session) -> None:
    assert api.post("/api/v1/intake", json=VALID).status_code == 200

    for table in ("matches", "clients", "providers", "simulation_runs", "waitlist_entries"):
        count = db_session.execute(text(f"select count(*) from {table}")).scalar()
        assert count == 0, f"{table} has {count} rows after an intake request"


@pytest.mark.parametrize(
    "override",
    [
        {"state": "ZZ"},
        {"insurance_payer": "Nonexistent Health"},
        {"needed_specialties": []},
        {"needed_specialties": ["astrology"]},
        {"needed_specialties": ["anxiety", "anxiety"]},
        {"preferred_modality": "carrier_pigeon"},
        {"preferred_language": "xx"},
        {"scenario": "nonsense"},
        {"seed": -1},
        {"seed": 100_001},
        {"limit": 0},
        {"limit": 21},
    ],
)
def test_intake_rejects_invalid_input(api: TestClient, override: dict[str, object]) -> None:
    res = api.post("/api/v1/intake", json={**VALID, **override})
    assert res.status_code == 422
