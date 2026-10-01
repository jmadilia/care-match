from fastapi.testclient import TestClient


def _create_client(api: TestClient) -> str:
    payload = {
        "name": "Waitlist Client",
        "state": "CA",
        "insurance_payer": "Aetna",
        "needed_specialties": ["anxiety"],
        "preferred_modality": "video",
        "preferred_language": "en",
        "urgency": "ROUTINE",
    }
    res = api.post("/api/v1/clients", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_waitlist_entry_crud(api: TestClient) -> None:
    client_id = _create_client(api)

    create_res = api.post("/api/v1/waitlist-entries", json={"client_id": client_id})
    assert create_res.status_code == 201
    entry = create_res.json()
    entry_id = entry["id"]
    assert entry["client_id"] == client_id
    assert entry["status"] == "WAITING"
    assert entry["resolved_at"] is None

    list_res = api.get("/api/v1/waitlist-entries", params={"client_id": client_id})
    assert list_res.status_code == 200
    assert any(e["id"] == entry_id for e in list_res.json())

    get_res = api.get(f"/api/v1/waitlist-entries/{entry_id}")
    assert get_res.status_code == 200

    missing_res = api.get("/api/v1/waitlist-entries/00000000-0000-0000-0000-000000000000")
    assert missing_res.status_code == 404


def test_waitlist_entry_resolution_sets_resolved_at(api: TestClient) -> None:
    client_id = _create_client(api)
    create_res = api.post("/api/v1/waitlist-entries", json={"client_id": client_id})
    entry_id = create_res.json()["id"]

    patch_res = api.patch(f"/api/v1/waitlist-entries/{entry_id}", json={"status": "MATCHED"})
    assert patch_res.status_code == 200
    resolved = patch_res.json()
    assert resolved["status"] == "MATCHED"
    assert resolved["resolved_at"] is not None


def test_waitlist_entry_create_rejects_unknown_client(api: TestClient) -> None:
    res = api.post(
        "/api/v1/waitlist-entries",
        json={"client_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert res.status_code == 404


def test_waitlist_entry_create_ignores_status_field(api: TestClient) -> None:
    # status isn't part of the create schema at all, new entries always start WAITING
    client_id = _create_client(api)
    res = api.post(
        "/api/v1/waitlist-entries", json={"client_id": client_id, "status": "MATCHED"}
    )
    assert res.status_code == 201
    assert res.json()["status"] == "WAITING"
