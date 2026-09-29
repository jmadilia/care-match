from fastapi.testclient import TestClient


def test_provider_crud(api: TestClient) -> None:
    payload = {
        "name": "Dr. Test Provider",
        "license_states": ["CA", "NY"],
        "specialties": ["anxiety", "trauma"],
        "modalities": ["video"],
        "languages": ["en"],
        "insurance_panels": ["Aetna"],
        "weekly_capacity": 20,
    }

    create_res = api.post("/api/v1/providers", json=payload)
    assert create_res.status_code == 201
    provider = create_res.json()
    provider_id = provider["id"]
    assert provider["name"] == payload["name"]

    list_res = api.get("/api/v1/providers")
    assert list_res.status_code == 200
    assert any(p["id"] == provider_id for p in list_res.json())

    get_res = api.get(f"/api/v1/providers/{provider_id}")
    assert get_res.status_code == 200

    patch_res = api.patch(f"/api/v1/providers/{provider_id}", json={"weekly_capacity": 25})
    assert patch_res.status_code == 200
    assert patch_res.json()["weekly_capacity"] == 25

    delete_res = api.delete(f"/api/v1/providers/{provider_id}")
    assert delete_res.status_code == 204

    missing_res = api.get(f"/api/v1/providers/{provider_id}")
    assert missing_res.status_code == 404
