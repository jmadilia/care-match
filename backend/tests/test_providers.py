from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_crud() -> None:
    payload = {
        "name": "Dr. Test Provider",
        "license_states": ["CA", "NY"],
        "specialties": ["anxiety", "trauma"],
        "modalities": ["video"],
        "languages": ["en"],
        "insurance_panels": ["Aetna"],
        "weekly_capacity": 20,
    }

    create_res = client.post("/api/v1/providers", json=payload)
    assert create_res.status_code == 201
    provider = create_res.json()
    provider_id = provider["id"]
    assert provider["name"] == payload["name"]

    list_res = client.get("/api/v1/providers")
    assert list_res.status_code == 200
    assert any(p["id"] == provider_id for p in list_res.json())

    get_res = client.get(f"/api/v1/providers/{provider_id}")
    assert get_res.status_code == 200

    patch_res = client.patch(f"/api/v1/providers/{provider_id}", json={"weekly_capacity": 25})
    assert patch_res.status_code == 200
    assert patch_res.json()["weekly_capacity"] == 25

    delete_res = client.delete(f"/api/v1/providers/{provider_id}")
    assert delete_res.status_code == 204

    missing_res = client.get(f"/api/v1/providers/{provider_id}")
    assert missing_res.status_code == 404
