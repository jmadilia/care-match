from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_provider() -> str:
    payload = {
        "name": "Dr. Match Provider",
        "license_states": ["CA"],
        "specialties": ["anxiety"],
        "modalities": ["video"],
        "languages": ["en"],
        "insurance_panels": ["Aetna"],
        "weekly_capacity": 20,
    }
    res = client.post("/api/v1/providers", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def _create_client() -> str:
    payload = {
        "name": "Match Client",
        "state": "CA",
        "insurance_payer": "Aetna",
        "needed_specialties": ["anxiety"],
        "preferred_modality": "video",
        "preferred_language": "en",
        "urgency": "ROUTINE",
    }
    res = client.post("/api/v1/clients", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_match_crud() -> None:
    provider_id = _create_provider()
    client_id = _create_client()

    payload = {
        "client_id": client_id,
        "provider_id": provider_id,
        "strategy": "greedy",
        "score": 0.85,
    }

    create_res = client.post("/api/v1/matches", json=payload)
    assert create_res.status_code == 201
    match = create_res.json()
    match_id = match["id"]
    assert match["client_id"] == client_id
    assert match["provider_id"] == provider_id
    assert match["status"] == "PROPOSED"

    get_res = client.get(f"/api/v1/matches/{match_id}")
    assert get_res.status_code == 200
    assert get_res.json()["strategy"] == "greedy"

    patch_res = client.patch(f"/api/v1/matches/{match_id}", json={"status": "ACCEPTED"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "ACCEPTED"

    missing_res = client.get("/api/v1/matches/00000000-0000-0000-0000-000000000000")
    assert missing_res.status_code == 404


def test_match_list_filters() -> None:
    provider_id = _create_provider()
    client_id = _create_client()

    client.post(
        "/api/v1/matches",
        json={
            "client_id": client_id,
            "provider_id": provider_id,
            "strategy": "greedy",
            "score": 0.5,
        },
    )
    client.post(
        "/api/v1/matches",
        json={
            "client_id": client_id,
            "provider_id": provider_id,
            "strategy": "stable_matching",
            "score": 0.9,
        },
    )

    by_strategy = client.get("/api/v1/matches", params={"strategy": "stable_matching"})
    assert by_strategy.status_code == 200
    results = by_strategy.json()
    assert len(results) >= 1
    assert all(m["strategy"] == "stable_matching" for m in results)

    by_client = client.get("/api/v1/matches", params={"client_id": client_id})
    assert by_client.status_code == 200
    assert all(m["client_id"] == client_id for m in by_client.json())

    by_status = client.get("/api/v1/matches", params={"status": "ACCEPTED"})
    assert by_status.status_code == 200
    assert all(m["status"] == "ACCEPTED" for m in by_status.json())


def test_match_create_rejects_invalid_status() -> None:
    provider_id = _create_provider()
    client_id = _create_client()

    payload = {
        "client_id": client_id,
        "provider_id": provider_id,
        "strategy": "greedy",
        "score": 0.5,
        "status": "NOT_A_REAL_STATUS",
    }

    res = client.post("/api/v1/matches", json=payload)
    assert res.status_code == 422


def test_match_create_rejects_unknown_client_or_provider() -> None:
    provider_id = _create_provider()
    client_id = _create_client()
    fake_id = "00000000-0000-0000-0000-000000000000"

    bad_client = client.post(
        "/api/v1/matches",
        json={
            "client_id": fake_id,
            "provider_id": provider_id,
            "strategy": "greedy",
            "score": 0.5,
        },
    )
    assert bad_client.status_code == 404

    bad_provider = client.post(
        "/api/v1/matches",
        json={
            "client_id": client_id,
            "provider_id": fake_id,
            "strategy": "greedy",
            "score": 0.5,
        },
    )
    assert bad_provider.status_code == 404
