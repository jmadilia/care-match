from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_client_crud() -> None:
    payload = {
        "name": "Test Client",
        "state": "CA",
        "insurance_payer": "Aetna",
        "needed_specialties": ["anxiety", "trauma"],
        "preferred_modality": "video",
        "preferred_language": "en",
        "urgency": "ELEVATED",
    }

    create_res = client.post("/api/v1/clients", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    client_id = created["id"]
    assert created["name"] == payload["name"]
    assert created["urgency"] == "ELEVATED"

    list_res = client.get("/api/v1/clients")
    assert list_res.status_code == 200
    assert any(c["id"] == client_id for c in list_res.json())

    get_res = client.get(f"/api/v1/clients/{client_id}")
    assert get_res.status_code == 200
    assert get_res.json()["insurance_payer"] == payload["insurance_payer"]

    patch_res = client.patch(f"/api/v1/clients/{client_id}", json={"urgency": "URGENT"})
    assert patch_res.status_code == 200
    assert patch_res.json()["urgency"] == "URGENT"

    delete_res = client.delete(f"/api/v1/clients/{client_id}")
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/v1/clients/{client_id}")
    assert missing_res.status_code == 404


def test_client_create_rejects_invalid_urgency() -> None:
    payload = {
        "name": "Bad Urgency Client",
        "state": "NY",
        "insurance_payer": "Cigna",
        "needed_specialties": ["depression"],
        "preferred_modality": "in_person",
        "preferred_language": "en",
        "urgency": "NOT_A_REAL_LEVEL",
    }

    res = client.post("/api/v1/clients", json=payload)
    assert res.status_code == 422
